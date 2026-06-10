"""Base protocol for mutation generation strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from pipeline_local.schemas.io_schemas import Step03bOutput


@dataclass
class StrategyConfig:
    """Container for strategy-specific configuration."""

    name: str
    params: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class MutationStrategy(Protocol):
    name: str  # "blosum" | "proteinmpnn" | "esm_scan" | "dual_b1_b2"

    def generate(self, config: dict) -> Step03bOutput: ...

    def validate_env(self) -> tuple[bool, str | None]: ...
