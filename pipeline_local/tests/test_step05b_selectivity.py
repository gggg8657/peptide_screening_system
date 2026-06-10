"""
test_step05b_selectivity.py
============================
Step 05b: Selectivity screening 단위 테스트

P1-3 부호 통일 (2026-05-13):
  selectivity_margin = max(ddG_off-target) - ddG(SSTR2)
  → 양수 = SSTR2 선택적 (step05c iPTM 컨벤션과 통일)

테스트 목록:
  1. TestComputeSelectivityMargin — margin 공식·부호·경계값 검증
  2. TestApplySelectivityGate    — 통과/탈락 분류 검증
  3. TestRunSelectivityScreening — 전체 흐름 (estimation mode mock)
  4. TestSchemaRoundtrip         — SelectivityResult / Step05bOutput 직렬화
  5. TestSignConventionAlignment — step05b vs step05c 부호 일관성
  6. TestGateThresholdsYaml      — gate_thresholds.yaml 로드 검증
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# 임포트
# ---------------------------------------------------------------------------

from pipeline_local.steps.step05b_selectivity import (
    compute_selectivity_margin,
    apply_selectivity_gate,
    run_selectivity_screening,
)

try:
    from pipeline_local.schemas.io_schemas import (
        DockingResult,
        OffTargetDockingResult,
        SelectivityResult,
        Step05bOutput,
    )
    _SCHEMAS_FROM_IO = True
except ImportError:
    _SCHEMAS_FROM_IO = False


# ===========================================================================
# 1. TestComputeSelectivityMargin
# ===========================================================================

class TestComputeSelectivityMargin:
    """margin = max(ddG_off-target) - ddG(SSTR2) — 양수 = SSTR2 선택적."""

    # --- 핵심 부호 검증 (P1-3) ---

    def test_positive_margin_when_sstr2_stronger(self):
        """SSTR2 ddG=-30, off-target ddG=-20 → margin = +10 (SSTR2 선택적).

        offtarget_max_allowed=-25.0 으로 완화: off-target ddG=-20 은 -25 이상이므로
        off-target 허용 기준도 통과 → 전체 passed=True
        """
        result = compute_selectivity_margin(
            seq_id="cand_A",
            sstr2_score=-30.0,
            offtarget_scores={"SSTR1": -20.0},
            margin_min=10.0,
            offtarget_max_allowed=-25.0,   # 완화: -20 >= -25 → 통과
        )
        assert abs(result.selectivity_margin - 10.0) < 1e-9, (
            f"예상 margin=+10.0, 실제={result.selectivity_margin:.3f}"
        )
        assert result.passed, "margin=+10 ≥ margin_min=+10 이므로 통과해야 함"

    def test_negative_margin_when_offtarget_stronger(self):
        """SSTR2 ddG=-10, off-target ddG=-30 → margin = -20 (off-target 우세)."""
        result = compute_selectivity_margin(
            seq_id="cand_B",
            sstr2_score=-10.0,
            offtarget_scores={"SSTR3": -30.0},
            margin_min=2.0,
            offtarget_max_allowed=-15.0,
        )
        assert abs(result.selectivity_margin - (-20.0)) < 1e-9, (
            f"예상 margin=-20.0, 실제={result.selectivity_margin:.3f}"
        )
        assert not result.passed, "margin=-20 < margin_min=+2 이므로 탈락해야 함"

    def test_zero_margin_boundary(self):
        """SSTR2 ddG=-20, off-target ddG=-20 → margin = 0.0 (동등 결합).

        offtarget_max_allowed=-25.0 완화: -20 >= -25 → off-target 허용 기준 통과
        """
        result = compute_selectivity_margin(
            seq_id="cand_C",
            sstr2_score=-20.0,
            offtarget_scores={"SSTR4": -20.0},
            margin_min=0.0,
            offtarget_max_allowed=-25.0,   # 완화
        )
        assert abs(result.selectivity_margin) < 1e-9
        assert result.passed, "margin=0.0 ≥ margin_min=0.0 이므로 통과해야 함"

    # --- best off-target 수용체 선정 ---

    def test_worst_offtarget_is_strongest_binder(self):
        """가장 음수인 off-target이 margin 기준으로 선택됨."""
        result = compute_selectivity_margin(
            seq_id="cand_D",
            sstr2_score=-30.0,
            offtarget_scores={
                "SSTR1": -15.0,
                "SSTR3": -25.0,  # 가장 강한 결합
                "SSTR4": -10.0,
            },
            margin_min=2.0,
        )
        # margin = max_offtarget - sstr2 = -25.0 - (-30.0) = +5.0
        # (worst_off = min(scores) = SSTR3)
        assert abs(result.selectivity_margin - 5.0) < 1e-9
        assert result.offtarget_max_receptor == "SSTR3"
        assert abs(result.offtarget_max_score - (-25.0)) < 1e-9

    def test_multiple_offtargets_picks_strongest(self):
        """5개 off-target 중 가장 강한 결합 하나가 margin 계산에 사용됨."""
        scores = {
            "SSTR1": -18.0,
            "SSTR3": -22.0,
            "SSTR4": -12.0,
            "SSTR5": -8.0,
        }
        sstr2 = -30.0
        result = compute_selectivity_margin("x", sstr2, scores)
        expected_margin = -22.0 - (-30.0)   # = +8.0
        assert abs(result.selectivity_margin - expected_margin) < 1e-9
        assert result.offtarget_max_receptor == "SSTR3"

    # --- 경계 및 특수 케이스 ---

    def test_empty_offtargets_passes_with_zero_margin(self):
        """off-target 없으면 margin=0.0, passed=True (neutral sentinel)."""
        result = compute_selectivity_margin(
            seq_id="cand_E",
            sstr2_score=-25.0,
            offtarget_scores={},
        )
        assert result.selectivity_margin == 0.0
        assert result.passed
        assert result.offtarget_max_receptor == "none"

    def test_offtarget_too_strong_fails_gate(self):
        """off-target이 offtarget_max_allowed보다 강하면 탈락."""
        result = compute_selectivity_margin(
            seq_id="cand_F",
            sstr2_score=-30.0,
            offtarget_scores={"SSTR1": -20.0},  # -20 < -15 → 너무 강한 결합
            margin_min=2.0,
            offtarget_max_allowed=-15.0,
        )
        # margin = -20 - (-30) = +10 (양수이지만)
        # worst_score = -20 >= -15 → False → 탈락
        assert not result.passed, (
            "off-target ddG=-20 < offtarget_max_allowed=-15 이므로 탈락해야 함"
        )

    def test_margin_below_minimum_fails(self):
        """margin이 margin_min보다 낮으면 탈락."""
        result = compute_selectivity_margin(
            seq_id="cand_G",
            sstr2_score=-30.0,
            offtarget_scores={"SSTR3": -28.0},
            margin_min=5.0,
            offtarget_max_allowed=-35.0,  # 완화
        )
        # margin = -28 - (-30) = +2 < margin_min=5
        assert abs(result.selectivity_margin - 2.0) < 1e-9
        assert not result.passed

    def test_both_gates_must_pass(self):
        """margin ≥ min AND worst_score ≥ allowed 둘 다 통과해야 합격."""
        # Case 1: margin OK, off-target 너무 강함 → 탈락
        r1 = compute_selectivity_margin(
            "x", -30.0, {"SSTR1": -20.0}, margin_min=5.0, offtarget_max_allowed=-15.0
        )
        assert not r1.passed  # worst=-20 < -15

        # Case 2: margin 부족, off-target OK → 탈락
        r2 = compute_selectivity_margin(
            "x", -30.0, {"SSTR1": -28.0}, margin_min=5.0, offtarget_max_allowed=-15.0
        )
        # margin = -28 - (-30) = +2 < 5 → 탈락
        assert not r2.passed

        # Case 3: 둘 다 OK → 통과 (offtarget_max_allowed 완화)
        r3 = compute_selectivity_margin(
            "x", -30.0, {"SSTR1": -18.0}, margin_min=5.0, offtarget_max_allowed=-25.0
        )
        # margin = -18 - (-30) = +12 ≥ 5 AND worst=-18 ≥ -25 → 통과
        assert r3.passed


# ===========================================================================
# 2. TestApplySelectivityGate
# ===========================================================================

class TestApplySelectivityGate:
    """apply_selectivity_gate 통과/탈락 분류 검증."""

    def _make_result(self, seq_id: str, margin: float, passed: bool) -> "SelectivityResult":
        return SelectivityResult(
            seq_id=seq_id,
            sstr2_dock_score=-25.0,
            offtarget_scores={},
            offtarget_max_score=0.0,
            offtarget_max_receptor="none",
            selectivity_margin=margin,
            passed=passed,
        )

    def test_split_passed_failed(self):
        results = [
            self._make_result("A", margin=+12.0, passed=True),
            self._make_result("B", margin=+3.0, passed=False),
            self._make_result("C", margin=-5.0, passed=False),
        ]
        passed, failed = apply_selectivity_gate(results)
        assert len(passed) == 1
        assert len(failed) == 2
        assert passed[0].seq_id == "A"

    def test_all_passed(self):
        results = [self._make_result(f"x{i}", +15.0, True) for i in range(5)]
        passed, failed = apply_selectivity_gate(results)
        assert len(passed) == 5
        assert len(failed) == 0

    def test_all_failed(self):
        results = [self._make_result(f"y{i}", -3.0, False) for i in range(3)]
        passed, failed = apply_selectivity_gate(results)
        assert len(passed) == 0
        assert len(failed) == 3

    def test_empty_input(self):
        passed, failed = apply_selectivity_gate([])
        assert passed == []
        assert failed == []


# ===========================================================================
# 3. TestRunSelectivityScreening — estimation mode
# ===========================================================================

class TestRunSelectivityScreening:
    """estimation mode에서 전체 파이프라인 smoke test."""

    def _make_candidate(self, seq_id: str, score: float = -25.0) -> "DockingResult":
        return DockingResult(
            seq_id=seq_id,
            engine="boltz",
            score=score,
            confidence=0.9,
            pose_pdb="",
            rank=1,
        )

    def test_estimation_mode_runs(self, tmp_path: Path):
        """estimation mode (receptor_pdb 없음) 정상 실행."""
        candidates = [
            self._make_candidate("cand_01", score=-30.0),
            self._make_candidate("cand_02", score=-10.0),
        ]
        offtargets = [
            {"name": "SSTR1"},  # pdb_path 없음 → estimation mode
            {"name": "SSTR3"},
        ]
        config = {
            "selectivity": {
                "top_k_for_selectivity": 10,
                "engine": "boltz2",
                "selectivity_margin_min": 2.0,
                "offtarget_max_allowed": -35.0,  # 완화 (estimation 스코어 범위)
                "selectivity_noise_std": 2.0,
                "selectivity_seed": 42,
            },
        }
        output = run_selectivity_screening(candidates, offtargets, config)
        assert len(output.selectivity_results) == 2
        # margin 부호 확인: estimation mode에서 base_score + abs(offset) > base_score
        # → worst_score > sstr2_score → margin > 0 (양수)
        for r in output.selectivity_results:
            assert isinstance(r.selectivity_margin, float)
            # estimation mode: offset은 항상 양수(abs)이므로 off-target > on-target → margin > 0
            assert r.selectivity_margin > 0.0, (
                f"{r.seq_id}: estimation margin={r.selectivity_margin:.3f} 이 0 이하"
            )

    def test_offtarget_details_count(self, tmp_path: Path):
        """offtarget_docking_details = candidates × off-target 수."""
        candidates = [self._make_candidate("c1"), self._make_candidate("c2")]
        offtargets = [{"name": "SSTR1"}, {"name": "SSTR3"}, {"name": "SSTR4"}]
        config = {"selectivity": {"offtarget_max_allowed": -35.0}}
        output = run_selectivity_screening(candidates, offtargets, config)
        assert len(output.offtarget_docking_details) == 2 * 3  # 6건


# ===========================================================================
# 4. TestSchemaRoundtrip
# ===========================================================================

class TestSchemaRoundtrip:
    """SelectivityResult / Step05bOutput 직렬화 라운드트립."""

    def _make_sel_result(self, seq_id: str = "bb00_seq00") -> "SelectivityResult":
        return SelectivityResult(
            seq_id=seq_id,
            sstr2_dock_score=-30.0,
            offtarget_scores={"SSTR1": -18.0, "SSTR3": -15.0},
            offtarget_max_score=-18.0,
            offtarget_max_receptor="SSTR1",
            selectivity_margin=12.0,   # +12.0 (양수 = selective)
            passed=True,
        )

    def test_selectivity_result_roundtrip(self):
        r = self._make_sel_result()
        d = r.to_dict()
        r2 = SelectivityResult.from_dict(d)
        assert r2.seq_id == r.seq_id
        assert abs(r2.selectivity_margin - 12.0) < 1e-9
        assert r2.passed is True
        assert r2.offtarget_max_receptor == "SSTR1"

    def test_positive_margin_survives_serialization(self):
        """양수 margin이 직렬화 후에도 양수를 유지한다."""
        r = self._make_sel_result()
        d = r.to_dict()
        assert d["selectivity_margin"] == pytest.approx(12.0)
        r2 = SelectivityResult.from_dict(d)
        assert r2.selectivity_margin > 0

    def test_step05b_output_roundtrip(self):
        sel = self._make_sel_result()
        ot = OffTargetDockingResult(
            seq_id="bb00_seq00",
            receptor_name="SSTR1",
            dock_score=-18.0,
            confidence=0.0,
            engine="estimation",
        )
        output = Step05bOutput(
            selectivity_results=[sel],
            offtarget_docking_details=[ot],
        )
        d = output.to_dict()
        output2 = Step05bOutput.from_dict(d)
        assert len(output2.selectivity_results) == 1
        assert output2.selectivity_results[0].selectivity_margin > 0
        assert len(output2.offtarget_docking_details) == 1


# ===========================================================================
# 5. TestSignConventionAlignment — step05b vs step05c 부호 일관성 (P1-3)
# ===========================================================================

class TestSignConventionAlignment:
    """step05b와 step05c의 selectivity_margin 부호 방향이 동일함을 검증.

    step05b: margin = max(ddG_off) - ddG(SSTR2)
    step05c: margin = iPTM(SSTR2) - max(iPTM(off))
    둘 다: margin > 0 ↔ SSTR2 selective (T2/T3)
    """

    def test_step05b_positive_margin_means_sstr2_selective(self):
        """ddG 기준: SSTR2가 off-target보다 강하면 margin > 0."""
        r = compute_selectivity_margin(
            "x",
            sstr2_score=-30.0,   # SSTR2 강한 결합
            offtarget_scores={"SSTR1": -15.0},  # off-target 약한 결합
        )
        assert r.selectivity_margin > 0, (
            "SSTR2가 off-target보다 강하면 margin이 양수여야 함 (P1-3 부호 통일)"
        )

    def test_step05b_negative_margin_means_offtarget_dominant(self):
        """off-target이 SSTR2보다 강하면 margin < 0."""
        r = compute_selectivity_margin(
            "x",
            sstr2_score=-10.0,   # SSTR2 약한 결합
            offtarget_scores={"SSTR3": -30.0},  # off-target 강한 결합
        )
        assert r.selectivity_margin < 0, (
            "off-target이 SSTR2보다 강하면 margin이 음수여야 함 (P1-3 부호 통일)"
        )

    def test_step05c_convention_reference(self):
        """step05c: iPTM(SSTR2) > max(off-target) → margin > 0."""
        from pipeline_local.steps.step05c_boltz_cross import compute_selectivity_margin as c5c_margin
        margin, _ = c5c_margin(
            sstr2_iptm=0.97,
            offtarget_iptm={"SSTR1": 0.90, "SSTR3": 0.88},
        )
        assert margin > 0, "step05c: SSTR2 iPTM > off-target → margin > 0"

    def test_both_use_same_sign_convention(self):
        """step05b 양수 margin ↔ step05c 양수 margin 의미 동일성 확인."""
        from pipeline_local.steps.step05c_boltz_cross import compute_selectivity_margin as c5c_margin

        # step05b: SSTR2 결합 강함 → margin > 0
        r5b = compute_selectivity_margin(
            "x",
            sstr2_score=-30.0,
            offtarget_scores={"SSTR1": -10.0},
        )

        # step05c: SSTR2 iPTM 높음 → margin > 0
        margin_5c, _ = c5c_margin(
            sstr2_iptm=0.95,
            offtarget_iptm={"SSTR1": 0.85},
        )

        assert r5b.selectivity_margin > 0, "step05b margin sign 오류"
        assert margin_5c > 0, "step05c margin sign 오류"
        # 둘 다 양수면 SSTR2 선택적 — 일관됨 ✓

    def test_t2_t3_positive_margin_equivalence(self):
        """step05c T2(margin≥0) / T3(margin≥0.03) → step05b도 margin≥0이 선택적."""
        from pipeline_local.steps.step05c_boltz_cross import classify_tier

        # T3 margin (step05c 기준)
        assert classify_tier(0.05) == "T3"
        # step05b margin > 0 → 선택적 (동일 방향)
        r = compute_selectivity_margin(
            "x", -30.0, {"SSTR1": -10.0},
            margin_min=0.0,
            offtarget_max_allowed=-15.0,   # -10 >= -15 → 통과
        )
        assert r.selectivity_margin > 0
        assert r.passed


# ===========================================================================
# 6. TestGateThresholdsYaml — selectivity_margin_min 값 검증
# ===========================================================================

class TestGateThresholdsYaml:
    """gate_thresholds.yaml의 selectivity_margin_min이 양수로 변경됐는지 확인."""

    def test_selectivity_margin_min_is_positive(self):
        """P1-3 변경 후: selectivity_margin_min >= 0 (양수 방향)."""
        import yaml
        config_path = Path(__file__).parent.parent / "config" / "gate_thresholds.yaml"
        assert config_path.exists(), f"gate_thresholds.yaml 없음: {config_path}"
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        margin_min = cfg.get("selectivity_margin_min")
        assert margin_min is not None, "selectivity_margin_min 키 없음"
        assert margin_min >= 0, (
            f"P1-3 이후 selectivity_margin_min은 양수여야 함, 현재: {margin_min}"
        )

    def test_selectivity_direction_higher_is_better(self):
        """final_score_weights.selectivity.direction = 'higher_is_better'."""
        import yaml
        config_path = Path(__file__).parent.parent / "config" / "gate_thresholds.yaml"
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        direction = (
            cfg.get("final_score_weights", {})
               .get("selectivity", {})
               .get("direction", "")
        )
        assert direction == "higher_is_better", (
            f"selectivity direction이 'higher_is_better'여야 함, 현재: {direction!r}"
        )

    def test_offtarget_max_allowed_still_negative(self):
        """offtarget_max_allowed는 여전히 음수 (ddG 상한)."""
        import yaml
        config_path = Path(__file__).parent.parent / "config" / "gate_thresholds.yaml"
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        ot_max = cfg.get("offtarget_max_allowed")
        assert ot_max is not None
        assert ot_max < 0, (
            f"offtarget_max_allowed는 음수(ddG 상한)여야 함, 현재: {ot_max}"
        )


# ===========================================================================
# 7. TestBindingPocketInterface — A-01 결합 포켓 좌표 파일 로드 테스트
# ===========================================================================

class TestBindingPocketInterface:
    """A-01: 결합 포켓 좌표 JSON 파일 로드 및 SelectivityRunner 인터페이스 검증."""

    # binding_pocket_SSTR2.json 표준 경로
    _POCKET_JSON = (
        Path(__file__).parent.parent.parent
        / "data" / "somatostatin_receptor" / "binding_pocket_SSTR2.json"
    )

    def test_pocket_json_exists(self):
        """binding_pocket_SSTR2.json 파일이 생성되어 있어야 한다."""
        assert self._POCKET_JSON.exists(), (
            f"A-01 산출물 binding_pocket_SSTR2.json 없음: {self._POCKET_JSON}\n"
            "pipeline_local/scripts/extract_binding_pocket.py 를 먼저 실행하세요."
        )

    def test_pocket_json_has_required_keys(self):
        """JSON에 center_x, center_y, center_z, radius, gnina_config 포함 여부."""
        if not self._POCKET_JSON.exists():
            pytest.skip("binding_pocket_SSTR2.json 없음 — test_pocket_json_exists 먼저 실행")
        with open(self._POCKET_JSON, encoding="utf-8") as fh:
            data = json.load(fh)
        for key in ("center_x", "center_y", "center_z", "radius", "gnina_config"):
            assert key in data, f"필수 키 '{key}' 없음"

    def test_pocket_center_is_numeric(self):
        """center_x/y/z 가 float 이어야 한다."""
        if not self._POCKET_JSON.exists():
            pytest.skip("binding_pocket_SSTR2.json 없음")
        with open(self._POCKET_JSON, encoding="utf-8") as fh:
            data = json.load(fh)
        for key in ("center_x", "center_y", "center_z"):
            assert isinstance(data[key], (int, float)), f"{key}가 숫자가 아님: {data[key]!r}"

    def test_pocket_residues_count(self):
        """TM5+TM6 핵심 잔기 8개가 모두 포함되어야 한다."""
        if not self._POCKET_JSON.exists():
            pytest.skip("binding_pocket_SSTR2.json 없음")
        with open(self._POCKET_JSON, encoding="utf-8") as fh:
            data = json.load(fh)
        expected_residues = {205, 208, 209, 212, 272, 273, 276, 279}
        actual_residues = set(data.get("residues", []))
        assert expected_residues == actual_residues, (
            f"잔기 불일치: 기대={sorted(expected_residues)}, 실제={sorted(actual_residues)}"
        )

    def test_pocket_gnina_config_structure(self):
        """gnina_config 에 center_x/y/z, size_x/y/z 키가 모두 있어야 한다."""
        if not self._POCKET_JSON.exists():
            pytest.skip("binding_pocket_SSTR2.json 없음")
        with open(self._POCKET_JSON, encoding="utf-8") as fh:
            data = json.load(fh)
        gnina_cfg = data.get("gnina_config", {})
        for key in ("center_x", "center_y", "center_z", "size_x", "size_y", "size_z"):
            assert key in gnina_cfg, f"gnina_config에 '{key}' 없음"

    def test_load_binding_pocket_helper(self):
        """모듈 수준 load_binding_pocket() 헬퍼가 올바른 딕셔너리를 반환한다."""
        if not self._POCKET_JSON.exists():
            pytest.skip("binding_pocket_SSTR2.json 없음")
        from pipeline_local.core.selectivity_runner import load_binding_pocket
        data = load_binding_pocket(str(self._POCKET_JSON))
        assert "center_x" in data
        assert "center_y" in data
        assert "center_z" in data
        assert isinstance(data["center_x"], (int, float))

    def test_load_binding_pocket_missing_file(self):
        """존재하지 않는 파일 경로 시 FileNotFoundError."""
        from pipeline_local.core.selectivity_runner import load_binding_pocket
        with pytest.raises(FileNotFoundError):
            load_binding_pocket("/nonexistent/path/binding_pocket.json")

    def test_load_binding_pocket_missing_keys(self, tmp_path: Path):
        """필수 키(center_x 등)가 없는 JSON 시 ValueError."""
        from pipeline_local.core.selectivity_runner import load_binding_pocket
        bad_json = tmp_path / "bad_pocket.json"
        bad_json.write_text('{"receptor": "SSTR2_7XNA"}', encoding="utf-8")
        with pytest.raises(ValueError, match="center_x"):
            load_binding_pocket(str(bad_json))

    def test_selectivity_runner_binding_pocket_init(self, tmp_path: Path):
        """SelectivityRunner(binding_pocket_json=...) 초기화 시 포켓 데이터 로드."""
        from pipeline_local.core.selectivity_runner import SelectivityRunner
        # 최소 유효 JSON 생성
        pocket_data = {
            "receptor": "SSTR2_7XNA",
            "center_x": -5.595,
            "center_y": -28.626,
            "center_z": 52.21,
            "radius": 13.035,
            "box_size": 30.0,
            "gnina_config": {
                "center_x": -5.595,
                "center_y": -28.626,
                "center_z": 52.21,
                "size_x": 30.0,
                "size_y": 30.0,
                "size_z": 30.0,
            },
        }
        pocket_file = tmp_path / "test_pocket.json"
        pocket_file.write_text(json.dumps(pocket_data), encoding="utf-8")

        runner = SelectivityRunner(binding_pocket_json=str(pocket_file))
        center = runner.get_pocket_center()
        assert center is not None, "get_pocket_center() 가 None 반환"
        assert len(center) == 3
        assert abs(center[0] - (-5.595)) < 1e-3, f"center_x 불일치: {center[0]}"

    def test_selectivity_runner_get_gnina_config(self, tmp_path: Path):
        """SelectivityRunner.get_gnina_config() 가 6개 키를 모두 반환한다."""
        from pipeline_local.core.selectivity_runner import SelectivityRunner
        pocket_data = {
            "center_x": -5.595,
            "center_y": -28.626,
            "center_z": 52.21,
            "radius": 13.035,
            "box_size": 30.0,
            "gnina_config": {
                "center_x": -5.595,
                "center_y": -28.626,
                "center_z": 52.21,
                "size_x": 30.0,
                "size_y": 30.0,
                "size_z": 30.0,
            },
        }
        pocket_file = tmp_path / "test_pocket.json"
        pocket_file.write_text(json.dumps(pocket_data), encoding="utf-8")

        runner = SelectivityRunner(binding_pocket_json=str(pocket_file))
        gnina_cfg = runner.get_gnina_config()
        assert gnina_cfg is not None
        for key in ("center_x", "center_y", "center_z", "size_x", "size_y", "size_z"):
            assert key in gnina_cfg, f"gnina_config에 '{key}' 없음"

    def test_selectivity_runner_no_pocket(self):
        """binding_pocket_json 미설정 시 get_pocket_center() / get_gnina_config() 가 None."""
        from pipeline_local.core.selectivity_runner import SelectivityRunner
        runner = SelectivityRunner()
        assert runner.get_pocket_center() is None
        assert runner.get_gnina_config() is None

    def test_aligned_pdb_files_exist(self):
        """A-01 정렬 산출물 {SSTRN}_aligned.pdb 4개가 모두 존재해야 한다."""
        data_dir = (
            Path(__file__).parent.parent.parent
            / "data" / "somatostatin_receptor"
        )
        for receptor in ("SSTR1", "SSTR3", "SSTR4", "SSTR5"):
            aligned_pdb = data_dir / f"{receptor}_aligned.pdb"
            assert aligned_pdb.exists(), (
                f"{receptor}_aligned.pdb 없음: {aligned_pdb}\n"
                "pipeline_local/scripts/align_subtypes.py 를 먼저 실행하세요."
            )
