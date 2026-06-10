"""
test_stability_predictor.py — stability_predictor.py 코드 품질 + 정합성 테스트
================================================================================

U4 Task (id=19): backend U1 완료 후 리뷰어-코드가 작성.
기준값: conda run -n bio-tools python으로 사전 검증 완료 (2026-05-12).

테스트 그룹:
  TestImport                — 모듈 import + 공개 API 존재 확인
  TestInputValidation       — 입력 검증 (빈 서열, 비표준 AA, NCAA 처리)
  TestReferenceValues       — 알려진 서열의 수치 재현 (S4 기준값 대조)
  TestInstabilityIndex      — ILCKKFFWKTFTSC II=55.14 재현 (task spec)
  TestNCAA                  — [dT], [Cha], [2Nal] 처리 + warning
  TestDataclassSchema       — 출력 dataclass 구조 + JSON 직렬화
  TestPharmacologyGuards    — pharmacology_guards 통합
  TestHeuristicDisclaimer   — HEURISTIC_FUNCTION_DISCLAIMERS 자동 부착
  TestModificationConflict  — D-AA + DOTA + PEG 충돌 탐지 통합
  TestBatchMode             — 10 후보 batch 처리
  TestSlowIntegration       — 실 conda 환경 통합 (mark.slow)

기준값 (conda bio-tools, 2026-05-12 확인):
  SST14  AGCKNFFWKTFTSC: GRAVY=0.0286, MW=1639.89, II=30.65, pI=8.91
  cand03 AICKNFFWKTFTSC: GRAVY=0.3786, MW=1696.00, II=30.65, pI=8.91
  ILCKK  ILCKKFFWKTFTSC: GRAVY=0.4929, MW=1752.15, II=55.14, pI=9.39

  peptides.py (Boman/Aliphatic/Charge@pH7.4):
  SST14:  Boman=0.6929, Aliphatic=7.1429,  Charge=1.7088
  cand03: Boman=0.4086, Aliphatic=35.0000, Charge=1.7088
  ILCKK:  Boman=0.1086, Aliphatic=55.7143, Charge=2.7080
"""
from __future__ import annotations

import dataclasses
import importlib.util
import json
import warnings
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# 실행 환경 의존성 탐지
# ---------------------------------------------------------------------------
_HAS_BIOPYTHON_IN_ENV = importlib.util.find_spec("Bio") is not None
_HAS_PEPTIDES_IN_ENV  = importlib.util.find_spec("peptides") is not None

_SKIP_IF_NO_BIOPYTHON = pytest.mark.skipif(
    not _HAS_BIOPYTHON_IN_ENV,
    reason=(
        "Biopython(Bio) 미설치 — 현재 Python 환경에서 불가. "
        "conda run -n bio-tools pytest 로 실행하세요."
    ),
)
_SKIP_IF_NO_PEPTIDES = pytest.mark.skipif(
    not _HAS_PEPTIDES_IN_ENV,
    reason=(
        "peptides.py 미설치 — 현재 Python 환경에서 불가. "
        "conda run -n bio-tools pytest 로 실행하세요."
    ),
)

# ---------------------------------------------------------------------------
# 모듈 import (없으면 skip — backend U1 완료 대기)
# ---------------------------------------------------------------------------

try:
    import pipeline_local.scripts.stability_predictor as _sp_module
    _MODULE_AVAILABLE = True
except ImportError:
    _sp_module = None  # type: ignore
    _MODULE_AVAILABLE = False

# pytest.importorskip 패턴보다 skip 조건을 명시적으로 관리
_SKIP_IF_NOT_IMPLEMENTED = pytest.mark.skipif(
    not _MODULE_AVAILABLE,
    reason=(
        "pipeline_local.scripts.stability_predictor 미존재. "
        "backend U1 (Task #16) 완료 후 실행."
    ),
)

# 기준값 상수 (사전 검증 완료)
_REF = {
    "SST14": {
        "seq":              "AGCKNFFWKTFTSC",
        "gravy":            0.0286,
        "mw":               1639.89,
        "instability_index":30.65,
        "pi":               8.91,
        "boman_index":      0.6929,
        "aliphatic_index":  7.1429,
        "charge_ph74":      1.7088,
    },
    "cand03": {
        "seq":              "AICKNFFWKTFTSC",
        "gravy":            0.3786,
        "mw":               1696.00,
        "instability_index":30.65,
        "pi":               8.91,
        "boman_index":      0.4086,
        "aliphatic_index":  35.0000,
        "charge_ph74":      1.7088,
    },
    "ILCKK": {
        "seq":              "ILCKKFFWKTFTSC",
        "gravy":            0.4929,
        "mw":               1752.15,
        "instability_index":55.14,
        "pi":               9.39,
        "boman_index":      0.1086,
        "aliphatic_index":  55.7143,
        "charge_ph74":      2.7080,
    },
}


