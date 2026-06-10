from __future__ import annotations

from pipeline_local.schemas.io_schemas import Step03bOutput, VariantEntry
from pipeline_local.strategies.base import MutationStrategy
from pipeline_local.strategies.dual_b1_b2 import DualB1B2Strategy
from pipeline_local.strategies.registry import get_strategy


SEED = "AGCKNFFWKTFTSC"
FIXED = {3: "C", 7: "F", 8: "W", 9: "K", 10: "T", 14: "C"}


def _variant(variant_id: str, sequence: str, source: str = "mock") -> VariantEntry:
    return VariantEntry(
        variant_id=variant_id,
        sequence=sequence,
        parent_sequence=SEED,
        mutations=[],
        n_mutations=0,
        blosum_total_score=0,
        source=source,
    )


def _output(variants: list[VariantEntry], strategy: str) -> Step03bOutput:
    return Step03bOutput(
        variants=variants,
        seed_sequence=SEED,
        fixed_positions=FIXED,
        total_generated=len(variants),
        strategy=strategy,
    )


class _FakeStrategy:
    def __init__(
        self,
        output: Step03bOutput | None = None,
        env: tuple[bool, str | None] = (True, None),
    ) -> None:
        self.output = output or _output([], "fake")
        self.env = env

    def validate_env(self) -> tuple[bool, str | None]:
        return self.env

    def generate(self, config: dict) -> Step03bOutput:
        return self.output


def _strategy(
    b1_output: Step03bOutput | None = None,
    b2_output: Step03bOutput | None = None,
    b1_env: tuple[bool, str | None] = (True, None),
    b2_env: tuple[bool, str | None] = (True, None),
) -> DualB1B2Strategy:
    strategy = DualB1B2Strategy()
    strategy.b1 = _FakeStrategy(b1_output, b1_env)
    strategy.b2 = _FakeStrategy(b2_output, b2_env)
    return strategy


def test_dual_b1_b2_strategy_conforms_to_protocol():
    strategy = DualB1B2Strategy()

    assert isinstance(strategy, MutationStrategy)
    assert strategy.name == "dual_b1_b2"
    assert isinstance(get_strategy("dual_b1_b2"), DualB1B2Strategy)


def test_validate_env_reports_b1_failure():
    ok, err = _strategy(b1_env=(False, "missing ligandmpnn")).validate_env()

    assert ok is False
    assert err == "B-1: ProteinMPNN: missing ligandmpnn"


def test_validate_env_reports_b2_failure_after_b1_passes():
    ok, err = _strategy(b2_env=(False, "missing torch")).validate_env()

    assert ok is False
    assert err == "B-2: ESM-Scan: missing torch"


def test_generate_smoke_merges_outputs_with_b1_priority():
    b1 = _output(
        [
            _variant("pmpnn_1", "SGCKNFFWKTFTSC"),
            _variant("pmpnn_2", "AGCRNFFWKTFTSC"),
        ],
        "proteinmpnn",
    )
    b2 = _output(
        [
            _variant("esm_1", "AGCRNFFWKTFTSC"),
            _variant("esm_2", "AGCKNFFWKTFLSC"),
        ],
        "esm_scan",
    )

    result = _strategy(b1, b2).generate({"approach_b": {"strategy": "dual_b1_b2"}})

    assert isinstance(result, Step03bOutput)
    assert result.strategy == "dual_b1_b2"
    assert result.seed_sequence == SEED
    assert result.fixed_positions == FIXED
    assert result.total_generated == 3
    assert [v.sequence for v in result.variants] == [
        "SGCKNFFWKTFTSC",
        "AGCRNFFWKTFTSC",
        "AGCKNFFWKTFLSC",
    ]
    assert [v.source for v in result.variants] == [
        "b1_proteinmpnn",
        "b1_proteinmpnn+b2_esm_scan",
        "b2_esm_scan",
    ]
    assert [v.variant_id for v in result.variants] == ["var_001", "var_002", "var_003"]


def test_merge_with_provenance_union_policy_and_variant_id_reassignment():
    merged = DualB1B2Strategy()._merge_with_provenance(
        [
            _variant("old_101", "SGCKNFFWKTFTSC"),
            _variant("old_102", "AGCRNFFWKTFTSC"),
        ],
        [
            _variant("old_201", "SGCKNFFWKTFTSC"),
            _variant("old_202", "AGCKNFFWKTFLSC"),
        ],
    )

    assert [v.sequence for v in merged] == [
        "SGCKNFFWKTFTSC",
        "AGCRNFFWKTFTSC",
        "AGCKNFFWKTFLSC",
    ]
    assert [v.source for v in merged] == [
        "b1_proteinmpnn+b2_esm_scan",
        "b1_proteinmpnn",
        "b2_esm_scan",
    ]
    assert [v.variant_id for v in merged] == ["var_001", "var_002", "var_003"]


def test_generate_applies_deterministic_max_variants_truncate_after_union():
    b1 = _output(
        [
            _variant("pmpnn_1", "SGCKNFFWKTFTSC"),
            _variant("pmpnn_2", "AGCRNFFWKTFTSC"),
        ],
        "proteinmpnn",
    )
    b2 = _output(
        [
            _variant("esm_1", "AGCKNFFWKTFLSC"),
            _variant("esm_2", "TGCKNFFWKTFTSC"),
        ],
        "esm_scan",
    )

    result = _strategy(b1, b2).generate(
        {"approach_b": {"strategy": "dual_b1_b2", "max_variants": 2}}
    )

    assert [v.sequence for v in result.variants] == [
        "SGCKNFFWKTFTSC",
        "AGCRNFFWKTFTSC",
    ]
    assert result.total_generated == 2
    assert [v.variant_id for v in result.variants] == ["var_001", "var_002"]
