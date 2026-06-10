from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Literal

import yaml
from pydantic import BaseModel, Field


class JoinPolicy(BaseModel):
    join_policy: Literal["all_of"] = "all_of"
    required_silos: List[str] = Field(default_factory=lambda: ["A", "B", "C"])
    optional_silos: List[str] = Field(default_factory=list)
    silo_modes: Dict[str, Literal["fast", "strict"]] = Field(
        default_factory=lambda: {"A": "strict", "B": "fast", "C": "strict"}
    )
    wait_timeout_sec: int = 7200
    on_system_fatal: Literal["abort", "manual_approval"] = "abort"

    model_config = {"extra": "forbid"}


class ResourcePolicy(BaseModel):
    scheduler_mode: Literal["adaptive"] = "adaptive"
    max_workers: Dict[str, int] = Field(default_factory=lambda: {"A": 3, "B": 2, "C": 1})
    queue_priority: List[str] = Field(default_factory=lambda: ["C", "B", "A"])

    model_config = {"extra": "forbid"}


class FailureClassifierPolicy(BaseModel):
    scientific: List[str] = Field(default_factory=lambda: ["gate_fail", "score_below_threshold", "constraint_violation"])
    system: List[str] = Field(default_factory=lambda: ["runtime_error", "dependency_error", "io_error", "timeout"])

    model_config = {"extra": "forbid"}


class RecoveryPolicy(BaseModel):
    retry_max: int = 3
    backoff_sec: List[int] = Field(default_factory=lambda: [10, 30, 60])
    healthcheck_required: bool = True

    model_config = {"extra": "forbid"}


class FailurePolicy(BaseModel):
    classify: FailureClassifierPolicy = Field(default_factory=FailureClassifierPolicy)
    recovery: RecoveryPolicy = Field(default_factory=RecoveryPolicy)

    model_config = {"extra": "forbid"}


class RankingFusionPolicy(BaseModel):
    method: Literal["weighted_sum", "pareto", "rank_product"] = "weighted_sum"
    normalize: Literal["minmax", "zscore", "none"] = "minmax"
    weights: Dict[str, float] = Field(default_factory=lambda: {"A": 0.34, "B": 0.33, "C": 0.33})

    model_config = {"extra": "forbid"}


class RankingPolicy(BaseModel):
    fusion: RankingFusionPolicy = Field(default_factory=RankingFusionPolicy)

    model_config = {"extra": "forbid"}


class OrchestrationPolicy(BaseModel):
    orchestration: JoinPolicy = Field(default_factory=JoinPolicy)
    resources: ResourcePolicy = Field(default_factory=ResourcePolicy)
    failure_policy: FailurePolicy = Field(default_factory=FailurePolicy)
    ranking: RankingPolicy = Field(default_factory=RankingPolicy)

    model_config = {"extra": "forbid"}


def load_orchestration_policy(yaml_path: str | Path) -> OrchestrationPolicy:
    text = Path(yaml_path).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("Policy root must be a mapping")

    # Pydantic v1/v2 compatibility
    if hasattr(OrchestrationPolicy, "model_validate"):
        return OrchestrationPolicy.model_validate(data)
    return OrchestrationPolicy.parse_obj(data)