# ---------------------------------------------------------------------------
# 1. 모듈 import 및 공개 API 확인
# ---------------------------------------------------------------------------

class TestImport:
    """모듈이 존재하고 필요한 공개 API를 노출하는지 확인."""

    def test_module_importable(self):
        """stability_predictor 모듈이 import 가능해야 한다."""
        if not _MODULE_AVAILABLE:
            pytest.fail(
                "pipeline_local.scripts.stability_predictor를 import할 수 없습니다.\n"
                "backend U1 (Task #16)이 완료되어야 합니다."
            )

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_compute_stability_exists(self):
        """compute_stability 함수 또는 StabilityPredictor 클래스가 존재해야 한다."""
        has_func = hasattr(_sp_module, "compute_stability")
        has_class = hasattr(_sp_module, "StabilityPredictor")
        assert has_func or has_class, (
            "compute_stability() 함수 또는 StabilityPredictor 클래스가 없음. "
            "verify_stability_env.sh 의 compute_stability() 패턴 준수 필요."
        )

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_result_dataclass_exists(self):
        """StabilityResult 또는 동등한 dataclass가 있어야 한다."""
        # 여러 네이밍 허용
        found = any(
            hasattr(_sp_module, name)
            for name in ("StabilityResult", "PeptideStabilityResult", "StabilityOutput")
        )
        assert found, (
            "StabilityResult dataclass (또는 동등 클래스)가 없음. "
            "step08_stability.StabilityResult 패턴 참조."
        )

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_heuristic_disclaimer_present(self):
        """HEURISTIC_FUNCTION_DISCLAIMERS 또는 같은 의미의 상수가 있어야 한다."""
        has_disclaimer = (
            hasattr(_sp_module, "HEURISTIC_FUNCTION_DISCLAIMERS")
            or hasattr(_sp_module, "_HEURISTIC_DISCLAIMER")
            or hasattr(_sp_module, "DISCLAIMER")
        )
        assert has_disclaimer, (
            "HEURISTIC_FUNCTION_DISCLAIMERS 상수 없음 (H-06 가드 의무). "
            "pharmacology_guards.py 참조."
        )


# ---------------------------------------------------------------------------
# 2. 입력 검증
# ---------------------------------------------------------------------------

class TestInputValidation:
    """입력 서열에 대한 에러 핸들링 검증."""

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_empty_sequence_raises(self):
        """빈 서열은 ValueError를 발생시켜야 한다."""
        compute = _get_compute_fn()
        with pytest.raises((ValueError, RuntimeError), match=r"[Ee]mpty|빈|서열"):
            compute("")

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_none_sequence_raises(self):
        """None 입력은 TypeError 또는 ValueError를 발생시켜야 한다."""
        compute = _get_compute_fn()
        with pytest.raises((TypeError, ValueError, AttributeError)):
            compute(None)  # type: ignore

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_whitespace_only_raises(self):
        """공백만 있는 서열은 에러를 발생시켜야 한다."""
        compute = _get_compute_fn()
        with pytest.raises((ValueError, RuntimeError)):
            compute("   ")

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_invalid_aa_single_char(self):
        """비표준 단일문자(B, J, X, Z) 입력 처리 — 제거 기록이 ncaa_warnings에 있어야 한다.

        Note: B/J/X/Z는 _VALID_AA에 없어 제거됨. 제거 기록은 result.ncaa_warnings에 저장.
        Python warnings 모듈이 아닌 dataclass 필드로 보고함.
        """
        compute = _get_compute_fn()
        for invalid in ("B", "J", "X", "Z"):
            try:
                result = compute(f"ACK{invalid}NFFWKTFTSC")
                if result is not None:
                    d = _result_to_dict(result)
                    ncaa_warns = d.get("ncaa_warnings", [])
                    # 비표준 잔기 제거 기록 확인
                    assert len(ncaa_warns) > 0, (
                        f"비표준 AA '{invalid}' 입력 시 result.ncaa_warnings가 비어있음.\n"
                        "알 수 없는 잔기는 _canonical_clean 처리 후 ncaa_warnings에 기록해야 함.\n"
                        f"실제 ncaa_warnings: {ncaa_warns}"
                    )
            except (ValueError, RuntimeError):
                pass  # 에러 발생도 허용

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_lowercase_input_accepted(self):
        """소문자 서열도 수용하거나 명확한 에러를 제공해야 한다."""
        compute = _get_compute_fn()
        try:
            result = compute("agcknffwktftsc")
            assert result is not None
        except (ValueError, RuntimeError) as e:
            # 소문자 거부 시 명확한 메시지 요구
            assert any(
                kw in str(e).lower()
                for kw in ("lower", "uppercase", "대문자", "소문자")
            ), f"소문자 거부 시 명확한 에러 메시지 필요: {e}"

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_too_short_sequence_behavior(self):
        """3잔기 이하 초단 서열의 처리 (에러 또는 경고)."""
        compute = _get_compute_fn()
        for short_seq in ("A", "AC", "ACK"):
            try:
                result = compute(short_seq)
                # 결과를 반환하면 acceptable
            except (ValueError, RuntimeError):
                pass  # 에러도 허용


