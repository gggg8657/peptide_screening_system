#!/usr/bin/env python3
"""
compute_docking_rmsd.py
=======================
도킹 포즈와 참조 구조 사이의 Cα RMSD 계산 스크립트.

BioPython Superimposer를 사용하여 예측 PDB와 참조 PDB 간
공통 잔기의 Cα 원자만 선택해 RMSD를 계산한다.

사용법 (CLI):
    python pipeline_local/scripts/compute_docking_rmsd.py \
        --pred pose_000.pdb \
        --ref  ref_complex.pdb \
        --chain A          # 펩타이드 체인 ID (기본 A)

    # 포즈 디렉터리 일괄 처리
    python pipeline_local/scripts/compute_docking_rmsd.py \
        --pred-dir poses/ \
        --ref ref_complex.pdb \
        --chain A

출력:
    JSON으로 RMSD, 매칭 잔기 수 등 출력 (stdout)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

try:
    from Bio import PDB
    from Bio.PDB import Superimposer
except ImportError as exc:
    print(f"[ERROR] biopython required: pip install biopython ({exc})", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Core RMSD calculation
# ---------------------------------------------------------------------------


def _extract_ca_atoms(
    structure_path: str | Path,
    chain_id: Optional[str] = None,
) -> Tuple[List, List[int]]:
    """
    PDB 파일에서 Cα 원자 리스트와 잔기 번호 리스트를 추출한다.

    Parameters
    ----------
    structure_path : str or Path
        PDB 파일 경로
    chain_id : str, optional
        추출할 체인 ID. None이면 첫 번째 체인 사용.

    Returns
    -------
    ca_atoms : list of Bio.PDB.Atom.Atom
        Cα 원자 리스트
    residue_ids : list of int
        잔기 번호 리스트 (ca_atoms와 1:1 대응)
    """
    parser = PDB.PDBParser(QUIET=True)
    structure = parser.get_structure("struct", str(structure_path))
    model = structure[0]

    if chain_id is None:
        # 첫 번째 체인 자동 선택
        chains = list(model.get_chains())
        if not chains:
            return [], []
        chain_id = chains[0].id

    if chain_id not in model:
        raise ValueError(
            f"Chain '{chain_id}' not found in {structure_path}. "
            f"Available: {[ch.id for ch in model.get_chains()]}"
        )

    ca_atoms: List = []
    residue_ids: List[int] = []

    for residue in model[chain_id].get_residues():
        # 표준 아미노산만 처리 (HETATM 제외)
        if residue.get_id()[0] != " ":
            continue
        if "CA" in residue:
            ca_atoms.append(residue["CA"])
            residue_ids.append(residue.get_id()[1])

    return ca_atoms, residue_ids


def compute_ca_rmsd(
    pred_pdb: str | Path,
    ref_pdb: str | Path,
    pred_chain: Optional[str] = None,
    ref_chain: Optional[str] = None,
    align: bool = True,
) -> dict:
    """
    예측 PDB와 참조 PDB 사이의 Cα RMSD를 계산한다.

    공통 잔기 번호를 기준으로 매칭하며, 잔기 수 불일치 시
    공통 잔기만 사용한다.

    Parameters
    ----------
    pred_pdb : str or Path
        예측 도킹 포즈 PDB 경로
    ref_pdb : str or Path
        참조 구조 PDB 경로
    pred_chain : str, optional
        예측 구조의 펩타이드 체인 ID
    ref_chain : str, optional
        참조 구조의 펩타이드 체인 ID
    align : bool
        True이면 Superimposer로 최적 정렬 후 RMSD 계산 (aligned RMSD).
        False이면 정렬 없이 위치 차이 RMSD.

    Returns
    -------
    dict with keys:
        rmsd_angstrom : float
        n_ca_matched : int
        pred_pdb : str
        ref_pdb : str
        pred_chain : str
        ref_chain : str
        aligned : bool
        warning : str or None
    """
    pred_cas, pred_ids = _extract_ca_atoms(pred_pdb, pred_chain)
    ref_cas, ref_ids = _extract_ca_atoms(ref_pdb, ref_chain)

    if not pred_cas:
        raise ValueError(f"No Cα atoms found in predicted PDB: {pred_pdb}")
    if not ref_cas:
        raise ValueError(f"No Cα atoms found in reference PDB: {ref_pdb}")

    # 공통 잔기 번호 매칭
    pred_by_id = {rid: atom for rid, atom in zip(pred_ids, pred_cas)}
    ref_by_id = {rid: atom for rid, atom in zip(ref_ids, ref_cas)}
    common_ids = sorted(set(pred_by_id.keys()) & set(ref_by_id.keys()))

    warning: Optional[str] = None
    if len(common_ids) < len(ref_ids):
        warning = (
            f"Residue mismatch: pred has {len(pred_ids)}, ref has {len(ref_ids)}, "
            f"using {len(common_ids)} common residues."
        )

    if not common_ids:
        raise ValueError(
            f"No common residues between {pred_pdb} (chain={pred_chain}) "
            f"and {ref_pdb} (chain={ref_chain})"
        )

    pred_atoms_matched = [pred_by_id[rid] for rid in common_ids]
    ref_atoms_matched = [ref_by_id[rid] for rid in common_ids]

    if align:
        sup = Superimposer()
        sup.set_atoms(ref_atoms_matched, pred_atoms_matched)
        rmsd = float(sup.rms)
    else:
        # 정렬 없이 직접 거리 계산
        diffs = np.array(
            [pred_by_id[rid].get_vector().get_array() - ref_by_id[rid].get_vector().get_array()
             for rid in common_ids]
        )
        rmsd = float(np.sqrt(np.mean(np.sum(diffs ** 2, axis=1))))

    return {
        "rmsd_angstrom": round(rmsd, 4),
        "n_ca_matched": len(common_ids),
        "pred_pdb": str(pred_pdb),
        "ref_pdb": str(ref_pdb),
        "pred_chain": pred_chain,
        "ref_chain": ref_chain,
        "aligned": align,
        "warning": warning,
    }


def compute_rmsd_batch(
    pred_pdbs: List[str | Path],
    ref_pdb: str | Path,
    pred_chain: Optional[str] = None,
    ref_chain: Optional[str] = None,
    rmsd_threshold: float = 2.0,
) -> dict:
    """
    여러 예측 포즈에 대해 RMSD를 일괄 계산하고 통계를 반환한다.

    Parameters
    ----------
    pred_pdbs : list
        예측 PDB 파일 경로 리스트
    ref_pdb : str or Path
        참조 구조 PDB 경로
    pred_chain : str, optional
        예측 포즈 펩타이드 체인 ID
    ref_chain : str, optional
        참조 구조 펩타이드 체인 ID
    rmsd_threshold : float
        성공 판정 기준 RMSD (Å), 기본값 2.0

    Returns
    -------
    dict with keys:
        results : list of per-pose dicts
        rmsd_success_rate : float  (0~1)
        n_success : int
        n_total : int
        rmsd_min : float
        rmsd_max : float
        rmsd_mean : float
        rmsd_threshold_angstrom : float
    """
    results = []
    for pdb in pred_pdbs:
        try:
            r = compute_ca_rmsd(pdb, ref_pdb, pred_chain=pred_chain, ref_chain=ref_chain)
        except Exception as exc:
            r = {
                "rmsd_angstrom": None,
                "n_ca_matched": 0,
                "pred_pdb": str(pdb),
                "ref_pdb": str(ref_pdb),
                "error": str(exc),
            }
        results.append(r)

    valid_rmsds = [r["rmsd_angstrom"] for r in results if r.get("rmsd_angstrom") is not None]
    n_success = sum(1 for v in valid_rmsds if v <= rmsd_threshold)
    n_total = len(results)

    return {
        "results": results,
        "rmsd_success_rate": round(n_success / n_total, 4) if n_total else 0.0,
        "n_success": n_success,
        "n_total": n_total,
        "rmsd_min": round(min(valid_rmsds), 4) if valid_rmsds else None,
        "rmsd_max": round(max(valid_rmsds), 4) if valid_rmsds else None,
        "rmsd_mean": round(float(np.mean(valid_rmsds)), 4) if valid_rmsds else None,
        "rmsd_threshold_angstrom": rmsd_threshold,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Cα RMSD calculation for docking pose evaluation"
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--pred", type=Path, help="Single predicted PDB file")
    group.add_argument("--pred-dir", type=Path, help="Directory of predicted PDB files")

    p.add_argument("--ref", type=Path, required=True, help="Reference PDB file")
    p.add_argument("--pred-chain", type=str, default=None, help="Peptide chain in pred PDB")
    p.add_argument("--ref-chain", type=str, default=None, help="Peptide chain in ref PDB")
    p.add_argument("--threshold", type=float, default=2.0, help="Success RMSD threshold (Å)")
    p.add_argument("--no-align", action="store_true", help="Skip superposition (raw RMSD)")
    return p


def main() -> None:
    args = build_parser().parse_args()

    if args.pred:
        result = compute_ca_rmsd(
            args.pred,
            args.ref,
            pred_chain=args.pred_chain,
            ref_chain=args.ref_chain,
            align=not args.no_align,
        )
        print(json.dumps(result, indent=2))
    else:
        pred_pdbs = sorted(args.pred_dir.glob("*.pdb"))
        if not pred_pdbs:
            print(f"[ERROR] No PDB files found in {args.pred_dir}", file=sys.stderr)
            sys.exit(1)
        result = compute_rmsd_batch(
            pred_pdbs,
            args.ref,
            pred_chain=args.pred_chain,
            ref_chain=args.ref_chain,
            rmsd_threshold=args.threshold,
        )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
