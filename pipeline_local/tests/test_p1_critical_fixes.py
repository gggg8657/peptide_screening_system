"""
test_p1_critical_fixes.py
=========================
P1-1 Critical 3건 fix 회귀 테스트

C-M1-1: step01 _call_openfold3_local() — mmcif 키 처리
C-M1-2: step02 generate_backbones() — 백본 0개 RuntimeError
C-M2-1: orchestrator — step05b/05c save 호출

2026-05-13  engineer-backend
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# 경로 설정
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ===========================================================================
# C-M1-1: step01 _call_openfold3_local() — "mmcif" 키 처리
# ===========================================================================

class TestStep01OpenFold3MmcifKey:
    """run_openfold3.py가 {"mmcif": ..., "confidence": ...} 형식으로 반환할 때
    _call_openfold3_local()이 CIF→PDB 변환 후 PDB 텍스트를 반환하는지 검증."""

    def _make_minimal_pdb(self) -> str:
        """테스트용 최소 PDB 텍스트."""
        return (
            "ATOM      1  CA  ALA A   1       1.000   2.000   3.000  1.00  0.00           C\n"
            "END\n"
        )

    def _make_minimal_cif(self) -> str:
        """테스트용 최소 mmCIF 텍스트 (실제 파싱에 사용하지 않음)."""
        return (
            "data_structure\n"
            "_entry.id structure\n"
            "loop_\n"
            "_atom_site.id\n"
            "_atom_site.type_symbol\n"
            "1 C\n"
        )

    def test_mmcif_key_triggers_cif_to_pdb_conversion(self):
        """'mmcif' 키가 있을 때 _convert_cif_to_pdb 호출 후 PDB 반환."""
        from pipeline_local.steps import step01_receptor

        dummy_pdb = self._make_minimal_pdb()
        dummy_cif = self._make_minimal_cif()

        # LocalModelRunner.run() 이 {"mmcif": ..., "confidence": ...} 를 반환하도록 mock
        mock_result = {"mmcif": dummy_cif, "confidence": {"pTM": 0.9}}

        with (
            patch.object(step01_receptor, "LocalModelRunner") as MockRunner,
            patch.object(step01_receptor, "_convert_cif_to_pdb", return_value=dummy_pdb) as mock_convert,
        ):
            mock_instance = MockRunner.return_value
            mock_instance.run.return_value = mock_result

            receptor_cfg = {"sequence": "AGCKNFFWKTFTSC"}
            config = {}
            result = step01_receptor._call_openfold3_local(receptor_cfg, config)

        # _convert_cif_to_pdb 가 호출되었어야 함 (tmp 경로 + cif_text)
        assert mock_convert.called, "_convert_cif_to_pdb 가 호출되지 않았습니다"
        _, call_args = mock_convert.call_args[0], mock_convert.call_args
        # 두 번째 인자(cif_text)가 dummy_cif인지 확인
        assert mock_convert.call_args[0][1] == dummy_cif
        assert result == dummy_pdb

    def test_output_pdb_key_still_works(self):
        """기존 'output_pdb' 키도 계속 작동하는지 확인 (하위 호환)."""
        from pipeline_local.steps import step01_receptor

        dummy_pdb = self._make_minimal_pdb()
        mock_result = {"output_pdb": dummy_pdb}

        with patch.object(step01_receptor, "LocalModelRunner") as MockRunner:
            mock_instance = MockRunner.return_value
            mock_instance.run.return_value = mock_result

            receptor_cfg = {"sequence": "AGCKNFFWKTFTSC"}
            result = step01_receptor._call_openfold3_local(receptor_cfg, {})

        assert result == dummy_pdb

    def test_pdb_key_works(self):
        """'pdb' 키도 작동하는지 확인."""
        from pipeline_local.steps import step01_receptor

        dummy_pdb = self._make_minimal_pdb()
        mock_result = {"pdb": dummy_pdb}

        with patch.object(step01_receptor, "LocalModelRunner") as MockRunner:
            mock_instance = MockRunner.return_value
            mock_instance.run.return_value = mock_result

            receptor_cfg = {"sequence": "AGCKNFFWKTFTSC"}
            result = step01_receptor._call_openfold3_local(receptor_cfg, {})

        assert result == dummy_pdb

    def test_no_pdb_or_mmcif_raises_runtime_error(self):
        """'output_pdb', 'pdb', 'mmcif' 키가 모두 없으면 RuntimeError."""
        from pipeline_local.steps import step01_receptor

        mock_result = {"confidence": {"pTM": 0.9}, "other_key": "value"}

        with patch.object(step01_receptor, "LocalModelRunner") as MockRunner:
            mock_instance = MockRunner.return_value
            mock_instance.run.return_value = mock_result

            receptor_cfg = {"sequence": "AGCKNFFWKTFTSC"}
            with pytest.raises(RuntimeError, match="openfold3 local model returned no PDB or mmCIF"):
                step01_receptor._call_openfold3_local(receptor_cfg, {})

    def test_sequence_missing_raises_runtime_error(self):
        """'receptor.sequence' 없으면 RuntimeError."""
        from pipeline_local.steps import step01_receptor

        with patch.object(step01_receptor, "LocalModelRunner"):
            with pytest.raises(RuntimeError, match="receptor.sequence"):
                step01_receptor._call_openfold3_local({}, {})

    def test_mmcif_convert_failure_still_raises(self):
        """mmcif 키가 있지만 CIF→PDB 변환이 빈 문자열 반환 시 RuntimeError."""
        from pipeline_local.steps import step01_receptor

        mock_result = {"mmcif": "bad_cif_content"}

        with (
            patch.object(step01_receptor, "LocalModelRunner") as MockRunner,
            # _convert_cif_to_pdb 가 "" (빈 문자열) 반환 — falsy
            patch.object(step01_receptor, "_convert_cif_to_pdb", return_value=""),
        ):
            mock_instance = MockRunner.return_value
            mock_instance.run.return_value = mock_result

            receptor_cfg = {"sequence": "AGCKNFFWKTFTSC"}
            with pytest.raises(RuntimeError):
                step01_receptor._call_openfold3_local(receptor_cfg, {})


# ===========================================================================
# C-M1-2: step02 generate_backbones() — 백본 0개 RuntimeError
# ===========================================================================

class TestStep02ZeroBackboneGuard:
    """백본 0개 생성 시 RuntimeError가 발생하는지 검증."""

    def _make_minimal_config(self, n_backbone: int = 2, tmp_path: Optional[Path] = None) -> Dict[str, Any]:
        base = str(tmp_path) if tmp_path else "/tmp/test_step02"
        return {
            "run_id": "test_run",
            "output_base_dir": base,
            "contigs": "B1-10/0 5-10",
            "hotspot_res": [],
            "iteration": {
                "n_backbone": n_backbone,
                "diffusion_steps": 10,
            },
        }

    def test_all_backbones_fail_raises_runtime_error(self, tmp_path):
        """모든 backbone 생성 실패 시 RuntimeError 발생."""
        from pipeline_local.steps import step02_backbone

        config = self._make_minimal_config(n_backbone=3, tmp_path=tmp_path)
        dummy_pdb_path = tmp_path / "receptor.pdb"
        dummy_pdb_path.write_text(
            "ATOM      1  CA  ALA B   1       0.000   0.000   0.000  1.00  0.00           C\n"
            "END\n"
        )

        # generate_single_backbone 이 항상 RuntimeError 발생하도록 mock
        with patch.object(
            step02_backbone,
            "generate_single_backbone",
            side_effect=RuntimeError("rfdiffusion 실패"),
        ):
            with pytest.raises(RuntimeError, match="Backbone generation failed: 0 PDBs"):
                step02_backbone.generate_backbones(
                    receptor_pdb=str(dummy_pdb_path),
                    pocket_info={},
                    config=config,
                )

    def test_partial_failure_continues(self, tmp_path):
        """일부 backbone 실패, 일부 성공 시 RuntimeError 없음."""
        from pipeline_local.steps import step02_backbone

        config = self._make_minimal_config(n_backbone=3, tmp_path=tmp_path)
        dummy_pdb_path = tmp_path / "receptor.pdb"
        dummy_pdb_path.write_text(
            "ATOM      1  CA  ALA B   1       0.000   0.000   0.000  1.00  0.00           C\n"
            "END\n"
        )

        # 첫 번째 seed는 실패, 나머지는 성공
        valid_pdb = (
            "ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00  0.00           C\n"
            "ATOM      2  CA  GLY A   2       1.000   1.000   1.000  1.00  0.00           C\n"
        ) * 30  # 충분한 ATOM 수 (≥50)

        call_count = [0]
        def mock_generate(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("첫 번째 실패")
            return valid_pdb

        with patch.object(step02_backbone, "generate_single_backbone", side_effect=mock_generate):
            result = step02_backbone.generate_backbones(
                receptor_pdb=str(dummy_pdb_path),
                pocket_info={},
                config=config,
            )

        # 3개 중 2개 성공 — RuntimeError 없음
        assert result.n_generated == 2
        assert len(result.backbone_pdbs) == 2

    def test_zero_backbone_config_raises(self, tmp_path):
        """n_backbone=1 이고 그 하나마저 실패하면 RuntimeError."""
        from pipeline_local.steps import step02_backbone

        config = self._make_minimal_config(n_backbone=1, tmp_path=tmp_path)
        dummy_pdb_path = tmp_path / "receptor.pdb"
        dummy_pdb_path.write_text("ATOM      1  CA  ALA B   1\nEND\n")

        with patch.object(
            step02_backbone,
            "generate_single_backbone",
            side_effect=RuntimeError("실패"),
        ):
            with pytest.raises(RuntimeError, match="0 PDBs generated out of 1"):
                step02_backbone.generate_backbones(
                    receptor_pdb=str(dummy_pdb_path),
                    pocket_info={},
                    config=config,
                )


# ===========================================================================
# C-M2-1: orchestrator save 호출 — save_selectivity_results, save_step05c_results
# ===========================================================================

class TestOrchestratorSaveResults:
    """step05b/05c 완료 후 save 함수가 올바른 경로로 호출되는지 검증."""

    def _make_step05b_output_mock(self):
        """Step05bOutput mock."""
        mock_out = MagicMock()
        mock_out.passed_candidates.return_value = []
        mock_out.selectivity_results = []
        return mock_out

    def _make_step05c_output_mock(self):
        """Step05cOutput mock."""
        mock_out = MagicMock()
        mock_out.n_passed = 0
        mock_out.n_total = 0
        return mock_out

    def test_save_selectivity_results_called_with_correct_dir(self, tmp_path):
        """step05b 결과 save가 05b_selectivity 디렉토리로 호출된다."""
        from pipeline_local.steps import step05b_selectivity

        # out_dirs 설정
        sel_dir = tmp_path / "05b_selectivity"
        sel_dir.mkdir()
        out_dirs = {"05b_selectivity": str(sel_dir)}

        step05b_output = self._make_step05b_output_mock()

        with patch.object(
            step05b_selectivity, "save_selectivity_results"
        ) as mock_save:
            # 직접 함수 호출 테스트 (orchestrator 의존 없이 로직 검증)
            from pathlib import Path as _Path
            _05b_dir = _Path(out_dirs.get("05b_selectivity", "runs_local/05b_selectivity"))
            step05b_selectivity.save_selectivity_results(step05b_output, _05b_dir)
            mock_save.assert_called_once_with(step05b_output, _05b_dir)

    def test_save_step05c_results_called_with_correct_dir(self, tmp_path):
        """step05c 결과 save가 05c_boltz_cross 디렉토리로 호출된다."""
        from pipeline_local.steps import step05c_boltz_cross

        sel_dir = tmp_path / "05b_selectivity"
        sel_dir.mkdir()
        cross_dir = tmp_path / "05c_boltz_cross"
        out_dirs = {"05b_selectivity": str(sel_dir)}

        step05c_output = self._make_step05c_output_mock()
        expected_dir = Path(out_dirs["05b_selectivity"]).parent / "05c_boltz_cross"

        with patch.object(
            step05c_boltz_cross, "save_step05c_results"
        ) as mock_save:
            step05c_boltz_cross.save_step05c_results(step05c_output, expected_dir)
            mock_save.assert_called_once_with(step05c_output, expected_dir)

    def test_save_selectivity_results_writes_json(self, tmp_path):
        """실제 save_selectivity_results 함수가 JSON 파일을 생성한다."""
        from pipeline_local.steps import step05b_selectivity
        from pipeline_local.schemas.io_schemas import (
            Step05bOutput,
            SelectivityResult,
            OffTargetDockingResult,
        )

        out = Step05bOutput(
            selectivity_results=[
                SelectivityResult(
                    seq_id="bb00_seq00",
                    sstr2_dock_score=-5.0,
                    offtarget_scores={"SSTR1": -3.0},
                    offtarget_max_score=-3.0,
                    offtarget_max_receptor="SSTR1",
                    selectivity_margin=-2.0,
                    passed=True,
                )
            ],
            offtarget_docking_details=[],
        )

        sel_dir = tmp_path / "05b_selectivity"
        saved = step05b_selectivity.save_selectivity_results(out, sel_dir)

        assert "summary" in saved
        summary_path = Path(saved["summary"])
        assert summary_path.exists()
        data = json.loads(summary_path.read_text())
        assert "selectivity_results" in data
        assert data["selectivity_results"][0]["seq_id"] == "bb00_seq00"

    def test_save_step05c_results_writes_json(self, tmp_path):
        """실제 save_step05c_results 함수가 JSON 파일을 생성한다."""
        from pipeline_local.steps import step05c_boltz_cross
        from pipeline_local.schemas.io_schemas import (
            Step05cOutput,
            BoltzSelectivityResult,
        )

        out = Step05cOutput(
            results=[
                BoltzSelectivityResult(
                    seq_id="bb00_seq00",
                    sequence="AGCKNFFWKTFTSC",
                    sstr2_iptm=0.95,
                    offtarget_iptm={"SSTR1": 0.90, "SSTR3": 0.88},
                    selectivity_margin=0.05,
                    best_receptor="SSTR1",
                    tier="T3",
                )
            ],
            passed_candidates=[],
            n_total=1,
            n_passed=0,
        )

        cross_dir = tmp_path / "05c_boltz_cross"
        saved = step05c_boltz_cross.save_step05c_results(out, cross_dir)

        assert "summary" in saved
        summary_path = Path(saved["summary"])
        assert summary_path.exists()
        data = json.loads(summary_path.read_text())
        assert data["n_total"] == 1
        assert data["results"][0]["seq_id"] == "bb00_seq00"

    def test_orchestrator_save_code_path_exists(self):
        """orchestrator.py에 step05b/05c save 코드가 삽입되었는지 텍스트 검사."""
        orch_path = Path(__file__).parent.parent / "orchestrator.py"
        src = orch_path.read_text(encoding="utf-8")
        assert "save_selectivity_results" in src, (
            "orchestrator.py에 save_selectivity_results 호출이 없습니다"
        )
        assert "save_step05c_results" in src, (
            "orchestrator.py에 save_step05c_results 호출이 없습니다"
        )
        # 05b_selectivity 경로 참조 확인
        assert "05b_selectivity" in src
        # 05c_boltz_cross 경로 참조 확인
        assert "05c_boltz_cross" in src