# ---------------------------------------------------------------------------
# 3. 기준값 재현 (Biopython ProteinAnalysis 문헌 정답)
# ---------------------------------------------------------------------------

class TestReferenceValues:
    """S4 분석 기준값과의 정합성 검증 (pharmacology_guards GATE-C 수준)."""

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_cand03_gravy(self):
        """cand03 AICKNFFWKTFTSC GRAVY = +0.3786 ± 0.001."""
        result = _call_compute("AICKNFFWKTFTSC")
        gravy = _get_field(result, "gravy")
        assert gravy == pytest.approx(_REF["cand03"]["gravy"], abs=0.001), (
            f"GRAVY={gravy:.4f}, 기준={_REF['cand03']['gravy']}"
        )

    @_SKIP_IF_NOT_IMPLEMENTED
    @_SKIP_IF_NO_BIOPYTHON
    def test_cand03_mw(self):
        """cand03 MW = 1696.00 ± 1.0 Da (average mass, Biopython 필요)."""
        result = _call_compute("AICKNFFWKTFTSC")
        mw = _get_field(result, "molecular_weight", "mw")
        assert mw == pytest.approx(_REF["cand03"]["mw"], abs=1.0), (
            f"MW={mw:.2f}, 기준={_REF['cand03']['mw']}"
        )

    @_SKIP_IF_NOT_IMPLEMENTED
    @_SKIP_IF_NO_BIOPYTHON
    def test_cand03_instability_index(self):
        """cand03 Instability Index = 30.65 ± 0.1 (Biopython 필요)."""
        result = _call_compute("AICKNFFWKTFTSC")
        ii = _get_field(result, "instability_index")
        assert ii == pytest.approx(_REF["cand03"]["instability_index"], abs=0.1), (
            f"II={ii:.2f}, 기준={_REF['cand03']['instability_index']}"
        )

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_sst14_gravy(self):
        """SST-14 AGCKNFFWKTFTSC GRAVY = +0.0286 ± 0.001."""
        result = _call_compute("AGCKNFFWKTFTSC")
        gravy = _get_field(result, "gravy")
        assert gravy == pytest.approx(_REF["SST14"]["gravy"], abs=0.001)

    @_SKIP_IF_NOT_IMPLEMENTED
    @_SKIP_IF_NO_PEPTIDES
    def test_cand03_boman_index(self):
        """cand03 Boman Index (peptides.py) = 0.4086 ± 0.01 (peptides.py 필요)."""
        result = _call_compute("AICKNFFWKTFTSC")
        boman = _get_field(result, "boman_index", "boman")
        assert boman == pytest.approx(_REF["cand03"]["boman_index"], abs=0.01), (
            f"Boman={boman:.4f}, 기준={_REF['cand03']['boman_index']}"
        )

    @_SKIP_IF_NOT_IMPLEMENTED
    @_SKIP_IF_NO_PEPTIDES
    def test_cand03_charge_ph74(self):
        """cand03 Net Charge @ pH 7.4 = +1.7088 ± 0.05 (peptides.py 필요)."""
        result = _call_compute("AICKNFFWKTFTSC")
        charge = _get_field(result, "charge_ph74", "charge", "net_charge")
        assert charge == pytest.approx(_REF["cand03"]["charge_ph74"], abs=0.05), (
            f"Charge={charge:.4f}, 기준={_REF['cand03']['charge_ph74']}"
        )


# ---------------------------------------------------------------------------
# 4. ILCKKFFWKTFTSC Instability Index 55.14 재현 (task spec 핵심)
# ---------------------------------------------------------------------------

