#!/usr/bin/env python3
"""
extract_binding_pocket.py
=========================
SSTR2(7XNA) 결합 포켓 중심 좌표 추출 스크립트.

핵심 잔기 (TM5: 205, 208, 209, 212 / TM6: 272, 273, 276, 279) CA 원자들의
기하학적 중심(centroid)과 반경을 계산하여 JSON 파일로 저장한다.

A-01 회의 결정: 결합 포켓 중심 = TM5(208,209) + TM6(272,273,276) 중심 좌표.
extract_pocket_center()가 이 표준 인터페이스를 구현한다.

Usage:
    python extract_binding_pocket.py \\
        --pdb data/somatostatin_receptor/SSTR2_7XNA.pdb \\
        --residues 208,209,272,273,276 \\
        --output data/somatostatin_receptor/binding_pocket_SSTR2.json

    python extract_binding_pocket.py \\
        --pdb data/somatostatin_receptor/SSTR2_7XNA.cif \\
        --residues 208,209,272,273,276 \\
        --output data/somatostatin_receptor/binding_pocket_SSTR2.json

Output (JSON):
    {
      "receptor":       "SSTR2_7XNA",
      "chain":          "A",
      "residues":       [205, 208, 209, 212, 272, 273, 276, 279],
      "residue_details": [...],
      "center_x":       float,
      "center_y":       float,
      "center_z":       float,
      "radius":         float,  # 포켓 잔기 최대 거리 (Å)
      "box_size":       30.0,   # AutoDock/GNINA 기본 박스 크기 (2×radius or min 30 Å)
      "gnina_config":   {...}   # GNINA/AutoDock-GPU 직접 사용 가능한 서브딕셔너리
    }

참고:
    - 잔기 번호는 SSTR2 7XNA PDB 파일 기준 (논문 서호성 박사 의견 §TM5/TM6 잔기표)
    - radius = max(CA 원자 → 중심 거리) + 5 Å 여유
    - GNINA/AutoDock-GPU: center_x/y/z, box_size 그대로 사용
    - BioPython 미설치 환경을 위해 numpy + 내장 PDB/CIF 파서 사용
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# 기본 핵심 잔기 (서호성 박사 의견, TM5/TM6 셀렉티비티 관련 잔기)
# ---------------------------------------------------------------------------
DEFAULT_KEY_RESIDUES: List[int] = [205, 208, 209, 212, 272, 273, 276, 279]

# 박스 여유 마진 (Å) — 포켓 최대 반경에 더함
_POCKET_MARGIN_ANG: float = 5.0

# 최소 박스 크기 (Å) — GNINA/AutoDock 권장 최솟값
_MIN_BOX_SIZE_ANG: float = 20.0

# 권장 박스 크기 (Å) — 표준 도킹 박스
_RECOMMENDED_BOX_SIZE_ANG: float = 30.0


# ---------------------------------------------------------------------------
# PDB 파서: CA 좌표 추출
# ---------------------------------------------------------------------------

def _parse_ca_coords(
    pdb_path: str,
    residues: List[int],
    chain: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """PDB 파일에서 지정 잔기의 CA 원자 좌표를 추출한다.

    Args:
        pdb_path: PDB 파일 경로
        residues: 추출할 잔기 번호 목록
        chain:    체인 ID (None이면 가장 긴 체인 자동 선택)

    Returns:
        [{"resnum": int, "resname": str, "chain": str,
          "x": float, "y": float, "z": float}, ...]

    Raises:
        ValueError: 요청 잔기 CA 원자를 하나도 찾지 못한 경우
    """
    target_set = set(residues)
    results: List[Dict[str, Any]] = []

    # chain=None이면 먼저 가장 긴 체인을 자동 감지
    if chain is None:
        chain = _detect_longest_chain(pdb_path)

    with open(pdb_path, "r", errors="replace") as fh:
        for line in fh:
            if not line.startswith("ATOM"):
                continue
            if len(line) < 54:
                continue
            atom_name = line[12:16].strip()
            if atom_name != "CA":
                continue
            chain_id = line[21]
            if chain is not None and chain_id != chain:
                continue
            try:
                resnum = int(line[22:26].strip())
            except ValueError:
                continue
            if resnum not in target_set:
                continue
            resname = line[17:20].strip()
            try:
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())
            except ValueError:
                continue
            results.append({
                "resnum": resnum,
                "resname": resname,
                "chain": chain_id,
                "x": x,
                "y": y,
                "z": z,
            })

    if not results:
        raise ValueError(
            f"PDB '{pdb_path}'에서 잔기 {residues} CA 원자를 찾지 못했습니다. "
            f"체인: {chain}"
        )
    return results


def _parse_all_atom_coords_cif(
    cif_path: str,
    residues: List[int],
    chain: Optional[str] = None,
) -> "np.ndarray":
    """mmCIF _atom_site 루프에서 지정 잔기의 heavy atom 좌표를 수집한다 (numpy 배열 반환).

    BioPython 없이 CIF를 직접 파싱한다.
    PDB 파일의 저자 잔기 번호와 맞추기 위해 auth_seq_id/auth_asym_id를 사용한다.

    Args:
        cif_path: CIF 파일 경로
        residues: 수집할 잔기 번호 목록
        chain:    체인 ID (None이면 모든 체인)

    Returns:
        shape (N, 3) numpy array. 원자가 없으면 shape (0, 3).
    """
    _THREE_TO_ONE_LOCAL = {
        "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
        "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
        "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
        "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
    }

    residue_set = set(residues)
    col_map: Dict[str, int] = {}
    in_loop = False
    col_idx = 0
    coords_list: List[Tuple[float, float, float]] = []

    with open(cif_path, "r", errors="replace") as f:
        for line in f:
            line = line.rstrip()
            if line.startswith("_atom_site."):
                field = line.split(".", 1)[1].strip()
                col_map[field] = col_idx
                col_idx += 1
                in_loop = True
                continue
            if in_loop:
                if line.startswith("_") or line.startswith("#") or not line:
                    if col_map:
                        in_loop = False
                        col_idx = 0
                        col_map = {}
                    continue
                parts = line.split()
                if not parts:
                    continue
                needed = {"group_PDB", "type_symbol", "label_alt_id", "label_comp_id",
                          "auth_asym_id", "auth_seq_id", "Cartn_x", "Cartn_y", "Cartn_z"}
                if not needed.issubset(col_map):
                    continue
                if len(parts) <= max(col_map[k] for k in needed):
                    continue
                group = parts[col_map["group_PDB"]]
                if group != "ATOM":
                    continue
                element = parts[col_map["type_symbol"]].upper()
                if element in {"H", "D"}:
                    continue
                altloc = parts[col_map["label_alt_id"]]
                if altloc not in (".", "?", "A"):
                    continue
                chain_id = parts[col_map["auth_asym_id"]]
                if chain is not None and chain_id != chain:
                    continue
                resname = parts[col_map["label_comp_id"]]
                if resname not in _THREE_TO_ONE_LOCAL:
                    continue
                try:
                    resseq = int(parts[col_map["auth_seq_id"]])
                except ValueError:
                    continue
                if resseq not in residue_set:
                    continue
                try:
                    x = float(parts[col_map["Cartn_x"]])
                    y = float(parts[col_map["Cartn_y"]])
                    z = float(parts[col_map["Cartn_z"]])
                except ValueError:
                    continue
                coords_list.append((x, y, z))

    if not coords_list:
        return np.empty((0, 3), dtype=float)
    return np.array(coords_list, dtype=float)


def _parse_all_atom_coords_pdb(
    pdb_path: str,
    residues: List[int],
    chain: Optional[str] = None,
) -> "np.ndarray":
    """PDB 파일에서 지정 잔기의 heavy atom 좌표를 수집한다 (numpy 배열 반환)."""
    residue_set = set(residues)
    coords_list: List[Tuple[float, float, float]] = []

    with open(pdb_path, "r", errors="replace") as fh:
        for line in fh:
            if not line.startswith("ATOM"):
                continue
            if len(line) < 54:
                continue
            chain_id = line[21]
            if chain is not None and chain_id != chain:
                continue
            altloc = line[16]
            if altloc not in (" ", "A"):
                continue
            try:
                resseq = int(line[22:26].strip())
            except ValueError:
                continue
            if resseq not in residue_set:
                continue
            element = line[76:78].strip().upper()
            if not element:
                element = line[12:16].strip()[0].upper()
            if element in {"H", "D"}:
                continue
            try:
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())
            except ValueError:
                continue
            coords_list.append((x, y, z))

    if not coords_list:
        return np.empty((0, 3), dtype=float)
    return np.array(coords_list, dtype=float)


def _detect_longest_chain(pdb_path: str) -> str:
    """PDB에서 가장 많은 CA 원자를 가진 체인 ID를 반환한다."""
    chain_count: Dict[str, int] = {}
    with open(pdb_path, "r", errors="replace") as fh:
        for line in fh:
            if not line.startswith("ATOM"):
                continue
            if len(line) < 22:
                continue
            if line[12:16].strip() != "CA":
                continue
            chain_id = line[21]
            chain_count[chain_id] = chain_count.get(chain_id, 0) + 1
    if not chain_count:
        raise ValueError(f"PDB '{pdb_path}'에서 ATOM CA 원자를 찾지 못했습니다.")
    return max(chain_count, key=chain_count.__getitem__)


# ---------------------------------------------------------------------------
# 중심 좌표 계산
# ---------------------------------------------------------------------------

def _compute_centroid(
    coords: List[Dict[str, Any]],
) -> Tuple[float, float, float]:
    """CA 원자 좌표들의 기하학적 중심(centroid)을 계산한다."""
    n = len(coords)
    cx = sum(c["x"] for c in coords) / n
    cy = sum(c["y"] for c in coords) / n
    cz = sum(c["z"] for c in coords) / n
    return cx, cy, cz


def _compute_radius(
    coords: List[Dict[str, Any]],
    cx: float,
    cy: float,
    cz: float,
) -> float:
    """중심으로부터 각 CA 원자까지의 최대 거리 + 마진을 반환한다."""
    max_dist = 0.0
    for c in coords:
        d = math.sqrt(
            (c["x"] - cx) ** 2
            + (c["y"] - cy) ** 2
            + (c["z"] - cz) ** 2
        )
        if d > max_dist:
            max_dist = d
    return round(max_dist + _POCKET_MARGIN_ANG, 3)


# ---------------------------------------------------------------------------
# 메인 추출 함수
# ---------------------------------------------------------------------------

def extract_binding_pocket(
    pdb_path: str,
    residues: Optional[List[int]] = None,
    chain: Optional[str] = None,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """SSTR2 결합 포켓 중심 좌표를 추출하여 딕셔너리로 반환한다.

    Args:
        pdb_path:    수용체 PDB 파일 경로
        residues:    핵심 잔기 번호 목록. None이면 DEFAULT_KEY_RESIDUES 사용.
        chain:       체인 ID. None이면 가장 긴 체인 자동 선택.
        output_path: JSON 저장 경로. None이면 저장하지 않음.

    Returns:
        결합 포켓 정보 딕셔너리 (JSON 직렬화 가능).

    Raises:
        ValueError: 잔기 CA 원자를 찾지 못한 경우
        FileNotFoundError: pdb_path 파일 없는 경우
    """
    if not Path(pdb_path).exists():
        raise FileNotFoundError(f"PDB 파일을 찾을 수 없습니다: {pdb_path}")

    key_residues = residues if residues is not None else DEFAULT_KEY_RESIDUES

    # CA 좌표 추출
    coords = _parse_ca_coords(pdb_path, key_residues, chain)

    # 발견된 잔기 / 미발견 잔기 보고
    found_resnums = {c["resnum"] for c in coords}
    missing = sorted(set(key_residues) - found_resnums)
    if missing:
        print(
            f"[경고] 다음 잔기 CA 원자를 PDB에서 찾지 못했습니다: {missing}",
            file=sys.stderr,
        )

    # 중심 좌표 계산
    cx, cy, cz = _compute_centroid(coords)

    # 포켓 반경 계산
    radius = _compute_radius(coords, cx, cy, cz)

    # 박스 크기 결정 (반경 × 2, 최소 20 Å, 권장 30 Å)
    box_size = max(_MIN_BOX_SIZE_ANG, min(_RECOMMENDED_BOX_SIZE_ANG, radius * 2.0))

    # 수용체 이름 (파일명 기반)
    receptor_name = Path(pdb_path).stem  # e.g. "SSTR2_7XNA"

    pocket_info: Dict[str, Any] = {
        "receptor": receptor_name,
        "chain": (chain or _detect_longest_chain(pdb_path)),
        "residues": sorted(key_residues),
        "residue_details": sorted(coords, key=lambda c: c["resnum"]),
        "center_x": round(cx, 3),
        "center_y": round(cy, 3),
        "center_z": round(cz, 3),
        "radius": radius,
        "box_size": round(box_size, 1),
        "gnina_config": {
            "center_x": round(cx, 3),
            "center_y": round(cy, 3),
            "center_z": round(cz, 3),
            "size_x": round(box_size, 1),
            "size_y": round(box_size, 1),
            "size_z": round(box_size, 1),
        },
        "notes": (
            "TM5 잔기: 205(TYR), 208(PHE), 209(ILE), 212(THR) / "
            "TM6 잔기: 272(PHE), 273(TYR), 276(ASN), 279(SER). "
            "서호성 박사 의견 기준 (KAERI-AIRL-MOM-2026-003). "
            "radius = max(CA→centroid) + 5Å 여유."
        ),
    }

    # 저장
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(pocket_info, fh, indent=2, ensure_ascii=False)
        print(f"[extract_binding_pocket] 저장 완료: {out}", file=sys.stderr)

    return pocket_info


# ---------------------------------------------------------------------------
# A-01 표준 인터페이스: extract_pocket_center
# ---------------------------------------------------------------------------

def extract_pocket_center(
    pdb_path: Path,
    residue_ids: List[int],
    chain: Optional[str] = None,
    min_box_size: float = 30.0,
) -> Dict[str, Any]:
    """SSTR2 결합 포켓 중심 좌표·반경·GNINA 박스를 계산한다.

    A-01 회의 결정: TM5(208/209) + TM6(272/273/276) 중심 좌표.
    PDB/CIF 양쪽 지원. 지정 잔기의 모든 원자를 사용한다 (CA 한정 아님).

    Args:
        pdb_path:     구조 파일 경로 (.pdb 또는 .cif)
        residue_ids:  포켓 잔기 번호 목록 (예: [208, 209, 272, 273, 276])
        chain:        체인 ID (None이면 PDB는 최장 체인, CIF는 모든 체인)
        min_box_size: GNINA 박스 최소 엣지 길이 (Å, 기본 30 Å)

    Returns:
        {
            "center_x": float,
            "center_y": float,
            "center_z": float,
            "radius_angstrom": float,
            "residue_ids": List[int],
            "source_pdb": str,
            "box_size": {"size_x": float, "size_y": float, "size_z": float},
        }

    Raises:
        FileNotFoundError: 파일 없음
        ValueError:        지정 잔기에 해당하는 원자를 찾을 수 없음
    """
    pdb_path = Path(pdb_path)
    if not pdb_path.exists():
        raise FileNotFoundError(f"구조 파일을 찾을 수 없습니다: {pdb_path}")

    suffix = pdb_path.suffix.lower()

    if suffix in (".cif", ".mmcif"):
        # CIF 파일: 모든 원자 좌표 수집
        coords = _parse_all_atom_coords_cif(str(pdb_path), residue_ids, chain)
    else:
        # PDB 파일: CIF와 동일하게 heavy atom 기준으로 포켓 중심 계산
        if chain is None:
            chain = _detect_longest_chain(str(pdb_path))
        coords = _parse_all_atom_coords_pdb(str(pdb_path), residue_ids, chain)

    if len(coords) == 0:
        raise ValueError(
            f"잔기 {residue_ids}에 해당하는 원자가 없습니다 "
            f"(파일: {pdb_path}, 체인: {chain}).\n"
            f"구조 파일에 해당 잔기 번호가 있는지 확인하세요."
        )

    center = coords.mean(axis=0)
    dists = np.linalg.norm(coords - center, axis=1)
    radius = float(dists.max())
    box_edge = max(min_box_size, radius * 2.0)

    return {
        "center_x": round(float(center[0]), 4),
        "center_y": round(float(center[1]), 4),
        "center_z": round(float(center[2]), 4),
        "radius_angstrom": round(radius, 4),
        "residue_ids": sorted(residue_ids),
        "source_pdb": str(pdb_path),
        "box_size": {
            "size_x": round(box_edge, 2),
            "size_y": round(box_edge, 2),
            "size_z": round(box_edge, 2),
        },
    }


# ---------------------------------------------------------------------------
# CLI 엔트리포인트
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "SSTR2 결합 포켓 중심 좌표 추출 — "
            "TM5/TM6 핵심 잔기 CA 원자 기하학적 중심 계산\n"
            "(A-01: TM5(208,209) + TM6(272,273,276) 중심 좌표)"
        )
    )
    parser.add_argument(
        "--pdb",
        required=True,
        help="수용체 구조 파일 경로 (PDB 또는 CIF, 예: data/somatostatin_receptor/SSTR2_7XNA.pdb)",
    )
    parser.add_argument(
        "--residues",
        default=None,
        help=(
            "핵심 잔기 번호 (쉼표 구분 또는 공백 구분). "
            "기본: 205,208,209,212,272,273,276,279 (TM5+TM6 전체). "
            "A-01 결합 포켓: 208,209,272,273,276"
        ),
    )
    parser.add_argument(
        "--chain",
        default=None,
        help="체인 ID (기본: 가장 긴 체인 자동 선택). 예: A",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "결과 JSON 저장 경로 (기본: 저장 안 함, stdout 출력). "
            "예: data/somatostatin_receptor/binding_pocket_SSTR2.json"
        ),
    )
    parser.add_argument(
        "--use-all-atoms",
        action="store_true",
        default=False,
        help="CA 원자만이 아닌 모든 원자 사용 (CIF 파일 자동 활성)",
    )
    args = parser.parse_args()

    # 잔기 목록 파싱 (쉼표 또는 공백 구분)
    if args.residues is not None:
        residues = [int(r.strip()) for r in args.residues.replace(",", " ").split()]
    else:
        residues = DEFAULT_KEY_RESIDUES

    # A-01 표준 인터페이스 사용 (PDB/CIF 통합)
    suffix = Path(args.pdb).suffix.lower()
    if suffix in (".cif", ".mmcif") or args.use_all_atoms:
        result = extract_pocket_center(
            pdb_path=Path(args.pdb),
            residue_ids=residues,
            chain=args.chain,
        )
        # GNINA 호환 형식으로 변환
        pocket_info: Dict[str, Any] = {
            "receptor": Path(args.pdb).stem,
            "chain": args.chain or "auto",
            "residues": result["residue_ids"],
            "center_x": result["center_x"],
            "center_y": result["center_y"],
            "center_z": result["center_z"],
            "radius": result["radius_angstrom"],
            "box_size": result["box_size"]["size_x"],
            "gnina_config": {
                "center_x": result["center_x"],
                "center_y": result["center_y"],
                "center_z": result["center_z"],
                "size_x": result["box_size"]["size_x"],
                "size_y": result["box_size"]["size_y"],
                "size_z": result["box_size"]["size_z"],
            },
            "source_pdb": result["source_pdb"],
            "notes": (
                "A-01 (서호성 박사 2026-04-06): "
                "TM5(208/209) + TM6(272/273/276) 중심 좌표. "
                "GNINA/AutoDock-GPU box 형식으로 출력."
            ),
        }
    else:
        pocket_info = extract_binding_pocket(
            pdb_path=args.pdb,
            residues=residues,
            chain=args.chain,
            output_path=None,
        )

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(pocket_info, fh, indent=2, ensure_ascii=False)
        print(f"[extract_binding_pocket] 저장 완료: {out}", file=sys.stderr)

    # stdout JSON 출력 (파이프라인 연동용)
    print(json.dumps(pocket_info, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
