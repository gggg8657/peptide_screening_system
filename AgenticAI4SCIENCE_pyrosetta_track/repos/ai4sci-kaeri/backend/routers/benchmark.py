"""Benchmark router adapted from llm_benchmark output directories."""
from __future__ import annotations

import statistics
from collections import defaultdict
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query

try:
    from llm_benchmark.scoring.aggregate import load_phase_results
    _BENCHMARK_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - depends on optional local benchmark tree
    load_phase_results = None  # type: ignore[assignment]
    _BENCHMARK_IMPORT_ERROR = exc

from ..schemas.dashboard import BenchmarkCell, BenchmarkResponse, FlowSpec, LLMSpec

router = APIRouter()

PHASE_ALIASES: dict[str, tuple[str, ...]] = {
    "Phase1": ("phase1",),
    "Phase2": ("phase2a", "phase2b"),
    "Phase3": ("phase3",),
    "V2": ("v2_phase1", "v2_phase2"),
}

MODEL_SPECS: dict[str, LLMSpec] = {
    "qwen3-32b": LLMSpec(id="qwen3-32b", short="q32", vram_gb=80),
    "qwen3-14b": LLMSpec(id="qwen3-14b", short="q14", vram_gb=40),
    "qwen3-7b": LLMSpec(id="qwen3-7b", short="q7", vram_gb=20),
    "qwen2.5-7b": LLMSpec(id="qwen2.5-7b", short="q2.5", vram_gb=20),
    "qwen3.5-27b": LLMSpec(id="qwen3.5-27b", short="q3.5", vram_gb=80),
    "gpt-oss-120b": LLMSpec(id="gpt-oss-120b", short="g120", vram_gb=240),
    "deepseek-r1-distill-32b": LLMSpec(id="deepseek-r1-distill-32b", short="ds32", vram_gb=80),
    "glm-z1-32b": LLMSpec(id="glm-z1-32b", short="glm", vram_gb=80),
}

FLOW_SPECS: dict[str, FlowSpec] = {
    "sequential": FlowSpec(id="sequential", name="Sequential", desc="P→B→Q→C→R 단방향"),
    "collaborative": FlowSpec(id="collaborative", name="Collaborative", desc="DebatingPlanner · 다중 합의"),
    "hierarchical": FlowSpec(id="hierarchical", name="Hierarchical", desc="Orchestrator · 승인/통합"),
}

MODEL_ALIASES = {
    "qwen3_32b": "qwen3-32b",
    "qwen3_14b": "qwen3-14b",
    "qwen3_7b": "qwen3-7b",
    "qwen2_5_7b": "qwen2.5-7b",
    "qwen3_5_27b": "qwen3.5-27b",
    "deepseek_r1_32b": "deepseek-r1-distill-32b",
    "glm_z1_32b": "glm-z1-32b",
    "gpt_oss_120b": "gpt-oss-120b",
}

FLOW_ALIASES = {
    "sequential": "sequential",
    "v2_sequential": "sequential",
    "collaborative": "collaborative",
    "hierarchical": "hierarchical",
}


def _normalize_model(model: str) -> str:
    return MODEL_ALIASES.get(model, model.replace("_", "-"))


def _normalize_flow(flow: str) -> str | None:
    return FLOW_ALIASES.get(flow)


def _load_results_for_alias(phase_alias: str) -> list[dict[str, Any]]:
    if load_phase_results is None:
        raise HTTPException(
            status_code=503,
            detail=f"llm_benchmark is unavailable: {_BENCHMARK_IMPORT_ERROR}",
        )

    results: list[dict[str, Any]] = []
    for actual_phase in PHASE_ALIASES.get(phase_alias, (phase_alias.lower(),)):
        results.extend(load_phase_results(actual_phase))
    return results


def _llm_spec(model_id: str) -> LLMSpec:
    return MODEL_SPECS.get(model_id, LLMSpec(id=model_id, short=model_id[:8], vram_gb=0))


def _build_cell(runs: list[dict[str, Any]]) -> BenchmarkCell:
    hit_rates = [float(run.get("ses", {}).get("hit_rate", 0.0)) for run in runs]
    elapsed = [float(run.get("elapsed_s", 0.0)) for run in runs]
    candidate_counts = [int(run.get("ses", {}).get("n_total", 0)) for run in runs]
    hit_counts = [int(run.get("ses", {}).get("n_hits", 0)) for run in runs]

    pass_rate = statistics.mean(hit_rates) * 100 if hit_rates else 0.0
    time_min = statistics.mean(elapsed) / 60 if elapsed else 0.0
    candidates = round(statistics.mean(candidate_counts)) if candidate_counts else 0
    t2 = round(statistics.mean(hit_counts)) if hit_counts else 0

    return BenchmarkCell(
        pass_rate=round(pass_rate, 2),
        time_min=round(time_min, 2),
        candidates=int(candidates),
        t2=int(t2),
        cost=0.0,
    )


@router.get("/results", response_model=BenchmarkResponse)
def benchmark_results(
    phase: Literal["Phase1", "Phase2", "Phase3", "V2"] = Query("V2"),
) -> BenchmarkResponse:
    """Adapt benchmark output dirs into the dashboard matrix schema."""
    raw_results = _load_results_for_alias(phase)
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))

    for run in raw_results:
        model_id = _normalize_model(str(run.get("model", "unknown")))
        flow_id = _normalize_flow(str(run.get("flow", "sequential")))
        if flow_id is None:
            continue
        grouped[model_id][flow_id].append(run)

    matrix: dict[str, dict[str, BenchmarkCell]] = {}
    for model_id, flows in grouped.items():
        matrix[model_id] = {
            flow_id: _build_cell(flow_runs)
            for flow_id, flow_runs in sorted(flows.items())
            if flow_id in FLOW_SPECS
        }

    llm_ids = sorted(matrix)
    flow_ids = [flow_id for flow_id in FLOW_SPECS if any(flow_id in flows for flows in matrix.values())]

    return BenchmarkResponse(
        phase=phase,
        total_runs=len(raw_results),
        llms=[_llm_spec(model_id) for model_id in llm_ids],
        flows=[FLOW_SPECS[flow_id] for flow_id in flow_ids],
        matrix=matrix,
    )
