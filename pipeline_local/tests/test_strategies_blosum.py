from __future__ import annotations

import pytest

from pipeline_local.schemas.io_schemas import Step03bOutput
from pipeline_local.strategies.base import MutationStrategy
from pipeline_local.strategies.blosum import BlosumStrategy
from pipeline_local.strategies.registry import get_strategy


def _smoke_config(strategy: str = "random") -> dict:
    return {
        "reference_peptide": {"sequence": "AGCKNFFWKTFTSC"},
        "approach_b": {
            "strategy": strategy,
            "fixed_positions": {3: "C", 7: "F", 8: "W", 9: "K", 10: "T", 14: "C"},
            "min_blosum_score": 0,
            "max_mutations_per_variant": 2,
            "max_variants": 12,
            "hydrophobicity_max_delta": 2.0,
        },
    }


def test_blosum_strategy_conforms_to_protocol_and_validates_env():
    strategy = BlosumStrategy()

    assert isinstance(strategy, MutationStrategy)
    assert strategy.name == "blosum"
    assert strategy.validate_env() == (True, None)


def test_registry_returns_blosum_strategy_and_rejects_unknown():
    strategy = get_strategy("blosum")

    assert isinstance(strategy, BlosumStrategy)
    with pytest.raises(ValueError, match="Unknown strategy"):
        get_strategy("missing")


def test_blosum_strategy_phase1_smoke_matches_dispatcher():
    from pipeline_local.steps.step03b_blosum_mutation import run_approach_b

    config = _smoke_config()

    direct = BlosumStrategy().generate(config)
    dispatched = run_approach_b(config)

    assert isinstance(direct, Step03bOutput)
    assert direct.to_dict() == dispatched.to_dict()
    assert direct.total_generated == len(direct.variants)
    assert direct.total_generated > 0
    assert all(v.variant_id == f"var_{i:03d}" for i, v in enumerate(direct.variants, start=1))


def test_dispatcher_accepts_new_strategy_key_without_changing_blosum_defaults():
    from pipeline_local.steps.step03b_blosum_mutation import run_approach_b

    legacy = run_approach_b(_smoke_config(strategy="random"))
    phase1 = run_approach_b(_smoke_config(strategy="blosum"))

    assert phase1.strategy == "approach_b"
    assert phase1.to_dict() == legacy.to_dict()
