#!/usr/bin/env python
"""
run_esmfold.py
==============
ESMFold 로컬 실행 래퍼.

ESMFold 모델을 로드하여 단일 서열의 구조를 예측한다.
step04_qc.py의 predict_and_evaluate()가 기대하는 PDB 포맷(B-factor에 pLDDT)을 그대로 출력한다.

Output JSON:
    {"pdb": "<pdb_text>", "mean_plddt": 0.85}
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
from typing import Optional

# 불필요한 경고 억제
warnings.filterwarnings("ignore")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ESMFold 로컬 실행 래퍼 — stdout에 JSON 출력"
    )
    parser.add_argument(
        "--sequence", required=False, help="예측할 아미노산 서열 (1문자 코드)"
    )
    parser.add_argument("--output-dir", required=False, default="/tmp", help="출력 파일 저장 디렉토리")
    parser.add_argument("--input-json", required=False, help="JSON payload 파일 경로")
    args = parser.parse_args()

    # batch_sequences: 배치 모드 시 [{"seq_id": ..., "sequence": ...}, ...] 저장
    args.batch_sequences = None

    # --input-json이 주어지면 payload에서 sequence 또는 sequences 추출
    if args.input_json and not args.sequence:
        with open(args.input_json) as f:
            payload = json.load(f)
        if "sequences" in payload:
            # 배치 모드: sequences 배열이 있으면 단일 모드 검사 스킵
            args.batch_sequences = payload["sequences"]
        else:
            args.sequence = payload.get("sequence", "")
        if not args.output_dir or args.output_dir == "/tmp":
            args.output_dir = str(Path(args.input_json).parent)

    if not args.sequence and args.batch_sequences is None:
        parser.error("--sequence, --input-json(sequence 키), 또는 --input-json(sequences 배열) 중 하나를 지정해야 합니다.")

    return args


def _extract_mean_plddt_from_pdb(pdb_text: str) -> float:
    """PDB ATOM 레코드의 B-factor 컬럼(60-66)에서 평균 pLDDT를 계산한다.

    ESMFold (HuggingFace transformers)는 B-factor를 0-1 스케일로 저장한다.
    0-100 스케일로 정규화해 반환한다.
    """
    values = []
    for line in pdb_text.splitlines():
        if not line.startswith("ATOM"):
            continue
        try:
            b_factor = float(line[60:66].strip())
            values.append(b_factor)
        except (ValueError, IndexError):
            continue
    if not values:
        return 0.0
    mean_val = sum(values) / len(values)
    # 0-1 스케일 감지 → 0-100 변환
    if mean_val <= 1.0:
        mean_val *= 100.0
    return mean_val


def _scale_pdb_bfactors(pdb_text: str) -> str:
    """PDB B-factor 컬럼을 0-1→0-100 스케일로 변환한다.

    ESMFold transformers 출력의 B-factor가 0-1 범위일 때만 적용.
    이미 0-100 범위면 그대로 반환.
    """
    lines = pdb_text.splitlines(keepends=True)
    atom_bfactors = []
    for line in lines:
        if line.startswith("ATOM") or line.startswith("HETATM"):
            try:
                atom_bfactors.append(float(line[60:66].strip()))
            except (ValueError, IndexError):
                pass
    if not atom_bfactors or max(atom_bfactors) > 1.0:
        return pdb_text  # 이미 0-100 스케일

    scaled_lines = []
    for line in lines:
        if (line.startswith("ATOM") or line.startswith("HETATM")) and len(line) >= 66:
            try:
                bfac = float(line[60:66].strip()) * 100.0
                scaled_line = line[:60] + f"{bfac:6.2f}" + line[66:]
                scaled_lines.append(scaled_line)
                continue
            except (ValueError, IndexError):
                pass
        scaled_lines.append(line)
    return "".join(scaled_lines)


def _load_esmfold_model():
    """ESMFold 모델을 로드하고 반환한다."""
    import torch

    # transformers 기반 ESMFold 로드
    try:
        from transformers import EsmForProteinFolding, AutoTokenizer

        print("[ESMFold] transformers 기반 ESMFold 로드 중...", file=sys.stderr)
        tokenizer = AutoTokenizer.from_pretrained("facebook/esmfold_v1")
        model = EsmForProteinFolding.from_pretrained(
            "facebook/esmfold_v1",
            low_cpu_mem_usage=True,
        )
        model = model.cuda() if torch.cuda.is_available() else model
        model.eval()
        return model, tokenizer, "transformers"
    except Exception as exc:
        print(
            f"[ESMFold] transformers 로드 실패: {exc}. esm 패키지 시도...",
            file=sys.stderr,
        )

    # esm 패키지 (Meta AI) 직접 사용 시도
    try:
        import esm

        print("[ESMFold] esm 패키지 기반 ESMFold 로드 중...", file=sys.stderr)
        model = esm.pretrained.esmfold_v1()
        model = model.cuda() if torch.cuda.is_available() else model
        model.eval()
        return model, None, "esm"
    except Exception as exc:
        raise RuntimeError(f"ESMFold 로드 실패 (transformers + esm 모두 실패): {exc}")


def _predict_structure_transformers(
    model, tokenizer, sequence: str
) -> str:
    """transformers ESMFold로 구조 예측 후 PDB 문자열 반환."""
    import torch

    tokenized = tokenizer(
        [sequence],
        return_tensors="pt",
        add_special_tokens=False,
    )
    if next(model.parameters()).is_cuda:
        tokenized = {k: v.cuda() for k, v in tokenized.items()}

    with torch.no_grad():
        output = model(**tokenized)

    # output.pdb_string이 없으면 convert_outputs_to_pdb 사용
    if hasattr(output, "pdb_string") and output.pdb_string:
        pdb_text = output.pdb_string[0]
    else:
        from transformers.models.esm.openfold_utils.protein import to_pdb, Protein

        # output을 PDB로 변환
        pdb_list = model.output_to_pdb(output)
        pdb_text = pdb_list[0]

    return pdb_text


def _predict_structure_esm(model, sequence: str) -> str:
    """esm 패키지 ESMFold로 구조 예측 후 PDB 문자열 반환."""
    import torch

    with torch.no_grad():
        output = model.infer_pdb(sequence)
    return output


def _predict_single(model, tokenizer, backend: str, sequence: str) -> str:
    """백엔드에 따라 단일 서열 구조 예측 후 PDB 문자열 반환."""
    if backend == "transformers":
        return _predict_structure_transformers(model, tokenizer, sequence)
    else:
        return _predict_structure_esm(model, sequence)


def main() -> None:
    args = _parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        model, tokenizer, backend = _load_esmfold_model()
        print(f"[ESMFold] 백엔드: {backend}", file=sys.stderr)
    except RuntimeError as exc:
        print(json.dumps({"error": str(exc)}), flush=True)
        sys.exit(1)

    # ── 배치 모드 ──────────────────────────────────────────────────────────
    if args.batch_sequences is not None:
        results = []
        total = len(args.batch_sequences)
        for i, entry in enumerate(args.batch_sequences, 1):
            seq_id = entry.get("seq_id", f"seq_{i}")
            sequence = entry.get("sequence", "")
            print(f"[ESMFold] 배치 {i}/{total}: {seq_id}", file=sys.stderr)
            try:
                pdb_text = _predict_single(model, tokenizer, backend, sequence)
                pdb_text = _scale_pdb_bfactors(pdb_text)
                mean_plddt = _extract_mean_plddt_from_pdb(pdb_text)
                results.append({
                    "seq_id": seq_id,
                    "pdb": pdb_text,
                    "mean_plddt": round(mean_plddt, 2),
                })
            except Exception as exc:
                print(f"[ESMFold] {seq_id} 예측 실패: {exc}", file=sys.stderr)
                results.append({
                    "seq_id": seq_id,
                    "pdb": "",
                    "mean_plddt": 0.0,
                    "error": str(exc),
                })
        print(json.dumps({"results": results}), flush=True)
        return

    # ── 단일 모드 (하위 호환) ───────────────────────────────────────────────
    try:
        pdb_text = _predict_single(model, tokenizer, backend, args.sequence)
        pdb_text = _scale_pdb_bfactors(pdb_text)
    except Exception as exc:
        print(
            json.dumps({"error": f"구조 예측 실패: {exc}"}), flush=True
        )
        sys.exit(1)

    # PDB 파일 저장 (선택적; caller가 필요 시 직접 파싱)
    pdb_path = out_dir / "esmfold_result.pdb"
    try:
        pdb_path.write_text(pdb_text, encoding="utf-8")
        print(f"[ESMFold] PDB 저장 완료: {pdb_path}", file=sys.stderr)
    except OSError as exc:
        print(f"[ESMFold] PDB 파일 저장 실패 (계속 진행): {exc}", file=sys.stderr)

    mean_plddt = _extract_mean_plddt_from_pdb(pdb_text)

    print(
        json.dumps({"pdb": pdb_text, "mean_plddt": round(mean_plddt, 2)}),
        flush=True,
    )


if __name__ == "__main__":
    main()
