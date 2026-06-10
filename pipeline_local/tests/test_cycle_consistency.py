"""test_cycle_consistency.py
============================
harness Stage 8f (VR-cycle-07 closure) — 사이클 자기 일관성 회귀.

`_workspace/phase3_experiment.py`의 `TEST_CASES`(expected route)와 production
modification_conflict.py의 실제 동작이 일치하는지를 자동 검증.

배경 (VR-cycle-07):
  Phase 5에서 C-04 severity를 WARNING → ERROR로 격상하면서, phase3_experiment.py의
  expected="warning"이 outdated되었음. 재실험에서 12/12 → 10/12로 회귀,
  수동으로 expected를 갱신해서야 12/12 회복. 향후 자동 일관성 검증 메커니즘 필요.

본 테스트는 production code(modification_conflict.py)가 변경될 때 phase3_experiment의
expected와 불일치하면 즉시 pytest로 catch한다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# _workspace 디렉토리는 .gitignore되어 있지만 phase3_experiment.py는 force-add됨.
# sys.path에 추가해서 import 가능하게 함.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_DIR = PROJECT_ROOT / "_workspace"
if WORKSPACE_DIR.exists() and str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

try:
    from phase3_experiment import TEST_CASES, SST14  # type: ignore[import-not-found]
    _PHASE3_AVAILABLE = True
except ImportError:
    _PHASE3_AVAILABLE = False

from pipeline_local.scripts.modification_conflict import check_conflicts


@pytest.mark.skipif(not _PHASE3_AVAILABLE, reason="_workspace/phase3_experiment.py not available")
class TestPhase3ProductionConsistency:
    """phase3_experiment의 expected 값이 production code의 실제 동작과 일치하는지."""

    @pytest.mark.parametrize("name,mods,expected", TEST_CASES if _PHASE3_AVAILABLE else [])
    def test_case_matches_production(self, name, mods, expected):
        """각 TEST_CASE의 expected가 production check_conflicts() 결과와 일치."""
        conflicts = check_conflicts(SST14, mods)
        errors = [c for c in conflicts if c.severity == "ERROR"]
        warnings = [c for c in conflicts if c.severity == "WARNING"]

        if expected is True:
            assert len(errors) == 0, (
                f"[{name}] expected PASS (no errors) but got {len(errors)} errors: "
                f"{[c.rule_id for c in errors]}"
            )
        elif expected is False:
            assert len(errors) > 0, (
                f"[{name}] expected ERROR but no errors found. "
                f"WARNINGs: {[c.rule_id for c in warnings]}"
            )
        elif expected == "warning":
            assert len(warnings) > 0, (
                f"[{name}] expected WARNING but none. "
                f"ERRORs: {[c.rule_id for c in errors]}"
            )
        else:
            pytest.fail(f"[{name}] unknown expected value: {expected!r}")

    def test_total_case_count(self):
        """TEST_CASES 카운트가 줄지 않았는지 (회귀 감지)."""
        assert len(TEST_CASES) >= 12, (
            f"Phase 3 TEST_CASES count regressed: {len(TEST_CASES)} < 12. "
            f"phase3_experiment.py를 의도 없이 삭제하지 않았는지 확인."
        )

    def test_sst14_constant(self):
        """SST-14 시퀀스 상수가 변경되지 않았는지."""
        assert SST14 == "AGCKNFFWKTFTSC", (
            f"SST14 시퀀스 변경 감지: {SST14}. 이는 도메인 핵심 상수이며 변경 시 "
            f"전체 사이클 산출물을 재실행해야 함."
        )
