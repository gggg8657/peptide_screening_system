from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence


@dataclass(frozen=True)
class FilterResult:
    passed: bool
    ng_positions: List[int]
    dg_positions: List[int]
    met_positions: List[int]
    aggregation_score: float
    rejection_reasons: List[str]


class DrugabilityFilter:
    hydrophobic_aas = set("AILMFWVY")

    def check_ng_deamidation(self, seq: str) -> List[int]:
        return [idx + 1 for idx in range(len(seq) - 1) if seq[idx : idx + 2] == "NG"]

    def check_dg_isomerization(self, seq: str) -> List[int]:
        return [idx + 1 for idx in range(len(seq) - 1) if seq[idx : idx + 2] == "DG"]

    def check_met_oxidation(self, seq: str) -> List[int]:
        return [idx + 1 for idx, aa in enumerate(seq) if aa == "M"]

    def check_aggregation_prone(self, seq: str) -> float:
        if not seq:
            return 0.0
        seq = seq.upper()
        hydrophobic_count = sum(1 for aa in seq if aa in self.hydrophobic_aas)
        return hydrophobic_count / float(len(seq))

    def filter_candidate(self, seq: str) -> FilterResult:
        seq = seq.upper()
        ng_positions = self.check_ng_deamidation(seq)
        dg_positions = self.check_dg_isomerization(seq)
        met_positions = self.check_met_oxidation(seq)
        aggregation_score = self.check_aggregation_prone(seq)

        reasons = []
        if ng_positions:
            reasons.append("contains_NG_motif")
        if dg_positions:
            reasons.append("contains_DG_motif")
        if met_positions:
            reasons.append("contains_methionine")
        if aggregation_score > 0.70:
            reasons.append("aggregation_risk")

        return FilterResult(
            passed=not reasons,
            ng_positions=ng_positions,
            dg_positions=dg_positions,
            met_positions=met_positions,
            aggregation_score=aggregation_score,
            rejection_reasons=reasons,
        )


class DuplicateFilter:
    def __init__(self, min_hamming_distance: int = 3):
        self.min_hamming_distance = min_hamming_distance
        self._sequences: List[str] = []

    def hamming_distance(self, seq1: str, seq2: str) -> int:
        if len(seq1) != len(seq2):
            raise ValueError("Hamming distance requires sequences of equal length")
        return sum(a != b for a, b in zip(seq1.upper(), seq2.upper()))

    def is_duplicate(self, seq: str) -> bool:
        return any(self.hamming_distance(seq, existing) < self.min_hamming_distance for existing in self._sequences)

    def add_sequence(self, seq: str) -> bool:
        if self.is_duplicate(seq):
            return False
        self._sequences.append(seq.upper())
        return True

    def get_unique_count(self) -> int:
        return len(self._sequences)
