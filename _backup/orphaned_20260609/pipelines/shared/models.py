from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class Silo(str, Enum):
    SILO_A = "silo_a"
    SILO_B = "silo_b"
    SILO_C = "silo_c"


class Modality(str, Enum):
    SMALL_MOL = "small_mol"
    PEPTIDE_VARIANT = "peptide_variant"
    DE_NOVO = "de_novo"
    SST14_MUTANT = "sst14_mutant"


@dataclass(frozen=True)
class UnifiedCandidate:
    """Cross-silo candidate representation for Unified Arbiter comparison.

    Every candidate from any silo/arm is converted into this schema so that
    heterogeneous modalities (small molecule, peptide variant, de novo binder,
    SST-14 mutant) can be compared on shared bridge metrics.
    """

    id: str
    silo: Silo
    modality: Modality
    structure: str
    raw_scores: Dict[str, float]
    bridge_metrics: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    provenance: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["silo"] = self.silo.value
        d["modality"] = self.modality.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UnifiedCandidate:
        return cls(
            id=data["id"],
            silo=Silo(data["silo"]),
            modality=Modality(data["modality"]),
            structure=data["structure"],
            raw_scores=data.get("raw_scores", {}),
            bridge_metrics=data.get("bridge_metrics", {}),
            confidence=data.get("confidence", 0.0),
            provenance=data.get("provenance", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CrossSiloManifest:
    """Audit trail for cross-silo comparison runs."""

    run_id: str
    timestamp: str
    silo_a_config_hash: str = ""
    silo_b_config_hash: str = ""
    total_candidates: int = 0
    silo_a_count: int = 0
    silo_b_count: int = 0
    candidates: List[UnifiedCandidate] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_json(self) -> str:
        d = asdict(self)
        d["candidates"] = [c.to_dict() for c in self.candidates]
        return json.dumps(d, indent=2, default=str)
