"""Analysis & SAR endpoints — 실험 로그 분석 결과 제공."""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from pipeline_local.backend.state import VALIDATION_DIR, EXP_LOG

router = APIRouter()


def _load_experiment_records() -> list:
    """experiment_log.jsonl 에서 레코드를 로드한다.

    원본 pyrosetta_flow.ranking 모듈을 재사용한다.
    """
    from pyrosetta_flow.ranking import load_experiment_records
    return load_experiment_records(EXP_LOG)


def _serve_or_compute_analysis(name: str) -> dict:
    """캐시된 분석 JSON이 있으면 반환, 없으면 재계산한다."""
    cached = VALIDATION_DIR / f"analysis_{name}.json"
    if cached.exists():
        try:
            return json.loads(cached.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    # 원본 AG_src backend.analysis 함수 재사용
    from backend.analysis import (
        convergence_by_iteration,
        cross_run_variance,
        rank_stability,
        gate_distribution,
        candidate_evidence,
        compute_full_analysis,
    )
    records = _load_experiment_records()
    funcs = {
        "convergence":        lambda: convergence_by_iteration(records),
        "cross_run_variance": lambda: cross_run_variance(records),
        "rank_stability":     lambda: rank_stability(records),
        "gate_distribution":  lambda: gate_distribution(records),
        "candidate_evidence": lambda: candidate_evidence(records),
        "summary":            lambda: compute_full_analysis(records),
    }
    fn = funcs.get(name)
    if fn is None:
        raise HTTPException(status_code=404, detail=f"알 수 없는 분석 항목: {name}")
    return fn()


@router.get("/analysis/convergence")
def convergence():
    return _serve_or_compute_analysis("convergence")


@router.get("/analysis/rank-stability")
def rank_stability():
    return _serve_or_compute_analysis("rank_stability")


@router.get("/analysis/gate-distribution")
def gate_distribution():
    return _serve_or_compute_analysis("gate_distribution")


@router.get("/analysis/candidate-evidence")
def candidate_evidence():
    return _serve_or_compute_analysis("candidate_evidence")


@router.get("/analysis/cross-run-variance")
def cross_run_variance():
    return _serve_or_compute_analysis("cross_run_variance")


@router.get("/analysis/summary")
def summary():
    return _serve_or_compute_analysis("summary")


@router.get("/analysis/sar-pssm")
def sar_pssm():
    """SAR PSSM 및 에피스타시스 쌍 분석 결과를 반환한다."""
    from backend.sar_analysis import compute_sar_pssm, compute_epistasis_pairs
    records = _load_experiment_records()
    result = compute_sar_pssm(records)
    result["epistasis_pairs"] = compute_epistasis_pairs(records)
    return result


@router.post("/analysis/refresh")
def refresh_all():
    """모든 분석 항목을 재계산하여 VALIDATION_DIR에 저장한다."""
    from backend.analysis import (
        convergence_by_iteration,
        cross_run_variance,
        rank_stability,
        gate_distribution,
        candidate_evidence,
        compute_full_analysis,
    )
    records = _load_experiment_records()
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    outputs = {
        "convergence":        convergence_by_iteration(records),
        "cross_run_variance": cross_run_variance(records),
        "rank_stability":     rank_stability(records),
        "gate_distribution":  gate_distribution(records),
        "candidate_evidence": candidate_evidence(records),
        "summary":            compute_full_analysis(records),
    }
    for name, data in outputs.items():
        path = VALIDATION_DIR / f"analysis_{name}.json"
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8",
        )
    return {"refreshed": list(outputs.keys()), "directory": str(VALIDATION_DIR)}
