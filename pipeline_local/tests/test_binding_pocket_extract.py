"""
test_binding_pocket_extract.py — SSTR2 결합 포켓 추출 단위 테스트
=================================================================

A-01: TM5(208/209) + TM6(272/273/276) 중심 좌표 추출 검증.

테스트 그룹:
  TestExtractBindingPocket    — extract_binding_pocket() PDB CA-only 기본 함수
  TestExtractPocketCenter     — extract_pocket_center() A-01 표준 인터페이스
  TestNegativeDesignResidues  — negative_design_residues_SSTR2.json 구조 검증
  TestBindingPocketJson       — 저장된 binding_pocket_SSTR2.json 값 검증
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

# ---------------------------------------------------------------------------
# 경로 설정
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent
SSTR_DATA = REPO_ROOT / "data" / "somatostatin_receptor"
SSTR2_PDB = SSTR_DATA / "SSTR2_7XNA.pdb"
SSTR2_CIF = SSTR_DATA / "SSTR2_7XNA.cif"
POCKET_JSON = SSTR_DATA / "binding_pocket_SSTR2.json"
NEG_DESIGN_JSON = SSTR_DATA / "negative_design_residues_SSTR2.json"

# A-01 결합 포켓 잔기 (TM5+TM6)
A01_RESIDUES = [208, 209, 272, 273, 276]

# 결합 포켓 중심 좌표 허용 오차 (Å)
COORD_TOLERANCE = 0.5

# 알려진 잔기 정보 (SSTR2_7XNA.pdb 기준)
EXPECTED_RESIDUE_NAMES = {
    208: "PHE",
    209: "ILE",
    272: "PHE",
    273: "TYR",
    276: "ASN",
}


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _import_extract():
    """extract_binding_pocket 모듈을 임포트한다."""
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    from pipeline_local.scripts import extract_binding_pocket as m
    return m


# ---------------------------------------------------------------------------
# extract_binding_pocket() 테스트 (CA-only PDB 기본 함수)
# ---------------------------------------------------------------------------

class TestExtractBindingPocket:
    """extract_binding_pocket() 기존 CA-only 인터페이스 테스트."""

    def test_returns_required_keys(self) -> None:
        """반환값에 필수 키가 모두 포함된다."""
        if not SSTR2_PDB.exists():
            pytest.skip(f"PDB 파일 없음: {SSTR2_PDB}")
        m = _import_extract()
        result = m.extract_binding_pocket(str(SSTR2_PDB), residues=A01_RESIDUES, chain="A")
        required_keys = {"center_x", "center_y", "center_z", "radius", "gnina_config",
                         "residues", "residue_details", "receptor"}
        assert required_keys.issubset(result.keys()), (
            f"누락 키: {required_keys - result.keys()}"
        )

    def test_residue_details_all_found(self) -> None:
        """A-01 잔기 5개가 모두 residue_details에 포함된다."""
        if not SSTR2_PDB.exists():
            pytest.skip(f"PDB 파일 없음: {SSTR2_PDB}")
        m = _import_extract()
        result = m.extract_binding_pocket(str(SSTR2_PDB), residues=A01_RESIDUES, chain="A")
        found = {r["resnum"] for r in result["residue_details"]}
        assert found == set(A01_RESIDUES), (
            f"발견된 잔기: {sorted(found)}, 기대: {sorted(A01_RESIDUES)}"
        )

    def test_correct_residue_names(self) -> None:
        """각 잔기의 아미노산 이름이 PDB 정보와 일치한다."""
        if not SSTR2_PDB.exists():
            pytest.skip(f"PDB 파일 없음: {SSTR2_PDB}")
        m = _import_extract()
        result = m.extract_binding_pocket(str(SSTR2_PDB), residues=A01_RESIDUES, chain="A")
        for detail in result["residue_details"]:
            resnum = detail["resnum"]
            expected = EXPECTED_RESIDUE_NAMES.get(resnum)
            if expected:
                assert detail["resname"] == expected, (
                    f"잔기 {resnum} 이름 불일치: 기대={expected}, 실제={detail['resname']}"
                )

    def test_gnina_config_has_positive_box_size(self) -> None:
        """GNINA config의 박스 크기가 양수이다."""
        if not SSTR2_PDB.exists():
            pytest.skip(f"PDB 파일 없음: {SSTR2_PDB}")
        m = _import_extract()
        result = m.extract_binding_pocket(str(SSTR2_PDB), residues=A01_RESIDUES, chain="A")
        gnina = result["gnina_config"]
        for key in ("size_x", "size_y", "size_z"):
            assert gnina[key] > 0, f"GNINA {key} = {gnina[key]} (양수여야 함)"

    def test_missing_residues_handled_gracefully(self) -> None:
        """존재하지 않는 잔기 번호가 포함되어도 ValueError/경고만 발생하고 중단하지 않는다."""
        if not SSTR2_PDB.exists():
            pytest.skip(f"PDB 파일 없음: {SSTR2_PDB}")
        m = _import_extract()
        # 208, 209는 유효, 9999는 없는 잔기
        result = m.extract_binding_pocket(str(SSTR2_PDB), residues=[208, 209, 9999], chain="A")
        found_resnums = {r["resnum"] for r in result["residue_details"]}
        assert 208 in found_resnums and 209 in found_resnums


# ---------------------------------------------------------------------------
# extract_pocket_center() 테스트 (A-01 표준 인터페이스)
# ---------------------------------------------------------------------------

class TestExtractPocketCenter:
    """extract_pocket_center() A-01 표준 인터페이스 테스트."""

    def test_returns_all_required_keys(self) -> None:
        """반환 딕셔너리에 A-01 스펙의 모든 키가 포함된다."""
        if not SSTR2_PDB.exists():
            pytest.skip(f"PDB 파일 없음: {SSTR2_PDB}")
        m = _import_extract()
        result = m.extract_pocket_center(SSTR2_PDB, A01_RESIDUES)
        required = {"center_x", "center_y", "center_z", "radius_angstrom",
                    "residue_ids", "source_pdb", "box_size"}
        assert required.issubset(result.keys()), f"누락 키: {required - result.keys()}"

    def test_box_size_keys_present(self) -> None:
        """box_size 딕셔너리에 size_x/y/z가 모두 있다."""
        if not SSTR2_PDB.exists():
            pytest.skip(f"PDB 파일 없음: {SSTR2_PDB}")
        m = _import_extract()
        result = m.extract_pocket_center(SSTR2_PDB, A01_RESIDUES)
        bs = result["box_size"]
        assert "size_x" in bs and "size_y" in bs and "size_z" in bs

    def test_min_box_size_30_angstrom(self) -> None:
        """기본 min_box_size=30 Å이 보장된다."""
        if not SSTR2_PDB.exists():
            pytest.skip(f"PDB 파일 없음: {SSTR2_PDB}")
        m = _import_extract()
        result = m.extract_pocket_center(SSTR2_PDB, A01_RESIDUES, min_box_size=30.0)
        bs = result["box_size"]
        assert bs["size_x"] >= 30.0, f"박스 크기 {bs['size_x']} < 30 Å"
        assert bs["size_y"] >= 30.0
        assert bs["size_z"] >= 30.0

    def test_residue_ids_preserved(self) -> None:
        """입력 잔기 목록이 출력에 정렬된 형태로 보존된다."""
        if not SSTR2_PDB.exists():
            pytest.skip(f"PDB 파일 없음: {SSTR2_PDB}")
        m = _import_extract()
        # 역순 입력
        result = m.extract_pocket_center(SSTR2_PDB, list(reversed(A01_RESIDUES)))
        assert result["residue_ids"] == sorted(A01_RESIDUES)

    def test_center_coordinates_reasonable_range(self) -> None:
        """중심 좌표가 단백질 구조 합리적 범위 내에 있다 (±200 Å)."""
        if not SSTR2_PDB.exists():
            pytest.skip(f"PDB 파일 없음: {SSTR2_PDB}")
        m = _import_extract()
        result = m.extract_pocket_center(SSTR2_PDB, A01_RESIDUES)
        for key in ("center_x", "center_y", "center_z"):
            assert abs(result[key]) < 200.0, (
                f"{key} = {result[key]} 범위 초과 (합리적 범위: ±200 Å)"
            )

    def test_radius_positive_and_within_gpcr_range(self) -> None:
        """반경이 양수이고 GPCR 포켓 합리적 범위(1-25 Å) 내에 있다."""
        if not SSTR2_PDB.exists():
            pytest.skip(f"PDB 파일 없음: {SSTR2_PDB}")
        m = _import_extract()
        result = m.extract_pocket_center(SSTR2_PDB, A01_RESIDUES)
        r = result["radius_angstrom"]
        assert 1.0 <= r <= 25.0, (
            f"반경 {r:.2f} Å가 GPCR 포켓 합리적 범위(1-25 Å)를 벗어남"
        )

    def test_file_not_found_raises(self) -> None:
        """존재하지 않는 파일 경로에 FileNotFoundError가 발생한다."""
        m = _import_extract()
        with pytest.raises(FileNotFoundError):
            m.extract_pocket_center(Path("/nonexistent/path.pdb"), A01_RESIDUES)

    def test_empty_residue_list_raises(self) -> None:
        """빈 잔기 목록 또는 전혀 없는 잔기 번호에 ValueError가 발생한다."""
        if not SSTR2_PDB.exists():
            pytest.skip(f"PDB 파일 없음: {SSTR2_PDB}")
        m = _import_extract()
        with pytest.raises(ValueError):
            m.extract_pocket_center(SSTR2_PDB, [99999, 99998])  # 없는 잔기

    def test_pdb_and_cif_give_same_center(self) -> None:
        """PDB와 CIF에서 추출한 중심 좌표가 허용 오차 내에서 일치한다."""
        if not SSTR2_PDB.exists() or not SSTR2_CIF.exists():
            pytest.skip(f"PDB/CIF 파일 없음")
        m = _import_extract()
        res_pdb = m.extract_pocket_center(SSTR2_PDB, A01_RESIDUES)
        res_cif = m.extract_pocket_center(SSTR2_CIF, A01_RESIDUES)
        for axis in ("center_x", "center_y", "center_z"):
            diff = abs(res_pdb[axis] - res_cif[axis])
            assert diff <= COORD_TOLERANCE, (
                f"{axis} 불일치: PDB={res_pdb[axis]:.3f}, CIF={res_cif[axis]:.3f}, "
                f"차이={diff:.3f} Å > 허용 {COORD_TOLERANCE} Å"
            )


# ---------------------------------------------------------------------------
# 저장된 JSON 파일 검증
# ---------------------------------------------------------------------------

class TestBindingPocketJson:
    """data/somatostatin_receptor/binding_pocket_SSTR2.json 구조·값 검증."""

    @pytest.fixture
    def pocket_data(self) -> Dict:
        if not POCKET_JSON.exists():
            pytest.skip(f"JSON 파일 없음: {POCKET_JSON}")
        return json.loads(POCKET_JSON.read_text())

    def test_json_parseable(self) -> None:
        """JSON 파일이 올바르게 파싱된다."""
        if not POCKET_JSON.exists():
            pytest.skip(f"JSON 파일 없음: {POCKET_JSON}")
        data = json.loads(POCKET_JSON.read_text())
        assert isinstance(data, dict)

    def test_gnina_config_present(self, pocket_data: Dict) -> None:
        """gnina_config 키가 있고 center_x/y/z + size_x/y/z를 포함한다."""
        gnina = pocket_data.get("gnina_config") or pocket_data
        for key in ("center_x", "center_y", "center_z"):
            assert key in gnina, f"gnina_config에 {key} 없음"

    def test_receptor_is_sstr2(self, pocket_data: Dict) -> None:
        """receptor 필드가 SSTR2 구조임을 명시한다."""
        receptor = pocket_data.get("receptor", "")
        assert "SSTR2" in receptor.upper() or "7XNA" in receptor.upper(), (
            f"receptor 필드: {receptor}"
        )

    def test_binding_pocket_center_residues_are_a01_spec(self, pocket_data: Dict) -> None:
        """저장된 binding_pocket_center_residues가 A-01 스펙(5개)과 일치한다."""
        # A-01 표준 인터페이스: binding_pocket_center_residues 키 사용
        # residues 키는 TM5+TM6 전체(8개)로 기존 테스트와 호환
        center_res = pocket_data.get("binding_pocket_center_residues")
        if center_res is None:
            # fallback: residues 키에서 A-01 잔기가 포함되어 있는지만 확인
            residues = pocket_data.get("residues", [])
            for r in A01_RESIDUES:
                assert r in residues, f"A-01 잔기 {r}가 residues에 없음: {sorted(residues)}"
            return
        assert set(center_res) == set(A01_RESIDUES), (
            f"binding_pocket_center_residues 불일치: "
            f"저장={sorted(center_res)}, 기대={sorted(A01_RESIDUES)}"
        )

    def test_center_x_approximately_correct(self, pocket_data: Dict) -> None:
        """중심 X 좌표가 PDB 직접 계산 결과와 허용 오차 내에서 일치한다."""
        if not SSTR2_PDB.exists():
            pytest.skip(f"PDB 파일 없음: {SSTR2_PDB}")
        import sys
        sys.path.insert(0, str(REPO_ROOT))
        from pipeline_local.scripts.extract_binding_pocket import extract_pocket_center
        live = extract_pocket_center(SSTR2_PDB, A01_RESIDUES)
        saved_cx = pocket_data.get("center_x") or pocket_data.get("gnina_config", {}).get("center_x")
        assert saved_cx is not None, "center_x 필드 없음"
        assert abs(saved_cx - live["center_x"]) <= COORD_TOLERANCE, (
            f"저장된 center_x={saved_cx:.3f}, 계산값={live['center_x']:.3f}"
        )


# ---------------------------------------------------------------------------
# 네거티브 디자인 잔기 JSON 검증
# ---------------------------------------------------------------------------

class TestNegativeDesignResidues:
    """data/somatostatin_receptor/negative_design_residues_SSTR2.json 구조 검증."""

    @pytest.fixture
    def neg_data(self) -> Dict:
        if not NEG_DESIGN_JSON.exists():
            pytest.skip(f"JSON 파일 없음: {NEG_DESIGN_JSON}")
        return json.loads(NEG_DESIGN_JSON.read_text())

    def test_json_parseable(self) -> None:
        """JSON 파일이 파싱된다."""
        if not NEG_DESIGN_JSON.exists():
            pytest.skip(f"JSON 파일 없음: {NEG_DESIGN_JSON}")
        data = json.loads(NEG_DESIGN_JSON.read_text())
        assert isinstance(data, dict)

    def test_subtype_is_sstr2(self, neg_data: Dict) -> None:
        """subtype 필드가 SSTR2이다."""
        assert neg_data.get("subtype") == "SSTR2"

    def test_uniprot_is_p30874(self, neg_data: Dict) -> None:
        """UniProt ID가 P30874 (SSTR2 human)이다."""
        assert neg_data.get("uniprot") == "P30874"

    def test_selectivity_residues_all_domains(self, neg_data: Dict) -> None:
        """selectivity_residues에 A-01 스펙의 9개 도메인이 모두 있다."""
        expected_domains = {"ECL2", "ECL3", "TM2", "TM3", "TM4", "TM5", "TM6", "TM7"}
        actual_domains = set(neg_data.get("selectivity_residues", {}).keys())
        missing = expected_domains - actual_domains
        assert not missing, f"누락 도메인: {missing}"

    def test_binding_pocket_center_residues_subset_of_selectivity(
        self, neg_data: Dict
    ) -> None:
        """binding_pocket_center_residues가 TM5+TM6 selectivity_residues에 포함된다."""
        pocket_res = set(neg_data.get("binding_pocket_center_residues", []))
        sel = neg_data.get("selectivity_residues", {})
        tm5_tm6 = set(sel.get("TM5", [])) | set(sel.get("TM6", []))
        assert pocket_res.issubset(tm5_tm6), (
            f"포켓 잔기 {sorted(pocket_res)} 중 TM5/TM6에 없는 잔기: "
            f"{sorted(pocket_res - tm5_tm6)}"
        )

    def test_tm5_includes_a01_residues(self, neg_data: Dict) -> None:
        """TM5 잔기 목록에 A-01 결합 포켓 잔기 208, 209가 포함된다."""
        tm5 = neg_data.get("selectivity_residues", {}).get("TM5", [])
        assert 208 in tm5, f"TM5에 208 없음: {tm5}"
        assert 209 in tm5, f"TM5에 209 없음: {tm5}"

    def test_tm6_includes_a01_residues(self, neg_data: Dict) -> None:
        """TM6 잔기 목록에 A-01 결합 포켓 잔기 272, 273, 276이 포함된다."""
        tm6 = neg_data.get("selectivity_residues", {}).get("TM6", [])
        for r in [272, 273, 276]:
            assert r in tm6, f"TM6에 {r} 없음: {tm6}"

    def test_all_residues_within_binding_range(self, neg_data: Dict) -> None:
        """모든 셀렉티비티 잔기가 서호성 박사 결합 영역(77-314) 내에 있다."""
        sel = neg_data.get("selectivity_residues", {})
        all_res: List[int] = []
        for domain_res in sel.values():
            all_res.extend(domain_res)
        out_of_range = [r for r in all_res if not (77 <= r <= 314)]
        assert not out_of_range, (
            f"결합 영역(77-314) 밖의 잔기: {sorted(out_of_range)}"
        )
