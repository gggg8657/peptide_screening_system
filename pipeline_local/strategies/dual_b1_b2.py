"""Dual B-1/B-2 mutation strategy.

Phase 4 combines ProteinMPNN (B-1) and ESM-Scan (B-2) with a deterministic
union merge. ProteinMPNN variants keep first priority; duplicate sequences from
ESM-Scan are represented by merging source provenance.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from pipeline_local.schemas.io_schemas import Step03bOutput, VariantEntry


class DualB1B2Strategy:
    """Generate variants with ProteinMPNN first, then ESM-Scan fallback coverage."""

    name = "dual_b1_b2"

    def __init__(self) -> None:
        from .esm_scan import ESMScanStrategy
        from .proteinmpnn import ProteinMPNNStrategy

        self.b1 = ProteinMPNNStrategy()
        self.b2 = ESMScanStrategy()

    def validate_env(self) -> tuple[bool, str | None]:
        ok1, err1 = self.b1.validate_env()
        ok2, err2 = self.b2.validate_env()
        if not ok1:
            return False, f"B-1: ProteinMPNN: {err1}"
        if not ok2:
            return False, f"B-2: ESM-Scan: {err2}"
        return True, None

    def generate(self, config: dict) -> Step03bOutput:
        out1 = self.b1.generate(config)
        out2 = self.b2.generate(config)
        merged = self._merge_with_provenance(out1.variants, out2.variants)

        ab_cfg = config.get("approach_b", config)
        max_variants = ab_cfg.get("max_variants")
        if max_variants is not None:
            # Deterministic truncate keeps B-1 priority and avoids random test drift.
            merged = merged[:int(max_variants)]
            self._assign_variant_ids(merged)

        return Step03bOutput(
            variants=merged,
            seed_sequence=out1.seed_sequence,
            fixed_positions=out1.fixed_positions,
            total_generated=len(merged),
            strategy="dual_b1_b2",
        )

    def _merge_with_provenance(
        self,
        v1: Iterable[VariantEntry],
        v2: Iterable[VariantEntry],
    ) -> list[VariantEntry]:
        """Union policy: duplicate sequences merge source as b1_proteinmpnn+b2_esm_scan."""
        by_seq: dict[str, VariantEntry] = {}

        for variant in v1:
            by_seq[variant.sequence] = replace(
                variant,
                source="b1_proteinmpnn",
            )

        for variant in v2:
            if variant.sequence in by_seq:
                existing = by_seq[variant.sequence]
                by_seq[variant.sequence] = replace(
                    existing,
                    source=f"{existing.source}+b2_esm_scan",
                )
            else:
                by_seq[variant.sequence] = replace(
                    variant,
                    source="b2_esm_scan",
                )

        result = list(by_seq.values())
        self._assign_variant_ids(result)
        return result

    @staticmethod
    def _assign_variant_ids(variants: list[VariantEntry]) -> None:
        for idx, variant in enumerate(variants, start=1):
            variant.variant_id = f"var_{idx:03d}"
