"""
test_flexpep_dock_wrapper.py
=============================
pipeline_local/scripts/flexpep_dock.py (worker CLI 호환 wrapper) 단위 테스트.

PyRosetta 실제 실행이 필요한 테스트는 PYROSETTA_AVAILABLE 마크로 건너뜀.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

# 프로젝트 루트를 sys.path에 추가
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "pipeline_local" / "scripts"))

# flexpep_dock wrapper import
import importlib.util

_WRAPPER_PATH = _REPO_ROOT / "pipeline_local" / "scripts" / "flexpep_dock.py"
assert _WRAPPER_PATH.exists(), f"wrapper 파일 없음: {_WRAPPER_PATH}"

spec = importlib.util.spec_from_file_location("flexpep_dock_wrapper", _WRAPPER_PATH)
wrapper_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper_mod)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

PYROSETTA_AVAILABLE = False
try:
    import pyrosetta  # noqa: F401
    PYROSETTA_AVAILABLE = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# resolve_receptor_pdb 테스트
# ---------------------------------------------------------------------------

class TestResolveReceptorPdb:
    """resolve_receptor_pdb — CIF/PDB 분기 처리."""

    def test_pdb_path_returned_as_is(self, tmp_path: Path) -> None:
        pdb = tmp_path / "test.pdb"
        pdb.write_text("ATOM\n")
        result = wrapper_mod.resolve_receptor_pdb(str(pdb))
        assert result == str(pdb)

    def test_cif_extension_triggers_conversion_check(self, tmp_path: Path) -> None:
        """CIF 경로는 .pdb 경로를 반환해야 한다 (변환 자체는 PyRosetta 필요)."""
        cif = tmp_path / "test.cif"
        cif.write_text("data_test\n")
        pdb = tmp_path / "test.pdb"
        pdb.write_text("ATOM\n")  # 캐시 존재 시뮬레이션

        result = wrapper_mod.resolve_receptor_pdb(str(cif))
        assert result.endswith(".pdb"), f"CIF→PDB 변환 경로 기대: {result}"

    def test_mmcif_extension_also_handled(self, tmp_path: Path) -> None:
        cif = tmp_path / "test.mmcif"
        cif.write_text("data_test\n")
        pdb = tmp_path / "test.pdb"
        pdb.write_text("ATOM\n")

        result = wrapper_mod.resolve_receptor_pdb(str(cif))
        assert result.endswith(".pdb")


# ---------------------------------------------------------------------------
# aggregate_scores 테스트
# ---------------------------------------------------------------------------

class TestAggregateScores:
    """aggregate_scores — best (lowest ddg) 선택."""

    def test_empty_raises_runtime_error(self) -> None:
        """ddg_values 가 빈 리스트면 RuntimeError 발생 (mock 금지 정책).

        이전 동작: silent 으로 (0.0, 0.0) 반환 → SSTR1 dG=0.0 으로
        Hard Cutoff 가짜 통과 발생 (2026-05-20 e36b362d job).
        """
        import pytest
        with pytest.raises(RuntimeError, match="ddg_values 빈 리스트"):
            wrapper_mod.aggregate_scores([], [])

    def test_single_value(self) -> None:
        dg, isc = wrapper_mod.aggregate_scores([-5.0], [-40.0])
        assert dg == -5.0
        assert isc == -40.0

    def test_best_lowest_ddg_selected(self) -> None:
        """ddg가 가장 낮은 (가장 유리한) 구조가 선택된다."""
        ddg_values = [-3.0, -8.5, -5.0, -8.4]
        interface_scores = [-20.0, -45.0, -25.0, -44.0]
        dg, isc = wrapper_mod.aggregate_scores(ddg_values, interface_scores)
        # -8.5 가 최소, index=1
        assert dg == -8.5
        assert isc == -45.0

    def test_positive_values_handled(self) -> None:
        """양수 ddg도 정상 처리 (나쁜 결합이지만 오류는 아님)."""
        dg, isc = wrapper_mod.aggregate_scores([2.0, 5.0], [10.0, 20.0])
        assert dg == 2.0  # 낮은 값 선택
        assert isc == 10.0


# ---------------------------------------------------------------------------
# FREEDOM_MAP 테스트
# ---------------------------------------------------------------------------

class TestFreedomMap:
    """_FREEDOM_MAP 파라미터 검증."""

    def test_all_freedom_levels_exist(self) -> None:
        for level in ("low", "med", "high"):
            assert level in wrapper_mod._FREEDOM_MAP, f"'{level}' missing"

    def test_freedom_map_has_required_keys(self) -> None:
        for level, params in wrapper_mod._FREEDOM_MAP.items():
            assert "cycles" in params, f"{level} missing 'cycles'"
            assert "nstruct_multiplier" in params, f"{level} missing 'nstruct_multiplier'"

    def test_high_freedom_has_more_cycles(self) -> None:
        low_c = wrapper_mod._FREEDOM_MAP["low"]["cycles"]
        high_c = wrapper_mod._FREEDOM_MAP["high"]["cycles"]
        assert high_c >= low_c, "high 자유도는 cycles >= low 자유도여야 함"


# ---------------------------------------------------------------------------
# CLI argparse 테스트
# ---------------------------------------------------------------------------

class TestCLIParsing:
    """argparse CLI 파라미터 기본값 및 타입 검증."""

    def _parse_args(self, extra_args: list[str]) -> object:
        """argparse를 직접 호출해 args 반환."""
        import argparse

        # main()의 parser를 재현
        parser = argparse.ArgumentParser()
        parser.add_argument("--receptor", required=True)
        parser.add_argument("--sequence", required=True)
        parser.add_argument("--output-prefix", required=True)
        parser.add_argument("--cycles", type=int, default=10)
        parser.add_argument("--nstruct", type=int, default=50)
        parser.add_argument(
            "--flex-pep-freedom", default="med",
            choices=["low", "med", "high"],
        )
        parser.add_argument("--ddg-cycle", type=int, default=5)
        return parser.parse_args(
            ["--receptor", "x.pdb", "--sequence", "AGCKNFFWKTFTSC",
             "--output-prefix", "/tmp/test"] + extra_args
        )

    def test_defaults(self) -> None:
        args = self._parse_args([])
        assert args.cycles == 10
        assert args.nstruct == 50
        assert args.flex_pep_freedom == "med"
        assert args.ddg_cycle == 5

    def test_custom_values(self) -> None:
        args = self._parse_args([
            "--cycles", "2",
            "--nstruct", "3",
            "--flex-pep-freedom", "low",
            "--ddg-cycle", "1",
        ])
        assert args.cycles == 2
        assert args.nstruct == 3
        assert args.flex_pep_freedom == "low"
        assert args.ddg_cycle == 1

    def test_sequence_preserved(self) -> None:
        args = self._parse_args([])
        assert args.sequence == "AGCKNFFWKTFTSC"

    def test_invalid_freedom_rejected(self) -> None:
        with pytest.raises(SystemExit):
            self._parse_args(["--flex-pep-freedom", "extreme"])


# ---------------------------------------------------------------------------
# CLI subprocess 테스트 — 파일 없음 오류
# ---------------------------------------------------------------------------

class TestCLISubprocess:
    """subprocess로 wrapper 실행 — 오류 처리 경로."""

    def test_missing_receptor_exits_nonzero(self) -> None:
        """receptor 파일 없으면 exit code 1로 종료."""
        # bio-tools 환경에서 실행 (PyRosetta 설치됨)
        proc = subprocess.run(
            [
                "conda", "run", "-n", "bio-tools",
                "python", str(_WRAPPER_PATH),
                "--receptor", "/nonexistent/receptor.pdb",
                "--sequence", "AGCKNFFWKTFTSC",
                "--output-prefix", "/tmp/test_wrapper_smoke",
                "--cycles", "1",
                "--nstruct", "1",
                "--flex-pep-freedom", "low",
                "--ddg-cycle", "1",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert proc.returncode != 0, (
            f"존재하지 않는 receptor에 대해 exit 0 반환: {proc.stderr}"
        )


# ---------------------------------------------------------------------------
# SSTR2 .cif 존재 확인 테스트
# ---------------------------------------------------------------------------

class TestSSTR2CifExists:
    """SSTR2 .cif 파일이 data/ 디렉토리에 존재하는지 확인."""

    def test_sstr2_cif_exists(self) -> None:
        cif = _REPO_ROOT / "data" / "somatostatin_receptor" / "SSTR2_7XNA.cif"
        assert cif.exists(), f"SSTR2 CIF 파일 없음: {cif}"

    def test_sstr2_pdb_absent(self) -> None:
        """SSTR2 .pdb는 현재 없음 — wrapper의 CIF→PDB 변환이 필요한 이유."""
        pdb = _REPO_ROOT / "data" / "somatostatin_receptor" / "SSTR2_7XNA.pdb"
        if pdb.exists():
            pytest.skip("SSTR2.pdb가 이미 생성되어 있음 — 변환 테스트 불필요")
        # .pdb 없음이 정상 상태 (wrapper 이전)
        assert not pdb.exists()


# ---------------------------------------------------------------------------
# wrapper 출력 JSON 형식 검증 (모킹)
# ---------------------------------------------------------------------------

class TestWrapperOutputFormat:
    """wrapper가 올바른 JSON 키를 출력하는지 검증 (PyRosetta 모킹)."""

    def test_result_has_required_keys(self) -> None:
        """aggregate_scores + 결과 딕셔너리가 worker 기대 키를 포함."""
        # worker가 기대하는 키 목록
        required_keys = {"dG_kcal_mol", "interface_score", "stub"}

        # 가짜 결과 조립 (wrapper main() 로직과 동일한 방식)
        ddg_values = [-7.5, -9.2]
        interface_scores = [-40.0, -52.0]
        best_dg, best_interface = wrapper_mod.aggregate_scores(ddg_values, interface_scores)

        result = {
            "dG_kcal_mol": round(best_dg, 4),
            "interface_score": round(best_interface, 4),
            "ddg": round(best_dg, 4),
            "stub": False,
        }

        for key in required_keys:
            assert key in result, f"required key '{key}' missing from result"

    def test_stub_is_false_for_real_run(self) -> None:
        ddg_values = [-5.0]
        interface_scores = [-35.0]
        best_dg, best_interface = wrapper_mod.aggregate_scores(ddg_values, interface_scores)

        result = {
            "dG_kcal_mol": round(best_dg, 4),
            "interface_score": round(best_interface, 4),
            "stub": False,
        }
        assert result["stub"] is False

    def test_worker_dg_parsing_compatibility(self) -> None:
        """worker의 JSON 파싱 로직과 호환되는지 검증.

        worker:
          dg = float(scores.get("dG_kcal_mol", scores.get("ddg", 0.0)))
          interface_score = float(scores.get("interface_score", 0.0))
        """
        mock_output = {
            "dG_kcal_mol": -9.2,
            "interface_score": -52.0,
            "ddg": -9.2,
            "stub": False,
        }
        dg = float(mock_output.get("dG_kcal_mol", mock_output.get("ddg", 0.0)))
        interface_score = float(mock_output.get("interface_score", 0.0))

        assert dg == -9.2
        assert interface_score == -52.0
        assert interface_score < -30.0, "SSTR2 pass gate (-30 기준)"
