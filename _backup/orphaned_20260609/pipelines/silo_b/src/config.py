from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError, validator


AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")


class PeptideMetadata(BaseModel):
    name: str
    template_sequence: str = Field(..., min_length=1)
    length: int = Field(..., ge=1)
    chain_id: str
    n_terminal_modification: str
    c_terminal_modification: str
    source: str

    @validator("template_sequence")
    def _validate_template_sequence(cls, value: str) -> str:
        invalid = sorted(set(value) - AMINO_ACIDS)
        if invalid:
            raise ValueError(f"Invalid amino acid codes in template sequence: {invalid}")
        return value

    @validator("length")
    def _validate_length(cls, value: int, values: Dict[str, Any]) -> int:
        seq = values.get("template_sequence")
        if seq is not None and value != len(seq):
            raise ValueError("length must match template_sequence length")
        return value

    class Config:
        extra = "forbid"


class ReceptorMetadata(BaseModel):
    name: str
    organism: str
    uniprot: str
    sequence_length: int = Field(..., ge=1)
    binding_mode_hint: str

    class Config:
        extra = "forbid"


class DisulfideMetadata(BaseModel):
    id: str
    residues: List[int]
    type: str
    constrained: bool

    @validator("residues", pre=True)
    def _validate_residues(cls, value: List[int]) -> List[int]:
        if not isinstance(value, list) or len(value) < 2:
            raise ValueError("disulfide residues must contain at least two positions")
        return value

    class Config:
        extra = "forbid"


class ChainInfo(BaseModel):
    cysteine_positions: List[int]
    cysteine_locked: bool

    @validator("cysteine_positions", each_item=True)
    def _validate_positions(cls, value: int) -> int:
        if value < 1:
            raise ValueError("cysteine position must be >= 1")
        return value

    class Config:
        extra = "forbid"


class PharmacophoreMetadata(BaseModel):
    motif_name: str
    positions: List[int]
    residues: Dict[int, str]
    mode: str

    @validator("positions", each_item=True)
    def _validate_positions(cls, value: int) -> int:
        if value < 1:
            raise ValueError("pharmacophore position must be >= 1")
        return value

    class Config:
        extra = "forbid"


class SequenceMetadata(BaseModel):
    peptide: PeptideMetadata
    receptor: ReceptorMetadata
    disulfides: List[DisulfideMetadata]
    chain_info: ChainInfo
    pharmacophore: PharmacophoreMetadata

    @validator("disulfides", pre=False)
    def _validate_disulfide_positions(cls, value: List[DisulfideMetadata], values: Dict[str, Any]) -> List[DisulfideMetadata]:
        peptide = values.get("peptide")
        if peptide is not None:
            max_len = peptide.length
            for disulfide in value:
                for pos in disulfide.residues:
                    if pos < 1 or pos > max_len:
                        raise ValueError("disulfide residue out of peptide index range")
        return value

    class Config:
        extra = "forbid"


class PairwiseConstraint(BaseModel):
    id: str
    type: str
    description: Optional[str] = None
    positions: List[int]
    mode: str
    aa_set: Optional[List[str]] = None
    aa_value: Optional[str] = None
    max_count: Optional[int] = None
    penalty_weight: float = 1.0

    @validator("positions", each_item=True)
    def _validate_positions(cls, value: int) -> int:
        if value < 1:
            raise ValueError("pairwise position must be >= 1")
        return value

    @validator("type")
    def _normalize_type(cls, value: str) -> str:
        value = value.lower().strip()
        if value not in {"hard", "soft"}:
            raise ValueError("pairwise.type must be 'hard' or 'soft'")
        return value

    @validator("mode")
    def _validate_mode(cls, value: str) -> str:
        if not value:
            raise ValueError("pairwise mode must be set")
        return value

    class Config:
        extra = "forbid"


