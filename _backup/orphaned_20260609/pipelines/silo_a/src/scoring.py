from __future__ import annotations

from typing import Dict, List

from .config import ScoringConfig
from .models import ArmName, CandidateRecord


class UnifiedScorer:
    """Normalize and score candidates across all three arms on a common scale."""

    def __init__(self, config: ScoringConfig):
        self.config = config

    def normalize(self, value: float, lo: float, hi: float) -> float:
        if hi == lo:
            return 0.0
        clamped = max(lo, min(hi, value))
        return (clamped - lo) / (hi - lo)

    def score_candidate(self, features: Dict[str, float], arm: ArmName) -> float:
        w = self.config.weights

        arm_score = 0.0
        arm_max = 0.0
        if arm == ArmName.SMALL_MOL:
            arm_score += w.qed * self.normalize(features.get("qed", 0.0), 0.0, 1.0)
            arm_score += w.dock_confidence * self.normalize(features.get("dock_confidence", 0.0), 0.0, 1.0)
            arm_max += w.qed + w.dock_confidence
        elif arm == ArmName.FLEXPEP:
            raw_de = features.get("delta_energy", 0.0)
            arm_score += w.delta_energy * self.normalize(-raw_de, 0.0, 50.0)
            arm_max += w.delta_energy
        elif arm == ArmName.DENOVO:
            arm_score += w.plddt * self.normalize(features.get("plddt", 0.0), 0.0, 100.0)
            arm_max += w.plddt

        normalized_arm = 0.0
        if arm_max > 0:
            normalized_arm = arm_score / arm_max
            if normalized_arm < 0.0:
                normalized_arm = 0.0
            elif normalized_arm > 1.0:
                normalized_arm = 1.0

        score = (1.0 - w.diversity) * normalized_arm
        score += w.diversity * self.normalize(features.get("diversity", 0.0), 0.0, 1.0)

        return round(max(0.0, min(1.0, score)), 4)

    def rank_candidates(self, candidates: List[CandidateRecord]) -> List[CandidateRecord]:
        scored = []
        for c in candidates:
            s = self.score_candidate(c.features, c.arm)
            scored.append(CandidateRecord(
                candidate_id=c.candidate_id,
                arm=c.arm,
                value=c.value,
                source=c.source,
                features=c.features,
                score=s,
                rank=None,
            ))
        scored.sort(key=lambda x: x.score or 0.0, reverse=True)
        ranked = []
        for i, c in enumerate(scored):
            ranked.append(CandidateRecord(
                candidate_id=c.candidate_id,
                arm=c.arm,
                value=c.value,
                source=c.source,
                features=c.features,
                score=c.score,
                rank=i + 1,
            ))
        return ranked
