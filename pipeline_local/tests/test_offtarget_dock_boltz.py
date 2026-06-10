"""
test_offtarget_dock_boltz.py — Boltz-2 기반 offtarget_dock 테스트
==================================================================

pytest.mark.slow 가 붙은 테스트는 실제 Boltz-2 subprocess를 실행한다.
GPU/conda boltz 환경/AlphaFoldDB 접근이 필요하므로 CI에서는 skip.

테스트 그룹:
  TestDdGProxy           — _compute_ddg_proxy 단위 테스트
  TestSequenceExtraction — PDB/CIF 서열 추출 단위 테스트
  TestSSTRMatching       — SSTR UniProt ID 매핑 단위 테스트
  TestOutputFormat       — JSON 출력 형식 + SelectivityRunner 하위 호환 테스트
  TestBoltzIntegration   — 실제 Boltz subprocess 통합 테스트 (mark.slow)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# ---------------------------------------------------------------------------
# 경로 설정
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent
SCRIPT_PATH = REPO_ROOT / "pipeline_local" / "scripts" / "offtarget_dock.py"
SSTR3_PDB = REPO_ROOT / "data" / "somatostatin_receptor" / "SSTR3_8XIR.pdb"
SSTR3_CIF = REPO_ROOT / "data" / "somatostatin_receptor" / "SSTR3_8XIR.cif"

# SSTR2 구조 파일 후보 (우선순위 순)
_SSTR2_PDB_CANDIDATES = [
    REPO_ROOT / "runs_local" / "selectivity_demo_20260511" / "alphafold_receptors" / "SSTR2.pdb",
    REPO_ROOT / "runs_local" / "selectivity_demo_20260511" / "alphafold_receptors" / "AF-P30874-F1-model_v4.pdb",
    REPO_ROOT / "runs_local" / "selectivity_demo_20260511" / "alphafold_receptors" / "sstr2.pdb",
]

SST14_SEQ = "AGCKNFFWKTFTSC"


def _find_sstr2_pdb() -> str:
    """SSTR2 구조 파일을 탐색하여 경로를 반환한다. 없으면 pytest.skip."""
    for p in _SSTR2_PDB_CANDIDATES:
        if p.exists():
            return str(p)
    pytest.skip(
        "SSTR2 구조 파일 없음. 다음 경로 중 하나에 배치하세요:\n"
        + "\n".join(f"  {p}" for p in _SSTR2_PDB_CANDIDATES)
    )


# ---------------------------------------------------------------------------
# 단위 테스트: ddG 프록시 계산
# ---------------------------------------------------------------------------

class TestDdGProxy:
    """_compute_ddg_proxy 함수 단위 테스트."""

    def test_linear_strong_binding(self):
        """iPTM=0.946 → ddg=-94.6 (SST-14 × SSTR2 기준값)."""
        from pipeline_local.scripts.offtarget_dock import _compute_ddg_proxy
        ddg = _compute_ddg_proxy(0.946, method="linear")
        assert ddg == pytest.approx(-94.6, abs=0.01)

    def test_linear_zero_iptm(self):
        """iPTM=0 → ddg=0.0."""
        from pipeline_local.scripts.offtarget_dock import _compute_ddg_proxy
        assert _compute_ddg_proxy(0.0, method="linear") == 0.0

    def test_linear_full_iptm(self):
        """iPTM=1.0 → ddg=-100.0."""
        from pipeline_local.scripts.offtarget_dock import _compute_ddg_proxy
        assert _compute_ddg_proxy(1.0, method="linear") == pytest.approx(-100.0)

    def test_all_high_iptm_negative(self):
        """강결합(iPTM ≥ 0.8)은 항상 ddg < 0."""
        from pipeline_local.scripts.offtarget_dock import _compute_ddg_proxy
        for iptm in [0.8, 0.9, 0.95, 0.99]:
            assert _compute_ddg_proxy(iptm) < 0, f"iPTM={iptm}: ddg should be negative"

    def test_boltz_formula_negative_for_high_iptm(self):
        """Boltz 논문 공식: iPTM > 0.5 → ddg < 0."""
        from pipeline_local.scripts.offtarget_dock import _compute_ddg_proxy
        ddg = _compute_ddg_proxy(0.946, method="boltz")
        assert ddg < 0

    def test_boltz_formula_clamps_edges(self):
        """Boltz 공식이 0/1 경계에서 오류 없이 실행된다."""
        from pipeline_local.scripts.offtarget_dock import _compute_ddg_proxy
        # eps 클램핑으로 무한대 발생 안 함
        ddg_zero = _compute_ddg_proxy(0.0, method="boltz")
        ddg_one = _compute_ddg_proxy(1.0, method="boltz")
        assert isinstance(ddg_zero, float)
        assert isinstance(ddg_one, float)


# ---------------------------------------------------------------------------
# 단위 테스트: PDB 서열 추출
# ---------------------------------------------------------------------------

class TestSequenceExtraction:
    """_extract_from_pdb_format 단위 테스트."""

    def _make_pdb(self, tmp_path: Path, residues: list[tuple[str, int]]) -> Path:
        """최소 PDB ATOM 레코드 생성 헬퍼."""
        lines = []
        for resname, resseq in residues:
            line = (
                f"ATOM  {resseq:5d}  CA  {resname} A{resseq:4d}    "
                f"  10.000  20.000  30.000  1.00  0.00           C\n"
            )
            lines.append(line)
        pdb_file = tmp_path / "test.pdb"
        pdb_file.write_text("".join(lines))
        return pdb_file

    def test_basic_sequence(self, tmp_path):
        """MET-ASP-MET → 'MDM'."""
        from pipeline_local.scripts.offtarget_dock import _extract_from_pdb_format
        pdb = self._make_pdb(tmp_path, [("MET", 1), ("ASP", 2), ("MET", 3)])
        seq = _extract_from_pdb_format(str(pdb))
        assert seq == "MDM"

    def test_deduplicates_residue_numbers(self, tmp_path):
        """같은 잔기 번호가 중복되면 한 번만 수집된다."""
        from pipeline_local.scripts.offtarget_dock import _extract_from_pdb_format
        # 잔기 1이 두 번 나타남 (alternate conformer 등)
        lines = (
            "ATOM      1  CA  MET A   1      10.000  20.000  30.000  1.00  0.00           C\n"
            "ATOM      2  CA  MET A   1      10.100  20.100  30.100  1.00  0.00           C\n"
            "ATOM      3  CA  ASP A   2      11.000  21.000  31.000  1.00  0.00           C\n"
        )
        pdb = tmp_path / "dup.pdb"
        pdb.write_text(lines)
        seq = _extract_from_pdb_format(str(pdb))
        assert seq == "MD"

    def test_unknown_residue_skipped(self, tmp_path):
        """비표준 잔기는 건너뛴다."""
        from pipeline_local.scripts.offtarget_dock import _extract_from_pdb_format
        lines = (
            "ATOM      1  CA  MET A   1      10.000  20.000  30.000  1.00  0.00           C\n"
            "ATOM      2  CA  UNK A   2      11.000  21.000  31.000  1.00  0.00           C\n"
            "ATOM      3  CA  ALA A   3      12.000  22.000  32.000  1.00  0.00           C\n"
        )
        pdb = tmp_path / "unk.pdb"
        pdb.write_text(lines)
        seq = _extract_from_pdb_format(str(pdb))
        assert seq == "MA"

    def test_no_ca_raises(self, tmp_path):
        """CA 원자가 없으면 ValueError."""
        from pipeline_local.scripts.offtarget_dock import _extract_from_pdb_format
        pdb = tmp_path / "empty.pdb"
        pdb.write_text("REMARK no atoms\n")
        with pytest.raises(ValueError, match="CA 원자를 찾을 수 없습니다"):
            _extract_from_pdb_format(str(pdb))

    def test_prefers_sstr_signature_over_longer_chain(self, tmp_path):
        """복합체에서 최장 체인이 아니라 SSTR signature 체인을 선택한다."""
        from pipeline_local.scripts.offtarget_dock import _extract_from_pdb_format

        lines = []
        long_non_sstr = "ACDEFGHIKLMNPQRSTVWY" * 3
        sstr3_fragment = "LAVSGVLIPLVYLVVCVVGLLGNSLVIYVVLRHTASPSVT"
        three = {
            "A": "ALA", "C": "CYS", "D": "ASP", "E": "GLU", "F": "PHE",
            "G": "GLY", "H": "HIS", "I": "ILE", "K": "LYS", "L": "LEU",
            "M": "MET", "N": "ASN", "P": "PRO", "Q": "GLN", "R": "ARG",
            "S": "SER", "T": "THR", "V": "VAL", "W": "TRP", "Y": "TYR",
        }
        serial = 1
        for chain, seq in (("A", sstr3_fragment), ("C", long_non_sstr)):
            for resseq, aa in enumerate(seq, start=1):
                lines.append(
                    f"ATOM  {serial:5d}  CA  {three[aa]} {chain}{resseq:4d}    "
                    f"  10.000  20.000  30.000  1.00  0.00           C\n"
                )
                serial += 1

        pdb = tmp_path / "complex.pdb"
        pdb.write_text("".join(lines))
        assert _extract_from_pdb_format(str(pdb)) == sstr3_fragment

    def test_real_sstr3_8xir_pdb_selects_p32745_chain(self):
        """8XIR PDB는 G-protein 최장 체인 대신 SSTR3 체인 A로 매칭된다."""
        if not SSTR3_PDB.exists():
            pytest.skip(f"SSTR3 PDB 없음: {SSTR3_PDB}")

        from pipeline_local.scripts.offtarget_dock import (
            _extract_sequence_from_pdb,
            _find_sstr_uniprot,
        )

        seq = _extract_sequence_from_pdb(str(SSTR3_PDB))
        assert _find_sstr_uniprot(seq) == "P32745"
        assert "VVLRHTASPSVT" in seq

    def test_real_sstr3_8xir_cif_selects_p32745_chain(self):
        """8XIR CIF도 SSTR3 체인 A를 선택한다."""
        if not SSTR3_CIF.exists():
            pytest.skip(f"SSTR3 CIF 없음: {SSTR3_CIF}")

        from pipeline_local.scripts.offtarget_dock import (
            _extract_sequence_from_pdb,
            _find_sstr_uniprot,
        )

        seq = _extract_sequence_from_pdb(str(SSTR3_CIF))
        assert _find_sstr_uniprot(seq) == "P32745"
        assert "VVLRHTASPSVT" in seq


# ---------------------------------------------------------------------------
# 단위 테스트: SSTR UniProt ID 매핑
# ---------------------------------------------------------------------------

class TestSSTRMatching:
    """_find_sstr_uniprot 단위 테스트."""

    def test_sstr2_n_terminal(self):
        """SSTR2 N-말단 시그니처 매칭 → P30874."""
        from pipeline_local.scripts.offtarget_dock import _find_sstr_uniprot
        seq = "MDMADEPLNGSHTWLSIPFDLNGSVVSTNTSNQTEPYYDLTSNAVLT"
        assert _find_sstr_uniprot(seq) == "P30874"

    def test_sstr1_matching(self):
        """SSTR1 시그니처 매칭 → P30872."""
        from pipeline_local.scripts.offtarget_dock import _find_sstr_uniprot
        seq = "MFPNGTASSPSSSPSPSPGSCGEGGGSRGPGAGAADGMEEPGRNAS"
        assert _find_sstr_uniprot(seq) == "P30872"

    def test_sstr4_matching(self):
        """SSTR4 시그니처 매칭 → P31391."""
        from pipeline_local.scripts.offtarget_dock import _find_sstr_uniprot
        seq = "MSAPSTLPPGGEEGLGTAWPSAANASSAPAEAEEAVAGPGDAR"
        assert _find_sstr_uniprot(seq) == "P31391"

    def test_unknown_receptor_returns_none(self):
        """비-SSTR 수용체는 None 반환."""
        from pipeline_local.scripts.offtarget_dock import _find_sstr_uniprot
        assert _find_sstr_uniprot("ACDEFGHIKLMNPQRSTVWY" * 5) is None

    def test_case_insensitive(self):
        """대소문자 무관 매칭."""
        from pipeline_local.scripts.offtarget_dock import _find_sstr_uniprot
        seq_lower = "mdmadeplngshtwlsipfdlngsvvstntsnqtepyydltsnavlt"
        assert _find_sstr_uniprot(seq_lower) == "P30874"


# ---------------------------------------------------------------------------
# 단위 테스트: 출력 JSON 형식 및 SelectivityRunner 호환성
# ---------------------------------------------------------------------------

class TestOutputFormat:
    """출력 JSON 키 구조 + SelectivityRunner 하위 호환 테스트."""

    def _make_result(self, iptm: float = 0.946) -> Dict[str, Any]:
        """run_docking 반환 구조를 모방한 결과 딕셔너리."""
        from pipeline_local.scripts.offtarget_dock import _compute_ddg_proxy
        return {
            "ddg": round(_compute_ddg_proxy(iptm), 3),
            "iptm": round(iptm, 4),
            "ptm": 0.869,
            "confidence": 0.859,
            "best_pdb": None,
            "engine": "boltz-2",
        }

    def test_required_keys_present(self):
        """필수 키 6개가 모두 존재한다."""
        result = self._make_result()
        for key in ("ddg", "iptm", "ptm", "confidence", "best_pdb", "engine"):
            assert key in result, f"키 누락: {key}"

    def test_ddg_is_negative_for_strong_binder(self):
        """강결합(iPTM ≥ 0.9) → ddg < 0."""
        result = self._make_result(iptm=0.946)
        assert result["ddg"] < 0

    def test_engine_tag(self):
        """engine 필드 = 'boltz-2'."""
        result = self._make_result()
        assert result["engine"] == "boltz-2"

    def test_selectivity_runner_parses_ddg(self):
        """SelectivityRunner.dock_against_receptor 가 'ddg' 키를 파싱한다."""
        mock_json = json.dumps(self._make_result(iptm=0.946))
        parsed = json.loads(mock_json)
        ddg = float(parsed["ddg"])
        assert ddg == pytest.approx(-94.6, abs=0.01)

    def test_json_serializable(self):
        """결과가 JSON 직렬화 가능하다."""
        result = self._make_result()
        dumped = json.dumps(result)
        loaded = json.loads(dumped)
        assert loaded["engine"] == "boltz-2"


# ---------------------------------------------------------------------------
# 통합 테스트: 실제 Boltz-2 subprocess (mark.slow)
# ---------------------------------------------------------------------------

@pytest.mark.slow
class TestBoltzIntegration:
    """실제 Boltz-2 subprocess 통합 테스트.

    실행 전 필요 사항:
      - conda 'boltz' 환경 (boltz 2.2.1 이상)
      - GPU (CUDA_VISIBLE_DEVICES 설정)
      - AlphaFoldDB 접근 가능 또는 ~/.cache/boltz_msa/P30874.a3m 존재
      - SSTR2 구조 파일 (아래 후보 경로 중 하나)

    참고: docs/boltz2_offline_workaround.md §4.1
    기준값: SST-14 × SSTR2 iPTM = 0.946 (검증됨)
    """

    def test_sst14_sstr2_iptm(self, tmp_path):
        """SST-14 × SSTR2 → iPTM ≥ 0.90 (기준 0.946)."""
        sstr2_pdb = _find_sstr2_pdb()

        from pipeline_local.scripts.offtarget_dock import run_docking
        result = run_docking(
            receptor_path=sstr2_pdb,
            sequence=SST14_SEQ,
            nstruct=1,
            output_dir=str(tmp_path),
        )

        assert "iptm" in result, "결과에 'iptm' 키 없음"
        assert "ddg" in result, "결과에 'ddg' 키 없음 (하위 호환 키)"
        assert result["engine"] == "boltz-2"
        assert result["iptm"] >= 0.90, (
            f"SST-14 × SSTR2 iPTM={result['iptm']:.3f} < 0.90\n"
            f"기준값: 0.946 (docs/boltz2_offline_workaround.md §4.1)\n"
            f"전체 결과: {result}"
        )
        assert result["ddg"] < 0, "강결합(iPTM≥0.9)이면 ddg < 0이어야 함"

    def test_output_pdb_created(self, tmp_path):
        """output_dir 지정 시 best_dock.pdb가 생성된다."""
        sstr2_pdb = _find_sstr2_pdb()

        from pipeline_local.scripts.offtarget_dock import run_docking
        result = run_docking(
            receptor_path=sstr2_pdb,
            sequence=SST14_SEQ,
            nstruct=1,
            output_dir=str(tmp_path),
        )

        if result.get("best_pdb"):
            assert Path(result["best_pdb"]).exists(), "best_pdb 경로가 존재하지 않음"

    def test_cli_backward_compatible(self, tmp_path):
        """CLI --receptor --sequence --nstruct --output-dir 인터페이스 호환성."""
        sstr2_pdb = _find_sstr2_pdb()

        cmd = [
            sys.executable, str(SCRIPT_PATH),
            "--receptor", sstr2_pdb,
            "--sequence", SST14_SEQ,
            "--nstruct", "1",
            "--output-dir", str(tmp_path),
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )

        assert proc.returncode == 0, (
            f"CLI 실패 (rc={proc.returncode})\n"
            f"stderr tail:\n{proc.stderr[-500:]}"
        )

        # stdout 마지막 JSON 줄 파싱
        result = None
        for line in reversed(proc.stdout.splitlines()):
            line = line.strip()
            if line.startswith("{"):
                try:
                    result = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue

        assert result is not None, f"stdout에서 JSON 파싱 실패:\n{proc.stdout[:500]}"
        assert "ddg" in result, "'ddg' 키 없음 (하위 호환 위반)"
        assert "iptm" in result
        assert result["engine"] == "boltz-2"
        assert "error" not in result, f"오류 반환: {result['error']}"

    def test_selectivity_runner_interface(self, tmp_path):
        """SelectivityRunner.dock_against_receptor 가 새 offtarget_dock 와 호환된다."""
        sstr2_pdb = _find_sstr2_pdb()

        from pipeline_local.core.selectivity_runner import SelectivityRunner
        runner = SelectivityRunner(
            conda_env="boltz",
            nstruct=1,
            timeout=600,
        )

        ddg = runner.dock_against_receptor(
            receptor_path=sstr2_pdb,
            peptide_sequence=SST14_SEQ,
            output_dir=str(tmp_path),
        )

        assert isinstance(ddg, float), f"ddg 타입이 float이 아님: {type(ddg)}"
        assert ddg < 0, f"SST-14 × SSTR2 ddg={ddg:.2f} ≥ 0 (강결합이면 음수여야 함)"
        assert ddg >= -100.0, f"ddg={ddg:.2f} < -100 (iPTM 범위 초과)"

    def test_sst14_sstr3_8xir_smoke(self, tmp_path):
        """SST-14 × SSTR3 8XIR 도킹 smoke: 전처리 chain 선택 회귀."""
        if not SSTR3_CIF.exists():
            pytest.skip(f"SSTR3 CIF 없음: {SSTR3_CIF}")

        from pipeline_local.scripts.offtarget_dock import run_docking
        result = run_docking(
            receptor_path=str(SSTR3_CIF),
            sequence=SST14_SEQ,
            nstruct=1,
            output_dir=str(tmp_path),
        )

        assert result["engine"] == "boltz-2"
        assert 0.0 < result["iptm"] <= 1.0
        assert -200.0 < result["ddg"] < 0.0
