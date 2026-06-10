from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

from .config import Scoring


class MultiObjectiveScorer:
    def __init__(self, config: Scoring):
        self.config = config

    def normalize(self, value: float, clip_min: float, clip_max: float) -> float:
        if clip_max == clip_min:
            return 0.0
        value = max(clip_min, min(clip_max, value))
        return (value - clip_min) / (clip_max - clip_min)

    def _violation_count(self, violations: Any) -> int:
        if isinstance(violations, int):
            return max(0, violations)
        if isinstance(violations, float):
            return int(violations)
        if isinstance(violations, (list, tuple, set)):
            return len(violations)
        return 0

    def _normalize_objective(self, value: float, metric: object) -> float:
        if metric is None:
            return 0.0
        clip = getattr(metric, "clip", None)
        clip_min = float(clip.min if clip else 0.0)
        clip_max = float(clip.max if clip else 1.0)
        goal = getattr(metric, "goal", "maximize")
        maximize = goal != "minimize"
        normalized = self.normalize(value, clip_min, clip_max)
        return normalized if maximize else (1.0 - normalized)

    def score_candidate(
        self,
        dg: float,
        stability: float,
        druggability: float,
        diversity: float,
        hil_confidence: float,
        hard_violations: int | Sequence[str] | list[tuple[str, float]],
        soft_violations: int | Sequence[str] | list[tuple[str, float]],
    ) -> float:
        docking_cfg = self.config.primary.docking_delta_g
        stability_cfg = self.config.primary.stability
        drug_cfg = self.config.auxiliary.druggability
        diversity_cfg = self.config.auxiliary.diversity
        hil_cfg = self.config.auxiliary.hil_confidence

        docking_score = self._normalize_objective(dg, docking_cfg)
        stability_score = self._normalize_objective(stability, stability_cfg)
        druggability_score = self._normalize_objective(druggability, drug_cfg)
        diversity_score = self._normalize_objective(diversity, diversity_cfg)
        hil_score = self._normalize_objective(hil_confidence, hil_cfg)

        raw = (
            docking_cfg.weight * docking_score
            + stability_cfg.weight * stability_score
            + drug_cfg.weight * druggability_score
            + diversity_cfg.weight * diversity_score
            + hil_cfg.weight * hil_score
        )
        hard_count = self._violation_count(hard_violations)
        penalty = hard_count * self.config.penalties.hard_violation
        if isinstance(soft_violations, (list, tuple)) and soft_violations and isinstance(soft_violations[0], (list, tuple)):
            penalty += sum(float(w) for _, w in soft_violations) * self.config.penalties.soft_violation_per_rule
        else:
            soft_count = self._violation_count(soft_violations)
            penalty += soft_count * self.config.penalties.soft_violation_per_rule
        return raw - penalty

    def rank_candidates(self, candidates: list[dict]) -> list[dict]:
        ranked: List[dict] = []
        for candidate in candidates:
            score = self.score_candidate(
                dg=float(candidate.get("dg", 0.0)),
                stability=float(candidate.get("stability", 0.0)),
                druggability=float(candidate.get("druggability", 0.0)),
                diversity=float(candidate.get("diversity", 0.0)),
                hil_confidence=float(candidate.get("hil_confidence", 0.0)),
                hard_violations=candidate.get("hard_violations", 0),
                soft_violations=candidate.get("soft_violations", 0),
            )
            entry = dict(candidate)
            entry["score"] = score
            ranked.append(entry)
        ranked.sort(key=lambda candidate: candidate.get("score", 0.0), reverse=True)
        return ranked
