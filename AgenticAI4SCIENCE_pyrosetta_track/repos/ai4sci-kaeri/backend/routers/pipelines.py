"""Dynamic pipeline router built from step module inventory."""
from __future__ import annotations

import importlib
import inspect
import re
from pathlib import Path
from typing import Any, Literal

import yaml
from fastapi import APIRouter, Query

from ..schemas.dashboard import CombinedPipeline, Pipeline, PipelineStage, PipelineTrack

router = APIRouter()

REPO_ROOT = Path(__file__).resolve().parents[5]
PIPELINE_LOCAL_ROOT = REPO_ROOT / "pipeline_local"
MODEL_PATHS_FILE = PIPELINE_LOCAL_ROOT / "config" / "model_paths.yaml"
GATE_THRESHOLDS_FILE = PIPELINE_LOCAL_ROOT / "config" / "gate_thresholds.yaml"

SILO_A_STEPS = [
    "step01_receptor",
    "step02_backbone",
    "step03_sequence",
    "step04_qc",
    "step05_docking",
    "step05b_selectivity",
    "step05c_boltz_cross",
    "step06_rosetta",
    "step07_analysis",
    "step08_stability",
]

SILO_B_STEPS = [
    # 마이그레이션 fix 2026-05-14: step02_backbone(RFdiffusion)은 Silo A 전용.
    # Silo B는 SST-14 결정 구조를 baseline으로 사용하므로 백본 생성 단계 없음.
    "step01_receptor",
    "step03b_blosum_mutation",
    "step04_qc",
    "step05_docking",
    "step05b_selectivity",
    "step05c_boltz_cross",
    "step06_rosetta",
    "step07_analysis",
    "step08_stability",
]

STAGE_META = {
    "step01_receptor": {"id": "01", "name": "Receptor", "group": "input", "tool": "PyRosetta · OpenFold3", "gpu": None, "env_fallback": "bio-tools"},
    "step02_backbone": {"id": "02", "name": "Backbone", "group": "gen", "tool": "RFdiffusion", "gpu": "H100×1", "env_fallback": "rfdiffusion"},
    "step03_sequence": {"id": "03", "name": "Sequence", "group": "gen", "tool": "ProteinMPNN", "gpu": "H100×1", "env_fallback": "proteinmpnn"},
    "step03b_blosum_mutation": {"id": "03b", "name": "Mutation", "group": "gen", "tool": "BLOSUM62 + LLM", "gpu": "H100×1", "env_fallback": "vllm-server"},
    "step04_qc": {"id": "04", "name": "QC", "group": "filter", "tool": "ESMFold", "gpu": "H100×1", "env_fallback": "esmfold"},
    "step05_docking": {"id": "05", "name": "Docking", "group": "score", "tool": "DiffPepBuilder + Boltz-2", "gpu": "H100×4", "env_fallback": "boltz"},
    "step05b_selectivity": {"id": "05b", "name": "Selectivity", "group": "score", "tool": "Boltz-2 × off-targets", "gpu": "H100×4", "env_fallback": "boltz"},
    "step05c_boltz_cross": {"id": "05c", "name": "Boltz cross", "group": "score", "tool": "Boltz-2 + AF MSA", "gpu": "H100×4", "env_fallback": "boltz"},
    "step06_rosetta": {"id": "06", "name": "Rosetta refine", "group": "refine", "tool": "FastRelax + FlexPepDock + ddG", "gpu": "CPU", "env_fallback": "bio-tools"},
    "step07_analysis": {"id": "07", "name": "Cluster", "group": "analyze", "tool": "FoldMason + PyMOL", "gpu": None, "env_fallback": "bio-tools"},
    "step08_stability": {"id": "08", "name": "Stability", "group": "analyze", "tool": "PepADMET + heuristics", "gpu": None, "env_fallback": "pepadmet"},
}

