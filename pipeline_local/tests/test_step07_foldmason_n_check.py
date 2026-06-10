"""test_step07_foldmason_n_check.py
====================================
F-05 회귀 테스트 — FoldMason alignment n<2 skip 처리.

검증 항목:
  - n=0: pdb_paths=[] → success=True, skipped=True, lddt_scores={}
  - n=1: pdb_paths=[single] → success=True, skipped=True, lddt_scores={}
  - n≥2: subprocess mock → success=True, skipped=False, lddt_scores 채워짐 (fallback)

run_analysis() 통합 검증:
  - n<2 입력 시 lddt_table.json 내용이 {"success": true, "skipped": true, "reason": "n<2"}

외부 FoldMason 바이너리를 일절 호출하지 않도록 monkeypatch로 subprocess.run 차단.
"""
from __future__ import annotations

import json
import os
import tempfile
import types
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixture: step07 모듈 임포트
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def step07():
    from pipeline_local.steps import step07_analysis
    return step07_analysis


# ---------------------------------------------------------------------------
# 테스트 케이스 1: n=0 → skip
# ---------------------------------------------------------------------------


class TestFoldMasonNCheck:
    """run_foldmason_alignment()의 n<2 skip 동작 검증."""

    def test_n0_returns_skip(self, step07, tmp_path: Path):
        """n=0: 빈 리스트 입력 시 success=True, skipped=True 반환."""
        result = step07.run_foldmason_alignment([], tmp_path)

        assert result.success is True, "n=0: success 가 False여서는 안 됨"
        assert result.skipped is True, "n=0: skipped 가 True 이어야 함"
        assert result.lddt_scores == {}, "n=0: lddt_scores 는 빈 dict"
        assert result.html_report == "", "n=0: html_report 는 빈 문자열"
        assert result.error is None, "n=0: error 는 None"

    def test_n1_returns_skip(self, step07, tmp_path: Path):
        """n=1: 단일 PDB 경로 입력 시 success=True, skipped=True 반환."""
        # 실제 파일 존재 여부와 무관하게 경로 문자열만 전달
        fake_pdb = str(tmp_path / "peptide_A.pdb")
        result = step07.run_foldmason_alignment([fake_pdb], tmp_path)

        assert result.success is True, "n=1: success 가 False여서는 안 됨"
        assert result.skipped is True, "n=1: skipped 가 True 이어야 함"
        assert result.lddt_scores == {}, "n=1: lddt_scores 는 빈 dict"
        assert result.html_report == "", "n=1: html_report 는 빈 문자열"
        assert result.error is None, "n=1: error 는 None"

    def test_n2_calls_subprocess_and_returns_success(self, step07, tmp_path: Path):
        """n=2: subprocess 호출 → returncode=0 → success=True, skipped=False."""
        fake_pdb1 = str(tmp_path / "peptide_A.pdb")
        fake_pdb2 = str(tmp_path / "peptide_B.pdb")
        # 파일 파싱에 사용되지 않지만 stem 추출 때 사용됨 → 파일 생성 불필요

        # subprocess.run mock: returncode=0, fm_aln_lddt.json 없음 → fallback 1.0
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stderr = ""
        mock_proc.stdout = ""

        with patch("pipeline_local.steps.step07_analysis.subprocess.run", return_value=mock_proc):
            result = step07.run_foldmason_alignment([fake_pdb1, fake_pdb2], tmp_path)

        assert result.success is True, "n=2: subprocess 성공 시 success=True"
        assert result.skipped is False, "n=2: skipped=False (정렬 실행됨)"
        assert result.error is None, "n=2: error=None"
        # fallback lDDT: 각 stem에 1.0 할당
        assert "peptide_A" in result.lddt_scores, "n=2: peptide_A 가 lddt_scores에 있어야 함"
        assert "peptide_B" in result.lddt_scores, "n=2: peptide_B 가 lddt_scores에 있어야 함"
        assert result.lddt_scores["peptide_A"] == pytest.approx(1.0)
        assert result.lddt_scores["peptide_B"] == pytest.approx(1.0)

    def test_n2_subprocess_failure_returns_success_false(self, step07, tmp_path: Path):
        """n=2: subprocess 실패(returncode!=0) → success=False, skipped=False, fallback lDDT=0.0."""
        fake_pdb1 = str(tmp_path / "peptide_C.pdb")
        fake_pdb2 = str(tmp_path / "peptide_D.pdb")

        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stderr = "FoldMason: binary not found"
        mock_proc.stdout = ""

        with patch("pipeline_local.steps.step07_analysis.subprocess.run", return_value=mock_proc):
            result = step07.run_foldmason_alignment([fake_pdb1, fake_pdb2], tmp_path)

        assert result.success is False, "n=2 subprocess 실패: success=False"
        assert result.skipped is False, "n=2 subprocess 실패: skipped=False (시도는 했으므로)"
        assert result.error is not None, "n=2 subprocess 실패: error 메시지 있어야 함"
        # fallback lDDT: 0.0
        assert result.lddt_scores.get("peptide_C") == pytest.approx(0.0)
        assert result.lddt_scores.get("peptide_D") == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 통합 테스트: run_analysis() → lddt_table.json 포맷 검증
