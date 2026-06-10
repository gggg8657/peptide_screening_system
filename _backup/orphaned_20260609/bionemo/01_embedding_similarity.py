#!/usr/bin/env python3
"""
시나리오 1: 분자 생성 & 유사도 비교
======================================
CMA-ES 최적화로 시드 분자에서 다양한 분자를 생성하고
Tanimoto 유사도를 비교합니다.

호스팅 API에서는 /generate 엔드포인트만 사용 가능하므로
embedding 대신 generate 기반 분석을 수행합니다.

사용법:
    python 01_embedding_similarity.py
"""

try:
    from .molmim_client import get_client
except ImportError:
    from molmim_client import get_client


def main():
    client = get_client()

    # 시드 분자들
    seeds = {
        "에탄올":     "CCO",
        "아스피린":   "CC(=O)Oc1ccccc1C(=O)O",
        "카페인":     "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
        "이부프로펜": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
    }

    print("=" * 70)
    print("시나리오 1: 시드 분자별 CMA-ES 분자 생성 & 유사도 비교")
    print("=" * 70)

    all_results = {}

    for name, smi in seeds.items():
        print(f"\n--- {name} ({smi}) ---")

        # CMA-ES로 QED 최적화 분자 생성
        try:
            mols = client.generate(
                smi=smi,
                num_molecules=5,
                algorithm="CMA-ES",
                property_name="QED",
                min_similarity=0.3,
                particles=10,
                iterations=3,
            )
            all_results[name] = mols
            print(f"  생성된 분자 {len(mols)}개:")
            for i, mol in enumerate(mols, 1):
                sample = mol.get("sample", mol.get("smiles", "?"))
                score = mol.get("score", "?")
                print(f"    {i}. {sample:50s}  QED={score}")
        except Exception as e:
            print(f"  오류: {e}")

    # 랜덤 샘플링 비교
    print(f"\n{'=' * 70}")
    print("랜덤 샘플링 vs CMA-ES 비교 (에탄올 기준)")
    print(f"{'=' * 70}")

    try:
        random_mols = client.sampling(smi="CCO", num_samples=5, scaled_radius=1.0)
        print("\n  [랜덤 샘플링]:")
        for i, mol in enumerate(random_mols, 1):
            sample = mol.get("sample", "?")
            score = mol.get("score", "?")
            print(f"    {i}. {sample:50s}  similarity={score}")
    except Exception as e:
        print(f"  오류: {e}")

    if "에탄올" in all_results:
        print("\n  [CMA-ES QED 최적화]:")
        for i, mol in enumerate(all_results["에탄올"], 1):
            sample = mol.get("sample", mol.get("smiles", "?"))
            score = mol.get("score", "?")
            print(f"    {i}. {sample:50s}  QED={score}")


if __name__ == "__main__":
    main()
