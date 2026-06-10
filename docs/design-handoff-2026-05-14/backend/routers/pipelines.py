"""
Silo별 파이프라인 구조 + per-step 상태 라우터.

마운트:
  app.include_router(pipelines.router, prefix="/api/pipelines", tags=["pipelines"])

데이터 소스:
  runs_local/{run_id}/state/checkpoint_iter{N}.json
  runs_local/{run_id}/{step}/  존재 여부로 status 추정
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from ..schemas.dashboard import (  # type: ignore
    Pipeline, CombinedPipeline, PipelineStage, PipelineTrack,
)

router = APIRouter()


SILO_A_STAGES_TEMPLATE = [
    dict(id="01",  name="Receptor",      group="input",   tool="PyRosetta · OpenFold3",                env="bio-tools"),
    dict(id="02",  name="Backbone",      group="gen",     tool="RFdiffusion",                          env="rfdiffusion", gpu="H100×1"),
    dict(id="03",  name="Sequence",      group="gen",     tool="ProteinMPNN k=8/bb",                   env="proteinmpnn", gpu="H100×1"),
    dict(id="04",  name="QC",            group="filter",  tool="ESMFold + SS-bond",                    env="esmfold",     gpu="H100×1", gate="pLDDT ≥ 60"),
    dict(id="05",  name="Docking",       group="score",   tool="Boltz-2 SSTR2 7XNA",                   env="boltz",       gpu="H100×4", gate="Top 20%"),
    dict(id="05b", name="Selectivity",   group="score",   tool="Boltz-2 × 4 off-target",               env="boltz",       gpu="H100×4", gate="margin ≤ −10"),
    dict(id="05c", name="Boltz cross",   group="score",   tool="Boltz-2 + AF MSA",                     env="boltz",       gpu="H100×4", gate="iPTM margin ≥ 0"),
    dict(id="06",  name="Rosetta refine",group="refine",  tool="FastRelax + FlexPepDock + ddG",        env="bio-tools",   gpu="CPU",    gate="ddG ≤ −1.0"),
    dict(id="07",  name="Cluster",       group="analyze", tool="FoldMason lDDT ≥ 0.6",                 env="bio-tools"),
    dict(id="08",  name="Stability",     group="analyze", tool="PepADMET + Boman + NEP",               env="pepadmet",                gate="t½ ≥ 50h"),
]

SILO_B_STAGES_TEMPLATE = [
    dict(id="01",  name="Receptor",      group="input",   tool="PyRosetta · OpenFold3",                env="bio-tools"),
    dict(id="CC",  name="Constraint",    group="input",   tool="FWKT freeze · C3–C14 SS",              env="—"),
    dict(id="03b", name="Mutation",      group="gen",     tool="BLOSUM62 + LLM (qwen3-32b) · ga_bo",   env="vllm-server", gpu="H100×1"),
    dict(id="DV",  name="Diversity",     group="filter",  tool="DuplicateFilter Hamming ≥ 2",          env="—"),
    dict(id="04",  name="QC",            group="filter",  tool="ESMFold + SS-bond",                    env="esmfold",     gpu="H100×1", gate="pLDDT ≥ 60"),
    dict(id="05",  name="Docking",       group="score",   tool="DiffDock + Boltz-2",                   env="boltz",       gpu="H100×4", gate="Top 20%"),
    dict(id="05b", name="Selectivity",   group="score",   tool="Boltz-2 × 4 off-target",               env="boltz",       gpu="H100×4", gate="margin ≤ −10"),
    dict(id="05c", name="Boltz cross",   group="score",   tool="Boltz-2 + AF MSA",                     env="boltz",       gpu="H100×4", gate="iPTM margin ≥ 0"),
    dict(id="06",  name="Rosetta refine",group="refine",  tool="FastRelax + FlexPepDock + ddG",        env="bio-tools",   gpu="CPU",    gate="ddG ≤ −1.0"),
    dict(id="07",  name="Cluster",       group="analyze", tool="FoldMason lDDT ≥ 0.6",                 env="bio-tools"),
    dict(id="08",  name="Stability",     group="analyze", tool="PepADMET + Boman + NEP",               env="pepadmet",                gate="t½ ≥ 50h"),
]


def _step_status(run_id: str | None, step_id: str) -> tuple[str, dict]:
    """run_id 기준 step의 실제 상태 추정. 디렉토리 존재 + checkpoint 읽기."""
    if not run_id:
        return ("queued", {})
    # TODO: 디렉토리 매핑 정교화
    base = Path(__file__).resolve().parents[3] / "runs_local" / run_id
    step_dir_map = {
        "01": "01_receptor",   "02": "02_backbone",   "03": "03_sequence",
        "03b": "03b_blosum",   "04": "04_qc",         "05": "05_docking",
        "05b": "05b_selectivity", "05c": "05c_boltz_cross",
        "06": "06_rosetta",    "07": "07_viz",        "08": "08_reports",
    }
    step_dir = base / step_dir_map.get(step_id, step_id)
    if step_dir.exists() and any(step_dir.iterdir()):
        return ("done", {})
    return ("queued", {})


def _hydrate_stage(template: dict, run_id: str | None) -> PipelineStage:
    status, extras = _step_status(run_id, template["id"])
    return PipelineStage(
        id=template["id"],
        name=template["name"],
        group=template["group"],
        tool=template["tool"],
        env=template.get("env"),
        gpu=template.get("gpu"),
        gate=template.get("gate"),
        status=status,
        **extras,
    )


@router.get("/{silo}", response_model=Pipeline | CombinedPipeline)
def get_pipeline(
    silo: Literal["A", "B", "Combined"],
    run_id: str | None = Query(None, description="실제 run의 상태로 hydrate"),
):
    if silo == "A":
        return Pipeline(
            name="Silo A · De Novo",
            description="RFdiffusion 백본부터 새로 디자인",
            stages=[_hydrate_stage(s, run_id) for s in SILO_A_STAGES_TEMPLATE],
        )
    if silo == "B":
        return Pipeline(
            name="Silo B · Mutation+Dock",
            description="SST-14 baseline에서 BLOSUM + LLM 변이",
            stages=[_hydrate_stage(s, run_id) for s in SILO_B_STAGES_TEMPLATE],
        )
    # Combined
    a_gen = [s for s in SILO_A_STAGES_TEMPLATE if s["id"] in ("02", "03")]
    b_gen = [s for s in SILO_B_STAGES_TEMPLATE if s["id"] in ("CC", "03b", "DV")]
    converge = [s for s in SILO_B_STAGES_TEMPLATE if s["id"] in ("04", "05", "05b", "05c", "06", "07", "08")]
    return CombinedPipeline(
        name="Dual Silo · A + B",
        description="병렬 generation → 통합 scoring · refine · analysis",
        input=_hydrate_stage(SILO_A_STAGES_TEMPLATE[0], run_id),
        tracks=[
            PipelineTrack(silo="A", label="de novo",  stages=[_hydrate_stage(s, run_id) for s in a_gen]),
            PipelineTrack(silo="B", label="mutation", stages=[_hydrate_stage(s, run_id) for s in b_gen]),
        ],
        converge=[_hydrate_stage(s, run_id) for s in converge],
    )