RUN_STEP_DIRS = {
    "01": "01_receptor",
    "02": "02_backbone",
    "03": "03_sequence",
    "03b": "03b_blosum",
    "04": "04_qc",
    "05": "05_docking",
    "05b": "05b_selectivity",
    "05c": "05c_boltz_cross",
    "06": "06_rosetta",
    "07": "07_viz",
    "08": "08_reports",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


MODEL_PATHS = _load_yaml(MODEL_PATHS_FILE)
GATE_THRESHOLDS = _load_yaml(GATE_THRESHOLDS_FILE)


def _extract_doc_summary(module_name: str) -> str:
    module = importlib.import_module(f"pipeline_local.steps.{module_name}")
    doc = inspect.getdoc(module) or ""
    for line in doc.splitlines():
        stripped = line.strip()
        if not stripped or stripped.endswith(".py") or set(stripped) == {"="}:
            continue
        return stripped
    return STAGE_META[module_name]["name"]


def _extract_description(module_name: str) -> str:
    summary = _extract_doc_summary(module_name)
    match = re.search(r"Step\s+[0-9A-Za-z]+:\s*(.+)", summary)
    return match.group(1).strip() if match else summary


def _resolve_env(module_name: str) -> str | None:
    models = MODEL_PATHS.get("models", {})
    model_keys = {
        "step01_receptor": ("openfold3",),
        "step02_backbone": ("rfdiffusion",),
        "step03_sequence": ("proteinmpnn",),
        "step04_qc": ("esmfold",),
        "step05_docking": ("boltz", "diffpepbuilder"),
        "step05b_selectivity": ("boltz",),
        "step05c_boltz_cross": ("boltz",),
    }.get(module_name, ())
    for key in model_keys:
        conda_env = models.get(key, {}).get("conda_env")
        if conda_env:
            return str(conda_env)
    return STAGE_META[module_name]["env_fallback"]


def _gate_text(stage_id: str) -> str | None:
    if stage_id == "04":
        mean_gate = GATE_THRESHOLDS.get("esmfold_plddt_min")
        iface_gate = GATE_THRESHOLDS.get("esmfold_interface_plddt_min")
        if mean_gate is not None and iface_gate is not None:
            return f"pLDDT ≥ {mean_gate}, interface ≥ {iface_gate}"
    if stage_id == "05":
        value = GATE_THRESHOLDS.get("docking_top_pct")
        if value is not None:
            return f"Top {value}%"
    if stage_id == "05b":
        margin = GATE_THRESHOLDS.get("selectivity_margin_min")
        if margin is not None:
            return f"margin ≤ {margin}"
    if stage_id == "05c":
        return "iPTM matrix review"
    if stage_id == "06":
        ddg = GATE_THRESHOLDS.get("rosetta_ddg_max")
        if ddg is not None:
            return f"ddG ≤ {ddg}"
    if stage_id == "07":
        lddt = GATE_THRESHOLDS.get("foldmason_lddt_min")
        if lddt is not None:
            return f"lDDT ≥ {lddt}"
    if stage_id == "08":
        hours = GATE_THRESHOLDS.get("stability_prescreen_min_hours")
        if hours is not None:
            return f"t½ ≥ {hours}h"
    return None


def _step_status(run_id: str | None, stage_id: str) -> tuple[str, dict[str, Any]]:
    if not isinstance(run_id, str) or not run_id:
        return "queued", {}
    run_dir = REPO_ROOT / "runs_local" / run_id / RUN_STEP_DIRS.get(stage_id, stage_id)
    if run_dir.exists() and any(run_dir.iterdir()):
        return "done", {}
    return "queued", {}


def _stage_from_module(module_name: str, run_id: str | None) -> PipelineStage:
    meta = STAGE_META[module_name]
    status, extras = _step_status(run_id, meta["id"])
    return PipelineStage(
        id=meta["id"],
        name=meta["name"],
        group=meta["group"],
        tool=meta["tool"],
        env=_resolve_env(module_name),
        status=status,
        description=_extract_description(module_name),
        gpu=meta["gpu"],
        gate=_gate_text(meta["id"]),
        **extras,
    )


@router.get("/{silo}", response_model=Pipeline | CombinedPipeline)
def get_pipeline(
    silo: Literal["A", "B", "Combined"],
    run_id: str | None = Query(None, description="실제 run의 상태로 hydrate"),
) -> Pipeline | CombinedPipeline:
    if silo == "A":
        return Pipeline(
            name="Silo A · De Novo",
            description="RFdiffusion 백본부터 새로 디자인",
            stages=[_stage_from_module(module_name, run_id) for module_name in SILO_A_STEPS],
        )
    if silo == "B":
        return Pipeline(
            name="Silo B · Mutation+Dock",
            description="SST-14 baseline에서 BLOSUM + LLM 변이",
            stages=[_stage_from_module(module_name, run_id) for module_name in SILO_B_STEPS],
        )

    return CombinedPipeline(
        name="Dual Silo · A + B",
        description="병렬 generation → 통합 scoring · refine · analysis",
        input=_stage_from_module("step01_receptor", run_id),
        tracks=[
            PipelineTrack(
                silo="A",
                label="de novo",
                stages=[_stage_from_module(module_name, run_id) for module_name in SILO_A_STEPS[1:3]],
            ),
            PipelineTrack(
                silo="B",
                label="mutation",
                stages=[_stage_from_module(module_name, run_id) for module_name in ("step03b_blosum_mutation",)],
            ),
        ],
        converge=[
            _stage_from_module(module_name, run_id)
            for module_name in (
                "step04_qc",
                "step05_docking",
                "step05b_selectivity",
                "step05c_boltz_cross",
                "step06_rosetta",
                "step07_analysis",
                "step08_stability",
            )
        ],
    )
