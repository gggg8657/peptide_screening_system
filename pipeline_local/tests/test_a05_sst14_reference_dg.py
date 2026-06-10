"""
test_a05_sst14_reference_dg.py
==============================
A-05 SST14 reference dG 통계 및 pharmacology_guards 통합 테스트.

테스트 범위:
  1. compute_statistics() — 정상 입력, 경계 케이스
  2. SST14_SSTR2_ref_ddg_flexpep LITERATURE_VALUES 항목 존재 확인
  3. reference JSON 스키마 검증
"""
from __future__ import annotations

import json
import math
import statistics
import tempfile
from pathlib import Path
from typing import List

import pytest

# ---------------------------------------------------------------------------
# 테스트 대상 import
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]

import sys
sys.path.insert(0, str(_REPO_ROOT / "pipeline_local" / "scripts"))

from run_sst14_reference_docking import compute_statistics  # type: ignore[import]


# ---------------------------------------------------------------------------
# 1. compute_statistics() 단위 테스트
# ---------------------------------------------------------------------------

class TestComputeStatistics:
    """compute_statistics() 함수 단위 테스트."""

    def test_basic_10_values(self) -> None:
        """n=10 정상 입력에서 통계값이 올바르게 계산되어야 한다."""
        # run_1 실측 기반 모의 데이터 (양수 범위)
        values = [550.0, 555.0, 560.0, 545.0, 570.0,
                  548.0, 562.0, 558.0, 553.0, 565.0]
        result = compute_statistics(values, elapsed_total=100.0)

        assert result["n_runs"] == 10
        assert result["sequence"] == "AGCKNFFWKTFTSC"
        assert result["receptor"] == "SSTR2_7XNA"
        assert result["stub"] is False
        assert result["engine"] == "pyrosetta-flexpep"

        # 평균 검증
        expected_mean = statistics.mean(values)
        assert abs(result["mean_dG_kcal_mol"] - expected_mean) < 0.01

        # 표준편차 검증
        expected_std = statistics.stdev(values)
        assert abs(result["std_dG_kcal_mol"] - expected_std) < 0.01

        # min/max 검증
        assert result["min_dG"] == min(values)
        assert result["max_dG"] == max(values)

    def test_ci_95_bounds(self) -> None:
        """95% CI는 mean을 포함해야 한다."""
        values = [550.0, 560.0, 570.0, 540.0, 555.0,
                  565.0, 545.0, 558.0, 562.0, 550.0]
        result = compute_statistics(values, elapsed_total=50.0)

        ci_lower = result["ci_95"][0]
        ci_upper = result["ci_95"][1]
        mean_val = result["mean_dG_kcal_mol"]

        assert ci_lower < mean_val < ci_upper, (
            f"95% CI [{ci_lower}, {ci_upper}]이 mean={mean_val}을 포함하지 않음"
        )

    def test_ci_95_length(self) -> None:
        """95% CI는 두 원소를 가져야 한다."""
        values = [100.0] * 10
        result = compute_statistics(values, elapsed_total=10.0)
        assert len(result["ci_95"]) == 2

    def test_n2_minimum(self) -> None:
        """n=2 최소 케이스에서도 통계가 계산되어야 한다."""
        values = [550.0, 560.0]
        result = compute_statistics(values, elapsed_total=20.0)
        assert result["n_runs"] == 2
        assert result["mean_dG_kcal_mol"] == pytest.approx(555.0)

    def test_zero_std_single_repeated(self) -> None:
        """모든 값이 동일한 경우 std=0이어야 한다."""
        values = [500.0] * 5
        result = compute_statistics(values, elapsed_total=5.0)
        assert result["std_dG_kcal_mol"] == pytest.approx(0.0, abs=0.001)

    def test_negative_values(self) -> None:
        """음수 dG 값도 올바르게 처리되어야 한다 (이상적 도킹 케이스)."""
        values = [-90.0, -92.0, -88.0, -95.0, -91.0,
                  -93.0, -89.0, -94.0, -87.0, -96.0]
        result = compute_statistics(values, elapsed_total=100.0)
        assert result["mean_dG_kcal_mol"] < 0.0
        assert result["min_dG"] < result["max_dG"]

    def test_empty_raises(self) -> None:
        """빈 리스트는 ValueError를 발생시켜야 한다."""
        with pytest.raises(ValueError, match="dG 값이 없습니다"):
            compute_statistics([], elapsed_total=0.0)

    def test_all_dG_values_stored(self) -> None:
        """모든 dG 값이 결과에 저장되어야 한다."""
        values = [551.41, 562.33, 545.78, 570.22, 558.90,
                  548.15, 563.44, 555.67, 568.11, 542.99]
        result = compute_statistics(values, elapsed_total=762.0)
        assert len(result["all_dG_values"]) == len(values)
        for orig, stored in zip(sorted(values), sorted(result["all_dG_values"])):
            assert abs(orig - stored) < 0.01

    def test_elapsed_total_stored(self) -> None:
        """elapsed_total_sec가 결과에 포함되어야 한다."""
        values = [500.0] * 3
        result = compute_statistics(values, elapsed_total=123.456)
        assert result["elapsed_total_sec"] == pytest.approx(123.5, abs=0.1)


# ---------------------------------------------------------------------------
# 2. pharmacology_guards LITERATURE_VALUES 항목 테스트
# ---------------------------------------------------------------------------

