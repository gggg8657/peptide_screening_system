"""test_composite_scorer_fallback_warn.py
=========================================
묶음 B 테스트: composite_scorer.py wrapper 실패 fallback 명시 경고 회귀.

검증 항목:
  - ADMET wrapper 실패 시 enrichment_notes에 ADMET_FALLBACK_WARNING 포함
  - ADMET wrapper 실패 시 fallback_admet_tox=True 설정
  - ADMET wrapper 실패 시 warnings 배열 누적
  - 정상 동작 시 fallback_admet_tox=False (silent fallback 없음 검증)

근거:
  reviewer-pharma §7-C — composite_scorer의 의뢰서 ADMET 0.10~0.25 값이
  wrapper 실패 fallback 값임을 명시하지 않으면 OOD 오분류를 숨기게 됨.
  _workspace/55_reviewer-pharma_prst-admet-ood-analysis.md §6:
  "의뢰서 ADMET 0.10~0.25 — composite_scorer fallback (실측값 아님)" → INVALID.
"""
from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from pipeline_local.scripts.composite_scorer import (
    ADMET_FALLBACK_WARNING,
    UNAVAILABLE_GRADE,
    _append_warning,
    _coerce_notes,
    enrich_candidates_from_wrappers,
)


# ---------------------------------------------------------------------------
# ADMET_FALLBACK_WARNING 상수 검증
# ---------------------------------------------------------------------------

class TestAdmetFallbackWarningConstant:
    """ADMET_FALLBACK_WARNING 상수 정의 검증."""

    def test_constant_defined(self):
        """ADMET_FALLBACK_WARNING 상수가 정의되어야 한다."""
        assert ADMET_FALLBACK_WARNING, "ADMET_FALLBACK_WARNING이 빈 문자열 또는 None"

    def test_constant_contains_fallback_marker(self):
        """ADMET_FALLBACK_WARNING은 'fallback value used'와 'REAL_MEASUREMENT_MISSING'을 포함해야 한다."""
        assert "fallback value used" in ADMET_FALLBACK_WARNING, (
            f"ADMET_FALLBACK_WARNING에 'fallback value used' 미포함: {ADMET_FALLBACK_WARNING!r}"
        )
        assert "REAL_MEASUREMENT_MISSING" in ADMET_FALLBACK_WARNING, (
            f"ADMET_FALLBACK_WARNING에 'REAL_MEASUREMENT_MISSING' 미포함: {ADMET_FALLBACK_WARNING!r}"
        )

    def test_constant_references_admet_tox_wrapper(self):
        """상수가 admet_tox_wrapper_failed 마커를 포함해야 한다."""
        assert "admet_tox_wrapper_failed" in ADMET_FALLBACK_WARNING, (
            f"ADMET_FALLBACK_WARNING에 'admet_tox_wrapper_failed' 미포함: {ADMET_FALLBACK_WARNING!r}"
        )


# ---------------------------------------------------------------------------
# _append_warning 함수 단위 테스트
# ---------------------------------------------------------------------------

class TestAppendWarning:
    """_append_warning() 내부 헬퍼 동작 검증."""

    def test_appends_to_notes_and_warnings(self):
        """_append_warning 호출 시 notes와 warnings 배열 모두 업데이트."""
        candidate: Dict[str, Any] = {"candidate_id": "cand_x", "warnings": []}
        notes: List[str] = []
        _append_warning(candidate, notes, ADMET_FALLBACK_WARNING)
        assert ADMET_FALLBACK_WARNING in notes
        assert ADMET_FALLBACK_WARNING in candidate["warnings"]

    def test_sets_fallback_admet_tox_true(self):
        """_append_warning 호출 시 fallback_admet_tox=True 설정."""
        candidate: Dict[str, Any] = {"candidate_id": "cand_y"}
        notes: List[str] = []
        _append_warning(candidate, notes, ADMET_FALLBACK_WARNING)
        assert candidate.get("fallback_admet_tox") is True

    def test_no_duplicate_in_notes(self):
        """동일 경고 중복 추가 방지."""
        candidate: Dict[str, Any] = {"candidate_id": "cand_z", "warnings": []}
        notes: List[str] = []
        _append_warning(candidate, notes, ADMET_FALLBACK_WARNING)
        _append_warning(candidate, notes, ADMET_FALLBACK_WARNING)
        assert notes.count(ADMET_FALLBACK_WARNING) == 1, (
            "_append_warning이 동일 경고를 중복으로 추가함"
        )
        assert candidate["warnings"].count(ADMET_FALLBACK_WARNING) == 1


