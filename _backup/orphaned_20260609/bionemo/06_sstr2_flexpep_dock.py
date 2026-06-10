#!/usr/bin/env python3
"""
Arm 2: Somatostatin 변이체 FlexPepDock 도킹
=============================================
AlphaFold3 복합체 구조를 초기 모델로 사용하여
Somatostatin 변이체를 PyRosetta FlexPepDock으로 평가.

사용법:
    python 06_sstr2_flexpep_dock.py
"""

import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
COMPLEX_PDB = PROJECT_ROOT / "data" / "fold_test1" / "fold_test1_model_0.pdb"
OUTPUT_DIR = PROJECT_ROOT / "results" / "sstr2_docking" / "arm2_flexpep"

# Somatostatin-14 야생형: AGCKNFFWKTFTSC (UniProt P61278)
# 활성 약효단(pharmacophore): Phe7-Trp8-Lys9-Thr10 (1-indexed)
WILDTYPE = "AGCKNFFWKTFTSC"

# 변이체 라이브러리
VARIANTS = {
    "wildtype":     WILDTYPE,
    # Alanine scanning (핵심 약효단 잔기)
    "F6A":          "AGCKNAFWKTFTSC",
    "F7A":          "AGCKNFAWKTFTSC",
    "W8A":          "AGCKNFFAKTFTSC",
    "K9A":          "AGCKNFFWATFTSC",
    "T10A":         "AGCKNFFWKAFTSC",
    "F11A":         "AGCKNFFWKTATSC",
    # Octreotide 유래 서열
    # 실제 Octreotide: D-Phe-Cys-Phe-D-Trp-Lys-Thr-Cys-Thr(ol)
    # 환형 (Cys2-Cys7 이황화결합), D-아미노산(pos 1,4)은 L로 근사
    # 선형 표현이므로 FlexPepDock에서 disulfide constraint 별도 필요
    "octreotide_linear": "FCFWKTCT",
    # 강화 변이체 (핵심 약효단 보존, 나머지 최적화)
    "enhanced_1":   "SGCKNFFWKTFTSC",  # A1S
    "enhanced_2":   "AGCRNFFWKTFTSC",  # K4R (Lys→Arg, 양전하 보존)
    "enhanced_3":   "AGCKNYFWKTFTSC",  # F6Y (Phe→Tyr, 수소결합 추가)
    "enhanced_4":   "AGCKNFFWRTFTSC",  # K9R (Lys→Arg, 양전하 보존)
    "enhanced_5":   "AGCKNFFWKTYTSC",  # F11Y (Phe→Tyr, 수소결합 추가)
}


