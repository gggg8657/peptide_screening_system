#!/usr/bin/env python3
"""
시나리오 3: 다단계 물성 최적화 파이프라인
==========================================
시드 분자에서 시작하여 다단계 CMA-ES 최적화로
QED (drug-likeness)를 최대화하면서 원래 분자와의
유사도를 유지하는 분자를 탐색합니다.

각 라운드의 최고 분자를 다음 라운드의 시드로 사용합니다.

사용법:
    python 03_property_optimization.py
    python 03_property_optimization.py --smi "c1ccc(cc1)N" --property QED --rounds 3
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
try:
    from .molmim_client import get_client
except ImportError:
    from molmim_client import get_client


def main():
    parser = argparse.ArgumentParser(description="MolMIM 물성 최적화 파이프라인")
    parser.add_argument("--smi", default="c1ccc2c(c1)cc(=O)oc2", help="시드 SMILES (기본: 쿠마린)")
    parser.add_argument("--property", default="QED", help="최적화 대상 (QED, plogP)")
    parser.add_argument("--rounds", type=int, default=3, help="최적화 반복 횟수")
    parser.add_argument("--num-molecules", type=int, default=10, help="라운드당 생성 수")
    parser.add_argument("--min-similarity", type=float, default=0.3, help="최소 유사도")
    parser.add_argument("--output", default=None, help="결과 JSON 저장 경로")
    args = parser.parse_args()

    client = get_client()

    print("=" * 60)
    print("시나리오 3: 다단계 물성 최적화 파이프라인")
    print("=" * 60)
    print(f"\n시드: {args.smi}")
    print(f"목표: {args.property} 최대화")
    print(f"라운드: {args.rounds}회, 라운드당 {args.num_molecules}개")
    print(f"최소 유사도: {args.min_similarity}")

    all_results = []
    current_seed = args.smi
    best_overall = {"sample": args.smi, "score": 0.0}

    for round_idx in range(1, args.rounds + 1):
        print(f"\n{'─' * 50}")
        print(f"라운드 {round_idx}/{args.rounds}  |  시드: {current_seed}")
        print(f"{'─' * 50}")

        try:
            generated = client.generate(
                smi=current_seed,
                num_molecules=args.num_molecules,
                property_name=args.property,
                minimize=False,
                min_similarity=args.min_similarity,
                particles=30,
                iterations=5,
            )

            round_best = None
            for mol in generated:
                if isinstance(mol, dict):
                    score = mol.get("score", 0)
                    if not isinstance(score, (int, float)):
                        continue
                    smi = mol.get("sample", mol.get("smiles", ""))
                    print(f"  {smi:50s}  {args.property}={score:.4f}")
                    if round_best is None or score > round_best.get("score", 0):
                        round_best = mol

            if round_best:
                all_results.append({
                    "round": round_idx,
                    "seed": current_seed,
                    "best": round_best,
                })
                # 다음 라운드의 시드로 사용
                if round_best.get("score", 0) > best_overall.get("score", 0):
                    best_overall = round_best
                current_seed = round_best.get("sample", round_best.get("smiles", current_seed))
                print(f"\n  -> 라운드 최고: {current_seed}")
                print(f"     {args.property}={round_best.get('score', 0):.4f}")

        except Exception as e:
            print(f"  라운드 {round_idx} 오류: {e}")
            all_results.append({"round": round_idx, "error": str(e)})

    # ── 최종 결과 ────────────────────────────────────────────

    print(f"\n{'=' * 60}")
    print("최적화 완료!")
    print(f"{'=' * 60}")
    print(f"  원본 시드:   {args.smi}")
    print(f"  최종 최적:   {best_overall.get('sample', best_overall.get('smiles', 'N/A'))}")
    print(f"  {args.property} 점수: {best_overall.get('score', 'N/A')}")

    # 결과 저장
    output_path = args.output or f"result_optimization_{datetime.now():%Y%m%d_%H%M%S}.json"
    output_path = Path(__file__).parent / output_path
    result_data = {
        "seed": args.smi,
        "property": args.property,
        "rounds": args.rounds,
        "best_overall": best_overall,
        "round_results": all_results,
        "timestamp": datetime.now().isoformat(),
    }
    output_path.write_text(json.dumps(result_data, indent=2, ensure_ascii=False))
    print(f"\n결과 저장: {output_path}")


if __name__ == "__main__":
    main()
