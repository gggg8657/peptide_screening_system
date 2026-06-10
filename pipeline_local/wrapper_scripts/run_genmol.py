#!/usr/bin/env python
"""
run_genmol.py
=============
GenMol 로컬 실행 래퍼.

GenMol Sampler의 fragment_completion() 또는 de_novo_generation()을 사용하여
seed SMILES 기반 분자를 생성한다.

GenMol 리포지토리:
    /home/dongjukim/Documents/workspace/repos/SST14-M_scr/local_models/genmol-repo/

Output JSON:
    {"molecules": [{"smiles": "CC(=O)...", "score": 0.9}, ...]}
    또는 에러 시:
    {"error": "<message>"}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

warnings.filterwarnings("ignore")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# GenMol 리포지토리 절대 경로
_GENMOL_REPO = Path(
    "/home/dongjukim/Documents/workspace/repos/SST14-M_scr/local_models/genmol-repo"
)
_GENMOL_SRC = _GENMOL_REPO / "src"

# PYTHONPATH에 GenMol src 추가 (임포트 전)
if str(_GENMOL_SRC) not in sys.path:
    sys.path.insert(0, str(_GENMOL_SRC))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GenMol 로컬 실행 래퍼 — stdout에 JSON 출력"
    )
    parser.add_argument(
        "--input-json",
        default=None,
        help="JSON payload 파일 경로 (다른 인자를 override)",
    )
    parser.add_argument(
        "--seed-smiles",
        default=None,
        help="시드 SMILES 문자열 (fragment completion의 시작점)",
    )
    parser.add_argument(
        "--num-molecules", type=int, default=10, help="생성할 분자 수"
    )
    parser.add_argument("--output-dir", required=True, help="출력 파일 저장 디렉토리")
    args = parser.parse_args()

    if args.input_json:
        with open(args.input_json) as f:
            payload = json.load(f)
        args.seed_smiles = payload.get("seed_smiles", args.seed_smiles)
        args.num_molecules = int(payload.get("num_molecules", args.num_molecules))

        if args.seed_smiles is None:
            parser.error("--input-json의 seed_smiles 키가 없고 --seed-smiles도 지정되지 않음")
    else:
        if args.seed_smiles is None:
            parser.error("--seed-smiles 또는 --input-json 중 하나를 지정해야 합니다.")

    return args


def _find_model_checkpoint() -> Optional[str]:
    """GenMol 모델 체크포인트 경로를 탐색한다."""
    # 기본 탐색 경로
    search_patterns = [
        str(_GENMOL_REPO / "data" / "*.ckpt"),
        str(_GENMOL_REPO / "data" / "*.pt"),
        str(_GENMOL_REPO / "checkpoints" / "*.ckpt"),
        str(_GENMOL_REPO / "**" / "*.ckpt"),
    ]
    import glob

    for pattern in search_patterns:
        candidates = sorted(glob.glob(pattern, recursive=True))
        if candidates:
            print(f"[GenMol] 체크포인트 발견: {candidates[0]}", file=sys.stderr)
            return candidates[0]

    # configs/base.yaml에서 model_path 키 읽기 시도
    config_path = _GENMOL_REPO / "configs" / "base.yaml"
    if config_path.exists():
        try:
            import yaml  # type: ignore

            config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            model_path = config.get("model_path", "")
            if model_path and Path(model_path).exists():
                return model_path
            # 상대 경로일 경우 GENMOL_REPO 기준으로 해석
            abs_path = _GENMOL_REPO / model_path
            if abs_path.exists():
                return str(abs_path)
        except Exception as exc:
            print(f"[GenMol] config 파싱 실패: {exc}", file=sys.stderr)

    return None


def _compute_molecule_score(smiles: str) -> float:
    """분자의 QED 점수를 계산하여 품질 지표로 사용한다.

    QED (Quantitative Estimate of Drug-likeness): 0 ~ 1 범위, 높을수록 좋음.
    rdkit이 없으면 0.0 반환.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import QED

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return 0.0
        return round(float(QED.qed(mol)), 4)
    except ImportError:
        return 0.0
    except Exception:
        return 0.0


