from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ArmName(str, Enum):
    POCKET = "pocket_analysis"
    SMALL_MOL = "arm1_smallmol"
    FLEXPEP = "arm2_flexpep"
    DENOVO = "arm3_denovo"


class RunStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class CandidateRecord:
    candidate_id: str
    arm: ArmName
    value: str
    source: str
    features: Dict[str, float]
    score: Optional[float] = None
    rank: Optional[int] = None


@dataclass(frozen=True)
class ArmResult:
    arm: ArmName
    run_id: str
    status: RunStatus
    started_at: datetime
    finished_at: datetime
    config_hash: str
    artifacts: Dict[str, str] = field(default_factory=dict)
    candidates: List[CandidateRecord] = field(default_factory=list)
    features: Dict[str, float] = field(default_factory=dict)
    score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