def run_arm2():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Arm 2: Somatostatin 변이체 FlexPepDock")
    print("=" * 60)
    print(f"복합체: {COMPLEX_PDB}")
    print(f"야생형: {WILDTYPE}")
    print(f"변이체: {len(VARIANTS)}개")

    results = []

    # PyRosetta FlexPepDock: 런타임에 import 시도
    HAS_PYROSETTA = False
    try:
        import pyrosetta  # noqa: F401
        HAS_PYROSETTA = True
        pyrosetta.init(extra_options="-mute all")
        print("PyRosetta 감지됨 — FlexPepDock 모드로 실행합니다.")
    except ImportError:
        print("PyRosetta 미설치 — 변이체 서열 분석 모드로 실행합니다.")
        print("(FlexPepDock 실행은 PyRosetta 설치 후 가능)")
    except Exception:
        HAS_PYROSETTA = False
        print("PyRosetta 초기화 실패 — 변이체 서열 분석 모드로 실행합니다.")
        print("(FlexPepDock 실행은 PyRosetta 정상 초기화 후 가능)")

    if HAS_PYROSETTA:
        from pyrosetta import pose_from_pdb
        from pyrosetta.rosetta.protocols.flexpep_docking import FlexPepDockingProtocol
        from pyrosetta.rosetta.core.scoring import get_score_function

        # 스코어 함수
        scorefxn = get_score_function()

        # 원본 복합체 로드
        print(f"\n원본 복합체 로드 중...")
        try:
            original_pose = pose_from_pdb(str(COMPLEX_PDB))
            original_score = scorefxn(original_pose)
            print(f"  원본 총 에너지: {original_score:.2f} REU")

            # 각 변이체에 대해 FlexPepDock
            for name, seq in VARIANTS.items():
                print(f"\n  [{name}] {seq}")
                try:
                    # 복합체 복사
                    pose = original_pose.clone()

                    # Chain A (펩타이드) 서열 변이
                    if seq != WILDTYPE and len(seq) == len(WILDTYPE):
                        chain_a_start = pose.chain_begin(1)
                        for i, (wt_aa, mut_aa) in enumerate(zip(WILDTYPE, seq)):
                            if wt_aa != mut_aa:
                                from pyrosetta.rosetta.protocols.simple_moves import MutateResidue
                                mutator = MutateResidue(chain_a_start + i, mut_aa)
                                mutator.apply(pose)

                    # FlexPepDock
                    fpdock = FlexPepDockingProtocol()
                    fpdock.apply(pose)

                    # 스코어링
                    score = scorefxn(pose)
                    delta = score - original_score

                    result = {
                        "name": name,
                        "sequence": seq,
                        "total_energy": score,
                        "delta_energy": delta,
                        "status": "success",
                    }
                    results.append(result)
                    print(f"    총 에너지: {score:.2f} REU (Δ={delta:+.2f})")

                    # 결과 PDB 저장
                    pose_pdb = OUTPUT_DIR / f"{name}.pdb"
                    pose.dump_pdb(str(pose_pdb))

                except Exception as e:
                    results.append({
                        "name": name,
                        "sequence": seq,
                        "status": "failed",
                        "error": str(e),
                    })
                    print(f"    오류: {e}")

        except Exception as e:
            print(f"  복합체 로드 실패: {e}")
            HAS_PYROSETTA = False

    if not HAS_PYROSETTA:
        # PyRosetta 없이 변이체 분석만 수행
        print(f"\n변이체 서열 분석 (도킹 미수행):")
        for name, seq in VARIANTS.items():
            mutations = []
            if len(seq) == len(WILDTYPE):
                for i, (wt, mut) in enumerate(zip(WILDTYPE, seq)):
                    if wt != mut:
                        mutations.append(f"{wt}{i+1}{mut}")

            result = {
                "name": name,
                "sequence": seq,
                "length": len(seq),
                "mutations": mutations,
                "status": "analysis_only",
            }
            results.append(result)
            mut_str = ", ".join(mutations) if mutations else "(야생형)"
            print(f"  {name:20s} {seq:16s} {mut_str}")

    # 결과 저장
    output_file = OUTPUT_DIR / f"arm2_results_{datetime.now():%Y%m%d_%H%M%S}.json"
    save_data = {
        "pipeline": "Arm 2: Peptide Variant FlexPepDock",
        "complex_pdb": str(COMPLEX_PDB),
        "wildtype": WILDTYPE,
        "pyrosetta_available": HAS_PYROSETTA,
        "num_variants": len(VARIANTS),
        "results": results,
        "timestamp": datetime.now().isoformat(),
    }
    output_file.write_text(json.dumps(save_data, indent=2, ensure_ascii=False))
    print(f"\n결과 저장: {output_file}")

    # 요약
    print(f"\n{'=' * 60}")
    print("Arm 2 요약")
    print(f"{'=' * 60}")
    if HAS_PYROSETTA:
        success = [r for r in results if r.get("status") == "success"]
        if success:
            best = min(success, key=lambda x: x.get("total_energy", float("inf")))
            print(f"  최저 에너지: {best['name']} ({best['total_energy']:.2f} REU)")
    print(f"  변이체 수: {len(VARIANTS)}개")
    print(f"  분석 완료: {len(results)}개")

    return results


if __name__ == "__main__":
    run_arm2()