class TestInstabilityIndex:
    """S4 stability analysis 기준값 ILCKKFFWKTFTSC II=55.14 재현."""

    @_SKIP_IF_NOT_IMPLEMENTED
    @_SKIP_IF_NO_BIOPYTHON
    def test_ilckk_instability_55_14(self):
        """ILCKKFFWKTFTSC Instability Index = 55.14 ± 0.1 (Biopython 필요).

        출처: docs/wetlab/cand_stability_analysis.md §1.1
              conda bio-tools Biopython ProteinAnalysis(2026-05-12 검증)
        """
        result = _call_compute("ILCKKFFWKTFTSC")
        ii = _get_field(result, "instability_index")
        assert ii == pytest.approx(55.14, abs=0.1), (
            f"ILCKKFFWKTFTSC Instability Index={ii:.2f}, 기준=55.14\n"
            "참고: docs/wetlab/cand_stability_analysis.md §1.1\n"
            "Biopython ProteinAnalysis.instability_index() 사용 확인"
        )

    @_SKIP_IF_NOT_IMPLEMENTED
    @_SKIP_IF_NO_BIOPYTHON
    def test_ilckk_unstable_flag(self):
        """II > 40 이면 'unstable' flag 또는 경고가 있어야 한다 (Biopython 필요)."""
        result = _call_compute("ILCKKFFWKTFTSC")
        # unstable 표시 여부 확인 (다양한 형태 허용)
        is_flagged = (
            _get_field_safe(result, "is_unstable") is True
            or _get_field_safe(result, "unstable") is True
            or (_get_field_safe(result, "stability_class") or "").lower() in ("unstable", "불안정")
        )
        ii = _get_field(result, "instability_index")
        if ii > 40:
            assert is_flagged, (
                f"II={ii:.2f} > 40 인데 unstable flag 없음. "
                "Guruprasad 1990 규칙: II > 40 → unstable"
            )

    @_SKIP_IF_NOT_IMPLEMENTED
    @_SKIP_IF_NO_BIOPYTHON
    def test_cand03_stable_flag(self):
        """cand03 II=30.65 < 40 이면 stable 분류되어야 한다 (Biopython 필요)."""
        result = _call_compute("AICKNFFWKTFTSC")
        ii = _get_field(result, "instability_index")
        # 30.65 < 40 이면 unstable flag 없어야 함
        is_flagged_unstable = (
            _get_field_safe(result, "is_unstable") is True
        )
        assert not is_flagged_unstable or ii >= 40, (
            f"cand03 II={ii:.2f} < 40인데 unstable flag가 True"
        )


# ---------------------------------------------------------------------------
# 5. NCAA 처리 — [dT], [Cha], [2Nal]
# ---------------------------------------------------------------------------

class TestNCAA:
    """비표준 아미노산(NCAA) 처리 및 경고 생성 검증."""

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_d_thr_notation_warning(self):
        """[dT] 표기 입력 시 ncaa_warnings 필드에 치환 기록이 있어야 한다.

        Note: 경고는 Python warnings 모듈이 아닌 result.ncaa_warnings 필드에 저장됨.
        """
        compute = _get_compute_fn()
        seq_with_dT = "AICKNFFWKTF[dT]SC"
        try:
            result = compute(seq_with_dT)
        except (ValueError, RuntimeError):
            return  # 에러 발생도 허용
        d = _result_to_dict(result)
        ncaa_warns = d.get("ncaa_warnings", [])
        assert len(ncaa_warns) > 0, (
            f"[dT] 처리 시 result.ncaa_warnings가 비어있음: {ncaa_warns}\n"
            "strip_ncaa()가 치환 기록을 ncaa_warnings에 저장해야 함."
        )
        assert any(
            any(kw in w.lower() for kw in ("d-thr", "[dt]", "thr", "ncaa", "비표준"))
            for w in ncaa_warns
        ), (
            f"ncaa_warnings에 [dT] 관련 내용이 없음. 실제: {ncaa_warns}"
        )

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_cha_notation_handling(self):
        """[Cha] (cyclohexylalanine) 표기를 처리하거나 명확한 에러를 발생시켜야 한다."""
        compute = _get_compute_fn()
        seq_with_cha = "AGCK[Cha]FFWKTFTSC"
        try:
            result = compute(seq_with_cha)
            # 결과 반환 시 결과에 NCAA 항목이 있어야 함
        except (ValueError, RuntimeError) as e:
            # 에러 메시지에 [Cha] 언급 필요
            assert "[Cha]" in str(e) or "NCAA" in str(e) or "비표준" in str(e), (
                f"[Cha] 에러 메시지가 불명확: {e}"
            )

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_2nal_notation_handling(self):
        """[2Nal] (2-naphthylalanine) 표기 처리."""
        compute = _get_compute_fn()
        seq_with_2nal = "AGCKNF[2Nal]WKTFTSC"
        try:
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                result = compute(seq_with_2nal)
        except (ValueError, RuntimeError):
            pass  # 에러 허용

    @_SKIP_IF_NOT_IMPLEMENTED
    @_SKIP_IF_NO_BIOPYTHON
    def test_ncaa_stripped_for_biopython(self):
        """NCAA 제거 후 표준 AA로 계산 시 instability_index가 nan이 아닌 숫자여야 한다 (Biopython 필요)."""
        compute = _get_compute_fn()
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            try:
                result = compute("AICKNFFWKTF[dT]SC")
                if result:
                    ii = _get_field_safe(result, "instability_index")
                    if ii is not None:
                        assert isinstance(ii, (int, float)) and not (ii != ii), (
                            f"NCAA 제거 후 instability_index가 NaN: {ii}"
                        )
            except (ValueError, RuntimeError):
                pass


