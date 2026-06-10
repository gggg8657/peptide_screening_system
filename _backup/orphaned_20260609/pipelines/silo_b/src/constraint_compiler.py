from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from .config import MutationConfig


@dataclass(frozen=True)
class CompiledConstraints:
    position_aa_map: Dict[int, Set[str]]
    frozen_positions: Set[int]
    pairwise_rules: List[dict]
    design_space_size: int
    mutable_positions: List[int]


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    hard_violations: List[str]
    soft_violations: List[Tuple[str, float]]
    penalty_score: float


class ConstraintCompiler:
    def __init__(self, config: MutationConfig):
        self.config = config
        self._compiled: CompiledConstraints | None = None

    def compile(self) -> CompiledConstraints:
        sequence = self.config.sequence_metadata.peptide.template_sequence
        per_pos_allowed = self.config.constraints.per_position_allowed_aas

        # Build full 1-based position map.
        position_aa_map: Dict[int, Set[str]] = {}
        for idx, residue in enumerate(sequence, start=1):
            allowed = per_pos_allowed.get(idx)
            if allowed is None:
                raise ValueError(f"Missing allowed amino acids for position {idx}")
            position_aa_map[idx] = set(allowed)

        frozen = set(self.config.constraints.frozen_positions)
        frozen.update(pos for pos in self.config.constraints.pharmacophore.require_positions)

        mutable_positions = [
            pos
            for pos in range(1, len(sequence) + 1)
            if pos not in frozen
        ]
        mutable_positions.sort()

        design_space_size = 1
        for pos in mutable_positions:
            size = len(position_aa_map[pos])
            if size <= 0:
                raise ValueError(f"No allowed residues for mutable position {pos}")
            design_space_size *= size

        pairwise_rules = [rule.dict() for rule in self.config.constraints.pairwise_rules]
        self._compiled = CompiledConstraints(
            position_aa_map=position_aa_map,
            frozen_positions=frozen,
            pairwise_rules=pairwise_rules,
            design_space_size=design_space_size,
            mutable_positions=mutable_positions,
        )
        return self._compiled

    def compute_design_space_size(self) -> int:
        return self._ensure_compiled().design_space_size

    def get_mutable_positions(self) -> List[int]:
        return list(self._ensure_compiled().mutable_positions)

    def get_allowed_aas(self, position: int) -> List[str]:
        allowed = self._ensure_compiled().position_aa_map.get(position, set())
        return sorted(allowed)

    def validate_sequence(self, seq: str) -> ValidationResult:
        compiled = self._ensure_compiled()

        hard_violations: List[str] = []
        soft_violations: List[Tuple[str, float]] = []
        penalty_score = 0.0

        if len(seq) != len(compiled.position_aa_map):
            hard_violations.append("sequence_length_mismatch")
            return ValidationResult(False, hard_violations, soft_violations, penalty_score)

        upper = seq.upper()

        for pos, residue in enumerate(upper, start=1):
            if residue not in compiled.position_aa_map[pos]:
                hard_violations.append(f"pos_{pos}_disallowed_{residue}")
                continue

            if pos in self.config.constraints.frozen_positions and residue != self.config.sequence_metadata.peptide.template_sequence[pos - 1]:
                hard_violations.append(f"pos_{pos}_frozen")

        # Pharmacophore anchors are mandatory across allowed map, but explicitly check too.
        for pos in self.config.constraints.pharmacophore.require_positions:
            expected = self.config.constraints.pharmacophore.required_residues[pos]
            if upper[pos - 1] != expected:
                hard_violations.append(f"pharmacophore_pos_{pos}_{expected}_{upper[pos - 1]}")

        for rule in self.config.constraints.pairwise_rules:
            rule_dict = rule.dict()
            positions = rule_dict.get("positions", [])
            residues_at_positions = [upper[p - 1] for p in positions]
            mode = rule_dict.get("mode")
            rule_id = rule_dict.get("id", "pairwise_rule")
            rule_type = rule_dict.get("type")
            penalty_weight = float(rule_dict.get("penalty_weight", 0.0))

            is_violation = False

            if mode == "not_both_in_set":
                aa_set = set(rule_dict.get("aa_set", []))
                if all(r in aa_set for r in residues_at_positions):
                    is_violation = True
            elif mode == "max_count":
                aa_set = set(rule_dict.get("aa_set", []))
                max_count = int(rule_dict.get("max_count", 0))
                if sum(1 for r in residues_at_positions if r in aa_set) > max_count:
                    is_violation = True
            elif mode == "not_both_equal":
                aa_value = rule_dict.get("aa_value")
                if len(residues_at_positions) >= 2 and residues_at_positions[0] == aa_value and residues_at_positions[1] == aa_value:
                    is_violation = True

            if is_violation:
                if rule_type == "hard":
                    hard_violations.append(f"pairwise_hard_{rule_id}")
                else:
                    penalty = penalty_weight
                    soft_violations.append((f"pairwise_soft_{rule_id}", penalty))
                    penalty_score += penalty

        valid = not hard_violations
        return ValidationResult(valid, hard_violations, soft_violations, penalty_score)

    def _ensure_compiled(self) -> CompiledConstraints:
        if self._compiled is None:
            return self.compile()
        return self._compiled
