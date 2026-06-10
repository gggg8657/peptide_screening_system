"""Registry for mutation generation strategies."""

from __future__ import annotations

from pipeline_local.strategies.base import MutationStrategy

from .blosum import BlosumStrategy
from .dual_b1_b2 import DualB1B2Strategy
from .esm_scan import ESMScanStrategy
from .proteinmpnn import ProteinMPNNStrategy


STRATEGIES: dict[str, type[MutationStrategy]] = {
    "blosum": BlosumStrategy,
    "esm_scan": ESMScanStrategy,
    "proteinmpnn": ProteinMPNNStrategy,
    "dual_b1_b2": DualB1B2Strategy,
}


def get_strategy(name: str) -> MutationStrategy:
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy '{name}'. Available: {list(STRATEGIES)}")
    return STRATEGIES[name]()
