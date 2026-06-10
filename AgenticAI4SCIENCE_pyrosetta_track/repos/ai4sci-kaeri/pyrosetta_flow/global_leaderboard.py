"""global_leaderboard.py — run 간 영속되는 글로벌 선택성 리더보드 (2026-06-10).

무한 발굴 엔진의 "기억": 매 epoch(run)의 선택성 측정(Δmargin)을 디스크에 누적해
다음 epoch이 ① 이미 도킹한 서열 재도킹 회피 ② in-loop 리더보드 warm-start
③ 역대 best Δmargin 단조 추적 에 사용한다. experiment_log.jsonl(서열 dedup·bandit)
과 상보 — 이쪽은 **선택성 축** 전담.

Δmargin = selectivity_margin − native_margin(home-advantage). >0 = native 초과 선택성.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_FILENAME = "global_selectivity_leaderboard.json"

_NATIVE_MARGIN_CACHE: Optional[float] = None


def _coerce_float(v: Any) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _native_margin() -> Optional[float]:
    """native SST-14 동일프로토콜 selectivity_margin (home-advantage 기준). Δ backfill 용."""
    global _NATIVE_MARGIN_CACHE
    if _NATIVE_MARGIN_CACHE is not None:
        return _NATIVE_MARGIN_CACHE
    path = Path(__file__).resolve().parents[1] / "data/somatostatin_receptor/curated/native_selectivity_baseline.json"
    try:
        if path.exists():
            _NATIVE_MARGIN_CACHE = float(json.loads(path.read_text()).get("margin"))
    except Exception:
        pass
    return _NATIVE_MARGIN_CACHE


class GlobalSelectivityLeaderboard:
    """선택성 측정 후보의 run-간 누적 리더보드. 서열 dedup, Δmargin 내림차순 top-N."""

    def __init__(self, capacity: int = 50):
        self.capacity = capacity
        self.entries: List[Dict[str, Any]] = []   # dedup-by-sequence, Δmargin desc
        self.screened_seqs: set = set()
        self.n_ingested_total: int = 0            # 누적 측정 횟수(중복 포함)

    # ------------------------------------------------------------------ I/O
    @classmethod
    def load(cls, path: Path, capacity: int = 50) -> "GlobalSelectivityLeaderboard":
        lb = cls(capacity=capacity)
        try:
            if Path(path).exists():
                data = json.loads(Path(path).read_text(encoding="utf-8"))
                lb.entries = data.get("entries", []) or []
                lb.screened_seqs = set(data.get("screened_seqs", []) or [])
                lb.n_ingested_total = int(data.get("n_ingested_total", len(lb.entries)))
                # 로드분도 screened 에 반영 (방어적)
                for e in lb.entries:
                    if e.get("sequence"):
                        lb.screened_seqs.add(e["sequence"])
        except Exception:
            pass  # 손상 시 빈 리더보드로 시작 (fail-open: 발굴은 계속)
        return lb

    def save(self, path: Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "capacity": self.capacity,
            "best_delta_margin": self.best_delta(),
            "n_unique": len(self.entries),
            "n_screened_unique": len(self.screened_seqs),
            "n_ingested_total": self.n_ingested_total,
            "entries": self.entries,
            "screened_seqs": sorted(self.screened_seqs),
        }
        tmp = Path(str(path) + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)   # atomic

    # ------------------------------------------------------------- mutation
    def add_measurement(self, seq: str, ddg: Optional[float], margin: Optional[float],
                        delta_margin: Optional[float], extra: Optional[Dict[str, Any]] = None,
                        run_id: str = "", ts: str = "") -> bool:
        """선택성 1건 반영. 신규 best 갱신이면 True. 동일 서열은 더 좋은 Δ만 유지."""
        if not seq or margin is None:
            return False
        self.n_ingested_total += 1
        self.screened_seqs.add(seq)
        dm = _coerce_float(delta_margin)
        if dm is None:  # post-loop 경로 등 Δ 미계산 시 native baseline 으로 backfill
            nat = _native_margin()
            m = _coerce_float(margin)
            if nat is not None and m is not None:
                dm = round(m - nat, 4)
        rec = {
            "sequence": seq,
            "ddg": _coerce_float(ddg),
            "margin": _coerce_float(margin),
            "delta_margin": dm,
            "hc50": (extra or {}).get("pepadmet_hc50"),
            "hc50_vs_native": (extra or {}).get("hc50_vs_native"),
            "more_toxic_than_native": (extra or {}).get("more_toxic_than_native"),
            "run_id": run_id,
            "ts": ts,
        }
        prev_best = self.best_delta()
        existing = next((e for e in self.entries if e["sequence"] == seq), None)
        if existing is not None:
            # 같은 서열이면 Δmargin 더 높은 측정으로만 갱신
            if dm is not None and (existing.get("delta_margin") is None or dm > existing["delta_margin"]):
                self.entries.remove(existing)
                self.entries.append(rec)
        else:
            self.entries.append(rec)
        self._resort()
        new_best = self.best_delta()
        return (new_best is not None) and (prev_best is None or new_best > prev_best + 1e-9)

    def ingest_artifacts(self, artifacts: Dict[str, Any]) -> Dict[str, Any]:
        """한 run 의 artifacts(dict)에서 선택성 측정을 모두 수집. 반환: 요약."""
        run_id = artifacts.get("run_id", "")
        n_new = 0
        improved = False

        def _scan(cand_list):
            nonlocal n_new, improved
            for c in cand_list or []:
                es = c.get("extra_scores", {}) or {}
                margin = es.get("selectivity_margin")
                if margin is None:
                    continue
                dm = es.get("delta_margin")
                if dm is None:  # post-loop 경로는 Δ 미계산 — margin 만 있을 때 그대로 둠(None)
                    pass
                if self.add_measurement(
                    seq=c.get("sequence", ""), ddg=c.get("ddg"), margin=margin,
                    delta_margin=dm, extra=es, run_id=run_id, ts=c.get("ts", ""),
                ):
                    improved = True
                n_new += 1

        for it in artifacts.get("iterations", []):
            _scan(it.get("candidates", []))
        _scan(artifacts.get("final_candidates", []))
        return {"n_measurements": n_new, "improved_best": improved,
                "best_delta_margin": self.best_delta(), "n_unique": len(self.entries)}

    def _resort(self) -> None:
        self.entries.sort(
            key=lambda e: (-(e["delta_margin"] if e.get("delta_margin") is not None else -1e9),
                           e.get("ddg") if e.get("ddg") is not None else 1e9)
        )
        self.entries = self.entries[: self.capacity]

    # --------------------------------------------------------------- query
    def best_delta(self) -> Optional[float]:
        ds = [e["delta_margin"] for e in self.entries if e.get("delta_margin") is not None]
        return max(ds) if ds else None

    def top(self, n: int = 10) -> List[Dict[str, Any]]:
        return self.entries[:n]

    def count_passing(self, ddg_max: float = -15.0) -> int:
        """엄격 기준 충족: Δmargin>0 & ddG≤ddg_max & 독성≤native.

        독성은 `more_toxic_than_native is False`(명시적 측정)만 통과로 인정한다.
        None(미측정·부트스트랩 stale)은 보수적으로 불통과 — 가짜 통과 판정 방지(fail-closed).
        """
        n = 0
        for e in self.entries:
            dm = e.get("delta_margin"); ddg = e.get("ddg")
            tox_ok = e.get("more_toxic_than_native") is False
            if dm is not None and dm > 0 and ddg is not None and ddg <= ddg_max and tox_ok:
                n += 1
        return n

    def warm_start_payload(self) -> Dict[str, Any]:
        """in-loop SelectivityLeaderboard 에 넘길 warm-start 데이터."""
        return {"screened_seqs": set(self.screened_seqs), "entries": list(self.entries)}