# ---------------------------------------------------------------------------
# enrich_candidates_from_wrappers — wrapper 실패 시나리오 테스트
# ---------------------------------------------------------------------------

def _make_candidate(cid: str = "prst_test", seq: str = "AGCKNFFWKTFTSC") -> Dict[str, Any]:
    return {"candidate_id": cid, "sequence": seq}


class TestCompositeScorerWarnOnWrapperFailure:
    """묶음 B: wrapper 실패 시 명시 경고 동작 회귀.

    admet wrapper가 예외를 발생시킬 때 enrichment_notes와 warnings에
    ADMET_FALLBACK_WARNING이 포함되고, fallback_admet_tox=True가 설정되어야 한다.
    """

    def test_composite_scorer_warn_on_wrapper_failure(self):
        """admet wrapper 예외 → ADMET_FALLBACK_WARNING 포함 + fallback_admet_tox=True."""
        candidate = _make_candidate()

        # enrich_candidates_from_wrappers 내부에서 lazy import되는 함수는
        # source 모듈에서 패치해야 한다.
        with (
            patch(
                "pipeline_local.scripts.predict_admet_pepadmet.predict_admet",
                side_effect=RuntimeError("mock admet failure"),
            ),
            patch(
                "pipeline_local.scripts.predict_halflife_pepmsnd.predict_halflife",
                return_value={"halflife_score": 5.0, "final_confidence_grade": "P4"},
            ),
            patch(
                "pipeline_local.scripts.sequence_to_smiles.sequence_to_linear_smiles",
                return_value={"smiles": "CC", "warnings": []},
            ),
        ):
            results = enrich_candidates_from_wrappers([candidate])

        assert len(results) == 1
        result = results[0]

        # ADMET_FALLBACK_WARNING이 enrichment_notes에 포함되어야 한다
        enrichment_notes = result.get("enrichment_notes", [])
        assert any(ADMET_FALLBACK_WARNING in n for n in enrichment_notes), (
            f"ADMET_FALLBACK_WARNING이 enrichment_notes에 없음. 현재 notes: {enrichment_notes}"
        )

        # fallback_admet_tox=True 확인
        assert result.get("fallback_admet_tox") is True, (
            f"admet wrapper 실패 후 fallback_admet_tox가 True가 아님: {result.get('fallback_admet_tox')}"
        )

        # warnings 배열에도 포함되어야 한다
        warnings_list = result.get("warnings", [])
        assert any(ADMET_FALLBACK_WARNING in w for w in warnings_list), (
            f"ADMET_FALLBACK_WARNING이 warnings 배열에 없음. 현재 warnings: {warnings_list}"
        )

        # admet_confidence_grade == UNAVAILABLE_GRADE
        assert result.get("admet_confidence_grade") == UNAVAILABLE_GRADE

    def test_composite_scorer_warn_on_wrapper_no_score(self):
        """admet wrapper 성공 but None score → ADMET_FALLBACK_WARNING 포함."""
        candidate = _make_candidate()

        # predict_admet이 성공하지만 추출 가능한 score가 없는 경우
        mock_admet_result: Dict[str, Any] = {"some_field": "no_tox_score"}

        with (
            patch(
                "pipeline_local.scripts.predict_admet_pepadmet.predict_admet",
                return_value=mock_admet_result,
            ),
            patch(
                "pipeline_local.scripts.predict_halflife_pepmsnd.predict_halflife",
                return_value={"halflife_score": 3.0, "final_confidence_grade": "P4"},
            ),
            patch(
                "pipeline_local.scripts.sequence_to_smiles.sequence_to_linear_smiles",
                return_value={"smiles": "CCC", "warnings": []},
            ),
        ):
            results = enrich_candidates_from_wrappers([candidate])

        assert len(results) == 1
        result = results[0]
        enrichment_notes = result.get("enrichment_notes", [])
        assert any(ADMET_FALLBACK_WARNING in n for n in enrichment_notes), (
            f"score=None 케이스에서 ADMET_FALLBACK_WARNING 미포함. notes: {enrichment_notes}"
        )
        assert result.get("fallback_admet_tox") is True