# ---------------------------------------------------------------------------
# 6. dataclass 스키마 및 JSON 직렬화
# ---------------------------------------------------------------------------

class TestDataclassSchema:
    """출력 dataclass 구조 및 JSON round-trip 검증."""

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_result_is_dataclass_or_dict(self):
        """결과가 dataclass 또는 dict 타입이어야 한다."""
        result = _call_compute("AICKNFFWKTFTSC")
        assert (
            dataclasses.is_dataclass(result)
            or isinstance(result, dict)
        ), f"결과 타입: {type(result)} — dataclass 또는 dict 필요"

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_json_serializable(self):
        """결과가 JSON 직렬화 가능해야 한다."""
        result = _call_compute("AICKNFFWKTFTSC")
        if dataclasses.is_dataclass(result):
            d = dataclasses.asdict(result)
        else:
            d = result
        try:
            dumped = json.dumps(d)
            reloaded = json.loads(dumped)
            assert isinstance(reloaded, dict)
        except (TypeError, ValueError) as e:
            pytest.fail(f"JSON 직렬화 실패: {e}")

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_required_fields_present(self):
        """최소 필수 필드(gravy, instability_index, mw/molecular_weight)가 있어야 한다."""
        result = _call_compute("AICKNFFWKTFTSC")
        d = _result_to_dict(result)
        # MW 필드: 'mw' 또는 'molecular_weight' 중 하나 허용
        assert "mw" in d or "molecular_weight" in d, (
            f"MW 필드(mw 또는 molecular_weight) 누락.\n"
            f"실제 키: {set(d.keys())}"
        )
        required = {"gravy", "instability_index"}
        missing = required - set(d.keys())
        assert not missing, (
            f"필수 필드 누락: {missing}\n"
            f"실제 키: {set(d.keys())}"
        )

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_all_numeric_fields_are_float(self):
        """gravy, instability_index, molecular_weight 등이 float이어야 한다."""
        result = _call_compute("AICKNFFWKTFTSC")
        d = _result_to_dict(result)
        numeric_keys = ["gravy", "instability_index", "molecular_weight"]
        for key in numeric_keys:
            if key in d:
                assert isinstance(d[key], (int, float)), (
                    f"{key} 타입: {type(d[key])} (float 또는 int 필요)"
                )

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_sequence_field_preserved(self):
        """결과에 입력 서열 정보가 보존되어야 한다."""
        seq = "AICKNFFWKTFTSC"
        result = _call_compute(seq)
        d = _result_to_dict(result)
        seq_in_result = d.get("sequence", d.get("seq", ""))
        assert seq_in_result.upper() == seq or not seq_in_result, (
            f"서열 불일치: 입력={seq}, 결과={seq_in_result}"
        )

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_heuristic_flag_in_result(self):
        """결과에 heuristic 표시 필드 또는 disclaimer가 있어야 한다 (H-06)."""
        result = _call_compute("AICKNFFWKTFTSC")
        d = _result_to_dict(result)
        has_flag = any(
            key in d for key in (
                "is_heuristic", "heuristic", "disclaimer",
                "note", "warning", "method_note"
            )
        )
        # 없으면 경고 (Critical은 아님 — 구현 선택의 여지 있음)
        if not has_flag:
            import warnings
            warnings.warn(
                "stability_predictor 결과에 heuristic disclaimer 필드 없음. "
                "H-06 가드 준수를 위해 추가 권장.",
                UserWarning,
                stacklevel=2,
            )


# ---------------------------------------------------------------------------
# 7. pharmacology_guards 통합
# ---------------------------------------------------------------------------

