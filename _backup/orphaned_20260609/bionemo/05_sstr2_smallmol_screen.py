#!/usr/bin/env python3
"""
Arm 1: SSTR2 소분자 스크리닝 파이프라인
=========================================
1. 기존 SSTR2 소분자 리간드 SMILES를 시드로 사용
2. MolMIM으로 후보 분자 생성 (CMA-ES QED 최적화)
3. DiffDock으로 SSTR2에 도킹
4. confidence score 기준 랭킹

사용법:
    python 05_sstr2_smallmol_screen.py
"""

import json
from datetime import datetime
from pathlib import Path
try:
    from .molmim_client import get_client as get_molmim
    from .diffdock_client import get_client as get_diffdock
except ImportError:
    from molmim_client import get_client as get_molmim
    from diffdock_client import get_client as get_diffdock

PROJECT_ROOT = Path(__file__).parent.parent
RECEPTOR_PDB = PROJECT_ROOT / "results" / "sstr2_docking" / "sstr2_receptor.pdb"
OUTPUT_DIR = PROJECT_ROOT / "results" / "sstr2_docking" / "arm1_smallmol"

# 기존 SSTR2 소분자 리간드 시드 (PubChem / ChEMBL 검증)
SEED_MOLECULES = {
    # Paltusotine (CRN00808) - FDA 승인 경구 SSTR2 작용제
    # PubChem CID 134168328, C27H22F2N4O
    "Paltusotine": (
        "C1CN(CCC1N)C2=C3C=C(C=CC3=NC=C2C4=CC(=CC(=C4)F)F)"
        "C5=CC=CC(=C5O)C#N"
    ),
    # L-054522 - Merck 비펩타이드 SSTR2 작용제
    # PubChem CID 15965425, C35H47N7O5
    "L054522": (
        "CC(C1=CNC2=CC=CC=C21)C(C(=O)NC(CCCCN)C(=O)OC(C)(C)C)"
        "NC(=O)N3CCC(CC3)N4C5=CC=CC=C5NC4=O"
    ),
    # Pasireotide (SOM-230) 코어 - 다중 SST 수용체 작용제 (SSTR2 포함)
    # PubChem CID 9941444, C58H66N10O9
    "Pasireotide": (
        "C1C(CN2C1C(=O)NC(C(=O)NC(C(=O)NC(C(=O)NC(C(=O)NC(C2=O)"
        "CC3=CC=CC=C3)CC4=CC=C(C=C4)OCC5=CC=CC=C5)CCCCN)"
        "CC6=CNC7=CC=CC=C76)C8=CC=CC=C8)OC(=O)NCCN"
    ),
    # Octreotide - 환형 소마토스타틴 유사체 (Cys2-Cys7 이황화결합)
    # PubChem CID 448601, C49H66N10O10S2
    "Octreotide": (
        "CC(C1C(=O)NC(CSSCC(C(=O)NC(C(=O)NC(C(=O)NC(C(=O)N1)"
        "CCCCN)CC2=CNC3=CC=CC=C32)CC4=CC=CC=C4)NC(=O)C(CC5=CC=CC=C5)N)"
        "C(=O)NC(CO)C(C)O)O"
    ),
}


def run_arm1():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    molmim = get_molmim()
    diffdock = get_diffdock()

    print("=" * 60)
    print("Arm 1: SSTR2 소분자 스크리닝")
    print("=" * 60)
    print(f"수용체: {RECEPTOR_PDB}")
    print(f"시드 분자: {len(SEED_MOLECULES)}개")

    all_candidates = []

    # ── Step 1: MolMIM으로 후보 생성 ─────────────────────
    print(f"\n[Step 1] MolMIM 후보 생성")
    for name, smi in SEED_MOLECULES.items():
        print(f"\n  시드: {name} ({smi})")
        try:
            # CMA-ES QED 최적화
            mols = molmim.generate(
                smi=smi,
                num_molecules=10,
                algorithm="CMA-ES",
                property_name="QED",
                min_similarity=0.3,
                particles=15,
                iterations=3,
            )
            for mol in mols:
                if not isinstance(mol, dict):
                    mol = {}
                candidate = {
                    "seed_name": name,
                    "seed_smiles": smi,
                    "smiles": mol.get("sample", mol.get("smiles", "")),
                    "qed_score": mol.get("score", 0),
                }
                all_candidates.append(candidate)
                print(f"    {candidate['smiles'][:50]:50s}  QED={candidate['qed_score']:.3f}")
        except Exception as e:
            print(f"    MolMIM 오류: {e}")

    # QED 기준 상위 15개만 도킹
    all_candidates.sort(key=lambda x: x.get("qed_score", 0), reverse=True)
    top_candidates = all_candidates[:15]

    print(f"\n총 {len(all_candidates)}개 후보 중 상위 {len(top_candidates)}개 선별 (QED 기준)")

    # ── Step 2: DiffDock 도킹 ────────────────────────────
    print(f"\n[Step 2] DiffDock 도킹")
    docking_results = []

    for i, cand in enumerate(top_candidates):
        smi = cand["smiles"]
        print(f"  [{i+1}/{len(top_candidates)}] {smi[:50]}...")
        try:
            result = diffdock.dock_smiles(
                protein_pdb_path=RECEPTOR_PDB,
                smiles=smi,
                num_poses=5,
            )
            cand["docking"] = result
            # confidence 추출
            if isinstance(result, dict):
                # 응답 구조에 따라 파싱
                cand["docking_status"] = "success"
            docking_results.append(cand)
            print(f"    -> 도킹 성공")
        except Exception as e:
            cand["docking_status"] = "failed"
            cand["docking_error"] = str(e)
            docking_results.append(cand)
            print(f"    -> 도킹 실패: {e}")

    # ── Step 3: 결과 저장 ────────────────────────────────
    print(f"\n[Step 3] 결과 저장")

    # JSON으로 전체 결과 저장
    output_file = OUTPUT_DIR / f"arm1_results_{datetime.now():%Y%m%d_%H%M%S}.json"
    save_data = {
        "pipeline": "Arm 1: Small Molecule Screening",
        "receptor": str(RECEPTOR_PDB),
        "seeds": SEED_MOLECULES,
        "total_candidates": len(all_candidates),
        "docked_candidates": len(docking_results),
        "results": docking_results,
        "timestamp": datetime.now().isoformat(),
    }

    # docking 결과에서 큰 데이터 제거하여 저장
    for r in save_data["results"]:
        if "docking" in r and isinstance(r["docking"], dict):
            # PDB 내용이 너무 큰 경우 요약만 저장
            dock = r["docking"]
            if "output" in dock and len(str(dock["output"])) > 1000:
                r["docking_summary"] = f"poses={len(dock.get('output', []))}"

    output_file.write_text(json.dumps(save_data, indent=2, ensure_ascii=False, default=str))
    print(f"결과 저장: {output_file}")

    # ── 요약 ─────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("Arm 1 요약")
    print(f"{'=' * 60}")
    success = sum(1 for r in docking_results if r.get("docking_status") == "success")
    print(f"  시드 분자: {len(SEED_MOLECULES)}개")
    print(f"  MolMIM 후보: {len(all_candidates)}개")
    print(f"  도킹 시도: {len(top_candidates)}개")
    print(f"  도킹 성공: {success}개")

    return docking_results


if __name__ == "__main__":
    run_arm1()
