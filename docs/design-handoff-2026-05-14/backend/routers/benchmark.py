"""
LLM Benchmark 라우터 — 5 sLLM × 3 flow 결과.

데이터 소스:
  llm_benchmark/analysis/*.json
  llm_benchmark/configs/v2_phase2_matrix.yaml

마운트:
  app.include_router(benchmark.router, prefix="/api/benchmark", tags=["benchmark"])
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from ..schemas.dashboard import (  # type: ignore
    BenchmarkResponse, BenchmarkCell, LLMSpec, FlowSpec,
)

router = APIRouter()


def _benchmark_root() -> Path:
    return Path(__file__).resolve().parents[3] / "llm_benchmark" / "analysis"


LLMS: list[LLMSpec] = [
    LLMSpec(id="qwen3-32b",               short="q32",  vram_gb=80),
    LLMSpec(id="qwen3-14b",               short="q14",  vram_gb=40),
    LLMSpec(id="qwen3-7b",                short="q7",   vram_gb=20),
    LLMSpec(id="gpt-oss-120b",            short="g120", vram_gb=240),
    LLMSpec(id="deepseek-r1-distill-32b", short="ds32", vram_gb=80),
]

FLOWS: list[FlowSpec] = [
    FlowSpec(id="sequential",    name="Sequential",    desc="P→B→Q→C→R 단방향"),
    FlowSpec(id="collaborative", name="Collaborative", desc="DebatingPlanner · 다중 합의"),
    FlowSpec(id="hierarchical",  name="Hierarchical",  desc="Orchestrator · 승인/통합"),
]

# Phase 별 결과 fallback (실제 JSON 없을 때).
# 실제 데이터는 llm_benchmark/analysis/phase{N}_summary.json 에서 로드.
_FALLBACK_MATRIX = {
    "qwen3-32b": {
        "sequential":    BenchmarkCell(pass_rate=87, time_min=38, candidates=12, t2=1, cost=1.0),
        "collaborative": BenchmarkCell(pass_rate=82, time_min=51, candidates=14, t2=1, cost=1.4),
        "hierarchical":  BenchmarkCell(pass_rate=78, time_min=49, candidates=11, t2=0, cost=1.5),
    },
    "qwen3-14b": {
        "sequential":    BenchmarkCell(pass_rate=81, time_min=32, candidates=10, t2=0, cost=0.5),
        "collaborative": BenchmarkCell(pass_rate=76, time_min=43, candidates=12, t2=0, cost=0.7),
        "hierarchical":  BenchmarkCell(pass_rate=71, time_min=41, candidates=9,  t2=0, cost=0.7),
    },
    "qwen3-7b": {
        "sequential":    BenchmarkCell(pass_rate=62, time_min=22, candidates=7,  t2=0, cost=0.25),
        "collaborative": BenchmarkCell(pass_rate=57, time_min=31, candidates=8,  t2=0, cost=0.35),
        "hierarchical":  BenchmarkCell(pass_rate=52, time_min=30, candidates=6,  t2=0, cost=0.36),
    },
    "gpt-oss-120b": {
        "sequential":    BenchmarkCell(pass_rate=90, time_min=58, candidates=13, t2=1, cost=2.8),
        "collaborative": BenchmarkCell(pass_rate=88, time_min=75, candidates=15, t2=2, cost=3.7),
        "hierarchical":  BenchmarkCell(pass_rate=84, time_min=71, candidates=12, t2=1, cost=3.8),
    },
    "deepseek-r1-distill-32b": {
        "sequential":    BenchmarkCell(pass_rate=79, time_min=42, candidates=10, t2=0, cost=1.1),
        "collaborative": BenchmarkCell(pass_rate=81, time_min=56, candidates=13, t2=1, cost=1.5),
        "hierarchical":  BenchmarkCell(pass_rate=73, time_min=53, candidates=10, t2=0, cost=1.6),
    },
}


@router.get("/results", response_model=BenchmarkResponse)
def benchmark_results(
    phase: Literal["Phase1", "Phase2", "Phase3", "V2"] = Query("V2"),
) -> BenchmarkResponse:
    """5 LLM × 3 flow 결과 매트릭스."""
    root = _benchmark_root()
    summary_path = root / f"{phase.lower()}_summary.json"

    if summary_path.exists():
        with summary_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        # TODO: 실제 JSON 구조에 맞춰 매핑
        matrix: dict[str, dict[str, BenchmarkCell]] = {}
        for llm_id, flows in raw.get("matrix", {}).items():
            matrix[llm_id] = {
                flow_id: BenchmarkCell(**cell) for flow_id, cell in flows.items()
            }
        total_runs = raw.get("total_runs", sum(len(v) * 6 for v in matrix.values()))
    else:
        matrix = _FALLBACK_MATRIX
        total_runs = 199

    return BenchmarkResponse(
        phase=phase,
        total_runs=total_runs,
        llms=LLMS,
        flows=FLOWS,
        matrix=matrix,
    )
