"""
strategy_ab_experiment.py
=========================
Phase 5: 4 strategy A/B 비교 실험 스크립트

동일 seed (SST-14 AGCKNFFWKTFTSC) + 동일 fixed_positions + 동일 max_variants=50으로
4가지 mutation strategy를 순차 실행하고, 각 strategy별 결과와 메트릭을 저장한다.

출력:
    runs_local/strategy_ab/{strategy_name}/variants.json  — Step03bOutput.to_dict()
    runs_local/strategy_ab/{strategy_name}/elapsed.json   — 실행 시간 + 환경 정보

Usage:
    python pipeline_local/scripts/strategy_ab_experiment.py
    python pipeline_local/scripts/strategy_ab_experiment.py --quick   # max_variants=5 smoke test
    python pipeline_local/scripts/strategy_ab_experiment.py --out-dir runs_local/strategy_ab
    python pipeline_local/scripts/strategy_ab_experiment.py --report  # 실험 후 보고서도 생성
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import platform
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# 프로젝트 루트를 sys.path에 추가 (스크립트 직접 실행 지원)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from pipeline_local.schemas.io_schemas import Step03bOutput, VariantEntry
from pipeline_local.strategies.blosum import (
    compute_blosum_distance,
    validate_constraints,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CUDA 디바이스 헬퍼
# ---------------------------------------------------------------------------

def _resolve_cuda_device(requested: str) -> str:
    """CUDA_VISIBLE_DEVICES 환경에서 안전한 디바이스 문자열을 반환한다.

    CUDA_VISIBLE_DEVICES 제약 내에서 논리 인덱스 0-based를 사용하므로
    요청 디바이스가 가용 범위를 초과하면 "cuda:0" 으로 폴백한다.
    CUDA 자체가 없으면 "cpu"를 반환한다.

    Args:
        requested: 요청 디바이스 문자열 (예: "cuda:0", "cuda:2", "cpu")

    Returns:
        실제 사용할 디바이스 문자열
    """
    if not requested.startswith("cuda"):
        return requested
    try:
        import torch
        if not torch.cuda.is_available():
            return "cpu"
        n_devices = torch.cuda.device_count()
        if n_devices == 0:
            return "cpu"
        # 논리 인덱스 파싱
        if ":" in requested:
            idx = int(requested.split(":", 1)[1])
        else:
            idx = 0
        if idx >= n_devices:
            logger.warning(
                "[AB] 요청 디바이스 %s 가용 범위 초과 (device_count=%d), cuda:0 사용",
                requested, n_devices,
            )
            return "cuda:0"
        return f"cuda:{idx}"
    except Exception:
        return "cpu"


# ---------------------------------------------------------------------------
# 실험 상수
# ---------------------------------------------------------------------------

SEED_SEQUENCE = "AGCKNFFWKTFTSC"
FIXED_POSITIONS: Dict[int, str] = {
    3: "C",
    7: "F",
    8: "W",
    9: "K",
    10: "T",
    14: "C",
}
STRATEGY_NAMES: List[str] = ["blosum", "esm_scan", "proteinmpnn", "dual_b1_b2"]


# ---------------------------------------------------------------------------
# 설정 빌더
# ---------------------------------------------------------------------------

def _build_config(max_variants: int) -> Dict[str, Any]:
    """공통 실험 설정 dict를 반환한다.

    모든 strategy가 동일한 seed/fixed_positions/max_variants를 사용한다.
    """
    return {
        "reference_peptide": {
            "sequence": SEED_SEQUENCE,
        },
        "approach_b": {
            "seed_sequence": SEED_SEQUENCE,
            "fixed_positions": FIXED_POSITIONS,
            "max_variants": max_variants,
            "min_blosum_score": 0,
            "max_mutations_per_variant": 3,
            "hydrophobicity_max_delta": 2.0,
            "strategy": "random",
            # ESM-Scan 옵션
            # fair-esm 설치 시: "esm2_t33_650M_UR50D" (esm.pretrained.* API)
            # transformers 전용 환경: "facebook/esm2_t33_650M_UR50D"
            # bio-tools 환경은 fair-esm이 우선 로드되므로 bare name 사용.
            # CUDA_VISIBLE_DEVICES=2,3 환경에서 논리 디바이스 인덱스는 0-based:
            #   cuda:0 → physical GPU 2, cuda:1 → physical GPU 3
            "esm_scan_opts": {
                "model": "esm2_t33_650M_UR50D",
                "device": _resolve_cuda_device("cuda:0"),
                "score_quantile": 0.7,
                "max_mutations_per_variant": 3,
            },
            # ProteinMPNN 옵션 (peptide_only 모드)
            # ligandmpnn subprocess는 별도 env에서 실행되므로 CUDA_VISIBLE_DEVICES 재설정
            "proteinmpnn_opts": {
                "mode": "peptide_only",
                "num_seq_per_target": max(max_variants * 2, 20),
                "sampling_temperature": 0.1,
                "device": _resolve_cuda_device("cuda:0"),
            },
        },
    }


# ---------------------------------------------------------------------------
# 메트릭 계산
# ---------------------------------------------------------------------------

def _hamming_distance(seq1: str, seq2: str) -> int:
    """두 시퀀스 간 Hamming distance를 계산한다."""
    min_len = min(len(seq1), len(seq2))
    return sum(1 for a, b in zip(seq1[:min_len], seq2[:min_len]) if a != b)


def compute_metrics(
    output: Step03bOutput,
    seed: str,
    fixed_positions: Dict[int, str],
) -> Dict[str, Any]:
    """strategy 출력으로부터 비교 메트릭을 계산한다.

    Args:
        output:          Step03bOutput
        seed:            원본 시퀀스
        fixed_positions: 고정 위치 매핑 (1-indexed)

    Returns:
        Dict with keys:
          unique_sequences, blosum_mean, fixed_preserved_count, fixed_violations,
          fixed_preservation_rate, hamming_mean, hamming_median, hamming_max,
          hamming_distribution
    """
    variants: List[VariantEntry] = output.variants
    n = len(variants)

    if n == 0:
        return {
            "unique_sequences": 0,
            "blosum_mean": None,
            "fixed_preserved_count": 0,
            "fixed_violations": 0,
            "fixed_preservation_rate": None,
            "hamming_mean": None,
            "hamming_median": None,
            "hamming_max": None,
            "hamming_distribution": [],
        }

    # 고유 시퀀스 수
    unique_seqs = len({v.sequence for v in variants})

    # BLOSUM score 평균 (평가 전용 — 모든 strategy에 동일 척도 적용)
    blosum_scores = [
        compute_blosum_distance(v.sequence, seed)
        for v in variants
    ]
    blosum_mean = sum(blosum_scores) / len(blosum_scores)

    # fixed_positions 보존률
    preserved_count = sum(
        1 for v in variants if validate_constraints(v.sequence, fixed_positions)
    )
    violations = n - preserved_count
    preservation_rate = preserved_count / n if n > 0 else None

    # Hamming distance 분포
    hamming_dists = [_hamming_distance(v.sequence, seed) for v in variants]
    hamming_sorted = sorted(hamming_dists)
    hamming_mean = sum(hamming_sorted) / len(hamming_sorted)
    mid = len(hamming_sorted) // 2
    if len(hamming_sorted) % 2 == 0:
        hamming_median = (hamming_sorted[mid - 1] + hamming_sorted[mid]) / 2
    else:
        hamming_median = float(hamming_sorted[mid])
    hamming_max = max(hamming_sorted)

    return {
        "unique_sequences": unique_seqs,
        "blosum_mean": round(blosum_mean, 4),
        "fixed_preserved_count": preserved_count,
        "fixed_violations": violations,
        "fixed_preservation_rate": round(preservation_rate, 6) if preservation_rate is not None else None,
        "hamming_mean": round(hamming_mean, 4),
        "hamming_median": round(hamming_median, 4),
        "hamming_max": int(hamming_max),
        "hamming_distribution": hamming_sorted,
    }


# ---------------------------------------------------------------------------
# 단일 strategy 실행
# ---------------------------------------------------------------------------

def run_strategy(
    strategy_name: str,
    config: Dict[str, Any],
    out_dir: str,
) -> Dict[str, Any]:
    """단일 strategy를 실행하고 결과를 저장한다.

    validate_env() 실패 시 skipped 결과를 반환한다.

    Args:
        strategy_name: "blosum" | "esm_scan" | "proteinmpnn" | "dual_b1_b2"
        config:        실험 설정 dict
        out_dir:       결과 저장 루트 디렉토리

    Returns:
        {
          "strategy": str,
          "status": "ok" | "skipped" | "error",
          "reason": str | None,
          "elapsed_sec": float,
          "metrics": Dict | None,
          "variants_path": str | None,
          "elapsed_path": str | None,
        }
    """
    from pipeline_local.strategies.registry import get_strategy

    strategy_dir = os.path.join(out_dir, strategy_name)
    os.makedirs(strategy_dir, exist_ok=True)

    result: Dict[str, Any] = {
        "strategy": strategy_name,
        "status": "ok",
        "reason": None,
        "elapsed_sec": 0.0,
        "metrics": None,
        "variants_path": None,
        "elapsed_path": None,
    }

    # 1. strategy 인스턴스 생성
    try:
        strategy = get_strategy(strategy_name)
    except Exception as exc:
        result["status"] = "error"
        result["reason"] = f"strategy 로드 실패: {exc}"
        logger.error("[AB] %s 로드 실패: %s", strategy_name, exc)
        return result

    # 2. validate_env
    try:
        env_ok, env_err = strategy.validate_env()
    except Exception as exc:
        result["status"] = "error"
        result["reason"] = f"validate_env 예외: {exc}"
        logger.error("[AB] %s validate_env 예외: %s", strategy_name, exc)
        return result

    if not env_ok:
        result["status"] = "skipped"
        result["reason"] = env_err
        logger.warning("[AB] %s SKIPPED: %s", strategy_name, env_err)
        # skipped.json 저장
        skipped_payload = {"skipped": True, "reason": env_err}
        skip_path = os.path.join(strategy_dir, "variants.json")
        with open(skip_path, "w", encoding="utf-8") as f:
            json.dump(skipped_payload, f, ensure_ascii=False, indent=2)
        result["variants_path"] = skip_path
        return result

    # 3. generate 실행 (wall clock 측정)
    logger.info("[AB] %s 시작", strategy_name)
    t0 = time.perf_counter()
    try:
        output: Step03bOutput = strategy.generate(config)
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        result["status"] = "error"
        result["reason"] = f"generate 실패: {exc}"
        result["elapsed_sec"] = round(elapsed, 3)
        logger.error("[AB] %s generate 실패 (%.1fs): %s", strategy_name, elapsed, exc)
        return result

    elapsed = time.perf_counter() - t0
    result["elapsed_sec"] = round(elapsed, 3)
    logger.info("[AB] %s 완료 (%.1fs): %d 변이체", strategy_name, elapsed, output.total_generated)

    # 4. 메트릭 계산
    max_variants = config.get("approach_b", {}).get("max_variants", 50)
    metrics = compute_metrics(output, SEED_SEQUENCE, FIXED_POSITIONS)
    metrics["total_generated"] = output.total_generated
    metrics["max_variants"] = max_variants
    result["metrics"] = metrics

    # 5. variants.json 저장
    variants_path = os.path.join(strategy_dir, "variants.json")
    with open(variants_path, "w", encoding="utf-8") as f:
        json.dump(output.to_dict(), f, ensure_ascii=False, indent=2)
    result["variants_path"] = variants_path

    # 6. elapsed.json 저장
    elapsed_payload = {
        "strategy": strategy_name,
        "elapsed_sec": result["elapsed_sec"],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "env": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "hostname": platform.node(),
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        },
        "config_summary": {
            "seed_sequence": SEED_SEQUENCE,
            "fixed_positions": {str(k): v for k, v in FIXED_POSITIONS.items()},
            "max_variants": max_variants,
        },
        "metrics": metrics,
    }
    elapsed_path = os.path.join(strategy_dir, "elapsed.json")
    with open(elapsed_path, "w", encoding="utf-8") as f:
        json.dump(elapsed_payload, f, ensure_ascii=False, indent=2)
    result["elapsed_path"] = elapsed_path

    return result


# ---------------------------------------------------------------------------
# 보고서 생성
# ---------------------------------------------------------------------------

def _format_row_value(val: Any, key: str) -> str:
    """보고서 표 셀 포매터."""
    if val is None:
        return "N/A"
    if key == "fixed_preservation_rate":
        return f"{val * 100:.1f}%"
    if key in ("blosum_mean", "hamming_mean", "hamming_median"):
        if isinstance(val, float):
            return f"{val:.2f}"
    if key == "elapsed_sec":
        return f"{val:.1f}s"
    return str(val)


def generate_report(
    results: List[Dict[str, Any]],
    report_path: str,
    max_variants: int,
) -> None:
    """A/B 비교 보고서 markdown을 생성한다.

    Args:
        results:     run_strategy 반환값 목록
        report_path: 보고서 파일 경로
        max_variants: 실험에 사용된 max_variants 값
    """
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: List[str] = []

    lines += [
        f"# 4 Strategy A/B 비교 — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "",
        f"*생성 시각: {now_str}*",
        "",
        "## 실험 조건",
        "",
        f"- seed: `{SEED_SEQUENCE}`",
        f"- fixed_positions: Cys3, FWKT(7-10), Cys14 — `{FIXED_POSITIONS}`",
        f"- max_variants: {max_variants}",
        "",
    ]

    # 결과 요약 표
    lines += [
        "## 결과 요약",
        "",
        "| Strategy | 상태 | unique seq | BLOSUM mean | fixed 보존 | hamming mean | hamming max | 시간 |",
        "|----------|------|-----------|-------------|------------|--------------|-------------|------|",
    ]

    for r in results:
        sname = r["strategy"]
        status = r["status"]
        if status == "skipped":
            reason_short = (r["reason"] or "")[:60]
            lines.append(
                f"| {sname} | SKIPPED ({reason_short}) | — | — | — | — | — | — |"
            )
        elif status == "error":
            reason_short = (r["reason"] or "")[:60]
            lines.append(
                f"| {sname} | ERROR ({reason_short}) | — | — | — | — | — | — |"
            )
        else:
            m = r.get("metrics") or {}
            unique_seq = m.get("unique_sequences", "N/A")
            blosum_mean = _format_row_value(m.get("blosum_mean"), "blosum_mean")
            fixed_rate = _format_row_value(m.get("fixed_preservation_rate"), "fixed_preservation_rate")
            violations = m.get("fixed_violations", 0)
            fixed_cell = fixed_rate if violations == 0 else f"{fixed_rate} ({violations} 위반)"
            hamming_mean = _format_row_value(m.get("hamming_mean"), "hamming_mean")
            hamming_max = m.get("hamming_max", "N/A")
            elapsed = _format_row_value(r.get("elapsed_sec"), "elapsed_sec")
            lines.append(
                f"| {sname} | OK | {unique_seq} | {blosum_mean} | {fixed_cell} | {hamming_mean} | {hamming_max} | {elapsed} |"
            )

    lines += ["", ""]

    # 상세 메트릭
    lines += ["## 상세 메트릭", ""]
    for r in results:
        sname = r["strategy"]
        lines.append(f"### {sname}")
        lines.append("")
        if r["status"] != "ok":
            lines.append(f"- 상태: {r['status']}")
            lines.append(f"- 사유: {r.get('reason', '')}")
        else:
            m = r.get("metrics") or {}
            lines.append(f"- 전체 생성 변이체: {m.get('total_generated', 'N/A')}")
            lines.append(f"- unique 시퀀스: {m.get('unique_sequences', 'N/A')}")
            lines.append(f"- BLOSUM score (seed 대비 평균): {m.get('blosum_mean', 'N/A')}")
            lines.append(f"- fixed_positions 보존: {m.get('fixed_preserved_count', 'N/A')}/{m.get('total_generated', 'N/A')} "
                         f"(위반 {m.get('fixed_violations', 0)}건)")
            lines.append(f"- hamming mean: {m.get('hamming_mean', 'N/A')}, median: {m.get('hamming_median', 'N/A')}, max: {m.get('hamming_max', 'N/A')}")
            lines.append(f"- 실행 시간: {r.get('elapsed_sec', 'N/A')}초")
        lines.append("")

    # 다양성 비교 분석 (텍스트)
    lines += [
        "## 다양성 비교",
        "",
    ]
    ok_results = [r for r in results if r["status"] == "ok"]
    if ok_results:
        # unique_sequences 기준 순위 (동점 시 hamming_mean 내림차순 — 탐색 공간 더 넓은 쪽 우선)
        ranked = sorted(
            ok_results,
            key=lambda r: (
                (r.get("metrics") or {}).get("unique_sequences", 0),
                (r.get("metrics") or {}).get("hamming_mean") or 0,
            ),
            reverse=True,
        )
        lines.append("**unique 시퀀스 수 (다양성) 순위:**")
        lines.append("")
        lines.append("> 동점 시 hamming distance mean(seed 대비 평균 변이 거리) 큰 쪽 우선 — 더 넓은 탐색 공간")
        lines.append("")
        for i, r in enumerate(ranked, start=1):
            m = r.get("metrics") or {}
            lines.append(f"{i}. `{r['strategy']}` — {m.get('unique_sequences', 'N/A')} unique seqs, hamming mean {m.get('hamming_mean', 'N/A')}")
        lines.append("")

        # hamming distance 분포 요약
        lines.append("**hamming distance 분포 (seed 대비 변이 거리):**")
        lines.append("")
        lines.append("| Strategy | mean | median | max |")
        lines.append("|----------|------|--------|-----|")
        for r in ok_results:
            m = r.get("metrics") or {}
            lines.append(
                f"| {r['strategy']} | {m.get('hamming_mean', 'N/A')} | "
                f"{m.get('hamming_median', 'N/A')} | {m.get('hamming_max', 'N/A')} |"
            )
        lines.append("")

        # BLOSUM 점수 분포 설명
        lines.append("**BLOSUM score (seed 대비, 높을수록 보수적 변이):**")
        lines.append("")
        ranked_blosum = sorted(
            ok_results,
            key=lambda r: (r.get("metrics") or {}).get("blosum_mean") or -999,
            reverse=True,
        )
        for i, r in enumerate(ranked_blosum, start=1):
            m = r.get("metrics") or {}
            lines.append(f"{i}. `{r['strategy']}` — BLOSUM mean {m.get('blosum_mean', 'N/A')}")
        lines.append("")
    else:
        lines.append("실행된 strategy가 없어 다양성 비교를 수행할 수 없습니다.")
        lines.append("")

    # 권고 운영 strategy
    lines += [
        "## 권고 운영 Strategy",
        "",
    ]
    if ok_results:
        # 선정 기준: (1) fixed 위반 0건, (2) unique_sequences 최대, (3) blosum_mean 고려
        candidates = [
            r for r in ok_results
            if (r.get("metrics") or {}).get("fixed_violations", 1) == 0
        ]
        if not candidates:
            candidates = ok_results

        best = max(
            candidates,
            key=lambda r: (
                -(r.get("metrics") or {}).get("fixed_violations", 999),
                (r.get("metrics") or {}).get("unique_sequences", 0),
                (r.get("metrics") or {}).get("blosum_mean") or -999,
            ),
        )
        best_name = best["strategy"]
        best_m = best.get("metrics") or {}

        lines.append(f"**권고: `{best_name}`**")
        lines.append("")
        lines.append("선정 기준 (우선순위):")
        lines.append("")
        lines.append("1. fixed_positions 위반 0건 (pharmacophore guard 완전 통과)")
        lines.append("2. unique 시퀀스 수 최대 (탐색 공간 다양성)")
        lines.append("3. BLOSUM mean 상위 (진화적 타당성)")
        lines.append("")
        lines.append(f"`{best_name}` 선정 근거:")
        lines.append(f"- fixed 위반: {best_m.get('fixed_violations', 'N/A')}건")
        lines.append(f"- unique 시퀀스: {best_m.get('unique_sequences', 'N/A')}")
        lines.append(f"- BLOSUM mean: {best_m.get('blosum_mean', 'N/A')}")
        lines.append(f"- 실행 시간: {best.get('elapsed_sec', 'N/A')}초")
        lines.append("")

        # 목적별 권고
        lines.append("### 목적별 권고 (운영 시나리오별)")
        lines.append("")
        lines.append("| 시나리오 | 권고 strategy | 근거 |")
        lines.append("|---------|--------------|------|")
        # BLOSUM 기반 보수적 탐색
        blosum_best = max(ok_results, key=lambda r: (r.get("metrics") or {}).get("blosum_mean") or -999)
        # 다양성 기반 (hamming)
        hamming_best = max(ok_results, key=lambda r: (r.get("metrics") or {}).get("hamming_mean") or 0)
        # 속도 기반
        speed_best = min(ok_results, key=lambda r: r.get("elapsed_sec") or 999999)
        lines.append(
            f"| 진화적 보수성 (BLOSUM 높음) | `{blosum_best['strategy']}` | BLOSUM mean {(blosum_best.get('metrics') or {}).get('blosum_mean', 'N/A')} — seed와 유사한 변이, pharmacophore 보존 최강 |"
        )
        lines.append(
            f"| 탐색 공간 다양성 (hamming 높음) | `{hamming_best['strategy']}` | hamming mean {(hamming_best.get('metrics') or {}).get('hamming_mean', 'N/A')} — seed에서 멀리 탐색, 신규 스캐폴드 발견 가능성 높음 |"
        )
        lines.append(
            f"| GPU/인프라 없는 환경 | `blosum` | 의존성 없음, 실행 시간 {speed_best.get('elapsed_sec', 'N/A')}초 이하 |"
        )
        lines.append(
            "| 생물물리학적 근거 + 다양성 균형 | `esm_scan` | LM zero-shot으로 진화 허용 변이 추출, BLOSUM과 hamming 사이 균형점 |"
        )
        lines.append(
            "| 하류 도킹 실험 최대 커버리지 | `dual_b1_b2` | ProteinMPNN(구조 기반) + ESM-Scan(서열 기반) union — 두 방법론의 variant pool 합산 |"
        )
        lines.append("")
        lines.append("> **참고**: 이 권고는 현재 실행 결과의 정량적 지표만 기반으로 합니다.")
        lines.append("> GPU 가용성/환경 제약에 따라 일부 strategy가 SKIPPED된 경우 전체 비교가 불완전할 수 있습니다.")
        lines.append("> 하류 도킹(Boltz/FlexPepDock) 결과와 교차 검증하여 최종 strategy를 결정하는 것을 권고합니다.")
        lines.append("")
    else:
        lines.append(
            "성공적으로 실행된 strategy가 없어 권고를 생성할 수 없습니다. "
            "환경 의존성을 확인하세요."
        )
        lines.append("")

    # SKIPPED/ERROR 요약
    skipped = [r for r in results if r["status"] in ("skipped", "error")]
    if skipped:
        lines += [
            "## SKIPPED / ERROR 상세",
            "",
        ]
        for r in skipped:
            lines.append(f"### {r['strategy']} ({r['status'].upper()})")
            lines.append("")
            lines.append(f"- 사유: {r.get('reason', '알 수 없음')}")
            lines.append("")

    # 푸터
    lines += [
        "---",
        "",
        f"*자동 생성: `pipeline_local/scripts/strategy_ab_experiment.py` — {now_str}*",
    ]

    os.makedirs(os.path.dirname(os.path.abspath(report_path)), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info("[AB] 보고서 저장: %s", report_path)


# ---------------------------------------------------------------------------
# CLI 진입점
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="4 strategy A/B 비교 실험",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="smoke test 모드: max_variants=5",
    )
    parser.add_argument(
        "--max-variants",
        type=int,
        default=50,
        dest="max_variants",
        help="max_variants (기본값: 50)",
    )
    parser.add_argument(
        "--out-dir",
        default="runs_local/strategy_ab",
        dest="out_dir",
        help="결과 저장 루트 디렉토리 (기본값: runs_local/strategy_ab)",
    )
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=STRATEGY_NAMES,
        help="실행할 strategy 이름 목록 (기본값: 4개 전체)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="실험 후 비교 보고서를 _workspace/release/에 생성",
    )
    parser.add_argument(
        "--report-path",
        default="_workspace/release/sod-2026-05-19-strategy-ab-experiment.md",
        dest="report_path",
        help="보고서 저장 경로",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="DEBUG 레벨 로깅 출력",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """A/B 실험 메인 진입점.

    Returns:
        0 (성공) 또는 1 (일부 strategy 오류)
    """
    args = parse_args(argv)

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    max_variants = 5 if args.quick else args.max_variants
    logger.info("=== 4 Strategy A/B 실험 시작 ===")
    logger.info("seed: %s, fixed_positions: %s, max_variants: %d", SEED_SEQUENCE, FIXED_POSITIONS, max_variants)
    logger.info("실행 strategy: %s", args.strategies)

    # out_dir 절대 경로로 정규화
    out_dir = args.out_dir
    if not os.path.isabs(out_dir):
        out_dir = os.path.join(_PROJECT_ROOT, out_dir)

    config = _build_config(max_variants)
    all_results: List[Dict[str, Any]] = []

    for strategy_name in args.strategies:
        logger.info("--- %s 시작 ---", strategy_name)
        result = run_strategy(strategy_name, config, out_dir)
        all_results.append(result)
        status_str = result["status"].upper()
        if result["status"] == "ok":
            m = result.get("metrics") or {}
            logger.info(
                "[%s] %s: unique=%d, blosum_mean=%s, fixed_rate=%s, hamming_mean=%s, elapsed=%.1fs",
                status_str, strategy_name,
                m.get("unique_sequences", 0),
                m.get("blosum_mean"),
                m.get("fixed_preservation_rate"),
                m.get("hamming_mean"),
                result.get("elapsed_sec", 0),
            )
        else:
            logger.warning("[%s] %s: %s", status_str, strategy_name, result.get("reason", ""))

    # summary.json 저장
    summary_path = os.path.join(out_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "experiment": "4_strategy_ab",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "seed_sequence": SEED_SEQUENCE,
                "fixed_positions": {str(k): v for k, v in FIXED_POSITIONS.items()},
                "max_variants": max_variants,
                "results": all_results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    logger.info("summary 저장: %s", summary_path)

    # 보고서 생성
    report_path = args.report_path
    if args.report or not args.quick:
        if not os.path.isabs(report_path):
            report_path = os.path.join(_PROJECT_ROOT, report_path)
        generate_report(all_results, report_path, max_variants)

    # 종료 코드
    has_error = any(r["status"] == "error" for r in all_results)
    if has_error:
        logger.warning("일부 strategy에서 오류가 발생했습니다. 결과를 확인하세요.")
        return 1

    logger.info("=== A/B 실험 완료 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
