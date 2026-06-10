"""
Validation Facade
==================
Single entry point for all validation functionality.

Wraps:
- backend.validation       → validate_batch (statistical math validation)
- backend.unified_validation → validate_unified, get_criteria_registry
                               (pharmacological + statistical combined)

Original modules remain intact — this is a facade, not a merge.
"""
from __future__ import annotations

from typing import Any

from backend.validation import validate_batch
from backend.unified_validation import get_criteria_registry, validate_unified

__all__ = [
    "validate_batch",
    "validate_unified",
    "get_criteria_registry",
]
