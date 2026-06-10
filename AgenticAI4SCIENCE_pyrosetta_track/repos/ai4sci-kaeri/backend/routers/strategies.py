"""Strategy runner router with user-selected mode, complex, and variants."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

StrategyId = Literal["blosum", "esm_scan", "proteinmpnn", "dual_b1_b2"]
ProteinMPNNMode = Literal["peptide_only", "receptor_context"]
RunStatus = Literal["queued", "running", "completed", "failed"]


class StrategyMeta(BaseModel):
    id: StrategyId
    name: str
    description: str
    supports_modes: list[str] = Field(default_factory=list)
    supports_complex_pdb: bool = False


class ProteinMPNNOptions(BaseModel):
    modes: list[dict[str, str]]
    complex_pdbs: list[str]


class StrategyRunRequest(BaseModel):
    strategy: StrategyId
    mode: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    complex_pdb: str | None = None
    max_variants: int = Field(default=8, ge=1, le=96)
    num_seq_per_target: int = Field(default=4, ge=1, le=128)


class StrategyRunResponse(BaseModel):
    job_id: str
    eta_seconds: int


class StrategyRunStatus(BaseModel):
    job_id: str
    strategy: StrategyId
    mode: str | None
    status: RunStatus
    progress: int
    eta_seconds: int
    created_at: datetime
    completed_at: datetime | None = None
    message: str


class StrategyVariant(BaseModel):
    id: str
    sequence: str
    score: float
    source_strategy: StrategyId
    mode: str | None = None
    complex_pdb: str | None = None
    rank: int
    selected: bool = False
    rejected: bool = False
    annotations: dict[str, Any] = Field(default_factory=dict)


class VariantSelectionRequest(BaseModel):
    selected_variant_ids: list[str] = Field(default_factory=list)
    rejected_variant_ids: list[str] = Field(default_factory=list)


class VariantSelectionResponse(BaseModel):
    job_id: str
    selected_variant_ids: list[str]
    rejected_variant_ids: list[str]


_STRATEGIES: list[StrategyMeta] = [
    StrategyMeta(
        id="blosum",
        name="BLOSUM mutation scan",
        description="Conservative substitution scan for SST14-like peptide variants.",
    ),
    StrategyMeta(
        id="esm_scan",
        name="ESM mutation scan",
        description="Language-model guided residue scan for plausibility and diversity.",
    ),
    StrategyMeta(
        id="proteinmpnn",
        name="ProteinMPNN strategy",
        description="ProteinMPNN sequence design with peptide-only or receptor-context mode.",
        supports_modes=["peptide_only", "receptor_context"],
        supports_complex_pdb=True,
    ),
    StrategyMeta(
        id="dual_b1_b2",
        name="Dual B1/B2",
        description="Combined branch strategy for B1/B2 mutation and docking candidates.",
    ),
]

_JOBS: dict[str, dict[str, Any]] = {}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _discover_complex_pdbs() -> list[str]:
    roots = [_project_root() / "runs", _project_root() / "runs_local", _project_root() / "data"]
    pdbs: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.pdb"):
            lowered = path.name.lower()
            if "complex" in lowered or "baseline" in lowered or "cand" in lowered:
                pdbs.append(str(path.relative_to(_project_root())))
            if len(pdbs) >= 50:
                return pdbs
    return pdbs


def _variant_sequences(strategy: StrategyId, max_variants: int) -> list[str]:
    seeds = {
        "blosum": ["AGCKNFFWKTFTSC", "AICKNFFWKTFTSC", "AGCKNFFWKTFSSC"],
        "esm_scan": ["AGCKNDFWKTFTSC", "YSCKNFFWKTFTSN", "APCKNFFWKTFSSC"],
        "proteinmpnn": ["AICKNFFWKTFTSC", "AVCKNFFWKTFTSC", "AICKNFWYKTFTSC"],
        "dual_b1_b2": ["AICKNFFWKTFTSC", "FCCKNFFWKTCTSC", "AGCKNDFWKTFGSE"],
    }[strategy]
    variants: list[str] = []
    while len(variants) < max_variants:
        variants.append(seeds[len(variants) % len(seeds)])
    return variants


def _build_variants(req: StrategyRunRequest, job_id: str) -> list[StrategyVariant]:
    variants: list[StrategyVariant] = []
    for idx, seq in enumerate(_variant_sequences(req.strategy, req.max_variants), start=1):
        variants.append(
            StrategyVariant(
                id=f"{job_id}-var-{idx:03d}",
                sequence=seq,
                score=round(-8.0 - (idx * 0.17), 3),
                source_strategy=req.strategy,
                mode=req.mode,
                complex_pdb=req.complex_pdb,
                rank=idx,
                annotations={
                    "mock": True,
                    "num_seq_per_target": req.num_seq_per_target,
                    "composite_scorer_ready": True,
                    "wetlab_order_ready": True,
                },
            )
        )
    return variants


def _get_job(job_id: str) -> dict[str, Any]:
    job = _JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"strategy run {job_id} not found")
    return job


@router.get("/strategies", response_model=list[StrategyMeta])
def list_strategies() -> list[StrategyMeta]:
    return _STRATEGIES


@router.get("/strategies/proteinmpnn/options", response_model=ProteinMPNNOptions)
def proteinmpnn_options() -> ProteinMPNNOptions:
    return ProteinMPNNOptions(
        modes=[
            {"id": "peptide_only", "label": "Peptide only"},
            {"id": "receptor_context", "label": "Receptor context"},
        ],
        complex_pdbs=_discover_complex_pdbs(),
    )


@router.post("/strategies/run", response_model=StrategyRunResponse)
def run_strategy(req: StrategyRunRequest) -> StrategyRunResponse:
    if req.strategy == "proteinmpnn":
        if req.mode not in ("peptide_only", "receptor_context"):
            raise HTTPException(status_code=400, detail="proteinmpnn mode must be peptide_only or receptor_context")
        if req.mode == "receptor_context" and not req.complex_pdb:
            raise HTTPException(status_code=400, detail="complex_pdb is required for receptor_context mode")

    job_id = f"strategy-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    _JOBS[job_id] = {
        "job_id": job_id,
        "request": req,
        "created_at": now,
        "completed_at": now,
        "status": "completed",
        "progress": 100,
        "eta_seconds": 0,
        "message": "mock strategy run completed",
        "variants": _build_variants(req, job_id),
        "selected_variant_ids": [],
        "rejected_variant_ids": [],
    }
    return StrategyRunResponse(job_id=job_id, eta_seconds=0)


@router.get("/strategies/runs/{job_id}", response_model=StrategyRunStatus)
def get_run_status(job_id: str) -> StrategyRunStatus:
    job = _get_job(job_id)
    req: StrategyRunRequest = job["request"]
    return StrategyRunStatus(
        job_id=job_id,
        strategy=req.strategy,
        mode=req.mode,
        status=job["status"],
        progress=job["progress"],
        eta_seconds=job["eta_seconds"],
        created_at=job["created_at"],
        completed_at=job["completed_at"],
        message=job["message"],
    )


@router.get("/strategies/runs/{job_id}/variants", response_model=list[StrategyVariant])
def get_run_variants(job_id: str) -> list[StrategyVariant]:
    job = _get_job(job_id)
    return job["variants"]


@router.post("/strategies/runs/{job_id}/select", response_model=VariantSelectionResponse)
def select_variants(job_id: str, req: VariantSelectionRequest) -> VariantSelectionResponse:
    job = _get_job(job_id)
    known_ids = {variant.id for variant in job["variants"]}
    unknown_ids = (set(req.selected_variant_ids) | set(req.rejected_variant_ids)) - known_ids
    if unknown_ids:
        raise HTTPException(status_code=400, detail=f"unknown variant ids: {sorted(unknown_ids)}")

    selected = set(req.selected_variant_ids)
    rejected = set(req.rejected_variant_ids) - selected
    for variant in job["variants"]:
        variant.selected = variant.id in selected
        variant.rejected = variant.id in rejected
    job["selected_variant_ids"] = sorted(selected)
    job["rejected_variant_ids"] = sorted(rejected)
    return VariantSelectionResponse(
        job_id=job_id,
        selected_variant_ids=job["selected_variant_ids"],
        rejected_variant_ids=job["rejected_variant_ids"],
    )


@router.get("/strategies/runs/{job_id}/selected", response_model=list[StrategyVariant])
def get_selected_variants(job_id: str) -> list[StrategyVariant]:
    job = _get_job(job_id)
    selected = set(job["selected_variant_ids"])
    return [variant for variant in job["variants"] if variant.id in selected]
