"""
Pydantic schemas for SSTR2 Dashboard endpoints.

drop-in at `backend/schemas/dashboard.py` (or alongside existing schemas).
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Run / Status

Silo = Literal["A", "B", "A+B"]
StageGroup = Literal["input", "gen", "filter", "score", "refine", "analyze"]
StageStatus = Literal["queued", "running", "done", "failed"]


class RunStatus(BaseModel):
    run_id: str
    started_at: datetime
    duration_seconds: int
    iteration: int
    max_iterations: int
    silo: Silo
    llm_model: str
    gpus: str
    seed: int
    current_step: str
    progress: float = Field(ge=0, le=1)
    state: Literal["running", "done", "failed", "queued"]


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline structure (per silo)

class PipelineStage(BaseModel):
    id: str
    name: str
    group: StageGroup
    tool: str
    env: str | None = None
    status: StageStatus
    in_count: int | None = None
    out_count: int | None = None
    in_unit: str | None = None
    out_unit: str | None = None
    time: str | None = None
    gpu: str | None = None
    gate: str | None = None
    pass_count: int | None = Field(None, alias="pass")
    fail_count: int | None = Field(None, alias="fail")
    progress: float | None = None

    class Config:
        populate_by_name = True


class PipelineTrack(BaseModel):
    silo: Literal["A", "B"]
    label: str
    stages: list[PipelineStage]


class Pipeline(BaseModel):
    """Linear silo pipeline (A or B)."""
    name: str
    description: str
    stages: list[PipelineStage]


class CombinedPipeline(BaseModel):
    """Combined dual-silo view with parallel tracks → converge."""
    name: str
    description: str
    input: PipelineStage
    tracks: list[PipelineTrack]
    converge: list[PipelineStage]


# ─────────────────────────────────────────────────────────────────────────────
# Candidates & selectivity

Tier = Literal["T0", "T1", "T2", "T3"]


class Candidate(BaseModel):
    id: str
    seq: str
    tier: Tier
    margin: float
    best_receptor: str
    iptm: dict[str, float]
    ddg: float | None = None
    source: str | None = None
    mutations: list[str] = []
    recommended: bool = False
    wildtype: bool = False
    notes: str | None = None


class CandidatesResponse(BaseModel):
    run_id: str
    wild_type: str
    candidates: list[Candidate]


# ─────────────────────────────────────────────────────────────────────────────
# 5-Agent log

AgentId = Literal["planner", "builder", "qcranker", "diversity", "critic", "reporter"]
AgentColor = Literal["violet", "blue", "cyan", "teal", "amber", "stone"]


class AgentSpec(BaseModel):
    id: AgentId
    name: str
    role: str
    color: AgentColor


class AgentEntry(BaseModel):
    ts: datetime
    agent: AgentId
    level: Literal["info", "warn", "error"] = "info"
    text: str


class AgentLogResponse(BaseModel):
    agents: list[AgentSpec]
    entries: list[AgentEntry]


# ─────────────────────────────────────────────────────────────────────────────
# Run launcher

class GateThresholds(BaseModel):
    plddt_mean: float = 60
    plddt_interface: float = 45
    disulfide_max_angstrom: float = 2.5
    docking_top_percent: float = 20
    diffdock_confidence_max: float = -1.0
    boltz_affinity_max: float = -8.0
    rosetta_ddg_max: float = -1.0
    rosetta_clash_max: int = 10
    selectivity_margin_max: float = -10.0
    off_target_max: float = -15.0
    boltz_iptm_margin_min: float = 0.0
    stability_half_life_min: float = 50.0
    foldmason_lddt_min: float = 0.6


class OffTargetReceptor(BaseModel):
    name: str
    uniprot: str
    pdb: str
    enabled: bool = True


class RunStartRequest(BaseModel):
    name: str
    silo: Silo
    iterations: int = Field(default=3, ge=1, le=20)
    seed: int = 42
    n_backbone: int = 10
    k_seq_per_backbone: int = 8
    top_m_rosetta: int = 10
    llm_model: str = "qwen3-32b"
    mutation_strategy: Literal["ga_bo", "enumerate", "sampling"] = "ga_bo"
    off_targets: list[str] = ["SSTR1", "SSTR3", "SSTR4", "SSTR5"]
    boltz_cross_enabled: bool = True
    gates: GateThresholds | None = None


class RunStartResponse(BaseModel):
    run_id: str
    started_at: datetime
    estimated_eta_minutes: int
    monitor_url: str


class PredictedPassRate(BaseModel):
    gate_id: str
    name: str
    rate: float = Field(ge=0, le=1)
    warn: bool = False


class PredictedPassRatesResponse(BaseModel):
    based_on: str
    predicted: list[PredictedPassRate]


# ─────────────────────────────────────────────────────────────────────────────
# cand03 variants

class Cand03Variant(BaseModel):
    id: str
    name: str
    seq: str
    modifications: list[str] = []
    hl_score: float
    chymotrypsin_sites: int
    trypsin_sites: int
    nep_sites: int
    priority: str
    rationale: str | None = None


class Cand03VariantsResponse(BaseModel):
    baseline: str = "cand03"
    variants: list[Cand03Variant]


# ─────────────────────────────────────────────────────────────────────────────
# Benchmark

class LLMSpec(BaseModel):
    id: str
    short: str
    vram_gb: int


class FlowSpec(BaseModel):
    id: Literal["sequential", "collaborative", "hierarchical"]
    name: str
    desc: str


class BenchmarkCell(BaseModel):
    pass_rate: float
    time_min: float
    candidates: int
    t2: int
    cost: float


class BenchmarkResponse(BaseModel):
    phase: str
    total_runs: int
    llms: list[LLMSpec]
    flows: list[FlowSpec]
    matrix: dict[str, dict[str, BenchmarkCell]]


# ─────────────────────────────────────────────────────────────────────────────
# Wetlab

WetlabStage = Literal["draft", "review", "approval", "PO", "shipped"]


class Reagent(BaseModel):
    name: str
    spec: str
    vendor: str
    unit_price_krw: int
    qty: int
    lead_days: str


class PredictedKi(BaseModel):
    receptor: str
    iptm: float
    sst14_ki_nm: float | None = None
    predicted_ki: str
    target: bool = False


class AcceptanceCriterion(BaseModel):
    criterion: str
    passed: bool | None = None


class TimelineEntry(BaseModel):
    week: str
    task: str
    actor: str


class WetlabProtocol(BaseModel):
    format: str
    tracer: str
    membrane: str
    concentration_range: str
    replicates: str
    negative_control: str
    readout: str
    analysis: str


class WetlabOrder(BaseModel):
    id: str
    candidate_id: str
    candidate_seq: str
    stage: WetlabStage
    total_krw: int
    lead_weeks: int
    requested_by: str
    created_at: datetime
    hypothesis: dict[str, str]
    predicted_ki: list[PredictedKi]
    reagents: list[Reagent]
    protocol: WetlabProtocol
    acceptance_criteria: list[AcceptanceCriterion]
    timeline: list[TimelineEntry]


class WetlabOrderListItem(BaseModel):
    id: str
    candidate_id: str
    stage: WetlabStage
    total_krw: int
    lead_weeks: int
    requested_by: str
    created_at: datetime


class WetlabOrderListResponse(BaseModel):
    orders: list[WetlabOrderListItem]


class WetlabTransitionRequest(BaseModel):
    to_stage: WetlabStage
    note: str | None = None