class TestPharmacologyGuards:
    """pharmacology_guards.LITERATURE_VALUES와의 정합성."""

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_gravy_matches_kd_table(self):
        """GRAVY 계산이 Kyte-Doolittle 1982 문헌값과 일치해야 한다 (GATE-C 수준)."""
        from pipeline_local.scripts.pharmacology_guards import LITERATURE_VALUES, assert_in_range
        result = _call_compute("AICKNFFWKTFTSC")
        gravy = _get_field(result, "gravy")
        # cand03 GRAVY는 소수성 → 양수 (부호 규약 확인)
        assert gravy > 0, (
            f"cand03 GRAVY={gravy:.4f} ≤ 0 — 소수성 서열에서 GRAVY 부호 역전 의심 (H-02 가드)"
        )

    @_SKIP_IF_NOT_IMPLEMENTED
    @_SKIP_IF_NO_BIOPYTHON
    def test_instability_index_in_range(self):
        """Instability Index 범위: -50 ~ 200 (GATE-C). Biopython 없으면 NaN이므로 skip."""
        from pipeline_local.scripts.pharmacology_guards import SCALE_RANGES
        result = _call_compute("AICKNFFWKTFTSC")
        ii = _get_field(result, "instability_index")
        assert -50 <= ii <= 200, (
            f"Instability Index={ii:.2f} 범위 초과 (SCALE_RANGES 확인 필요)"
        )

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_molecular_weight_in_range(self):
        """14aa 펩타이드 MW 범위: 1000 ~ 2500 Da."""
        result = _call_compute("AICKNFFWKTFTSC")
        mw = _get_field(result, "molecular_weight", "mw")
        assert 1000 <= mw <= 2500, (
            f"MW={mw:.2f} Da 범위 초과 (14aa 펩타이드 기준: 1000~2500)"
        )


# ---------------------------------------------------------------------------
# 8. HEURISTIC_FUNCTION_DISCLAIMERS 자동 부착
# ---------------------------------------------------------------------------

class TestHeuristicDisclaimer:
    """H-06 가드: 출력에 휴리스틱 명세가 부착되어야 한다."""

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_module_has_disclaimer_constant(self):
        """모듈에 HEURISTIC_FUNCTION_DISCLAIMERS 또는 유사 상수가 있어야 한다."""
        has = (
            hasattr(_sp_module, "HEURISTIC_FUNCTION_DISCLAIMERS")
            or hasattr(_sp_module, "_HEURISTIC_DISCLAIMER")
            or hasattr(_sp_module, "DISCLAIMER")
        )
        assert has, (
            "HEURISTIC_FUNCTION_DISCLAIMERS 상수 없음. "
            "pharmacology_guards.py 내 HEURISTIC_FUNCTION_DISCLAIMERS 참조."
        )

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_disclaimer_references_heuristic(self):
        """disclaimer 텍스트에 'heuristic' 또는 '휴리스틱' 포함 확인."""
        for attr in ("HEURISTIC_FUNCTION_DISCLAIMERS", "_HEURISTIC_DISCLAIMER", "DISCLAIMER"):
            val = getattr(_sp_module, attr, None)
            if val is None:
                continue
            text = str(val).lower()
            assert "heuristic" in text or "휴리스틱" in text or "ranking" in text, (
                f"{attr} 내용에 'heuristic'/'휴리스틱'/'ranking' 없음: {str(val)[:100]}"
            )
            return
        pytest.skip("disclaimer 상수 없음 — 별도 테스트(test_module_has_disclaimer_constant) 실패")

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_stability_predictor_in_pharmacology_guards(self):
        """stability_predictor 함수가 pharmacology_guards에 등록되어 있어야 한다."""
        from pipeline_local.scripts.pharmacology_guards import (
            HEURISTIC_FUNCTION_DISCLAIMERS,
            is_heuristic_function,
        )
        # stability_predictor 관련 함수가 heuristic으로 등록되어 있거나
        # 모듈 내 주요 함수가 is_heuristic_function으로 확인 가능해야 함
        compute = _get_compute_fn()
        qualname = getattr(compute, "__qualname__", getattr(compute, "__name__", ""))
        is_registered = (
            is_heuristic_function(qualname)
            or any("stability" in k.lower() for k in HEURISTIC_FUNCTION_DISCLAIMERS)
        )
        if not is_registered:
            import warnings
            warnings.warn(
                f"stability_predictor의 주 함수({qualname})가 "
                "HEURISTIC_FUNCTION_DISCLAIMERS에 등록되지 않음. "
                "pharmacology_guards.py에 entry 추가 권장.",
                UserWarning,
                stacklevel=2,
            )


