"""continuous.py — 무한 발굴 오케스트레이터 (2026-06-10).

기존 단발 run(run_pyrosetta_agentic_mutdock_flow) 위에 얇은 epoch 루프를 씌워
**STOP 파일이 생길 때까지 무한 발굴**한다. run 간 학습은 experiment_log.jsonl(서열
dedup·bandit) + global_selectivity_leaderboard.json(Δmargin)으로 누적된다.

설계 원칙
- **사람이 조절**: control 파일(JSON)을 매 epoch 시작 시 다시 읽어 knobs 반영(재시작 불필요).
- **STOP 파일**: 존재하면 현재 epoch까지 마치고 graceful 종료.
- **수렴→다양성 탈출**: 글로벌 best Δmargin 이 patience epoch 동안 정체하면 변이 다양성↑
  (max_random_mutations 상향, seed 교체)로 local optimum 탈출. 개선 시 base 로 리셋.
- **진행 가시화**: status 파일에 epoch·역대 best·통과 후보 수·다양성 레벨 기록.
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, Optional

from .schema import FlowConfig
from .global_leaderboard import GlobalSelectivityLeaderboard


# control 파일에서 override 허용하는 FlowConfig 필드 (안전 화이트리스트)
_CONTROL_FIELDS = {
    "n_candidates", "max_iterations", "top_k", "selectivity_max_per_iter",
    "max_random_mutations", "rosetta_ddg_max", "objective_mode",
    "design_positions", "validation_n_trials", "selectivity_top_k",
}


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _apply_control(base: FlowConfig, control: Dict[str, Any]) -> FlowConfig:
    """control 파일의 화이트리스트 필드만 base config 에 덮어쓴다."""
    overrides = {k: v for k, v in control.items() if k in _CONTROL_FIELDS}
    return replace(base, **overrides) if overrides else base


class DiversityPolicy:
    """글로벌 best Δmargin 정체 시 변이 다양성을 끌어올려 local optimum 탈출."""

    def __init__(self, patience: int = 3, base_mutations: int = 3,
                 max_mutations_cap: int = 6):
        self.patience = patience
        self.base_mutations = base_mutations
        self.max_mutations_cap = max_mutations_cap
        self.level = 0                       # 다양성 레벨 (0=base)
        self._best: Optional[float] = None
        self._stale = 0

    def update(self, global_best: Optional[float]) -> Dict[str, Any]:
        """epoch 결과 반영 후 다음 epoch 다양성 파라미터 반환."""
        improved = False
        if global_best is not None and (self._best is None or global_best > self._best + 1e-9):
            self._best = global_best
            self._stale = 0
            self.level = 0                   # 개선 → 탐색 집중(base 복귀)
            improved = True
        else:
            self._stale += 1
            if self._stale >= self.patience:
                self.level += 1              # 정체 → 다양성 단계 상승
                self._stale = 0
        mutations = min(self.max_mutations_cap, self.base_mutations + self.level)
        return {"improved": improved, "level": self.level, "stale": self._stale,
                "max_random_mutations": mutations}


def run_continuous_discovery(
    base_config: FlowConfig,
    repo_root: Path,
    control_path: Path,
    stop_path: Path,
    status_path: Path,
    max_epochs: Optional[int] = None,
    poll_on_stop: bool = False,
    epoch_pause_s: float = 0.0,
) -> Dict[str, Any]:
    """STOP 파일이 생길 때까지(또는 max_epochs 도달까지) 무한 발굴.

    Args:
        base_config: 기준 FlowConfig (inloop_selectivity 강제 ON).
        control_path: 사람이 조절하는 JSON knobs (매 epoch 재로드).
        stop_path: 이 파일이 존재하면 graceful 종료.
        status_path: 진행 상황 기록 파일.
        max_epochs: None 이면 무한. 정수면 그만큼만.
        poll_on_stop: True 면 STOP 제거 시 재개를 위해 대기(미사용 기본).
    """
    from . import run_pyrosetta_agentic_mutdock_flow  # 지연 import (무거운 의존성)

    # 무한 엔진: in-loop 선택성 필수 + native baseline 첫 epoch만 측정 후 캐시 재사용
    base_config = replace(base_config, inloop_selectivity=True, reuse_baseline=True)
    global_lb_path = repo_root / base_config.output_dir / "global_selectivity_leaderboard.json"

    control0 = _read_json(control_path)
    policy = DiversityPolicy(
        patience=int(control0.get("patience", 3)),
        base_mutations=int(control0.get("base_mutations", base_config.max_random_mutations)),
        max_mutations_cap=int(control0.get("max_mutations_cap", 6)),
    )

    epoch = 0
    history = []
    t0 = time.time()
    stop_reason = "max_epochs"

    while True:
        if stop_path.exists():
            stop_reason = "stop_file"
            print(f"[continuous] STOP 파일 감지({stop_path}) — graceful 종료", file=sys.stderr)
            break
        if max_epochs is not None and epoch >= max_epochs:
            stop_reason = "max_epochs"
            break

        epoch += 1
        control = _read_json(control_path)            # 매 epoch 재로드 (사람 조절 반영)
        cfg = _apply_control(base_config, control)

        # 다양성: epoch 마다 새 seed 로 탐색 영역 이동 + 직전 정책이 정한 변이 수 적용
        cfg = replace(cfg, seed_base=base_config.seed_base + epoch * 1000)
        # 직전 epoch 결과로 결정된 다양성 레벨 적용
        if history:
            cfg = replace(cfg, max_random_mutations=history[-1]["next_max_mutations"])

        # 선택적 목표-도달 자동 정지
        target = control.get("target_pass_count")
        if target and control.get("stop_on_target", False):
            lb_now = GlobalSelectivityLeaderboard.load(global_lb_path)
            if lb_now.count_passing(ddg_max=cfg.rosetta_ddg_max) >= int(target):
                stop_reason = "target_reached"
                print(f"[continuous] 목표 도달(통과 {target}건) — 종료", file=sys.stderr)
                epoch -= 1
                break

        print(f"\n[continuous] ===== EPOCH {epoch} 시작 (seed={cfg.seed_base}, "
              f"mut≤{cfg.max_random_mutations}, n_cand={cfg.n_candidates}, "
              f"max_iter={cfg.max_iterations}) =====", file=sys.stderr)

        epoch_t0 = time.time()
        try:
            artifacts = run_pyrosetta_agentic_mutdock_flow(cfg)
            ran_ok = True
            err = ""
        except Exception as exc:  # epoch 실패는 무한 루프를 죽이지 않는다
            ran_ok = False
            err = repr(exc)
            print(f"[continuous] EPOCH {epoch} 실패(continue): {err}", file=sys.stderr)

        # 글로벌 리더보드(runner 가 이미 저장) 재로드 → 진행 판정
        lb = GlobalSelectivityLeaderboard.load(global_lb_path)
        global_best = lb.best_delta()
        decision = policy.update(global_best)

        rec = {
            "epoch": epoch,
            "seed_base": cfg.seed_base,
            "max_random_mutations": cfg.max_random_mutations,
            "ran_ok": ran_ok,
            "error": err,
            "global_best_delta": global_best,
            "n_unique_screened": len(lb.entries),
            "passing_count": lb.count_passing(ddg_max=cfg.rosetta_ddg_max),
            "diversity_level": decision["level"],
            "stale_epochs": decision["stale"],
            "improved": decision["improved"],
            "next_max_mutations": decision["max_random_mutations"],
            "epoch_seconds": round(time.time() - epoch_t0, 1),
        }
        history.append(rec)

        _atomic_write_json(status_path, {
            "running": True,
            "epochs_done": epoch,
            "elapsed_seconds": round(time.time() - t0, 1),
            "global_best_delta_margin": global_best,
            "passing_count": rec["passing_count"],
            "diversity_level": decision["level"],
            "top": lb.top(10),
            "last_epoch": rec,
            "history": history[-50:],
        })
        print(f"[continuous] EPOCH {epoch} 완료: 역대 best Δ={global_best}, "
              f"통과 {rec['passing_count']}건, 다양성 레벨={decision['level']} "
              f"(개선={decision['improved']}), {rec['epoch_seconds']}s", file=sys.stderr)

        if epoch_pause_s > 0:
            time.sleep(epoch_pause_s)

    # 종료 상태 기록
    lb = GlobalSelectivityLeaderboard.load(global_lb_path)
    final = {
        "running": False,
        "stop_reason": stop_reason,
        "epochs_done": epoch,
        "elapsed_seconds": round(time.time() - t0, 1),
        "global_best_delta_margin": lb.best_delta(),
        "passing_count": lb.count_passing(ddg_max=base_config.rosetta_ddg_max),
        "top": lb.top(10),
        "history": history,
    }
    _atomic_write_json(status_path, final)
    print(f"[continuous] 종료({stop_reason}): {epoch} epochs, 역대 best Δ={lb.best_delta()}, "
          f"통과 {final['passing_count']}건", file=sys.stderr)
    return final