from pharmacology_guards import LITERATURE_VALUES  # type: ignore[import]


class TestPharmacologyGuardsA05:
    """A-05 관련 LITERATURE_VALUES 항목 검증."""

    def test_flexpep_entry_exists(self) -> None:
        """SST14_SSTR2_ref_ddg_flexpep 항목이 LITERATURE_VALUES에 존재해야 한다."""
        assert "SST14_SSTR2_ref_ddg_flexpep" in LITERATURE_VALUES, (
            "A-05 FlexPepDock reference 항목이 LITERATURE_VALUES에 없음 — "
            "pharmacology_guards.py 업데이트 필요"
        )

    def test_flexpep_entry_structure(self) -> None:
        """SST14_SSTR2_ref_ddg_flexpep 항목이 올바른 구조를 가져야 한다."""
        entry = LITERATURE_VALUES.get("SST14_SSTR2_ref_ddg_flexpep", {})
        assert "ref_ddg_reu_mean" in entry, "ref_ddg_reu_mean 키 없음"

        val_tuple = entry["ref_ddg_reu_mean"]
        assert len(val_tuple) == 3, "LITERATURE_VALUES 항목은 (value, source, comment) 3-tuple이어야 함"

        value, source, comment = val_tuple
        assert isinstance(value, (int, float)), f"값이 숫자가 아님: {type(value)}"
        assert isinstance(source, str) and len(source) > 5, "출처 문자열 없음"
        assert isinstance(comment, str) and len(comment) > 5, "주석 문자열 없음"

    def test_boltz2_entry_preserved(self) -> None:
        """기존 Boltz2 항목이 변경되지 않아야 한다."""
        assert "SST14_SSTR2_ref_ddg_boltz2" in LITERATURE_VALUES
        val, src, _ = LITERATURE_VALUES["SST14_SSTR2_ref_ddg_boltz2"]["ref_ddg_reu"]
        assert val == pytest.approx(-95.024, abs=0.001), (
            f"Boltz2 reference 값이 변경됨: {val} (예상: -95.024)"
        )


# ---------------------------------------------------------------------------
# 3. reference JSON 스키마 테스트
# ---------------------------------------------------------------------------

_REF_JSON_PATH = (
    _REPO_ROOT / "data" / "somatostatin_receptor" / "SST14_SSTR2_reference_dG.json"
)

_REQUIRED_KEYS = [
    "sequence", "receptor", "n_runs", "mean_dG_kcal_mol", "std_dG_kcal_mol",
    "min_dG", "max_dG", "median_dG", "ci_95", "elapsed_total_sec", "stub",
]


class TestReferenceJSON:
    """SST14_SSTR2_reference_dG.json 스키마 검증."""

    @pytest.fixture(autouse=True)
    def _require_json(self) -> None:
        """reference JSON 파일이 없으면 테스트를 건너뜀."""
        if not _REF_JSON_PATH.exists():
            pytest.skip(
                f"reference JSON 파일 없음: {_REF_JSON_PATH} "
                "— 도킹 완료 후 재실행 필요"
            )

    def test_json_parseable(self) -> None:
        """reference JSON이 파싱 가능해야 한다."""
        with open(_REF_JSON_PATH) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_required_keys(self) -> None:
        """필수 키가 모두 존재해야 한다."""
        with open(_REF_JSON_PATH) as f:
            data = json.load(f)
        missing = [k for k in _REQUIRED_KEYS if k not in data]
        assert not missing, f"누락된 키: {missing}"

    def test_sequence_correct(self) -> None:
        """sequence가 SST14 원형과 일치해야 한다."""
        with open(_REF_JSON_PATH) as f:
            data = json.load(f)
        assert data["sequence"] == "AGCKNFFWKTFTSC"

    def test_n_runs_gte_10(self) -> None:
        """n_runs가 10 이상이어야 한다 (A-05 요구사항)."""
        with open(_REF_JSON_PATH) as f:
            data = json.load(f)
        assert data["n_runs"] >= 10, f"n_runs={data['n_runs']} < 10 (A-05 요구사항 미충족)"

    def test_ci_95_valid(self) -> None:
        """95% CI가 2원소 리스트이고 lower < upper이어야 한다."""
        with open(_REF_JSON_PATH) as f:
            data = json.load(f)
        ci = data["ci_95"]
        assert len(ci) == 2
        assert ci[0] < ci[1], f"CI 역전: {ci[0]} >= {ci[1]}"

    def test_stub_false(self) -> None:
        """stub가 False여야 한다 (실제 도킹 결과)."""
        with open(_REF_JSON_PATH) as f:
            data = json.load(f)
        assert data["stub"] is False

    def test_std_finite(self) -> None:
        """std_dG_kcal_mol이 유한한 숫자여야 한다."""
        with open(_REF_JSON_PATH) as f:
            data = json.load(f)
        std = data["std_dG_kcal_mol"]
        assert math.isfinite(std), f"std가 유한하지 않음: {std}"

    def test_min_lte_mean_lte_max(self) -> None:
        """min_dG ≤ mean_dG ≤ max_dG이어야 한다."""
        with open(_REF_JSON_PATH) as f:
            data = json.load(f)
        assert data["min_dG"] <= data["mean_dG_kcal_mol"] <= data["max_dG"], (
            f"순서 위반: min={data['min_dG']}, mean={data['mean_dG_kcal_mol']}, max={data['max_dG']}"
        )
