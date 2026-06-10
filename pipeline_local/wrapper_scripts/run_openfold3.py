#!/usr/bin/env python
"""
run_openfold3.py
================
OpenFold3 로컬 실행 래퍼.

step01_receptor.py의 _call_openfold3()가 기대하는 PDB/mmCIF 출력을 반환한다.
OpenFold3 로컬 설치가 있으면 사용하고, 없으면 AlphaFold3 스타일 폴백을 시도한다.

입력 JSON 형식 (--query-json):
    {
        "sequences": [
            {"protein": {"id": "A", "sequence": "MKTLLLT..."}}
        ]
    }

Output JSON:
    {
        "mmcif": "<mmcif_content>",
        "confidence": {"pTM": 0.91, "ipTM": 0.85, "mean_plddt": 88.5}
    }
    또는 에러 시:
    {"error": "<message>"}
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

warnings.filterwarnings("ignore")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def _build_query_json_from_payload(
    payload: Dict[str, Any], output_dir: Path
) -> str:
    """JSON payload에서 OpenFold3 query JSON 파일을 생성하고 경로를 반환한다.

    payload 형식:
        {"sequence": "MKTLLLT...", "name": "SSTR2"}

    기존 query JSON 형식으로 변환한다:
        {"sequences": [{"protein": {"id": "A", "sequence": "..."}}]}
    """
    import tempfile

    sequence = payload.get("sequence", "")
    name = payload.get("name", "protein")

    query: Dict[str, Any] = {
        "name": name,
        "sequences": [
            {"protein": {"id": "A", "sequence": sequence}}
        ],
    }

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, dir=str(output_dir)
    )
    json.dump(query, tmp)
    tmp.flush()
    tmp.close()
    return tmp.name


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OpenFold3 로컬 실행 래퍼 — stdout에 JSON 출력"
    )
    parser.add_argument(
        "--input-json",
        default=None,
        help="JSON payload 파일 경로 (--query-json을 자동 생성하여 override)",
    )
    parser.add_argument(
        "--query-json",
        default=None,
        help="입력 JSON 파일 경로 (sequences 배열 포함)",
    )
    parser.add_argument("--output-dir", required=True, help="출력 파일 저장 디렉토리")
    args = parser.parse_args()

    if args.input_json:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(args.input_json) as f:
            payload = json.load(f)
        args.query_json = _build_query_json_from_payload(payload, out_dir)
    elif args.query_json is None:
        parser.error("--query-json 또는 --input-json 중 하나를 지정해야 합니다.")

    return args


def _load_query_json(query_json_path: str) -> Dict[str, Any]:
    """입력 JSON 파일을 파싱한다."""
    path = Path(query_json_path)
    if not path.exists():
        raise FileNotFoundError(f"입력 JSON 파일 없음: {query_json_path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_sequence_from_query(query: Dict[str, Any]) -> Optional[str]:
    """query JSON에서 첫 번째 단백질 서열을 추출한다."""
    for item in query.get("sequences", []):
        protein = item.get("protein", {})
        seq = protein.get("sequence", "")
        if seq:
            return seq
    return None


def _run_openfold3_subprocess(
    query_json_path: str, output_dir: Path
) -> None:
    """OpenFold3 로컬 설치를 subprocess로 실행한다.

    openfold3 predict <query_json> --output_dir <output_dir> 형식을 가정한다.
    실제 설치 방식에 따라 커맨드를 조정해야 할 수 있다.
    """
    # OpenFold3 CLI 탐색
    openfold3_cmd = None
    candidates = [
        "openfold3",                    # PATH에 설치된 경우
        str(Path(sys.prefix) / "bin" / "openfold3"),
        "python -m openfold3.predict",  # 패키지 모듈 실행
    ]
    for candidate in candidates:
        try:
            result = subprocess.run(
                candidate.split() + ["--help"],
                capture_output=True,
                timeout=10,
            )
            if result.returncode in (0, 1):  # --help는 일반적으로 0 또는 1 반환
                openfold3_cmd = candidate.split()
                break
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

    if openfold3_cmd is None:
        raise FileNotFoundError(
            "openfold3 CLI를 찾을 수 없음. OpenFold3가 conda 환경에 설치되어 있어야 합니다."
        )

    cmd = openfold3_cmd + [
        "predict",
        query_json_path,
        "--output_dir", str(output_dir),
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"OpenFold3 실행 실패 (exit {result.returncode})")


def _run_esmfold_mmcif_fallback(
    sequence: str, output_dir: Path
) -> str:
    """OpenFold3가 없을 때 ESMFold로 폴백하여 PDB → mmCIF 형식으로 반환한다.

    실제 mmCIF가 아닌 PDB 텍스트를 반환하지만,
    caller가 pdb 키와 mmcif 키를 모두 지원할 경우를 위한 폴백이다.
    """
    import torch
    import warnings

    warnings.filterwarnings("ignore")

    try:
        from transformers import EsmForProteinFolding, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained("facebook/esmfold_v1")
        model = EsmForProteinFolding.from_pretrained(
            "facebook/esmfold_v1", low_cpu_mem_usage=True
        )
        model = model.cuda() if torch.cuda.is_available() else model
        model.eval()

        tokenized = tokenizer(
            [sequence], return_tensors="pt", add_special_tokens=False
        )
        if next(model.parameters()).is_cuda:
            tokenized = {k: v.cuda() for k, v in tokenized.items()}

        with torch.no_grad():
            output = model(**tokenized)

        pdb_list = model.output_to_pdb(output)
        return pdb_list[0]

    except Exception as exc:
        raise RuntimeError(f"ESMFold 폴백 실패: {exc}")


def _find_mmcif_output(output_dir: Path) -> Optional[str]:
    """출력 디렉토리에서 mmCIF 또는 CIF 파일을 찾는다."""
    for ext in ("*.cif", "*.mmcif"):
        candidates = sorted(glob.glob(str(output_dir / "**" / ext), recursive=True))
        if candidates:
            print(f"[OpenFold3] mmCIF 발견: {candidates[0]}", file=sys.stderr)
            return Path(candidates[0]).read_text(encoding="utf-8")
    return None


def _parse_confidence(output_dir: Path) -> Dict[str, Any]:
    """OpenFold3 출력 디렉토리에서 신뢰도 지표를 파싱한다."""
    # confidence JSON 파일 탐색
    for pattern in ("*confidence*.json", "*scores*.json", "ranking_debug.json"):
        candidates = sorted(
            glob.glob(str(output_dir / "**" / pattern), recursive=True)
        )
        if candidates:
            try:
                raw = json.loads(Path(candidates[0]).read_text(encoding="utf-8"))
                return {
                    "pTM": raw.get("ptm", raw.get("pTM", 0.0)),
                    "ipTM": raw.get("iptm", raw.get("ipTM", 0.0)),
                    "mean_plddt": raw.get(
                        "mean_plddt",
                        raw.get("plddt", 0.0) if isinstance(raw.get("plddt"), float) else 0.0,
                    ),
                    "raw": raw,
                }
            except Exception:
                pass
    return {}


def main() -> None:
    args = _parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 입력 JSON 파싱
    try:
        query = _load_query_json(args.query_json)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": f"입력 JSON 파싱 실패: {exc}"}), flush=True)
        sys.exit(1)

    # OpenFold3 실행 시도
    mmcif_content: Optional[str] = None
    confidence: Dict[str, Any] = {}

    try:
        _run_openfold3_subprocess(
            query_json_path=str(Path(args.query_json).resolve()),
            output_dir=out_dir,
        )
        print("[OpenFold3] 예측 완료", file=sys.stderr)
        mmcif_content = _find_mmcif_output(out_dir)
        confidence = _parse_confidence(out_dir)
    except (FileNotFoundError, RuntimeError) as exc:
        print(
            f"[OpenFold3] 실행 실패: {exc}. ESMFold 폴백 사용...",
            file=sys.stderr,
        )

        # ESMFold 폴백
        sequence = _extract_sequence_from_query(query)
        if not sequence:
            print(
                json.dumps({"error": "입력 JSON에서 단백질 서열을 찾을 수 없음"}),
                flush=True,
            )
            sys.exit(1)

        try:
            mmcif_content = _run_esmfold_mmcif_fallback(sequence, out_dir)
            print("[ESMFold 폴백] 예측 완료", file=sys.stderr)
        except RuntimeError as exc2:
            print(
                json.dumps({"error": f"OpenFold3 및 ESMFold 폴백 모두 실패: {exc2}"}),
                flush=True,
            )
            sys.exit(1)

    if mmcif_content is None:
        print(
            json.dumps({"error": "출력 mmCIF 파일을 찾을 수 없음"}),
            flush=True,
        )
        sys.exit(1)

    # 출력 파일 저장
    out_file = out_dir / "structure.cif"
    try:
        out_file.write_text(mmcif_content, encoding="utf-8")
        print(f"[OpenFold3] 구조 파일 저장: {out_file}", file=sys.stderr)
    except OSError as exc:
        print(f"[OpenFold3] 파일 저장 실패 (계속 진행): {exc}", file=sys.stderr)

    print(
        json.dumps({"mmcif": mmcif_content, "confidence": confidence}),
        flush=True,
    )


if __name__ == "__main__":
    main()