def _generate_with_genmol(
    seed_smiles: str,
    num_molecules: int,
    model_path: str,
) -> List[str]:
    """GenMol Sampler를 사용하여 seed SMILES 기반 분자를 생성한다.

    seed_smiles에 '*' 기호가 있으면 fragment_completion,
    없으면 fragment_linking 또는 scaffold_decoration을 사용한다.
    완전한 SMILES라면 lead optimization을 시도한다.
    """
    from genmol.sampler import Sampler  # type: ignore

    print(f"[GenMol] 모델 로드 중: {model_path}", file=sys.stderr)
    sampler = Sampler(model_path)
    print("[GenMol] 모델 로드 완료", file=sys.stderr)

    if "*" in seed_smiles:
        # Fragment completion: attachment point(*)가 있는 단편에서 완성
        print(f"[GenMol] fragment_completion 모드: {seed_smiles}", file=sys.stderr)
        results = sampler.fragment_completion(
            fragment=seed_smiles,
            num_samples=num_molecules,
            softmax_temp=1.2,
            randomness=2,
        )
    else:
        # Lead optimization: 기존 분자 기반 변형
        # SMILES가 유효한지 확인
        try:
            from rdkit import Chem

            mol = Chem.MolFromSmiles(seed_smiles)
            valid = mol is not None
        except ImportError:
            valid = True  # rdkit 없으면 일단 시도

        if valid and len(seed_smiles) > 5:
            print(
                f"[GenMol] lead_optimization 모드: {seed_smiles[:50]}...",
                file=sys.stderr,
            )
            # scaffold_morphing이 없으면 fragment_completion 폴백
            try:
                results = sampler.scaffold_morphing(
                    smiles=seed_smiles,
                    num_samples=num_molecules,
                    softmax_temp=1.2,
                    randomness=2,
                )
            except AttributeError:
                # scaffold_morphing 미지원 시 fragment_completion 사용
                # seed SMILES에 attachment point 추가
                results = sampler.fragment_completion(
                    fragment=seed_smiles + ".*",
                    num_samples=num_molecules,
                    softmax_temp=1.2,
                    randomness=2,
                    apply_filter=False,
                )
        else:
            # De novo 생성 (seed 무시)
            print("[GenMol] de_novo_generation 모드", file=sys.stderr)
            results = sampler.de_novo_generation(
                num_samples=num_molecules,
                softmax_temp=0.8,
                randomness=0.5,
                min_add_len=40,
            )

    return results if results else []


def main() -> None:
    args = _parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 모델 체크포인트 탐색
    model_path = _find_model_checkpoint()
    if model_path is None:
        print(
            json.dumps(
                {
                    "error": (
                        f"GenMol 체크포인트를 찾을 수 없음. "
                        f"{_GENMOL_REPO}/data/ 디렉토리에 .ckpt 파일을 배치하세요."
                    )
                }
            ),
            flush=True,
        )
        sys.exit(1)

    try:
        smiles_list = _generate_with_genmol(
            seed_smiles=args.seed_smiles,
            num_molecules=args.num_molecules,
            model_path=model_path,
        )
        print(f"[GenMol] {len(smiles_list)}개 분자 생성 완료", file=sys.stderr)
    except Exception as exc:
        print(json.dumps({"error": f"GenMol 생성 실패: {exc}"}), flush=True)
        sys.exit(1)

    if not smiles_list:
        print(json.dumps({"error": "생성된 분자 없음"}), flush=True)
        sys.exit(1)

    # QED 스코어 계산 및 결과 구성
    molecules: List[Dict[str, Any]] = []
    for smiles in smiles_list:
        if not smiles or not isinstance(smiles, str):
            continue
        smiles = smiles.strip()
        if not smiles:
            continue
        score = _compute_molecule_score(smiles)
        molecules.append({"smiles": smiles, "score": score})

    # QED 기준 내림차순 정렬
    molecules.sort(key=lambda m: m["score"], reverse=True)

    # SMILES 파일로도 저장
    smiles_path = out_dir / "generated_molecules.smi"
    smiles_lines = [
        f"{m['smiles']}\t{m['score']:.4f}" for m in molecules
    ]
    smiles_path.write_text("\n".join(smiles_lines) + "\n", encoding="utf-8")
    print(f"[GenMol] SMILES 저장: {smiles_path}", file=sys.stderr)

    print(json.dumps({"molecules": molecules}), flush=True)


if __name__ == "__main__":
    main()