class ConstraintsPharmacophore(BaseModel):
    require_positions: List[int]
    required_residues: Dict[int, str]
    preserve_geometry: bool
    max_sidechain_shift_rmsd_ao: float

    @validator("require_positions", each_item=True)
    def _validate_positions(cls, value: int) -> int:
        if value < 1:
            raise ValueError("require_positions must be >=1")
        return value

    class Config:
        extra = "forbid"


class Constraints(BaseModel):
    frozen_positions: List[int]
    per_position_allowed_aas: Dict[int, List[str]]
    pairwise_rules: List[PairwiseConstraint]
    pharmacophore: ConstraintsPharmacophore

    @validator("frozen_positions", each_item=True)
    def _validate_frozen_positions(cls, value: int) -> int:
        if value < 1:
            raise ValueError("frozen position must be >=1")
        return value

    class Config:
        extra = "forbid"


class StrategyFallback(BaseModel):
    low_space_threshold: int
    low_density_threshold: float
    fallback_primary: str
    fallback_secondary: str

    class Config:
        extra = "forbid"


class Strategy(BaseModel):
    primary: str
    fallback: StrategyFallback

    class Config:
        extra = "forbid"


class Budget(BaseModel):
    total_candidates: int
    adaptive_rounds: int
    per_round_max: int
    approach_b_allocation_ratio: float
    approach_a_allocation_ratio: float

    class Config:
        extra = "forbid"


class DiversityPolicy(BaseModel):
    min_hamming_distance: int
    max_seq_identity: float
    ngram_diversity_weight: float
    cluster_before_docking: bool
    cluster_max_size: int

    class Config:
        extra = "forbid"


class Mutation(BaseModel):
    mutation_rate: float
    mutation_mode: str
    preserve_motif: bool

    class Config:
        extra = "forbid"


class ApproachBApi(BaseModel):
    provider: str
    endpoint_env: str

    class Config:
        extra = "forbid"


class ApproachB(BaseModel):
    enabled: bool
    docking_timeout_sec: int
    batch_size: int
    max_fail_retries: int
    api: ApproachBApi

    class Config:
        extra = "forbid"


class ApproachATrigger(BaseModel):
    gate2_pass_top_k: int
    min_docking_z: float
    min_diversity_gap: float

    class Config:
        extra = "forbid"


class ApproachA(BaseModel):
    enabled: bool
    trigger: ApproachATrigger
    timeout_sec_per_candidate: int
    batch_size: int

    class Config:
        extra = "forbid"


class Generator(BaseModel):
    strategy: Strategy
    budget: Budget
    diversity_policy: DiversityPolicy
    mutation: Mutation
    approach_b: ApproachB
    approach_a: ApproachA

    class Config:
        extra = "forbid"


class DrugabilityFilters(BaseModel):
    enabled: bool
    max_molecular_weight: int
    min_logp: float
    max_logp: float
    max_positive_charge: int
    min_topology_stability_score: float
    max_hydrophobic_fragment_ratio: float

    class Config:
        extra = "forbid"


class ValidationStructure(BaseModel):
    require_disulfide_geometry: bool
    max_steric_clash: float
    max_backbone_rmsd_to_template: float

    class Config:
        extra = "forbid"


class Dedupe(BaseModel):
    enabled: bool
    sequence_identity_threshold: float
    keep_top_by_identity: int
    torsion_fingerprint_kl_threshold: float
    near_neighbour_window: int

    class Config:
        extra = "forbid"


class Validation(BaseModel):
    drugability_filters: DrugabilityFilters
    structure: ValidationStructure
    dedupe: Dedupe

    class Config:
        extra = "forbid"


class ScoreClip(BaseModel):
    min: float
    max: float

    class Config:
        extra = "forbid"


class PrimaryMetric(BaseModel):
    weight: float
    goal: str
    clip: ScoreClip
    source: Optional[str] = None

    class Config:
        extra = "forbid"


class PrimaryScoring(BaseModel):
    docking_delta_g: PrimaryMetric
    stability: PrimaryMetric

    class Config:
        extra = "forbid"


