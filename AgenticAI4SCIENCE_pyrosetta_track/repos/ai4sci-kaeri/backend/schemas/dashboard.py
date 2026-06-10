"""Dashboard API schemas used by migration routers."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, Field, field_validator

StageGroup = Literal["input", "gen", "filter", "score", "refine", "analyze"]
StageStatus = Literal["queued", "running", "done", "failed"]


class PipelineStage(BaseModel):
    id: str
    name: str
    group: StageGroup
    tool: str
    env: str | None = None
    status: StageStatus
    description: str | None = None
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

    model_config = {"populate_by_name": True}


class PipelineTrack(BaseModel):
    silo: Literal["A", "B"]
    label: str
    stages: list[PipelineStage]


class Pipeline(BaseModel):
    name: str
    description: str
    stages: list[PipelineStage]


class CombinedPipeline(BaseModel):
    name: str
    description: str
    input: PipelineStage
    tracks: list[PipelineTrack]
    converge: list[PipelineStage]


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


class GateThresholds(BaseModel):
    esmfold_plddt_min: float = Field(default=60.0, validation_alias=AliasChoices("esmfold_plddt_min", "plddt_mean"))
    esmfold_interface_plddt_min: float = Field(default=45.0, validation_alias=AliasChoices("esmfold_interface_plddt_min", "plddt_interface"))
    disulfide_bond_max_distance: float = Field(default=2.5, validation_alias=AliasChoices("disulfide_bond_max_distance", "disulfide_max_angstrom"))
    docking_top_pct: float = Field(default=20.0, ge=0.0, le=100.0, validation_alias=AliasChoices("docking_top_pct", "docking_top_percent"))
    diffdock_confidence_max: float = -1.0
    boltz2_affinity_threshold: float = Field(default=-8.0, validation_alias=AliasChoices("boltz2_affinity_threshold", "boltz_affinity_max"))
    rosetta_ddg_max: float = -1.0
    rosetta_clash_max: int = Field(default=10, ge=0)
    selectivity_margin_min: float = Field(default=-10.0, validation_alias=AliasChoices("selectivity_margin_min", "selectivity_margin_max"))
    offtarget_max_allowed: float = Field(default=-15.0, validation_alias=AliasChoices("offtarget_max_allowed", "off_target_max"))
    boltz_iptm_margin_min: float = 0.0
    stability_prescreen_min_hours: float = Field(default=50.0, ge=0.0, validation_alias=AliasChoices("stability_prescreen_min_hours", "stability_half_life_min"))
    foldmason_lddt_min: float = Field(default=0.6, ge=0.0, le=1.0)

    model_config = {"populate_by_name": True}


class RunStartRequest(BaseModel):
    name: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{1,80}$")
    silo: Literal["A", "B"]
    iterations: int = Field(default=3, ge=1, le=20)
    seed: int = Field(default=42, ge=0, le=2_147_483_647)
    n_backbone: int = Field(default=10, ge=1, le=1000)
    k_seq_per_backbone: int = Field(default=8, ge=1, le=1000)
    top_m_rosetta: int = Field(default=10, ge=1, le=1000)
    llm_model: str = Field(default="qwen3-32b", min_length=1, max_length=120)
    mutation_strategy: Literal["ga_bo", "enumerate", "sampling"] = "ga_bo"
    off_targets: list[str] = Field(default_factory=lambda: ["SSTR1", "SSTR3", "SSTR4", "SSTR5"])
    boltz_cross_enabled: bool = True
    gates: GateThresholds | None = None

    @field_validator("off_targets")
    @classmethod
    def validate_off_targets(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("off_targets must not be empty")
        normalized = [item.strip() for item in value]
        if any(not item for item in normalized):
            raise ValueError("off_targets must not contain blank values")
        if len(set(normalized)) != len(normalized):
            raise ValueError("off_targets must be unique")
        return normalized


class RunStartResponse(BaseModel):
    run_id: str
    started_at: datetime
    estimated_eta_minutes: int
    monitor_url: str


class PredictedPassRate(BaseModel):
    gate_id: str
    name: str
    rate: float = Field(ge=0.0, le=1.0)
    warn: bool = False


class PredictedPassRatesResponse(BaseModel):
    based_on: str
    predicted: list[PredictedPassRate]


WetlabStage = Literal["draft", "submitted", "approved", "shipped", "returned"]


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
    # FlexPepDock Manual Selectivity 연결 (선택적)
    # 결과 페이지에서 wetlab order 생성 시 job_id 전달 → 주문서에 selectivity 메타 포함
    flexpepdock_job_id: str | None = None


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