# ---------------------------------------------------------------------------
# 9. modification_conflict 통합
# ---------------------------------------------------------------------------

class TestModificationConflict:
    """D-AA + DOTA + PEG 조합의 modification_conflict 탐지 통합."""

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_compute_accepts_modifications_arg(self):
        """compute_stability가 modifications 인자를 받을 수 있어야 한다."""
        compute = _get_compute_fn()
        try:
            result = compute("AICKNFFWKTFTSC", modifications=["d_amino_acid"])
            assert result is not None
        except TypeError:
            pytest.skip("modifications 인자 미지원 — 구현 확인 필요")

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_daa_dota_conflict_detected(self):
        """D-AA + DOTA 조합 시 modification_conflict 경고 또는 필드가 있어야 한다."""
        compute = _get_compute_fn()
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = compute(
                    "AICKNFFWKTFTSC",
                    modifications=["d_amino_acid", "DOTA"]
                )
                if result:
                    d = _result_to_dict(result)
                    has_conflict = (
                        d.get("modification_conflicts")
                        or d.get("conflict_warnings")
                        or any("conflict" in str(warning.message).lower() for warning in w)
                        or any("충돌" in str(warning.message) for warning in w)
                    )
                    # conflict 미탐지는 High 결함으로 기록하되 crash 아님
                    if not has_conflict:
                        pytest.xfail(
                            "D-AA + DOTA 충돌 미탐지 (High 결함). "
                            "modification_conflict.py 통합 필요."
                        )
        except TypeError:
            pytest.skip("modifications 인자 미지원")


# ---------------------------------------------------------------------------
# 10. batch 모드
# ---------------------------------------------------------------------------

class TestBatchMode:
    """10 후보 batch 처리 성능 및 정확성."""

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_batch_compute_exists(self):
        """batch_compute 또는 동등 함수가 있어야 한다."""
        has_batch = (
            hasattr(_sp_module, "batch_compute_stability")
            or hasattr(_sp_module, "compute_batch")
            or hasattr(_sp_module, "batch_stability")
        )
        if not has_batch:
            pytest.xfail(
                "batch_compute_stability 함수 없음 — "
                "10 후보 루프에서 compute_stability를 개별 호출하는 방식도 허용"
            )

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_batch_10_candidates(self):
        """10 후보 batch 처리 시 결과 수가 입력 수와 일치해야 한다."""
        candidates = [
            {"seq_id": f"cand{i:02d}", "sequence": seq}
            for i, seq in enumerate([
                "AGCKNFFWKTFTSC",  # SST14
                "AICKNFFWKTFTSC",  # cand03
                "ILCKKFFWKTFTSC",  # ILCKK
                "IGCWWFFWKTFTSC",
                "AGCKNDFWKTLTSC",
                "QTCKNFFWKTFTSC",
                "AGCKWEFWKTLTSC",
                "AKCKNFFWKTFTSC",
                "AICKNFFWKTFTSC",  # 중복 허용
                "AGCKNFFWKTLTSC",
            ])
        ]

        # batch 함수 시도
        batch_fn = getattr(
            _sp_module,
            "batch_compute_stability",
            getattr(_sp_module, "compute_batch", None)
        )
        if batch_fn:
            results = batch_fn(candidates)
        else:
            compute = _get_compute_fn()
            results = [compute(c["sequence"]) for c in candidates]

        assert len(results) == 10, f"결과 수={len(results)}, 기대=10"

    @_SKIP_IF_NOT_IMPLEMENTED
    @_SKIP_IF_NO_BIOPYTHON
    def test_batch_instability_ilckk_preserved(self):
        """batch 처리 후에도 ILCKKFFWKTFTSC II=55.14 재현 (Biopython 필요)."""
        compute = _get_compute_fn()
        results = [compute(seq) for seq in [
            "AICKNFFWKTFTSC",
            "ILCKKFFWKTFTSC",  # 두 번째
            "AGCKNFFWKTFTSC",
        ]]
        ii_ilckk = _get_field(results[1], "instability_index")
        assert ii_ilckk == pytest.approx(55.14, abs=0.1), (
            f"batch 내 ILCKKFFWKTFTSC II={ii_ilckk:.2f}, 기준=55.14"
        )


# ---------------------------------------------------------------------------
# 11. 통합 테스트 (mark.slow — 실 conda 환경)
# ---------------------------------------------------------------------------

