#!/usr/bin/env python
"""
run_esm2.py
===========
ESM-2 임베딩 추출 래퍼.

ESM-2 (esm2_t33_650M_UR50D) 모델로 단백질 서열의 임베딩을 추출한다.
마지막 레이어의 평균 풀링을 사용하며, 임베딩 차원은 모델에 따라 다르다:
  - esm2_t6_8M_UR50D    → 320
  - esm2_t12_35M_UR50D  → 480
  - esm2_t30_150M_UR50D → 640
  - esm2_t33_650M_UR50D → 1280  (기본값)
  - esm2_t36_3B_UR50D   → 2560

Output JSON:
    {"embedding": [0.1, -0.3, ...], "dim": 1280}
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
from typing import List, Optional

warnings.filterwarnings("ignore")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# 기본 ESM-2 모델 이름 (변경 시 이 상수만 수정)
_DEFAULT_ESM2_MODEL = "facebook/esm2_t33_650M_UR50D"
_DEFAULT_EMBEDDING_DIM = 1280


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ESM-2 임베딩 추출 래퍼 — stdout에 JSON 출력"
    )
    parser.add_argument(
        "--input-json",
        default=None,
        help="JSON payload 파일 경로 (다른 인자를 override)",
    )
    parser.add_argument(
        "--sequence", default=None, help="임베딩을 추출할 아미노산 서열 (1문자 코드)"
    )
    parser.add_argument("--output-dir", required=True, help="출력 파일 저장 디렉토리")
    parser.add_argument(
        "--model-name",
        default=_DEFAULT_ESM2_MODEL,
        help=f"Hugging Face 모델 이름 (기본값: {_DEFAULT_ESM2_MODEL})",
    )
    parser.add_argument(
        "--layer",
        type=int,
        default=-1,
        help="추출할 레이어 인덱스 (-1 = 마지막 레이어, 기본값)",
    )
    args = parser.parse_args()

    if args.input_json:
        with open(args.input_json) as f:
            payload = json.load(f)
        args.sequence = payload.get("sequence", args.sequence)
        # 선택적 필드
        if "model_name" in payload:
            args.model_name = payload["model_name"]
        if "layer" in payload:
            args.layer = int(payload["layer"])

        if args.sequence is None:
            parser.error("--input-json의 sequence 키가 없고 --sequence도 지정되지 않음")
    else:
        if args.sequence is None:
            parser.error("--sequence 또는 --input-json 중 하나를 지정해야 합니다.")

    return args


def _load_esm2_transformers(model_name: str):
    """Hugging Face transformers 기반 ESM-2 모델을 로드한다."""
    import torch
    from transformers import AutoTokenizer, EsmModel

    print(f"[ESM-2] 모델 로드 중: {model_name}", file=sys.stderr)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = EsmModel.from_pretrained(model_name)
    model.eval()
    if torch.cuda.is_available():
        model = model.cuda()
        print(
            f"[ESM-2] GPU 사용: {torch.cuda.get_device_name(0)}", file=sys.stderr
        )
    else:
        print("[ESM-2] CPU 사용", file=sys.stderr)
    return model, tokenizer


def _load_esm2_meta(model_name: str):
    """Meta AI esm 패키지 기반 ESM-2 모델을 로드한다.

    model_name에서 파라미터 크기를 추론하여 적절한 pretrained 함수를 호출한다.
    """
    import torch
    import esm  # type: ignore

    # model_name 예: "facebook/esm2_t33_650M_UR50D" → "esm2_t33_650M_UR50D"
    short_name = model_name.split("/")[-1]

    model_fn_map = {
        "esm2_t6_8M_UR50D": esm.pretrained.esm2_t6_8M_UR50D,
        "esm2_t12_35M_UR50D": esm.pretrained.esm2_t12_35M_UR50D,
        "esm2_t30_150M_UR50D": esm.pretrained.esm2_t30_150M_UR50D,
        "esm2_t33_650M_UR50D": esm.pretrained.esm2_t33_650M_UR50D,
        "esm2_t36_3B_UR50D": esm.pretrained.esm2_t36_3B_UR50D,
        "esm2_t48_15B_UR50D": esm.pretrained.esm2_t48_15B_UR50D,
    }

    if short_name not in model_fn_map:
        raise ValueError(
            f"지원하지 않는 ESM-2 모델: {short_name}. "
            f"지원 목록: {list(model_fn_map.keys())}"
        )

    model, alphabet = model_fn_map[short_name]()
    model.eval()
    if torch.cuda.is_available():
        model = model.cuda()
    return model, alphabet


def _extract_embedding_transformers(
    model, tokenizer, sequence: str, layer: int
) -> List[float]:
    """transformers ESM-2로 임베딩을 추출하고 평균 풀링한다.

    layer=-1은 마지막 히든 레이어를 의미한다.
    특수 토큰 ([CLS], [EOS])은 제외하고 실제 잔기 위치만 평균한다.
    """
    import torch

    inputs = tokenizer(
        sequence,
        return_tensors="pt",
        add_special_tokens=True,
    )
    if next(model.parameters()).is_cuda:
        inputs = {k: v.cuda() for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True)

    # hidden_states: tuple of (n_layers + 1) tensors, shape (1, seq_len, dim)
    hidden_states = outputs.hidden_states
    # layer=-1은 last hidden state (== hidden_states[-1])
    target_layer = hidden_states[layer]  # shape: (1, seq_len, dim)

    # 특수 토큰 제외: attention_mask에서 1인 위치 중
    # CLS(첫 토큰)와 EOS(마지막 토큰) 제외
    attention_mask = inputs["attention_mask"]  # (1, seq_len)
    # 실제 서열 토큰만 슬라이싱 (첫 토큰 CLS, 마지막 EOS 제외)
    seq_embedding = target_layer[0, 1:-1, :]  # (seq_len - 2, dim)

    # 평균 풀링
    mean_embedding = seq_embedding.mean(dim=0)  # (dim,)

    return mean_embedding.cpu().float().tolist()


def _extract_embedding_meta(
    model, alphabet, sequence: str, layer: int
) -> List[float]:
    """Meta AI esm 패키지로 임베딩을 추출하고 평균 풀링한다."""
    import torch

    batch_converter = alphabet.get_batch_converter()
    data = [("protein", sequence)]
    _, _, tokens = batch_converter(data)

    if next(model.parameters()).is_cuda:
        tokens = tokens.cuda()

    with torch.no_grad():
        results = model(tokens, repr_layers=[model.num_layers], return_contacts=False)

    # repr_layers 기준: 마지막 레이어의 representations
    representations = results["representations"][model.num_layers]
    # shape: (1, seq_len+2, dim) — [BOS] seq [EOS] 포함
    # 특수 토큰 제외
    seq_embedding = representations[0, 1:-1, :]  # (seq_len, dim)
    mean_embedding = seq_embedding.mean(dim=0)

    return mean_embedding.cpu().float().tolist()


def main() -> None:
    args = _parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    embedding: Optional[List[float]] = None
    dim: int = _DEFAULT_EMBEDDING_DIM

    # 1순위: Hugging Face transformers
    try:
        model, tokenizer = _load_esm2_transformers(args.model_name)
        print("[ESM-2] transformers 백엔드 사용", file=sys.stderr)
        embedding = _extract_embedding_transformers(
            model, tokenizer, args.sequence, args.layer
        )
        dim = len(embedding)
        print(f"[ESM-2] 임베딩 추출 완료 (dim={dim})", file=sys.stderr)
    except Exception as exc:
        print(
            f"[ESM-2] transformers 실패: {exc}. esm 패키지 시도...",
            file=sys.stderr,
        )

        # 2순위: Meta AI esm 패키지
        try:
            model, alphabet = _load_esm2_meta(args.model_name)
            print("[ESM-2] esm 패키지 백엔드 사용", file=sys.stderr)
            embedding = _extract_embedding_meta(
                model, alphabet, args.sequence, args.layer
            )
            dim = len(embedding)
            print(f"[ESM-2] 임베딩 추출 완료 (dim={dim})", file=sys.stderr)
        except Exception as exc2:
            print(
                json.dumps(
                    {"error": f"ESM-2 임베딩 추출 실패 (transformers + esm 모두 실패): {exc2}"}
                ),
                flush=True,
            )
            sys.exit(1)

    if embedding is None:
        print(json.dumps({"error": "임베딩 추출 실패"}), flush=True)
        sys.exit(1)

    # numpy 배열로 저장 (선택적)
    try:
        import numpy as np

        npy_path = out_dir / "esm2_embedding.npy"
        np.save(str(npy_path), np.array(embedding, dtype=np.float32))
        print(f"[ESM-2] numpy 임베딩 저장: {npy_path}", file=sys.stderr)
    except ImportError:
        pass  # numpy 없으면 JSON만 출력

    print(json.dumps({"embedding": embedding, "dim": dim}), flush=True)


if __name__ == "__main__":
    main()
