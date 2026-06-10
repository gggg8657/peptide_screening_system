from __future__ import annotations

import inspect

from pipeline_local import orchestrator


def test_orchestrator_avoids_runtime_lookup_and_anonymous_stub():
    source = inspect.getsource(orchestrator)

    assert "locals().get(" not in source
    assert "type('R', ()," not in source
    assert 'StepResult(' in source
