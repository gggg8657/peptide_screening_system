#!/usr/bin/env python3
"""
align_subtypes.py
=================
SSTR1/3/4/5 → SSTR2(7XNA) 구조 정렬 스크립트.

PyMOL cealign 또는 biopython Bio.PDB Superimposer(CA 기반)를 사용하여
off-target 수용체 구조들을 SSTR2 기준 좌표계로 정렬한다.

Usage:
    # PyMOL (기본, cealign — 서열 비의존적 정렬):
    conda run -n bio-tools python align_subtypes.py \\
        --ref  data/somatostatin_receptor/SSTR2_7XNA.pdb \\
        --targets SSTR1 SSTR3 SSTR4 SSTR5 \\
        --data-dir data/somatostatin_receptor \\
        --method pymol

    # biopython (cealign 불가 시 CA-RMSD 기반):
    python align_subtypes.py \\
        --ref  data/somatostatin_receptor/SSTR2_7XNA.pdb \\
        --targets SSTR1 SSTR3 SSTR4 SSTR5 \\
        --method biopython

Output:
    data/somatostatin_receptor/SSTR{1,3,4,5}_aligned.pdb

수용체-PDB ID 매핑:
    SSTR1 → SSTR1_9IK8.pdb
    SSTR2 → SSTR2_7XNA.pdb  (기준)
    SSTR3 → SSTR3_8XIR.pdb
    SSTR4 → SSTR4_7XMT.pdb
    SSTR5 → SSTR5_8ZBJ.pdb
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 수용체 PDB 파일명 매핑
# ---------------------------------------------------------------------------

RECEPTOR_PDB_MAP: Dict[str, str] = {
    "SSTR1": "SSTR1_9IK8.pdb",
    "SSTR2": "SSTR2_7XNA.pdb",
    "SSTR3": "SSTR3_8XIR.pdb",
    "SSTR4": "SSTR4_7XMT.pdb",
    "SSTR5": "SSTR5_8ZBJ.pdb",
}


# ---------------------------------------------------------------------------
# PyMOL cealign 기반 정렬
# ---------------------------------------------------------------------------

def _align_with_pymol(
    ref_pdb: str,
    target_pdb: str,
    output_pdb: str,
    ref_name: str = "ref",
    target_name: str = "target",
) -> Dict[str, Any]:
    """PyMOL cealign을 사용하여 target을 ref에 정렬한다.

    Args:
        ref_pdb:     기준 구조 PDB 경로 (SSTR2)
        target_pdb:  정렬 대상 PDB 경로
        output_pdb:  정렬 결과 저장 경로
        ref_name:    PyMOL 내부 기준 구조 이름
        target_name: PyMOL 내부 대상 구조 이름

    Returns:
        {"rmsd": float, "aligned_atoms": int, "method": "cealign"}

    Raises:
        ImportError: PyMOL을 import할 수 없는 경우
        RuntimeError: cealign 실패
    """
    try:
        from pymol import cmd
    except ImportError as exc:
        raise ImportError(
            "PyMOL을 import할 수 없습니다. "
            "conda run -n bio-tools python align_subtypes.py 로 실행하세요."
        ) from exc

    # PyMOL 세션 초기화
    cmd.reinitialize()

    cmd.load(ref_pdb, ref_name)
    cmd.load(target_pdb, target_name)

    # cealign: 서열 비의존적 구조 정렬 (CE 알고리즘)
    result = cmd.cealign(target=ref_name, mobile=target_name)

    # 결과 저장
    Path(output_pdb).parent.mkdir(parents=True, exist_ok=True)
    cmd.save(output_pdb, target_name)

    rmsd = result.get("RMSD", result.get("rms", 0.0)) if isinstance(result, dict) else 0.0
    aligned = result.get("alignment_length", 0) if isinstance(result, dict) else 0

    print(
        f"[PyMOL cealign] {Path(target_pdb).name} → {Path(ref_pdb).name}: "
        f"RMSD={rmsd:.3f} Å, aligned={aligned} atoms → {output_pdb}",
        file=sys.stderr,
    )

    cmd.delete("all")

    return {"rmsd": round(float(rmsd), 3), "aligned_atoms": aligned, "method": "cealign"}


# ---------------------------------------------------------------------------
# biopython Superimposer 기반 정렬 (폴백)
# ---------------------------------------------------------------------------

def _align_with_biopython(
    ref_pdb: str,
    target_pdb: str,
    output_pdb: str,
) -> Dict[str, Any]:
    """biopython Superimposer(CA 기반)로 target을 ref에 정렬한다.

    공통 잔기 번호의 CA 원자를 기반으로 회전/이동 행렬을 계산한다.
    서열 길이가 다를 수 있으므로 공통 잔기 번호 교집합만 사용한다.

    Args:
        ref_pdb:    기준 구조 PDB 경로
        target_pdb: 정렬 대상 PDB 경로
        output_pdb: 결과 저장 경로

    Returns:
        {"rmsd": float, "aligned_atoms": int, "method": "biopython_superimposer"}

    Raises:
        ImportError: biopython 없는 경우
        ValueError: 공통 CA 잔기가 10개 미만인 경우
    """
    try:
        from Bio.PDB import PDBParser, PDBIO, Superimposer
        import numpy as np
    except ImportError as exc:
        raise ImportError(
            "biopython 또는 numpy를 import할 수 없습니다. "
            "pip install biopython numpy 또는 conda install biopython numpy"
        ) from exc

    parser = PDBParser(QUIET=True)

    ref_struct = parser.get_structure("ref", ref_pdb)
    tgt_struct = parser.get_structure("target", target_pdb)

    # 가장 긴 체인의 CA 원자 수집
    def _get_ca_atoms(structure):
        chains = sorted(structure.get_chains(), key=lambda c: len(list(c.get_residues())), reverse=True)
        best_chain = chains[0]
        ca_by_resnum = {}
        for residue in best_chain.get_residues():
            resnum = residue.get_id()[1]
            if "CA" in residue:
                ca_by_resnum[resnum] = residue["CA"]
        return ca_by_resnum

    ref_cas = _get_ca_atoms(ref_struct)
    tgt_cas = _get_ca_atoms(tgt_struct)

    # 공통 잔기 번호 교집합
    common_resnums = sorted(set(ref_cas.keys()) & set(tgt_cas.keys()))
    if len(common_resnums) < 10:
        raise ValueError(
            f"공통 CA 잔기가 너무 적습니다 ({len(common_resnums)}개). "
            f"ref={len(ref_cas)}, target={len(tgt_cas)}"
        )

    ref_atoms = [ref_cas[r] for r in common_resnums]
    tgt_atoms = [tgt_cas[r] for r in common_resnums]

    # Superimposer: target 구조를 ref에 정렬
    sup = Superimposer()
    sup.set_atoms(ref_atoms, tgt_atoms)
    sup.apply(list(tgt_struct.get_atoms()))

    rmsd = sup.rms
    n_aligned = len(common_resnums)

    # 결과 저장
    Path(output_pdb).parent.mkdir(parents=True, exist_ok=True)
    io = PDBIO()
    io.set_structure(tgt_struct)
    io.save(output_pdb)

    print(
        f"[biopython] {Path(target_pdb).name} → {Path(ref_pdb).name}: "
        f"RMSD={rmsd:.3f} Å, aligned={n_aligned} CA atoms → {output_pdb}",
        file=sys.stderr,
    )

    return {"rmsd": round(float(rmsd), 3), "aligned_atoms": n_aligned, "method": "biopython_superimposer"}


# ---------------------------------------------------------------------------
# 단일 수용체 정렬
# ---------------------------------------------------------------------------

def align_receptor(
    ref_pdb: str,
    target_pdb: str,
    output_pdb: str,
    method: str = "pymol",
) -> Dict[str, Any]:
    """수용체 구조를 ref에 정렬하고 결과 딕셔너리를 반환한다.

    method 우선순위:
        1. "pymol" — cealign (서열 비의존적, 권장)
        2. "biopython" — CA-RMSD Superimposer (폴백)
        3. "auto" — pymol 시도 후 실패 시 biopython

    Args:
        ref_pdb:    기준 구조 PDB 경로 (SSTR2_7XNA.pdb)
        target_pdb: 정렬 대상 PDB 경로
        output_pdb: 정렬 결과 저장 경로
        method:     "pymol", "biopython", 또는 "auto"

    Returns:
        {"rmsd": float, "aligned_atoms": int, "method": str,
         "input": str, "output": str}

    Raises:
        RuntimeError: 모든 정렬 방법 실패 시
    """
    if method in ("pymol", "auto"):
        try:
            result = _align_with_pymol(ref_pdb, target_pdb, output_pdb)
            result.update({"input": target_pdb, "output": output_pdb})
            return result
        except (ImportError, Exception) as exc:
            if method == "pymol":
                raise RuntimeError(f"PyMOL cealign 실패: {exc}") from exc
            print(
                f"[경고] PyMOL 실패 ({exc}), biopython으로 폴백합니다.",
                file=sys.stderr,
            )

    # biopython 폴백
    result = _align_with_biopython(ref_pdb, target_pdb, output_pdb)
    result.update({"input": target_pdb, "output": output_pdb})
    return result


# ---------------------------------------------------------------------------
# 배치 정렬
# ---------------------------------------------------------------------------

def align_all_subtypes(
    ref_pdb: str,
    data_dir: str,
    targets: Optional[List[str]] = None,
    method: str = "auto",
    output_dir: Optional[str] = None,
    summary_path: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """SSTR1/3/4/5를 SSTR2에 정렬하고 결과 요약을 반환한다.

    Args:
        ref_pdb:      기준 구조 PDB 경로 (SSTR2_7XNA.pdb)
        data_dir:     SSTR PDB 파일이 위치한 디렉토리
        targets:      정렬할 수용체 이름 목록. None이면 ["SSTR1","SSTR3","SSTR4","SSTR5"]
        method:       "pymol", "biopython", 또는 "auto"
        output_dir:   정렬 결과 PDB 저장 디렉토리. None이면 data_dir 사용.
        summary_path: 결과 요약 JSON 저장 경로. None이면 저장 안 함.

    Returns:
        {"SSTR1": {...}, "SSTR3": {...}, ...}  — 각 수용체별 정렬 결과
    """
    if targets is None:
        targets = ["SSTR1", "SSTR3", "SSTR4", "SSTR5"]

    data_path = Path(data_dir)
    out_path = Path(output_dir) if output_dir else data_path

    results: Dict[str, Dict[str, Any]] = {}

    for receptor_name in targets:
        pdb_filename = RECEPTOR_PDB_MAP.get(receptor_name)
        if pdb_filename is None:
            print(
                f"[경고] {receptor_name} 매핑 없음 — 건너뜀",
                file=sys.stderr,
            )
            results[receptor_name] = {"error": f"PDB 매핑 없음: {receptor_name}"}
            continue

        target_pdb = str(data_path / pdb_filename)
        if not Path(target_pdb).exists():
            print(
                f"[경고] {target_pdb} 없음 — 건너뜀",
                file=sys.stderr,
            )
            results[receptor_name] = {"error": f"파일 없음: {target_pdb}"}
            continue

        output_pdb = str(out_path / f"{receptor_name}_aligned.pdb")

        try:
            align_result = align_receptor(
                ref_pdb=ref_pdb,
                target_pdb=target_pdb,
                output_pdb=output_pdb,
                method=method,
            )
            results[receptor_name] = align_result
            print(
                f"[align_all_subtypes] {receptor_name}: "
                f"RMSD={align_result['rmsd']:.3f} Å, "
                f"method={align_result['method']}",
                file=sys.stderr,
            )
        except Exception as exc:
            print(
                f"[오류] {receptor_name} 정렬 실패: {exc}",
                file=sys.stderr,
            )
            results[receptor_name] = {"error": str(exc)}

    # 요약 JSON 저장
    if summary_path:
        summary = {
            "ref_pdb": str(ref_pdb),
            "method": method,
            "results": results,
        }
        out_summary = Path(summary_path)
        out_summary.parent.mkdir(parents=True, exist_ok=True)
        with open(out_summary, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2, ensure_ascii=False)
        print(f"[align_all_subtypes] 요약 저장: {out_summary}", file=sys.stderr)

    return results


# ---------------------------------------------------------------------------
# CLI 엔트리포인트
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "SSTR1/3/4/5 → SSTR2(7XNA) 구조 정렬 (PyMOL cealign 또는 biopython)"
        )
    )
    parser.add_argument(
        "--ref",
        default="data/somatostatin_receptor/SSTR2_7XNA.pdb",
        help="기준 구조 PDB 경로 (기본: SSTR2_7XNA.pdb)",
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        default=["SSTR1", "SSTR3", "SSTR4", "SSTR5"],
        help="정렬할 수용체 이름 (기본: SSTR1 SSTR3 SSTR4 SSTR5)",
    )
    parser.add_argument(
        "--data-dir",
        default="data/somatostatin_receptor",
        help="SSTR PDB 파일 디렉토리 (기본: data/somatostatin_receptor)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="정렬 결과 PDB 저장 디렉토리 (기본: --data-dir와 동일)",
    )
    parser.add_argument(
        "--method",
        choices=["pymol", "biopython", "auto"],
        default="auto",
        help="정렬 방법: pymol(cealign), biopython(CA-RMSD), auto(pymol→biopython 폴백)",
    )
    parser.add_argument(
        "--summary",
        default=None,
        help="결과 요약 JSON 저장 경로 (선택)",
    )
    args = parser.parse_args()

    results = align_all_subtypes(
        ref_pdb=args.ref,
        data_dir=args.data_dir,
        targets=args.targets,
        method=args.method,
        output_dir=args.output_dir,
        summary_path=args.summary,
    )

    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
