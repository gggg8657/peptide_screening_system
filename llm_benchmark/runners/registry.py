"""Flow runner registry — maps flow name to runner class."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseFlowRunner

_REGISTRY: dict[str, str] = {
    "sequential": "runners.base.SequentialFlowRunner",
    "collaborative": "runners.collaborative.CollaborativeFlowRunner",
    "hierarchical": "runners.hierarchical.HierarchicalFlowRunner",
    "v2_sequential": "runners.v2_sequential.V2SequentialFlowRunner",
}


def get_runner(flow_name: str) -> type["BaseFlowRunner"]:
    """Return the runner class for the given flow pattern name."""
    import importlib

    dotpath = _REGISTRY[flow_name]
    module_path, class_name = dotpath.rsplit(".", 1)
    module = importlib.import_module(f"llm_benchmark.{module_path}")
    return getattr(module, class_name)
