"""test_pharmacology_guards.py
==============================
회귀 테스트: harness Stage 5 약리학 환각 가드.

본 테스트의 목적:
  1) pharmacology_guards 모듈 자체의 동작 검증
  2) 코드베이스의 lookup table을 LITERATURE_VALUES와 대조하여
     무단 변경/오기재(H-01) 회귀 차단
  3) 부호 규약(H-02) invariant 보존 확인
  4) Stage 5에서 정의한 GATE-C 범위 가드 동작 확인

알려진 과거 결함 (재발생 차단):
  - Radzicka-Wolfenden P=0.0 (정답 -2.54)
  - Radzicka-Wolfenden S=1.15 (정답 3.40)
  - N-end half-life Pro=20.0 (정답 30.0 — 효모 vs 포유류 종 혼동)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from pipeline_local.scripts.pharmacology_guards import (
    ENDPOINT_CONFIDENCE,
    HEURISTIC_FUNCTION_DISCLAIMERS,
    LITERATURE_VALUES,
    SCALE_RANGES,
    SIGN_CONVENTIONS,
    assert_in_range,
    assert_literature_value,
    attach_confidence,
    audit_table,
    check_pepadmet_applicability,
    check_sign_convention,
    is_heuristic_function,
)


# ---------------------------------------------------------------------------
# 1. 가드 모듈 자체 검증
# ---------------------------------------------------------------------------


class TestGuardModuleInternal:
    """pharmacology_guards 모듈 자체의 동작."""

    def test_literature_values_populated(self):
        assert "kyte_doolittle" in LITERATURE_VALUES
        assert "radzicka_wolfenden_boman_convention" in LITERATURE_VALUES
        assert "nend_half_life_mammalian_hours" in LITERATURE_VALUES
        assert "lehninger_pka_sidechain" in LITERATURE_VALUES
        assert "SST14_SSTR2_ref_ddg_flexpep" in LITERATURE_VALUES
        assert "SST14_SSTR2_ref_ddg_boltz2" in LITERATURE_VALUES

    def test_sst14_reference_ddg_registered(self):
        flexpep = LITERATURE_VALUES["SST14_SSTR2_ref_ddg_flexpep"]
        boltz2 = LITERATURE_VALUES["SST14_SSTR2_ref_ddg_boltz2"]

        assert flexpep["ref_ddg_reu_mean"][0] == pytest.approx(553.857)
        assert flexpep["ref_ddg_reu_std"][0] == pytest.approx(4.024)
        assert flexpep["n"][0] == 10
        assert boltz2["ref_ddg_reu"][0] == pytest.approx(-95.024)

    def test_each_literature_entry_has_source(self):
        for table_name, truth in LITERATURE_VALUES.items():
            for key, entry in truth.items():
                assert len(entry) == 3, f"{table_name}[{key}]: must be (value, source, comment)"
                value, source, comment = entry
                assert source, f"{table_name}[{key}]: missing source"
                assert comment, f"{table_name}[{key}]: missing comment"

    def test_scale_ranges_well_formed(self):
        for scale, (lo, hi) in SCALE_RANGES.items():
            assert lo < hi, f"{scale}: lo={lo} must be < hi={hi}"

    def test_sign_conventions_documented(self):
        # 모든 주요 척도가 부호 규약을 가져야 함
        required = {"kyte_doolittle", "boman_index", "instability_index", "n_end_half_life"}
        assert required.issubset(SIGN_CONVENTIONS.keys())


class TestHeuristicFunctionDisclaimers:
    """VR-cycle-09 (H-06) 가드: 휴리스틱 함수의 정직한 명세 회귀."""

    def test_predict_half_life_registered(self):
        """predict_half_life는 휴리스틱 함수로 등록되어야 함 (H-06 가드 의무)."""
        assert is_heuristic_function(
            "pipeline_local.steps.step08_stability.predict_half_life"
        ), "predict_half_life가 HEURISTIC_FUNCTION_DISCLAIMERS에서 누락됨 — H-06 환각 위험"

    def test_each_disclaimer_has_required_fields(self):
        """각 disclaimer가 필수 필드를 모두 가지는지."""
        required = {
            "surface_unit",
            "actual_meaning",
            "limitations",
            "valid_use",
            "invalid_use",
            "confidence_grade",
            "fix_status",
        }
        for qualname, entry in HEURISTIC_FUNCTION_DISCLAIMERS.items():
            missing = required - set(entry.keys())
            assert not missing, f"{qualname}: missing required fields {missing}"

    def test_confidence_grade_is_heuristic(self):
        """휴리스틱 함수의 confidence_grade는 'HEURISTIC' 카테고리 강제."""
        for qualname, entry in HEURISTIC_FUNCTION_DISCLAIMERS.items():
            assert entry["confidence_grade"] == "HEURISTIC", (
                f"{qualname}: confidence_grade가 HEURISTIC이 아님. "
                f"H-06 환각 위험 — HIGH/MED/LOW로 분류하면 임상 단위로 오인 가능."
            )

    def test_unknown_function_not_heuristic(self):
        """미등록 함수는 휴리스틱 아님."""
        assert not is_heuristic_function("nonexistent.module.function")
        assert not is_heuristic_function("")

    def test_protease_vulnerability_registered(self):
        """VR-S5-01 closure: _PROTEASE_VULNERABILITY가 출처 부재 휴리스틱으로 등록."""
        qn = "pipeline_local.steps.step08_stability._PROTEASE_VULNERABILITY"
        assert is_heuristic_function(qn), (
            f"{qn} 미등록 — VR-S5-01 (출처 부재 휴리스틱) 가드 누락"
        )
        entry = HEURISTIC_FUNCTION_DISCLAIMERS[qn]
        assert "VR-S5-01" in entry["limitations"] or "VR-S5-01" in entry["fix_status"]

    def test_pyrosetta_sequence_only_pose_registered(self):
        """VR-cycle-08 closure: sequence-only pose 한계 등록."""
        qn = "pyrosetta.pose_from_sequence_ideal_coord"
        assert is_heuristic_function(qn), (
            f"{qn} 미등록 — VR-cycle-08 (PDB 좌표 부재) 가드 누락"
        )
        entry = HEURISTIC_FUNCTION_DISCLAIMERS[qn]
        assert "ref2015" in entry["surface_unit"] or "ref2015" in entry["actual_meaning"]
        assert "VR-cycle-08" in entry["limitations"] or "VR-cycle-08" in entry["fix_status"]

    def test_pepadmet_disclaimer_registered(self):
        """A-03: pepADMET UNAVAILABLE/HEURISTIC 가드 등록."""
        qn = "external_tool.pepadmet"
        assert is_heuristic_function(qn), f"{qn} 미등록 — A-03 pepADMET 가드 누락"
        entry = HEURISTIC_FUNCTION_DISCLAIMERS[qn]
        assert entry["confidence_grade"] == "HEURISTIC"
        assert "HTTP 403" in entry["disclaimer"]
        assert "DOTA" in entry["disclaimer"]


class TestPepadmetApplicability:
    """A-03: pepADMET 적용 가능성 가드."""

    def test_d_amino_acid_sequence_not_recommended(self):
        result = check_pepadmet_applicability("Ala-D-Phe-d-trp")
        assert result["recommended"] is False
        assert result["d_amino_acid_present"] is True
        assert result["absolute_confidence"] == "LOW"
        assert "V-02/V-03" in result["reason"]

    def test_dota_sequence_not_recommended(self):
        result = check_pepadmet_applicability("AGCKNFFWKTFTSC", has_dota=True)
        assert result["recommended"] is False
        assert result["dota_chelator_present"] is True
        assert "DOTA" in result["reason"]

    def test_l_amino_acid_sequence_recommended_low_confidence(self):
        result = check_pepadmet_applicability("AGCKNFFWKTFTSC")
        assert result["recommended"] is True
        assert result["d_amino_acid_present"] is False
        assert result["dota_chelator_present"] is False
        assert result["absolute_confidence"] == "LOW"

    # ── SS-bond OOD 가드 테스트 (2026-05-21 — reviewer-pharma §7-C) ──────────

    def test_check_pepadmet_applicability_cyclic_ss_bond_blocked(self):
        """SMILES 내 'SS' 서브구조 감지 시 recommended=False, reason에 OOD 명시.

        PRST-001~004는 Cys3-Cys14 이황화결합(CSSC 서브구조)을 포함하므로
        pepADMET binary_toxicity OOD 판정이 되어야 한다.
        reviewer-pharma §2.2: 14aa SS-bond binary label 0건.
        """
        # AGCKNFFWKTFTSC (SST-14 native): SMILES에 'SS' 포함 (Cys3-Cys14 SS bond)
        ss_smiles = "N[C@@H](C)C(=O)N[C@@H](CS)CSSCCC"  # 'SS' 포함 최소 예시
        result = check_pepadmet_applicability("AGCKNFFWKTFTSC", smiles=ss_smiles)
        assert result["recommended"] is False, (
            "cyclic SS-bond SMILES가 감지됐는데 recommended=True — OOD 가드 누락"
        )
        assert result["cyclic_ss_bond_present"] is True
        assert "cyclic SS-bond peptide OOD" in result["reason"]
        assert result["absolute_confidence"] == "LOW"

    def test_check_pepadmet_applicability_d_aa_still_blocked(self):
        """회귀: D-AA 차단이 SS-bond 가드 추가 후에도 동작해야 한다."""
        result = check_pepadmet_applicability("Ala-D-Phe-d-trp")
        assert result["recommended"] is False
        assert result["d_amino_acid_present"] is True
        assert result["absolute_confidence"] == "LOW"
        assert "V-02/V-03" in result["reason"]
        # cyclic_ss_bond_present 필드가 추가됐는지 확인 (SMILES 미제공 → False)
        assert result["cyclic_ss_bond_present"] is False

    def test_check_pepadmet_applicability_linear_peptide_allowed(self):
        """회귀: SS bond 없는 선형 L-AA 펩타이드는 여전히 recommended=True.

        SMILES에 'SS' 없으면 cyclic_ss_bond_present=False → 차단 안 됨.
        """
        linear_smiles = "N[C@@H](CC(=O)O)C(=O)N[C@@H](C)C(=O)O"  # Asp-Ala (SS 없음)
        result = check_pepadmet_applicability("DA", smiles=linear_smiles)
        assert result["recommended"] is True
        assert result["cyclic_ss_bond_present"] is False
        assert result["absolute_confidence"] == "LOW"


# ---------------------------------------------------------------------------
# 2. 정상 동작 경로
# ---------------------------------------------------------------------------


class TestAssertLiteratureValue:

    def test_correct_value_passes(self):
        ok_table = {"I": 4.5, "R": -4.5}
        assert_literature_value(ok_table, "kyte_doolittle", "I")
        assert_literature_value(ok_table, "kyte_doolittle", "R")

    def test_wrong_value_raises(self):
        bad_table = {"I": 99.9}
        with pytest.raises(AssertionError, match="literature says 4.5"):
            assert_literature_value(bad_table, "kyte_doolittle", "I")

    def test_missing_key_raises(self):
        with pytest.raises(AssertionError, match="missing key"):
            assert_literature_value({}, "kyte_doolittle", "I")

    def test_unknown_table_raises(self):
        with pytest.raises(KeyError, match="Unknown literature table"):
            assert_literature_value({}, "nonexistent_scale", "X")

    def test_unknown_key_raises(self):
        with pytest.raises(KeyError, match="not registered"):
            assert_literature_value({"I": 4.5}, "kyte_doolittle", "Z")


class TestAssertInRange:

    def test_within_range_passes(self):
        assert_in_range(2.0, "boman_index_kcal_per_mol")
        assert_in_range(50.0, "instability_index")

    def test_below_min_raises(self):
        with pytest.raises(AssertionError, match="RANGE-CHECK FAIL"):
            assert_in_range(-10.0, "boman_index_kcal_per_mol")

    def test_above_max_raises(self):
        with pytest.raises(AssertionError, match="RANGE-CHECK FAIL"):
            assert_in_range(200.0, "instability_index")

    def test_context_in_message(self):
        with pytest.raises(AssertionError, match=r"cand-007"):
            assert_in_range(-99.0, "boman_index_kcal_per_mol", context="cand-007")

    def test_unknown_scale_raises(self):
        with pytest.raises(KeyError):
            assert_in_range(1.0, "made_up_scale")


class TestCheckSignConvention:

    def test_kyte_doolittle_I_more_hydrophobic_than_R(self):
        kd = {"I": 4.5, "R": -4.5}
        check_sign_convention("kyte_doolittle", "I", "R", kd)

    def test_kyte_doolittle_violation_detected(self):
        # 부호 역전된 가짜 테이블
        bad_kd = {"I": -4.5, "R": 4.5}
        with pytest.raises(AssertionError, match="SIGN-CONVENTION VIOLATION"):
            check_sign_convention("kyte_doolittle", "I", "R", bad_kd)


class TestAuditTable:

    def test_clean_table_returns_no_violations(self):
        clean = {key: entry[0] for key, entry in LITERATURE_VALUES["kyte_doolittle"].items()}
        violations = audit_table(clean, "kyte_doolittle")
        assert violations == []

    def test_mutated_table_caught(self):
        clean = {key: entry[0] for key, entry in LITERATURE_VALUES["kyte_doolittle"].items()}
        clean["I"] = 99.9  # 무단 변경
        violations = audit_table(clean, "kyte_doolittle")
        assert len(violations) == 1
        assert violations[0].key == "I"
        assert violations[0].actual_value == 99.9
        assert violations[0].expected_value == 4.5


# ---------------------------------------------------------------------------
# 3. ★ 실제 코드베이스 lookup table과 LITERATURE_VALUES 대조 (회귀)
# ---------------------------------------------------------------------------
#
# pharma_properties.py가 다른 레포(AgenticAI4SCIENCE_pyrosetta_track)에 있으므로
# import는 best-effort. 실패하면 skip.


def _try_import_pharma_properties():
    """AG_src.pipeline.pharma_properties를 best-effort로 import."""
    repo_root = Path(__file__).resolve().parents[2]
    candidate = repo_root / "AgenticAI4SCIENCE_pyrosetta_track" / "repos" / "ai4sci-kaeri"
    if candidate.exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
    try:
        from AG_src.pipeline import pharma_properties as pp
        return pp
    except ImportError:
        return None


class TestPharmaPropertiesRegression:
    """실제 lookup table이 문헌 정답과 일치하는지."""

    @pytest.fixture(scope="class")
    def pp(self):
        module = _try_import_pharma_properties()
        if module is None:
            pytest.skip("AG_src.pipeline.pharma_properties not importable in this environment")
        return module

    def test_kyte_doolittle_table_matches_literature(self, pp):
        violations = audit_table(pp.KD_HYDROPATHY, "kyte_doolittle")
        assert violations == [], f"KD table mismatches: {[(v.key, v.actual_value, v.expected_value) for v in violations]}"

    def test_rw_transfer_boman_convention(self, pp):
        violations = audit_table(pp.RW_TRANSFER, "radzicka_wolfenden_boman_convention")
        assert violations == [], (
            f"RW_TRANSFER table mismatches (Boman convention): "
            f"{[(v.key, v.actual_value, v.expected_value, v.message) for v in violations]}"
        )

    def test_nend_half_life_pro_is_30_not_20(self, pp):
        """Regression: 알려진 historical defect — Pro=20.0 (yeast)을 mammalian 30.0과 혼동."""
        pro_entry = pp.NEND_HALFLIFE["P"]
        # NEND_HALFLIFE는 (hours, category) 튜플
        assert pro_entry[0] == 30.0, (
            f"NEND_HALFLIFE['P'] = {pro_entry[0]} but Varshavsky 1996 mammalian reticulocyte says 30.0. "
            f"Possible species/condition confusion (yeast Pro half-life is ~20h)."
        )

    def test_nend_half_life_table_matches_literature(self, pp):
        violations = audit_table(pp.NEND_HALFLIFE, "nend_half_life_mammalian_hours")
        assert violations == [], f"NEND_HALFLIFE mismatches: {[(v.key, v.actual_value, v.expected_value) for v in violations]}"

    def test_lehninger_pka_matches(self, pp):
        violations = audit_table(pp.PKA_SIDECHAIN, "lehninger_pka_sidechain")
        assert violations == [], f"PKA mismatches: {violations}"


class TestPharmaPropertiesSignConventions:
    """부호 규약 invariant이 lookup table에서 유지되는지."""

    @pytest.fixture(scope="class")
    def pp(self):
        module = _try_import_pharma_properties()
        if module is None:
            pytest.skip("AG_src.pipeline.pharma_properties not importable")
        return module

    def test_kyte_doolittle_sign(self, pp):
        check_sign_convention("kyte_doolittle", "I", "R", pp.KD_HYDROPATHY)

    def test_boman_convention_sign(self, pp):
        # Boman convention: R(친수성) > I(소수성)
        check_sign_convention("boman_index", "R", "I", pp.RW_TRANSFER)


class TestPharmaPropertiesOutputRanges:
    """함수 출력이 합리 범위 내에 있는지 (GATE-C)."""

    @pytest.fixture(scope="class")
    def pp(self):
        module = _try_import_pharma_properties()
        if module is None:
            pytest.skip("AG_src.pipeline.pharma_properties not importable")
        instance = module.PharmaProperties()
        return instance

    def test_sst14_gravy_in_range(self, pp):
        gravy = pp.calculate_gravy("AGCKNFFWKTFTSC")
        assert_in_range(gravy, "kyte_doolittle_mean", context="SST-14 native")

    def test_sst14_boman_in_range(self, pp):
        bi = pp.calculate_boman_index("AGCKNFFWKTFTSC")
        assert_in_range(bi, "boman_index_kcal_per_mol", context="SST-14 native")

    def test_sst14_instability_in_range(self, pp):
        ii = pp.calculate_instability_index("AGCKNFFWKTFTSC")
        assert_in_range(ii, "instability_index", context="SST-14 native")

    def test_all_lys_extreme_but_in_range(self, pp):
        """극단 케이스도 범위 내여야 함."""
        seq = "K" * 14
        bi = pp.calculate_boman_index(seq)
        assert_in_range(bi, "boman_index_kcal_per_mol", context="all-K extreme")


# ---------------------------------------------------------------------------
# 4. step08_stability 출력 범위 회귀
# ---------------------------------------------------------------------------


class TestStep08StabilityOutputRange:
    """predict_half_life의 출력이 PREDICTED_HALF_LIFE 범위 내."""

    @pytest.fixture(scope="class")
    def step08(self):
        try:
            from pipeline_local.steps import step08_stability
            return step08_stability
        except ImportError as e:
            pytest.skip(f"step08_stability not importable: {e}")

    def test_sst14_native_within_range(self, step08):
        hl = step08.predict_half_life("AGCKNFFWKTFTSC", [])
        assert_in_range(hl, "predicted_half_life_hours", context="SST-14 native, no mods")

    def test_with_all_modifications_within_range(self, step08):
        hl = step08.predict_half_life(
            "AGCKNFFWKTFTSC",
            ["fatty_acid", "pegylation", "d_amino_acid", "cyclization"],
        )
        assert_in_range(hl, "predicted_half_life_hours", context="SST-14 + all mods")

    def test_lower_bound_enforced(self, step08):
        # 빈 modification + 매우 취약한 서열도 음수가 되어선 안 됨
        hl = step08.predict_half_life("RRRRRRRRRR", [])
        assert hl >= 0.5, f"predicted_half_life={hl} violates min 0.5h floor"

    def test_extreme_modifications_capped(self, step08):
        # 동일 modification을 여러 번 넣어도 비현실 값 안 됨
        hl = step08.predict_half_life("AGCKNFFWKTFTSC", ["fatty_acid"] * 10)
        assert_in_range(hl, "predicted_half_life_hours", context="repeated fatty_acid (sanity)")


# ---------------------------------------------------------------------------
# 11. TestEndpointConfidenceExternalTools — P1/P2 sprint 손실 복구 (2026-05-20)
#     출처: _workspace/release/p1-action-items-execution-2026-05-19.md §2 (16개)
#           _workspace/release/p2-binding-pocket-pepmsnd-pepadmet-execution-2026-05-19.md §1 (24개)
# ---------------------------------------------------------------------------


class TestEndpointConfidenceExternalTools:
    """ENDPOINT_CONFIDENCE 외부 도구 신규 11개 + HEURISTIC 4개 + attach_confidence 패치 회귀."""

    # ── 혈청 반감기 7개 등록 검증 ────────────────────────────────────────
    def test_halflife_pepmsnd_registered(self):
        e = ENDPOINT_CONFIDENCE["halflife_pepmsnd"]
        assert e["grade"] == "P3", "PepMSND P1→P3 강등 (이진 분류 한계)"
        assert e["tool"] == "PepMSND"
        assert e["d_amino_acid_support"] is False
        assert any("이진 분류" in w or "binary" in w.lower() for w in e["warnings"])

    def test_halflife_plifepred_registered(self):
        e = ENDPOINT_CONFIDENCE["halflife_plifepred"]
        assert e["grade"] == "P2"
        assert "Mathur" in e["source_doi"]

    def test_halflife_plifepred2_is_p4_v_infra_01(self):
        e = ENDPOINT_CONFIDENCE["halflife_plifepred2"]
        assert e["grade"] == "P4", "§V-infra-01 단위 미명시 → P4 강제"
        assert any("V-infra-01" in w or "단위" in w for w in e["warnings"])

    def test_halflife_ml_peptide_is_p3(self):
        e = ENDPOINT_CONFIDENCE["halflife_ml_peptide"]
        assert e["grade"] == "P3"

    def test_halflife_protparam_is_p4_n_end_rule(self):
        """N-end rule = 세포내 메커니즘 → 혈청 t½ 완전 불일치 → P4."""
        e = ENDPOINT_CONFIDENCE["halflife_protparam"]
        assert e["grade"] == "P4"
        # 단수 키 사용 검증
        assert "warning" in e
        assert "N-end rule" in e["warning"]

    def test_halflife_hlp_is_p4_and_has_gi_warning(self):
        e = ENDPOINT_CONFIDENCE["halflife_hlp"]
        assert e["grade"] == "P4"
        assert any("GI" in w or "장내" in w for w in e["warnings"])
        assert any("1.6초" in w or "1.6" in w for w in e["warnings"])

    def test_halflife_peptiderranker_is_p4(self):
        e = ENDPOINT_CONFIDENCE["halflife_peptiderranker"]
        assert e["grade"] == "P4"
        # 단수 키 사용 검증
        assert "warning" in e
        assert "생물활성" in e["warning"] or "bioactivity" in e["warning"].lower()

    # ── ADMET 도구 4개 등록 검증 ─────────────────────────────────────────
    def test_admet_pepadmet_is_p1(self):
        """pepADMET P1 — 인프라(HTTP 403)와 분리, 정확도 기준 (Wang 2026 R²=0.84-0.90)."""
        e = ENDPOINT_CONFIDENCE["admet_pepadmet"]
        assert e["grade"] == "P1", "원 논문 R²=0.84-0.90 기준 P1"
        assert "Wang" in e["source_doi"]
        assert e["d_amino_acid_support"] is False

    def test_admet_pepadmet_warns_dota_ood(self):
        e = ENDPOINT_CONFIDENCE["admet_pepadmet"]
        assert any("DOTA" in w for w in e["warnings"])

    def test_pepadmet_toxicity_registered_with_partial_daa_support(self):
        e = ENDPOINT_CONFIDENCE["pepadmet_toxicity"]
        assert e["grade"] == "P1"
        assert e["d_amino_acid_support"] == "partial"
        assert e["local_install_status"] == "partial"
        assert e["api_status"] == "blocked"
        assert e["reference"] == "github.com/ifyoungnet/pepADMET"
        assert "L-AA 입력 시만 신뢰" in e["notes"]

    def test_admet_modlamp_is_p3(self):
        e = ENDPOINT_CONFIDENCE["admet_modlamp"]
        assert e["grade"] == "P3"
        # 단수 키 사용 검증
        assert "warning" in e

    def test_admet_ai_is_p2(self):
        e = ENDPOINT_CONFIDENCE["admet_ai"]
        assert e["grade"] == "P2"
        assert any("소분자" in w or "small" in w.lower() for w in e["warnings"])

    def test_admet_fab_is_unknown_and_no_url(self):
        """Fab-ADMET 원출처 미식별 → UNKNOWN + url=None 강제."""
        e = ENDPOINT_CONFIDENCE["admet_fab"]
        assert e["grade"] == "UNKNOWN"
        assert e["url"] is None
        # 단수 키 사용 검증
        assert "warning" in e

    # ── D-AA 지원 매트릭스 검증 (전수) ───────────────────────────────────
    def test_d_amino_acid_support_explicit_for_all_external_tools(self):
        external_keys = [
            "halflife_pepmsnd", "halflife_plifepred", "halflife_plifepred2",
            "halflife_ml_peptide", "halflife_protparam", "halflife_hlp",
            "halflife_peptiderranker",
            "admet_pepadmet", "admet_modlamp", "admet_ai", "admet_fab",
        ]
        for k in external_keys:
            assert "d_amino_acid_support" in ENDPOINT_CONFIDENCE[k], \
                f"{k}: d_amino_acid_support 명시 누락 (C-04 D-AA 가드)"

    # ── HEURISTIC_FUNCTION_DISCLAIMERS 4 항목 검증 ───────────────────────
    def test_pepmsnd_heuristic_disclaimer_registered(self):
        d = HEURISTIC_FUNCTION_DISCLAIMERS["external_tool.halflife_pepmsnd"]
        assert d["confidence_grade"] == "HEURISTIC"
        assert "이진 분류" in d["limitations"] or "binary" in d["limitations"].lower()

    def test_hlp_heuristic_disclaimer_gi_only(self):
        d = HEURISTIC_FUNCTION_DISCLAIMERS["external_tool.halflife_hlp"]
        assert d["confidence_grade"] == "HEURISTIC"
        assert "GI" in d["surface_unit"] or "intestinal" in d["surface_unit"].lower()
        assert "혈청" in d["limitations"] or "serum" in d["limitations"].lower()

    def test_admet_pepadmet_heuristic_dota_ood(self):
        d = HEURISTIC_FUNCTION_DISCLAIMERS["external_tool.admet_pepadmet"]
        assert d["confidence_grade"] == "HEURISTIC"
        assert "DOTA" in d["limitations"]

    def test_plifepred2_heuristic_v_infra_01(self):
        d = HEURISTIC_FUNCTION_DISCLAIMERS["external_tool.halflife_plifepred2"]
        assert d["confidence_grade"] == "HEURISTIC"
        assert "V-infra-01" in d["fix_status"] or "V-infra-01" in d["limitations"]

    # ── attach_confidence 단수 "warning" 키 호환 패치 검증 ───────────────
    def test_attach_confidence_single_warning_key_injected(self):
        """warning 단수 키도 confidence_warnings에 누락 없이 포함되어야 함."""
        result = attach_confidence({}, "halflife_protparam")
        warnings = result["confidence_warnings"]
        assert any("N-end rule" in w for w in warnings), \
            "단수 'warning' 키가 confidence_warnings 누락 (회귀)"

    def test_attach_confidence_single_warning_admet_modlamp(self):
        result = attach_confidence({}, "admet_modlamp")
        warnings = result["confidence_warnings"]
        assert any("물리화학" in w or "descriptors" in w.lower() for w in warnings)

    def test_attach_confidence_external_halflife_pepmsnd(self):
        """ENDPOINT_CONFIDENCE 외부 도구 키 + HEURISTIC 결합."""
        result = attach_confidence(
            {"halflife_label": "stable"},
            "halflife_pepmsnd",
            heuristic_functions_used=["external_tool.halflife_pepmsnd"],
        )
        assert result["confidence_grade"] == "P3"
        # 단순 warnings (3건) + HEURISTIC disclaimer (1건) 결합
        warnings = result["confidence_warnings"]
        assert any("HEURISTIC" in w for w in warnings), "HEURISTIC disclaimer 누락"

    def test_attach_confidence_admet_fab_unknown_grade(self):
        result = attach_confidence({}, "admet_fab")
        assert result["confidence_grade"] == "UNKNOWN"
        # 단수 warning 키
        assert any("미식별" in w or "원출처" in w for w in result["confidence_warnings"])

    # ── 외부 도구 ENDPOINT_CONFIDENCE에 내부 A/B/C 등급 사용 금지 ──────────
    def test_no_internal_endpoint_grade_for_external_tools(self):
        external_keys = [
            "halflife_pepmsnd", "halflife_plifepred", "halflife_plifepred2",
            "halflife_ml_peptide", "halflife_protparam", "halflife_hlp",
            "halflife_peptiderranker",
            "admet_pepadmet", "admet_modlamp", "admet_ai", "admet_fab",
        ]
        invalid_grades = {"A", "B", "C"}
        for k in external_keys:
            grade = ENDPOINT_CONFIDENCE[k]["grade"]
            assert grade not in invalid_grades, \
                f"{k}: 외부 도구는 P1~P4/UNKNOWN/HEURISTIC만 — 내부 등급 {grade} 부적합"

    # ── PepMSND dataset_note (V-01) 등록 검증 ──────────────────────────
    def test_pepmsnd_dataset_note_registered(self):
        """V-01: PepMSND 635 entries + D-AA 116개(18.3%) 명시 (로컬 학습 근거)."""
        e = ENDPOINT_CONFIDENCE["halflife_pepmsnd"]
        assert "dataset_note" in e
        assert "635" in e["dataset_note"]
        assert "116" in e["dataset_note"] or "18.3%" in e["dataset_note"]

    # ── C-04/C-07 도메인 가드 ──────────────────────────────────────────
    def test_c04_no_external_tool_supports_d_aa_directly(self):
        """C-04 가드: 어느 외부 도구도 D-AA 직접 t½ 예측 지원 주장 금지.

        예외: webmetabase는 간접 지원 (half_life_direct=False) — D-AA 절단 사이트 예측만.
        """
        external_keys = [
            "halflife_pepmsnd", "halflife_plifepred", "halflife_plifepred2",
            "halflife_ml_peptide", "halflife_protparam", "halflife_hlp",
            "halflife_peptiderranker",
            "admet_pepadmet", "admet_modlamp", "admet_ai",
        ]
        for k in external_keys:
            v = ENDPOINT_CONFIDENCE[k].get("d_amino_acid_support")
            assert v is False, f"{k}: d_amino_acid_support={v} (False 강제)"

    def test_c07_dota_no_tool_supports_dota(self):
        """C-07: DOTA 결합 펩타이드는 모든 ADMET 도구 OOD."""
        e = ENDPOINT_CONFIDENCE["admet_pepadmet"]
        assert any("DOTA" in w for w in e["warnings"]), \
            "admet_pepadmet: DOTA OOD 경고 누락 (C-07 가드)"

    # ── A-02 신규 2개 등록 검증 (2026-05-20) ──────────────────────────────
    def test_halflife_webmetabase_indirect_registered(self):
        """WebMetabase: D-AA 간접 지원 유일 도구 — P3 grade, half_life_direct=False."""
        e = ENDPOINT_CONFIDENCE["halflife_webmetabase_indirect"]
        assert e["grade"] == "P3"
        assert e["d_amino_acid_support"] is True  # 유일한 D-AA 직접 지원 도구
        assert e["half_life_direct"] is False  # 간접 지표
        assert "Radchenko" in e["source"]

    def test_halflife_hle_regression_albumin_registered(self):
        """HLE Regression: albumin-binding subset R²=0.879, n=26."""
        e = ENDPOINT_CONFIDENCE["halflife_hle_regression_albumin"]
        assert e["grade"] == "P3"
        assert e["d_amino_acid_support"] is False
        assert e["callable"] == "pipeline_local.scripts.predict_halflife_pepmsnd.predict_halflife_hle_regression"
        assert e.get("benchmark_r2_albumin_binding") == 0.879
        assert e.get("n_training") == 26
        assert "Glassman" in e["source"]

    def test_webmetabase_only_d_aa_supporter_in_external_tools(self):
        """C-04 정정: WebMetabase는 D-AA 지원하는 유일한 외부 도구 (간접)."""
        daa_supporters = [k for k, v in ENDPOINT_CONFIDENCE.items()
                           if isinstance(v, dict) and v.get("d_amino_acid_support") is True]
        assert daa_supporters == ["halflife_webmetabase_indirect"], \
            f"D-AA 지원 도구는 webmetabase만 — 발견: {daa_supporters}"