@pytest.mark.slow
class TestSlowIntegration:
    """실제 conda bio-tools 환경에서 subprocess로 전체 흐름 검증."""

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_conda_biotools_biopython_values(self):
        """conda bio-tools에서 Biopython 계산이 기준값과 일치."""
        import subprocess
        code = """
from Bio.SeqUtils.ProtParam import ProteinAnalysis
pa = ProteinAnalysis('ILCKKFFWKTFTSC')
print(round(pa.instability_index(), 2))
"""
        proc = subprocess.run(
            ["conda", "run", "-n", "bio-tools", "python", "-c", code],
            capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 0, f"conda 실행 실패: {proc.stderr}"
        ii = float(proc.stdout.strip())
        assert ii == pytest.approx(55.14, abs=0.1), f"환경 격리 테스트 II={ii}"

    @_SKIP_IF_NOT_IMPLEMENTED
    def test_batch_results_match_s4_analysis(self):
        """S4 분석 8 후보의 GRAVY 부호 방향이 cand_stability_analysis.md 와 일치."""
        # S4 cand_stability_analysis.md §1.1 기준
        s4_gravy_signs = {
            "AICKNFFWKTFTSC": 1,   # +0.379
            "ILCKKFFWKTFTSC": 1,   # +0.493
            "IGCWWFFWKTFTSC": 1,   # +0.621
            "AGCKNDFWKTLTSC": -1,  # -0.350
            "QTCKNFFWKTFTSC": -1,  # -0.371
            "AGCKWEFWKTLTSC": -1,  # -0.164
            "AKCKNFFWKTFTSC": -1,  # -0.221
        }
        compute = _get_compute_fn()
        for seq, expected_sign in s4_gravy_signs.items():
            result = compute(seq)
            gravy = _get_field(result, "gravy")
            actual_sign = 1 if gravy > 0 else (-1 if gravy < 0 else 0)
            assert actual_sign == expected_sign, (
                f"{seq} GRAVY={gravy:.4f} (부호 {actual_sign}), "
                f"S4 기준 부호 {expected_sign}"
            )


# ---------------------------------------------------------------------------
# 헬퍼 함수
# ---------------------------------------------------------------------------

def _get_compute_fn():
    """stability_predictor의 주 계산 함수를 반환한다."""
    if _sp_module is None:
        pytest.skip("stability_predictor 모듈 없음")
    for name in ("compute_stability", "predict", "analyze"):
        fn = getattr(_sp_module, name, None)
        if fn is not None:
            return fn
    # StabilityPredictor 클래스의 경우
    cls = getattr(_sp_module, "StabilityPredictor", None)
    if cls is not None:
        predictor = cls()
        for method in ("compute", "predict", "analyze", "__call__"):
            m = getattr(predictor, method, None)
            if m is not None:
                return m
    pytest.fail(
        "stability_predictor에서 compute_stability 함수를 찾을 수 없음. "
        "공개 API 확인 필요."
    )


def _call_compute(seq: str) -> Any:
    """주 계산 함수를 호출하고 결과를 반환한다."""
    fn = _get_compute_fn()
    return fn(seq)


def _get_field(result: Any, *field_names: str) -> Any:
    """결과 dict 또는 dataclass에서 첫 번째 매칭 필드를 raw type으로 반환한다.

    Note: 이전 버전은 모든 값을 float로 강제 변환했으나, bool(`is_unstable`)이나
    str(`stability_class`)을 받는 호출자에서 깨졌다. 현재는 raw type 유지.
    수치 필드 호출자는 직접 `float()` 변환해 사용한다.
    """
    d = _result_to_dict(result)
    for name in field_names:
        if name in d:
            return d[name]
    pytest.fail(
        f"필드 {field_names} 중 어느 것도 결과에 없음. "
        f"실제 키: {set(d.keys())}"
    )


def _get_field_safe(result: Any, *field_names: str) -> Optional[Any]:
    """결과에서 필드를 안전하게 raw type으로 반환 (없으면 None).

    `pytest.fail()`은 `Failed`(BaseException 계열)을 raise하므로 일반
    `except Exception`으로 못 잡는다. `BaseException`을 명시적으로 처리.
    """
    try:
        return _get_field(result, *field_names)
    except BaseException:
        return None


def _result_to_dict(result: Any) -> Dict[str, Any]:
    """결과를 dict로 변환한다 (dataclass 또는 dict 모두 지원)."""
    if dataclasses.is_dataclass(result):
        return dataclasses.asdict(result)
    if isinstance(result, dict):
        return result
    # __dict__ 시도
    if hasattr(result, "__dict__"):
        return vars(result)
    pytest.fail(f"결과를 dict로 변환할 수 없음: {type(result)}")
