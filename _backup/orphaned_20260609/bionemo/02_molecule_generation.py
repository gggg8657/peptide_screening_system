#!/usr/bin/env python3
"""
시나리오 2: 시드 분자 기반 신규 분자 생성
==========================================
시드 SMILES에서 CMA-ES 및 랜덤 샘플링으로 새 분자를 생성합니다.

사용법:
    python 02_molecule_generation.py
    python 02_molecule_generation.py --smi "CC(=O)Oc1ccccc1C(=O)O"  # 아스피린 기반
"""

import argparse
try:
    from .molmim_client import get_client
except ImportError:
    from molmim_client import get_client


def main():
    parser = argparse.ArgumentParser(description="MolMIM 분자 생성")
    parser.add_argument("--smi", default="CC(=O)Oc1ccccc1C(=O)O", help="시드 SMILES (기본: 아스피린)")
    parser.add_argument("--num-molecules", type=int, default=10, help="생성할 분자 수")
    parser.add_argument("--radius", type=float, default=1.0, help="샘플링 반경")
    parser.add_argument("--property", default="QED", help="최적화 물성 (QED, plogP)")
    args = parser.parse_args()

    client = get_client()

    print("=" * 60)
    print("시나리오 2: 시드 분자 기반 신규 분자 생성")
    print("=" * 60)
    print(f"\n시드 SMILES: {args.smi}")

    # ── Part A: 랜덤 샘플링 ────────────────────────────────

    print(f"\n[Part A] 랜덤 샘플링 ({args.num_molecules}개, 반경={args.radius})")
    try:
        samples = client.sampling(
            smi=args.smi,
            num_samples=args.num_molecules,
            scaled_radius=args.radius,
        )
        print(f"  생성된 분자 {len(samples)}개:")
        for i, mol in enumerate(samples, 1):
            if isinstance(mol, dict):
                score = mol.get("score", 0)
                score_text = f"{score:.4f}" if isinstance(score, (int, float)) else str(score)
                print(f"    {i:2d}. {mol.get('sample', '?'):50s}  "
                      f"similarity={score_text}")
            else:
                print(f"    {i:2d}. {mol}")
    except Exception as e:
        print(f"  샘플링 오류: {e}")

    # ── Part B: CMA-ES 최적화 생성 ─────────────────────────

    print(f"\n[Part B] CMA-ES 최적화 ({args.property} 최대화)")
    try:
        generated = client.generate(
            smi=args.smi,
            num_molecules=args.num_molecules,
            algorithm="CMA-ES",
            property_name=args.property,
            min_similarity=0.3,
            particles=20,
            iterations=3,
        )
        print(f"  생성된 분자 {len(generated)}개:")
        for i, mol in enumerate(generated, 1):
            if isinstance(mol, dict):
                score = mol.get("score", 0)
                score_text = f"{score:.4f}" if isinstance(score, (int, float)) else str(score)
                print(f"    {i:2d}. {mol.get('sample', mol.get('smiles', '?')):50s}  "
                      f"{args.property}={score_text}")
            else:
                print(f"    {i:2d}. {mol}")
    except Exception as e:
        print(f"  생성 오류: {e}")

    # ── Part C: plogP 최적화 비교 ──────────────────────────

    print(f"\n[Part C] plogP 최소화")
    try:
        generated_plogp = client.generate(
            smi=args.smi,
            num_molecules=5,
            algorithm="CMA-ES",
            property_name="plogP",
            minimize=True,
            min_similarity=0.3,
            particles=15,
            iterations=3,
        )
        print(f"  생성된 분자 {len(generated_plogp)}개:")
        for i, mol in enumerate(generated_plogp, 1):
            if isinstance(mol, dict):
                score = mol.get("score", 0)
                score_text = f"{score:.4f}" if isinstance(score, (int, float)) else str(score)
                print(f"    {i:2d}. {mol.get('sample', '?'):50s}  "
                      f"plogP={score_text}")
            else:
                print(f"    {i:2d}. {mol}")
    except Exception as e:
        print(f"  plogP 최적화 오류: {e}")


if __name__ == "__main__":
    main()
