#!/usr/bin/env python
"""
run_boltz.py
============
Boltz 로컬 실행 래퍼.

`boltz predict` CLI를 subprocess로 호출한다.
step05_docking.py의 predict_with_boltz2()가 기대하는 형식으로 결과를 반환한다.

입력 YAML 형식 (--input-yaml):
    sequences:
      - protein:
          id: A
          sequence: "MKTLLLTLVVVTIVCLDLGYT..."
      - protein:
          id: B
          sequence: "CFWKTCT..."

Output JSON:
    {
        "structure_cif": "<cif_content>",
        "confidence": {
            "affinity_kcal_mol": -8.5,
            "ipTM": 0.82,
            "pTM": 0.91
        }
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
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# 3-letter → 1-letter 아미노산 코드 매핑
_AA3TO1 = {
    "ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F",
    "GLY": "G", "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L",
    "MET": "M", "ASN": "N", "PRO": "P", "GLN": "Q", "ARG": "R",
    "SER": "S", "THR": "T", "VAL": "V", "TRP": "W", "TYR": "Y",
}


def _extract_sequence_from_pdb(pdb_text: str) -> str:
    """PDB 텍스트에서 첫 번째 체인의 아미노산 서열을 추출한다."""
    residues: list[tuple[int, str]] = []
    seen: set[int] = set()
    for line in pdb_text.splitlines():
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            resname = line[17:20].strip()
            resnum = int(line[22:26].strip())
            if resnum not in seen and resname in _AA3TO1:
                seen.add(resnum)
                residues.append((resnum, _AA3TO1[resname]))
    residues.sort()
    return "".join(aa for _, aa in residues)


def _build_boltz_yaml_from_payload(payload: Dict[str, Any], output_dir: Path) -> str:
    """JSON payload에서 Boltz YAML 입력 파일을 생성하고 경로를 반환한다.

    payload 형식:
        {"sequences": [...], "receptor_pdb": "...", "peptide_sequence": "..."}

    sequences 키가 있으면 그대로 사용하고,
    없으면 receptor_pdb + peptide_sequence로 구성한다.
    """
    lines: list[str] = ["version: 1", "sequences:"]

    sequences = payload.get("sequences")
    if sequences:
        for entry in sequences:
            if isinstance(entry, dict):
                protein = entry.get("protein", {})
                chain_id = protein.get("id", "A")
                seq = protein.get("sequence", "")
                lines.append(f"  - protein:")
                lines.append(f"      id: {chain_id}")
                lines.append(f'      sequence: "{seq}"')
                lines.append(f'      msa: "empty"')  # single-sequence 모드 (완전 로컬)
    else:
        receptor_pdb_text = payload.get("receptor_pdb", "")
        receptor_sequence = payload.get("receptor_sequence", "")
        peptide_sequence = payload.get("peptide_sequence", "")

        # receptor: 서열이 있으면 sequence 모드, 없으면 PDB에서 서열 추출
        if receptor_pdb_text and not receptor_sequence:
            receptor_sequence = _extract_sequence_from_pdb(receptor_pdb_text)

        if receptor_sequence:
            lines.append(f"  - protein:")
            lines.append(f"      id: A")
            lines.append(f'      sequence: "{receptor_sequence}"')
            lines.append(f'      msa: "empty"')

        if peptide_sequence:
            lines.append(f"  - protein:")
            lines.append(f"      id: B")
            lines.append(f'      sequence: "{peptide_sequence}"')
            lines.append(f'      msa: "empty"')

    yaml_text = "\n".join(lines) + "\n"
    yaml_tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=str(output_dir)
    )
    yaml_tmp.write(yaml_text)
    yaml_tmp.flush()
    yaml_tmp.close()
    return yaml_tmp.name


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Boltz 로컬 실행 래퍼 — stdout에 JSON 출력"
    )
    parser.add_argument(
        "--input-json",
        default=None,
        help="JSON payload 파일 경로 (--input-yaml을 자동 생성하여 override)",
    )
    parser.add_argument(
        "--input-yaml", default=None, help="Boltz 입력 YAML 파일 경로"
    )
    parser.add_argument("--output-dir", required=True, help="출력 파일 저장 디렉토리")
    args = parser.parse_args()

    if args.input_json:
        # output_dir가 있어야 임시 YAML을 그 안에 생성할 수 있음
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(args.input_json) as f:
            payload = json.load(f)
        args.input_yaml = _build_boltz_yaml_from_payload(payload, out_dir)
    elif args.input_yaml is None:
        parser.error("--input-yaml 또는 --input-json 중 하나를 지정해야 합니다.")

    return args


def _run_boltz_predict(input_yaml: str, output_dir: Path) -> Path:
    """boltz predict CLI를 실행하고 출력 디렉토리를 반환한다.

    Single-sequence 모드 (msa: "empty") + --no_kernels 로 완전 로컬 실행.
    cuequivariance 커널 없이도 동작하며, MSA 서버 불필요.
    """
    cmd = [
        "boltz",
        "predict",
        input_yaml,
        "--out_dir", str(output_dir),
        "--override",           # 기존 결과 덮어쓰기
        "--no_kernels",         # cuequivariance 커널 비활성화 (호환성)
        "--num_workers", "0",   # DataLoader 직렬 (안정성)
    ]
    print("[Boltz] 완전 로컬 모드 (single-seq, no_kernels)", file=sys.stderr)

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True,
        )
    except FileNotFoundError:
        raise RuntimeError("boltz CLI를 찾을 수 없음. 'pip install boltz' 또는 conda install boltz 로 설치 필요.")

    if result.returncode != 0:
        raise RuntimeError(f"boltz predict 실패 (exit {result.returncode})")

    return output_dir


def _find_output_cif(output_dir: Path) -> Optional[str]:
    """Boltz 출력 디렉토리에서 CIF 파일을 찾아 내용을 반환한다.

    boltz predict 출력 구조:
        <output_dir>/
          predictions/
            <input_name>/
              <input_name>_model_0.cif
              confidence_<input_name>_model_0.json
    """
    # CIF 파일 탐색 (predictions 하위 디렉토리 포함)
    cif_candidates = sorted(
        glob.glob(str(output_dir / "**" / "*.cif"), recursive=True)
    )
    if not cif_candidates:
        return None

    # 첫 번째(best) CIF 사용
    cif_path = Path(cif_candidates[0])
    print(f"[Boltz] CIF 파일 발견: {cif_path}", file=sys.stderr)
    return cif_path.read_text(encoding="utf-8")


def _parse_confidence_json(output_dir: Path) -> Dict[str, Any]:
    """Boltz confidence JSON 파일에서 신뢰도 지표를 파싱한다.

    boltz는 confidence_<name>_model_0.json 파일을 출력하며
    ptm, iptm, affinity 등을 포함한다.
    """
    json_candidates = sorted(
        glob.glob(str(output_dir / "**" / "confidence_*.json"), recursive=True)
    )
    if not json_candidates:
        return {}

    conf_path = Path(json_candidates[0])
    print(f"[Boltz] confidence JSON 발견: {conf_path}", file=sys.stderr)
    try:
        raw = json.loads(conf_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[Boltz] confidence JSON 파싱 실패: {exc}", file=sys.stderr)
        return {}

    # 키 정규화: boltz 출력 키를 통일된 형식으로 변환
    confidence: Dict[str, Any] = {}
    confidence["pTM"] = raw.get("ptm", raw.get("pTM", 0.0))
    confidence["ipTM"] = raw.get("iptm", raw.get("ipTM", 0.0))
    # boltz2는 binding affinity를 별도 키로 제공할 수 있음
    affinity = raw.get("affinity_kcal_mol", raw.get("binding_affinity", None))
    if affinity is not None:
        confidence["affinity_kcal_mol"] = float(affinity)
    # 전체 raw 데이터도 포함
    confidence["raw"] = raw

    return confidence


def main() -> None:
    args = _parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    input_yaml = str(Path(args.input_yaml).resolve())

    try:
        _run_boltz_predict(input_yaml=input_yaml, output_dir=out_dir)
        print("[Boltz] 예측 완료", file=sys.stderr)
    except RuntimeError as exc:
        print(json.dumps({"error": str(exc)}), flush=True)
        sys.exit(1)

    # 출력 수집
    cif_content = _find_output_cif(out_dir)
    if cif_content is None:
        print(
            json.dumps({"error": "Boltz 출력 CIF 파일을 찾을 수 없음"}),
            flush=True,
        )
        sys.exit(1)

    confidence = _parse_confidence_json(out_dir)

    print(
        json.dumps({"structure_cif": cif_content, "confidence": confidence}),
        flush=True,
    )


if __name__ == "__main__":
    main()
