#!/usr/bin/env python3
"""
Step 0: SSTR2 바인딩 포켓 분석
================================
AlphaFold3 복합체(SSTR2 + Somatostatin)에서:
1. Somatostatin(Chain A) 기준 5Å 이내 SSTR2(Chain B) 잔기 추출
2. SSTR2 단독 PDB 추출 (도킹 수용체용)
3. 바인딩 포켓 잔기 리스트 (RFdiffusion hotspot_res용)

사용법:
    python 04_sstr2_pocket_analysis.py
"""

import json
from pathlib import Path
from Bio.PDB import PDBParser, PDBIO, Select
from Bio.PDB.NeighborSearch import NeighborSearch
import numpy as np

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
PDB_PATH = PROJECT_ROOT / "data" / "fold_test1" / "fold_test1_model_0.pdb"
OUTPUT_DIR = PROJECT_ROOT / "results" / "sstr2_docking"

LIGAND_CHAIN = "A"   # Somatostatin-14
RECEPTOR_CHAIN = "B"  # SSTR2
CUTOFF_DISTANCE = 5.0  # Angstrom


class ChainSelect(Select):
    """특정 체인만 선택하는 셀렉터"""
    def __init__(self, chain_id):
        self.chain_id = chain_id

    def accept_chain(self, chain):
        return chain.get_id() == self.chain_id


def analyze_binding_pocket():
    """바인딩 포켓 분석 메인 함수"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. PDB 파싱
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("sstr2_complex", str(PDB_PATH))
    model = structure[0]

    if LIGAND_CHAIN not in model:
        raise KeyError(f"체인 {LIGAND_CHAIN}를 찾을 수 없습니다: {PDB_PATH}")
    if RECEPTOR_CHAIN not in model:
        raise KeyError(f"체인 {RECEPTOR_CHAIN}를 찾을 수 없습니다: {PDB_PATH}")

    chain_a = model[LIGAND_CHAIN]    # Somatostatin
    chain_b = model[RECEPTOR_CHAIN]  # SSTR2

    print("=" * 60)
    print("Step 0: SSTR2 바인딩 포켓 분석")
    print("=" * 60)
    print(f"\n입력: {PDB_PATH}")
    print(f"Chain A (리간드):  Somatostatin-14, {len(list(chain_a.get_residues()))} 잔기")
    print(f"Chain B (수용체):  SSTR2, {len(list(chain_b.get_residues()))} 잔기")
    print(f"접촉 거리 컷오프:  {CUTOFF_DISTANCE} Å")

    # 2. Chain B 원자들로 NeighborSearch 구축
    receptor_atoms = list(chain_b.get_atoms())
    ns = NeighborSearch(receptor_atoms)

    # 3. Chain A 원자 기준으로 5Å 이내 Chain B 잔기 탐색
    contact_residues = set()
    contact_details = []

    for lig_residue in chain_a.get_residues():
        for lig_atom in lig_residue.get_atoms():
            nearby = ns.search(lig_atom.get_vector().get_array(), CUTOFF_DISTANCE, level="R")
            for res in nearby:
                if res.get_parent().get_id() == RECEPTOR_CHAIN:
                    resname = res.get_resname()
                    resid = res.get_id()[1]
                    contact_residues.add((resid, resname))

    # 정렬
    contact_residues = sorted(contact_residues, key=lambda x: x[0])

    print(f"\n바인딩 포켓 잔기 ({len(contact_residues)}개):")
    for resid, resname in contact_residues:
        print(f"  {RECEPTOR_CHAIN}{resid:4d} {resname}")

    # 4. Somatostatin 잔기별 접촉 상세
    print(f"\nSomatostatin 잔기별 접촉 분석:")
    for lig_residue in chain_a.get_residues():
        lig_resid = lig_residue.get_id()[1]
        lig_resname = lig_residue.get_resname()
        contacts = set()
        min_dist = float("inf")

        for lig_atom in lig_residue.get_atoms():
            nearby = ns.search(lig_atom.get_vector().get_array(), CUTOFF_DISTANCE, level="A")
            for rec_atom in nearby:
                rec_res = rec_atom.get_parent()
                if rec_res.get_parent().get_id() == RECEPTOR_CHAIN:
                    rec_resid = rec_res.get_id()[1]
                    rec_resname = rec_res.get_resname()
                    contacts.add(f"{RECEPTOR_CHAIN}{rec_resid}({rec_resname})")
                    dist = lig_atom - rec_atom
                    if dist < min_dist:
                        min_dist = dist

        if contacts:
            print(f"  A{lig_resid:3d} {lig_resname:3s} → "
                  f"{', '.join(sorted(contacts))}  (min={min_dist:.2f}Å)")

    # 5. SSTR2 단독 PDB 저장
    receptor_pdb = OUTPUT_DIR / "sstr2_receptor.pdb"
    io = PDBIO()
    io.set_structure(structure)
    io.save(str(receptor_pdb), ChainSelect(RECEPTOR_CHAIN))
    print(f"\nSSTR2 단독 PDB 저장: {receptor_pdb}")

    # 6. 바인딩 포켓 정보 JSON 저장
    hotspot_res = [f"{RECEPTOR_CHAIN}{resid}" for resid, _ in contact_residues]
    pocket_info = {
        "pdb_source": str(PDB_PATH),
        "ligand_chain": LIGAND_CHAIN,
        "receptor_chain": RECEPTOR_CHAIN,
        "cutoff_angstrom": CUTOFF_DISTANCE,
        "num_pocket_residues": len(contact_residues),
        "pocket_residues": [
            {"chain": RECEPTOR_CHAIN, "resid": resid, "resname": resname}
            for resid, resname in contact_residues
        ],
        "hotspot_res": hotspot_res,
        "receptor_pdb": str(receptor_pdb),
    }

    pocket_json = OUTPUT_DIR / "binding_pocket.json"
    pocket_json.write_text(json.dumps(pocket_info, indent=2, ensure_ascii=False))
    print(f"바인딩 포켓 JSON 저장: {pocket_json}")

    # 7. RFdiffusion용 contigs 문자열 생성
    receptor_residues = list(chain_b.get_residues())
    first_resid = receptor_residues[0].get_id()[1]
    last_resid = receptor_residues[-1].get_id()[1]
    contigs = f"{RECEPTOR_CHAIN}{first_resid}-{last_resid}/0 10-30"
    print(f"\nRFdiffusion contigs: {contigs}")
    print(f"RFdiffusion hotspot_res: {hotspot_res[:10]}{'...' if len(hotspot_res) > 10 else ''}")

    pocket_info["rfdiffusion"] = {
        "contigs": contigs,
        "hotspot_res": hotspot_res,
    }
    pocket_json.write_text(json.dumps(pocket_info, indent=2, ensure_ascii=False))

    return pocket_info


if __name__ == "__main__":
    result = analyze_binding_pocket()
    print(f"\n완료! 포켓 잔기 {result['num_pocket_residues']}개 추출")
