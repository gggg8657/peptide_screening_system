from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence


def _pairwise_hamming_distance(seq1: str, seq2: str) -> int:
    if len(seq1) != len(seq2):
        raise ValueError("pairwise_hamming_distance requires equal length sequences")
    return sum(a != b for a, b in zip(seq1.upper(), seq2.upper()))


@dataclass(frozen=True)
class Gate1Report:
    candidate_count: int
    filter_stats: Dict[str, int]
    pass_rate: float


@dataclass(frozen=True)
class Gate2Report:
    top_k_scores: List[float]
    pareto_front_size: int
    diversity_score: float


@dataclass(frozen=True)
class Gate3Report:
    final_candidates: int
    refinement_ready_count: int


class HILGate(ABC):
    @abstractmethod
    def gate_1_review(self, candidates: Sequence[str], filter_results: Sequence[Any]) -> Gate1Report:
        raise NotImplementedError

    @abstractmethod
    def gate_2_review(self, scored_candidates: Sequence[dict]) -> Gate2Report:
        raise NotImplementedError

    @abstractmethod
    def gate_3_review(self, refined_candidates: Sequence[dict]) -> Gate3Report:
        raise NotImplementedError

    def request_approval(self, report: Any) -> bool:
        return True


class DefaultHILGate(HILGate):
    def gate_1_review(self, candidates: Sequence[str], filter_results: Sequence[Any]) -> Gate1Report:
        candidate_count = len(candidates)
        passed = 0
        filter_stats: Dict[str, int] = {}
        for result in filter_results:
            if getattr(result, "passed", False):
                passed += 1
                continue
            reasons = getattr(result, "rejection_reasons", [])
            if not reasons:
                continue
            for reason in reasons:
                filter_stats[str(reason)] = filter_stats.get(str(reason), 0) + 1
        pass_rate = passed / float(candidate_count) if candidate_count else 0.0
        return Gate1Report(candidate_count=candidate_count, filter_stats=filter_stats, pass_rate=pass_rate)

    def gate_2_review(self, scored_candidates: Sequence[dict]) -> Gate2Report:
        if not scored_candidates:
            return Gate2Report(top_k_scores=[], pareto_front_size=0, diversity_score=0.0)

        sorted_candidates = sorted(scored_candidates, key=lambda item: item.get("score", 0.0), reverse=True)
        top_k_scores = [float(item.get("score", 0.0)) for item in sorted_candidates[: min(5, len(sorted_candidates))]]

        sequences = [str(item.get("sequence", "")) for item in scored_candidates]
        objectives: List[tuple[float, float]] = []
        for item in scored_candidates:
            score = float(item.get("score", 0.0))
            diversity = float(item.get("diversity", 0.0))
            objectives.append((score, diversity))
        pareto_front_size = 0
        for i, left in enumerate(objectives):
            is_dominated = False
            for j, right in enumerate(objectives):
                if i == j:
                    continue
                if right[0] >= left[0] and right[1] >= left[1] and (right[0] > left[0] or right[1] > left[1]):
                    is_dominated = True
                    break
            if not is_dominated:
                pareto_front_size += 1

        diversity_score = 0.0
        if len(sequences) > 1:
            dists = []
            for i in range(len(sequences)):
                for j in range(i + 1, len(sequences)):
                    if sequences[i] and sequences[j]:
                        try:
                            dists.append(_pairwise_hamming_distance(sequences[i], sequences[j]))
                        except ValueError:
                            continue
            if dists:
                max_len = max(len(seq) for seq in sequences if seq)
                if max_len > 0:
                    diversity_score = sum(dists) / (len(dists) * max_len)

        return Gate2Report(
            top_k_scores=top_k_scores,
            pareto_front_size=pareto_front_size,
            diversity_score=diversity_score,
        )

    def gate_3_review(self, refined_candidates: Sequence[dict]) -> Gate3Report:
        final_candidates = len(refined_candidates)
        refinement_ready_count = 0
        for candidate in refined_candidates:
            if candidate.get("refinement_ready", True):
                refinement_ready_count += 1
        return Gate3Report(
            final_candidates=final_candidates,
            refinement_ready_count=refinement_ready_count,
        )