class TestCompositeScorerNoSilentFallback:
    """묶음 B: silent fallback 없음 — 정상 동작 시 fallback_admet_tox=False.

    admet wrapper가 정상적으로 score를 반환하면 fallback_admet_tox=False여야 하고,
    ADMET_FALLBACK_WARNING이 enrichment_notes에 없어야 한다.
    """

    def test_composite_scorer_no_silent_fallback_on_success(self):
        """admet wrapper 정상 반환 → fallback_admet_tox=False, WARN 없음."""
        candidate = _make_candidate()

        mock_admet_result: Dict[str, Any] = {
            "admet_tox": 0.15,
            "final_confidence_grade": "P1",
        }

        with (
            patch(
                "pipeline_local.scripts.predict_admet_pepadmet.predict_admet",
                return_value=mock_admet_result,
            ),
            patch(
                "pipeline_local.scripts.predict_halflife_pepmsnd.predict_halflife",
                return_value={"halflife_score": 7.0, "final_confidence_grade": "P3"},
            ),
            patch(
                "pipeline_local.scripts.sequence_to_smiles.sequence_to_linear_smiles",
                return_value={"smiles": "CCCC", "warnings": []},
            ),
        ):
            results = enrich_candidates_from_wrappers([candidate])

        assert len(results) == 1
        result = results[0]

        # 정상 동작 시 fallback_admet_tox는 False (또는 미설정 → 기본값 False)
        assert not result.get("fallback_admet_tox", False), (
            f"admet wrapper 정상 반환 후 fallback_admet_tox가 True: 의도하지 않은 fallback 표시"
        )

        # ADMET_FALLBACK_WARNING이 enrichment_notes에 없어야 한다
        enrichment_notes = result.get("enrichment_notes", [])
        assert not any(ADMET_FALLBACK_WARNING in n for n in enrichment_notes), (
            f"정상 동작 케이스에서 ADMET_FALLBACK_WARNING이 발생: silent fallback 방지 실패. "
            f"notes: {enrichment_notes}"
        )

        # 실제 admet_tox 값이 설정되어야 한다
        assert result.get("admet_tox") == pytest.approx(0.15), (
            f"admet_tox 값이 0.15로 설정되지 않음: {result.get('admet_tox')}"
        )

    def test_composite_scorer_d_aa_no_fallback_warning(self):
        """D-AA 후보는 wrapper 스킵 (UNAVAILABLE) — ADMET_FALLBACK_WARNING 미적용.

        D-AA 후보의 enrichment_notes에는 wrapper 스킵 메시지만 있어야 하고,
        ADMET_FALLBACK_WARNING은 포함되지 않아야 한다.
        (D-AA 스킵은 fallback이 아니라 intentional skip)
        """
        d_aa_candidate = _make_candidate(seq="d-Ala-Gly-Cys")

        with (
            patch(
                "pipeline_local.scripts.predict_admet_pepadmet.predict_admet",
                side_effect=RuntimeError("should not be called"),
            ),
            patch(
                "pipeline_local.scripts.predict_halflife_pepmsnd.predict_halflife",
                side_effect=RuntimeError("should not be called"),
            ),
            patch(
                "pipeline_local.scripts.sequence_to_smiles.sequence_to_linear_smiles",
                side_effect=RuntimeError("should not be called"),
            ),
        ):
            results = enrich_candidates_from_wrappers([d_aa_candidate])

        assert len(results) == 1
        result = results[0]
        assert result.get("admet_confidence_grade") == UNAVAILABLE_GRADE
        # D-AA는 intentional skip — ADMET_FALLBACK_WARNING 해당 없음
        enrichment_notes = result.get("enrichment_notes", [])
        assert not any(ADMET_FALLBACK_WARNING in n for n in enrichment_notes), (
            "D-AA 스킵에 ADMET_FALLBACK_WARNING이 잘못 포함됨"
        )
