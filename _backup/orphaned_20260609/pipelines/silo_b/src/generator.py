from __future__ import annotations

import random
from typing import List

from .config import MutationConfig
from .constraint_compiler import ConstraintCompiler, CompiledConstraints
from .filters import DuplicateFilter


class MutantGenerator:
    """Generate constrained mutants from a compiled constraint set."""

    STRATEGY_ENUMERATE = "enumerate"
    STRATEGY_SAMPLE = "sampling"

    def __init__(self, compiled_constraints: CompiledConstraints, config: MutationConfig):
        self.compiled_constraints = compiled_constraints
        self.config = config
        self.template = config.sequence_metadata.peptide.template_sequence.upper()
        self.compiled = compiled_constraints
        self._validator = ConstraintCompiler(config)
        self._validator._compiled = compiled_constraints
        self.mutable_positions = list(compiled_constraints.mutable_positions)
        self.strategy = self._select_strategy()

    def _select_strategy(self) -> str:
        space_size = self.compiled.design_space_size
        threshold = self.config.generator.strategy.fallback.low_space_threshold
        if space_size <= threshold:
            return self.STRATEGY_ENUMERATE
        density = self._estimate_constraint_density(sample_size=min(space_size, 128))
        if density < self.config.generator.strategy.fallback.low_density_threshold:
            return self.STRATEGY_SAMPLE
        return self.config.generator.strategy.fallback.fallback_secondary

    def _estimate_constraint_density(self, sample_size: int) -> float:
        if sample_size <= 0:
            return 0.0
        if self.compiled.design_space_size == 0:
            return 0.0
        rng = random.Random(self.config.seed + 19)
        valid = 0
        for _ in range(sample_size):
            candidate = self._generate_single(rng)
            result = self._validator.validate_sequence(candidate)
            if result.valid:
                valid += 1
        return valid / float(sample_size)

    def _is_valid(self, sequence: str) -> bool:
        return self._validator.validate_sequence(sequence).valid

    def _generate_single(self, rng: random.Random) -> str:
        seq = list(self.template)
        for position in self.mutable_positions:
            allowed = sorted(self.compiled.position_aa_map[position])
            if not allowed:
                raise ValueError(f"No allowed amino acids for position {position}")
            seq[position - 1] = rng.choice(allowed)
        return "".join(seq)

    def _random_constrained(self, rng: random.Random) -> str:
        attempts = 0
        max_attempts = 10_000
        while attempts < max_attempts:
            candidate = self._generate_single(rng)
            if self._is_valid(candidate):
                return candidate
            attempts += 1
        raise RuntimeError("Unable to sample a valid candidate under current constraints")

    def enumerate_all(self) -> list[str]:
        if self.compiled.design_space_size <= 0:
            return []
        if self.compiled.design_space_size > 1_000_000:
            raise ValueError("Design space too large for full enumeration")

        mutable_positions = list(self.mutable_positions)
        allowed_by_position = [sorted(self.compiled.position_aa_map[pos]) for pos in mutable_positions]
        results: list[str] = []
        seq = list(self.template)

        def backtrack(level: int) -> None:
            if level == len(mutable_positions):
                candidate = "".join(seq)
                if self._is_valid(candidate):
                    results.append(candidate)
                return

            position = mutable_positions[level]
            for aa in allowed_by_position[level]:
                seq[position - 1] = aa
                backtrack(level + 1)

        backtrack(0)
        return results

    def sample_diverse(self, n: int, seed: int) -> list[str]:
        if n <= 0:
            return []

        if self.strategy == self.STRATEGY_ENUMERATE:
            all_candidates = self.enumerate_all()
            return list(dict.fromkeys(all_candidates))[:n]

        rng = random.Random(seed)
        min_distance = max(1, self.config.generator.diversity_policy.min_hamming_distance)
        deduper = DuplicateFilter(min_hamming_distance=min_distance)
        unique: list[str] = []

        attempts = 0
        max_attempts = max(1_000, n * 100)
        while len(unique) < n and attempts < max_attempts:
            candidate = self._random_constrained(rng)
            if candidate in unique:
                attempts += 1
                continue
            if deduper.is_duplicate(candidate):
                attempts += 1
                continue
            deduper.add_sequence(candidate)
            unique.append(candidate)
            attempts += 1

        if len(unique) < n:
            for candidate in self.enumerate_all():
                if candidate in unique:
                    continue
                if deduper.is_duplicate(candidate):
                    continue
                deduper.add_sequence(candidate)
                unique.append(candidate)
                if len(unique) >= n:
                    break
        return unique[:n]