class AuxiliaryMetric(BaseModel):
    weight: float
    goal: str
    source: str
    clip: ScoreClip

    class Config:
        extra = "forbid"


class AuxiliaryScoring(BaseModel):
    druggability: AuxiliaryMetric
    diversity: AuxiliaryMetric
    hil_confidence: AuxiliaryMetric

    class Config:
        extra = "forbid"


class Penalties(BaseModel):
    hard_violation: float
    soft_violation_per_rule: float
    duplicate_penalty: float

    class Config:
        extra = "forbid"


class ScoringNormalization(BaseModel):
    method: str
    epsilon: float

    class Config:
        extra = "forbid"


class Scoring(BaseModel):
    primary: PrimaryScoring
    auxiliary: AuxiliaryScoring
    penalties: Penalties
    normalization: ScoringNormalization

    class Config:
        extra = "forbid"


class BatchSize(BaseModel):
    generation: int
    docking: int
    approach_a: int

    class Config:
        extra = "forbid"


class StopCriteria(BaseModel):
    min_candidates_for_gate2: int
    min_gate2_ratio: float
    max_wallclock_hours: int

    class Config:
        extra = "forbid"


class HIlGate(BaseModel):
    enabled: bool
    purpose: Optional[str] = None
    required_fields: Optional[List[str]] = None
    docking_top_ratio: Optional[float] = None
    min_dock_score_quantile: Optional[float] = None
    require_diversity_margin: Optional[float] = None
    min_top_candidates_for_review: Optional[int] = None
    review_deadline_min: Optional[int] = None
    escalates_to_approach_a: Optional[bool] = None

    class Config:
        extra = "forbid"


class HIlGates(BaseModel):
    gate_1: HIlGate
    gate_2: HIlGate
    gate_3: HIlGate

    class Config:
        extra = "forbid"


class SeedLineage(BaseModel):
    base_seed: int
    stage_seeds: Dict[str, int]

    class Config:
        extra = "forbid"


class Output(BaseModel):
    manifest_path: str
    candidates_path: str
    logs_path: str
    checkpoint_interval: int

    class Config:
        extra = "forbid"


class Orchestration(BaseModel):
    batch_size: BatchSize
    adaptive_steps: int
    stop_criteria: StopCriteria
    hil_gates: HIlGates
    seed_lineage: SeedLineage
    output: Output

    class Config:
        extra = "forbid"


class MutationConfig(BaseModel):
    pipeline_name: str
    config_version: str
    schema_version: int
    created_utc: str
    seed: int

    sequence_metadata: SequenceMetadata
    constraints: Constraints
    generator: Generator
    validation: Validation
    scoring: Scoring
    orchestration: Orchestration

    class Config:
        extra = "forbid"


def _normalize_for_hash(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        data = obj.dict()
        return _normalize_for_hash(data)
    if isinstance(obj, dict):
        return {str(key): _normalize_for_hash(value) for key, value in sorted(obj.items(), key=lambda item: str(item[0]))}
    if isinstance(obj, list):
        return [_normalize_for_hash(item) for item in obj]
    if isinstance(obj, tuple):
        return [_normalize_for_hash(item) for item in obj]
    if isinstance(obj, set):
        return sorted(_normalize_for_hash(item) for item in obj)
    return obj


def load_config(yaml_path: str | Path) -> MutationConfig:
    yaml_text = Path(yaml_path).read_text(encoding="utf-8")
    data = yaml.safe_load(yaml_text)
    if not isinstance(data, dict):
        raise ValueError("Configuration root must be a mapping")
    return MutationConfig.model_validate(data)


def config_hash(config: MutationConfig) -> str:
    canonical_data = _normalize_for_hash(config)
    canonical_yaml = yaml.dump(canonical_data, sort_keys=True)
    return sha256(canonical_yaml.encode("utf-8")).hexdigest()