# ---------------------------------------------------------------------------


class TestRunAnalysisLddtTableFormat:
    """run_analysis() 호출 시 lddt_table.json 내용 검증."""

    def _make_candidate(self, step07, seq_id: str, pdb_path: str):
        """테스트용 RosettaResult 객체 생성."""
        from pipeline_local.schemas.io_schemas import RosettaResult
        return RosettaResult(
            seq_id=seq_id,
            ddg=-6.0,
            total_score=-120.0,
            clash_score=0.0,
            constraint_violations=0,
            refined_pdb=pdb_path,
        )

    def test_lddt_table_json_skip_format_when_n0(self, step07, tmp_path: Path):
        """refined PDB 없는 후보 목록 → n=0 → lddt_table.json = skip 포맷."""
        candidates = [
            self._make_candidate(step07, "seq_001", ""),   # refined_pdb 없음
            self._make_candidate(step07, "seq_002", ""),
        ]
        config: Dict[str, Any] = {
            "run_id": "test_n0",
            "output_base_dir": str(tmp_path),
        }

        # PyMOL / interface analysis도 외부 호출 없도록 mock
        with patch("pipeline_local.steps.step07_analysis.subprocess.run") as mock_sub, \
             patch("pipeline_local.steps.step07_analysis.run_interface_analysis") as mock_iface:
            mock_sub.return_value = MagicMock(returncode=0, stderr="", stdout="")
            mock_iface.return_value = step07.InterfaceReport(
                contact_residues_receptor=[],
                contact_residues_peptide=[],
                buried_sasa=0.0,
                n_hbonds=0,
                n_salt_bridges=0,
            )
            step07.run_analysis(candidates, "", config)

        lddt_json = tmp_path / "test_n0" / "07_viz" / "lddt_table.json"
        assert lddt_json.exists(), "lddt_table.json 파일이 생성되어야 함"
        data = json.loads(lddt_json.read_text(encoding="utf-8"))

        assert data.get("success") is True, "skip 시 success=True"
        assert data.get("skipped") is True, "skip 시 skipped=True"
        assert data.get("reason") == "n<2", "skip 시 reason='n<2'"
        # success:false / error 키가 없어야 함
        assert "error" not in data or data["error"] is None, "skip 시 error 없어야 함"

    def test_lddt_table_json_normal_format_when_n2(self, step07, tmp_path: Path):
        """refined PDB 2개 → FoldMason 실행 → lddt_table.json = 정상 포맷 (skipped=False)."""
        # 실제 파일 생성 (Path.exists() 검사를 통과하기 위해)
        pdb1 = tmp_path / "peptide_A.pdb"
        pdb2 = tmp_path / "peptide_B.pdb"
        pdb1.write_text("ATOM\n", encoding="utf-8")
        pdb2.write_text("ATOM\n", encoding="utf-8")

        candidates = [
            self._make_candidate(step07, "seq_A", str(pdb1)),
            self._make_candidate(step07, "seq_B", str(pdb2)),
        ]
        config: Dict[str, Any] = {
            "run_id": "test_n2",
            "output_base_dir": str(tmp_path),
        }

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stderr = ""
        mock_proc.stdout = ""

        with patch("pipeline_local.steps.step07_analysis.subprocess.run", return_value=mock_proc), \
             patch("pipeline_local.steps.step07_analysis.run_interface_analysis") as mock_iface:
            mock_iface.return_value = step07.InterfaceReport(
                contact_residues_receptor=[],
                contact_residues_peptide=[],
                buried_sasa=0.0,
                n_hbonds=0,
                n_salt_bridges=0,
            )
            step07.run_analysis(candidates, "", config)

        lddt_json = tmp_path / "test_n2" / "07_viz" / "lddt_table.json"
        assert lddt_json.exists(), "lddt_table.json 파일이 생성되어야 함"
        data = json.loads(lddt_json.read_text(encoding="utf-8"))

        assert data.get("success") is True, "n=2 정상 실행: success=True"
        assert data.get("skipped") is False, "n=2 정상 실행: skipped=False"
        assert "lddt_scores" in data, "n=2 정상 실행: lddt_scores 키 존재"
        # reason 키 없거나 None
        assert "reason" not in data or data["reason"] is None
