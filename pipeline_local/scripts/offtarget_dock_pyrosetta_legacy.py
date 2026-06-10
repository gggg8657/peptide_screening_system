#!/usr/bin/env python3
"""
offtarget_dock.py — PyRosetta FlexPepDock off-target docking subprocess script
===============================================================================
수용체 구조(CIF/PDB)와 펩타이드 서열을 입력으로 받아
FlexPepDock으로 도킹한 후 ddG를 stdout JSON으로 출력한다.

Usage:
    conda run -n bio-tools python offtarget_dock.py \
        --receptor /path/to/receptor.cif \
        --sequence AGCKNFFWKTFTSC \
        --nstruct 20 \
        --output-dir /path/to/output

Output (stdout, 마지막 줄):
    {"ddg": -5.23, "mean_ddg": -4.87, "nstruct": 20, "scores": [...]}

Error (stdout):
    {"error": "메시지"}
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    import pyrosetta

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# PyRosetta 초기화
# ---------------------------------------------------------------------------

def _init_pyrosetta() -> None:
    """PyRosetta를 CIF/PDB 모두 지원하도록 초기화한다."""
    import pyrosetta  # type: ignore

    pyrosetta.init(
        " ".join([
            "-ignore_unrecognized_res true",
            "-load_PDB_components false",
            "-ignore_zero_occupancy false",
            "-no_nstruct_label true",
            "-packing:pack_missing_sidechains false",
            "-mute all",
            "-out:levels core.io:999",
        ]),
        silent=True,
    )


# ---------------------------------------------------------------------------
# 수용체 로드 — NCAA 체인 제거 + 리간드 위치 추출
# ---------------------------------------------------------------------------

def _load_receptor_and_ligand_center(
    receptor_path: str,
) -> Tuple[pyrosetta.Pose, Optional[Tuple[float, float, float]]]:
    """수용체 CIF/PDB를 로드한다.

    Returns:
        (clean_receptor, ligand_center)
        - clean_receptor: canonical AA만 포함한 Pose
        - ligand_center: NCAA/리간드 체인의 CA 질량 중심 (없으면 None)
    """
    import pyrosetta  # type: ignore

    raw = pyrosetta.pose_from_file(receptor_path)
    pdb_info = raw.pdb_info()

    # 1) 체인별 canonical/non-canonical 분류
    chain_has_ncaa: Dict[str, bool] = {}
    chain_residues: Dict[str, List[int]] = {}
    for i in range(1, raw.total_residue() + 1):
        ch = pdb_info.chain(i)
        chain_residues.setdefault(ch, []).append(i)
        if not raw.residue(i).type().is_canonical_aa():
            chain_has_ncaa[ch] = True

    keep_chains = {ch for ch in chain_residues if not chain_has_ncaa.get(ch, False)}
    ncaa_chains = {ch for ch in chain_residues if chain_has_ncaa.get(ch, False)}

    # 2) 리간드 체인(NCAA 포함)의 질량 중심 추출
    ligand_center: Optional[Tuple[float, float, float]] = None
    if ncaa_chains:
        lx, ly, lz, n = 0.0, 0.0, 0.0, 0
        for ch in ncaa_chains:
            for idx in chain_residues[ch]:
                res = raw.residue(idx)
                # CA가 있으면 CA, 없으면 첫 번째 중원자
                for atom_name in ("CA", "C", "N"):
                    if res.has(atom_name):
                        xyz = res.xyz(atom_name)
                        lx += xyz.x; ly += xyz.y; lz += xyz.z
                        n += 1
                        break
        if n > 0:
            ligand_center = (lx / n, ly / n, lz / n)

    # 3) canonical 체인만 남긴 PDB 생성
    with tempfile.NamedTemporaryFile(suffix=".pdb", delete=False) as f:
        tmp_path = f.name

    raw.dump_pdb(tmp_path)

    with open(tmp_path, "r") as f:
        lines = f.readlines()
    with open(tmp_path, "w") as f:
        for line in lines:
            if line.startswith(("ATOM", "HETATM", "TER")):
                chain = line[21] if len(line) > 21 else ""
                if chain in keep_chains:
                    f.write(line)
            elif not line.startswith("CONECT"):
                f.write(line)

    try:
        clean = pyrosetta.pose_from_pdb(tmp_path)
    finally:
        os.unlink(tmp_path)

    # 4) PyRosetta에서 리간드 못 찾은 경우: CIF HETATM에서 직접 파싱
    if ligand_center is None and receptor_path.lower().endswith(".cif"):
        ligand_center = _parse_hetatm_center_from_cif(receptor_path)

    logger.info(
        "수용체 로드: %d → %d residues (제거 체인: %s), 리간드 중심: %s",
        raw.total_residue(), clean.total_residue(),
        ncaa_chains or "없음", ligand_center,
    )
    return clean, ligand_center


def _parse_hetatm_center_from_cif(cif_path: str) -> Optional[Tuple[float, float, float]]:
    """CIF 파일에서 HETATM 좌표를 직접 파싱하여 리간드 질량 중심을 반환한다.

    HOH(물)는 제외하고, non-polymer 리간드의 좌표만 수집.
    """
    coords: List[Tuple[float, float, float]] = []
    with open(cif_path, "r") as f:
        for line in f:
            if not line.startswith("HETATM"):
                continue
            parts = line.split()
            # CIF HETATM: comp_id는 보통 5번째 필드
            if len(parts) < 12:
                continue
            comp_id = parts[5] if len(parts) > 5 else ""
            if comp_id == "HOH":
                continue
            try:
                x = float(parts[10])
                y = float(parts[11])
                z = float(parts[12])
                coords.append((x, y, z))
            except (ValueError, IndexError):
                continue

    if not coords:
        return None

    cx = sum(c[0] for c in coords) / len(coords)
    cy = sum(c[1] for c in coords) / len(coords)
    cz = sum(c[2] for c in coords) / len(coords)
    logger.info("CIF HETATM 파싱: %d 원자 → 리간드 중심 (%.1f, %.1f, %.1f)", len(coords), cx, cy, cz)
    return (cx, cy, cz)


# ---------------------------------------------------------------------------
# 펩타이드 배치 — 리간드 위치 기반
# ---------------------------------------------------------------------------

def _place_peptide_at(
    receptor: pyrosetta.Pose,
    peptide: pyrosetta.Pose,
    target_center: Tuple[float, float, float],
    jitter: float = 3.0,
) -> pyrosetta.Pose:
    """펩타이드를 리간드 위치 바깥에 clash-free로 배치한 복합체 Pose를 반환한다.

    전략: 수용체 질량 중심 → 리간드 중심 방향으로 리간드에서 30 Å 바깥에 배치.
    FlexPepDock lowres 단계가 펩타이드를 접근시키면서 도킹한다.
    """
    import pyrosetta  # type: ignore
    from pyrosetta.rosetta.core.pose import append_pose_to_pose  # type: ignore
    from pyrosetta.rosetta.numeric import xyzVector_double_t as V3  # type: ignore
    import random
    import math

    tx, ty, tz = target_center

    # 수용체 질량 중심
    n_rec = receptor.total_residue()
    rx, ry, rz = 0.0, 0.0, 0.0
    for i in range(1, n_rec + 1):
        xyz = receptor.residue(i).xyz("CA")
        rx += xyz.x; ry += xyz.y; rz += xyz.z
    rx /= n_rec; ry /= n_rec; rz /= n_rec

    # 수용체 중심 → 리간드 방향의 단위 벡터
    vx, vy, vz = tx - rx, ty - ry, tz - rz
    vmag = math.sqrt(vx**2 + vy**2 + vz**2) or 1.0
    vx /= vmag; vy /= vmag; vz /= vmag

    # 리간드 위치에서 바깥 방향 30 Å에 배치 (clash 회피)
    offset = 30.0
    place_x = tx + vx * offset + random.uniform(-jitter, jitter)
    place_y = ty + vy * offset + random.uniform(-jitter, jitter)
    place_z = tz + vz * offset + random.uniform(-jitter, jitter)

    # 펩타이드 현재 질량 중심
    n_pep = peptide.total_residue()
    px, py, pz = 0.0, 0.0, 0.0
    for i in range(1, n_pep + 1):
        xyz = peptide.residue(i).xyz("CA")
        px += xyz.x; py += xyz.y; pz += xyz.z
    px /= n_pep; py /= n_pep; pz /= n_pep

    # 이동
    dx, dy, dz = place_x - px, place_y - py, place_z - pz
    for i in range(1, n_pep + 1):
        for j in range(1, peptide.residue(i).natoms() + 1):
            old = peptide.residue(i).xyz(j)
            peptide.residue(i).set_xyz(j, V3(old.x + dx, old.y + dy, old.z + dz))

    complex_pose = receptor.clone()
    append_pose_to_pose(complex_pose, peptide, new_chain=True)
    return complex_pose


def _receptor_surface_center(receptor: pyrosetta.Pose) -> Tuple[float, float, float]:
    """리간드 정보가 없을 때 수용체 표면 추정 중심을 반환한다.

    전략: 전체 CA 질량 중심에서 20 Å 오프셋 (대략적 표면)
    """
    n = receptor.total_residue()
    cx, cy, cz = 0.0, 0.0, 0.0
    for i in range(1, n + 1):
        xyz = receptor.residue(i).xyz("CA")
        cx += xyz.x; cy += xyz.y; cz += xyz.z
    cx /= n; cy /= n; cz /= n
    return (cx + 20.0, cy, cz)


# ---------------------------------------------------------------------------
# Interface ddG 계산
# ---------------------------------------------------------------------------

def _score_interface_ddg(
    pose: pyrosetta.Pose,
    sfxn: pyrosetta.ScoreFunction,
    peptide_start: int = 0,
) -> float:
    """InterfaceAnalyzerMover로 펩타이드-수용체 interface ddG를 계산한다.

    모든 jump를 시도하고, 가장 유의미한(ddG가 가장 낮은) interface를 반환한다.
    펩타이드 체인이 여러 jump 중 어디에 해당하는지 자동 탐색.
    """
    from pyrosetta.rosetta.protocols.analysis import InterfaceAnalyzerMover  # type: ignore

    n_jumps = pose.num_jump()
    if n_jumps < 1:
        return sfxn(pose)

    # 모든 jump에서 interface를 평가, 가장 큰 SASA를 가진 jump의 ddG 반환
    best_dsasa = 0.0
    best_ddg = 0.0
    for j in range(1, n_jumps + 1):
        try:
            iam = InterfaceAnalyzerMover(j)
            iam.set_compute_packstat(False)
            iam.set_pack_separated(True)
            iam.set_scorefunction(sfxn)
            iam.apply(pose)
            ddg = iam.get_interface_dG()
            dsasa = iam.get_interface_delta_sasa()
            # 가장 큰 buried SASA를 가진 interface = 펩타이드-수용체 interface
            if dsasa > best_dsasa:
                best_dsasa = dsasa
                best_ddg = ddg
        except Exception:
            continue

    return best_ddg


# ---------------------------------------------------------------------------
# 메인 도킹 함수
# ---------------------------------------------------------------------------

def run_docking(
    receptor_path: str,
    sequence: str,
    nstruct: int = 20,
    output_dir: Optional[str] = None,
) -> dict:
    """FlexPepDock 도킹 실행. nstruct 반복 중 최저 ddG를 반환한다.

    워크플로우:
        1. 수용체 로드 + NCAA 체인 제거 + 리간드 중심 추출
        2. 각 반복:
           a. 리간드 위치에 펩타이드 배치 (jitter로 다양성 확보)
           b. FlexPepDockingProtocol 실행
           c. InterfaceAnalyzerMover로 ddG 계산
    """
    import pyrosetta  # type: ignore

    sfxn = pyrosetta.get_fa_scorefxn()

    # 수용체 + 리간드 위치 로드
    receptor, ligand_center = _load_receptor_and_ligand_center(receptor_path)
    if ligand_center is None:
        ligand_center = _receptor_surface_center(receptor)
        logger.warning("리간드 중심 없음 — 수용체 표면 중심 사용: %s", ligand_center)

    peptide_template = pyrosetta.pose_from_sequence(sequence, "fa_standard")

    # FlexPepDock 프로토콜
    try:
        from pyrosetta.rosetta.protocols.flexpep_docking import FlexPepDockingProtocol  # type: ignore
        use_flexpep = True
    except ImportError:
        use_flexpep = False
        logger.warning("FlexPepDockingProtocol import 실패 — minimize 폴백 사용")

    scores: list[float] = []
    best_ddg = float("inf")
    best_pose: Optional[pyrosetta.Pose] = None

    for i in range(nstruct):
        try:
            # 리간드 위치에 펩타이드 배치 (매 반복 jitter)
            p = _place_peptide_at(
                receptor, peptide_template.clone(),
                ligand_center, jitter=5.0,
            )

            if use_flexpep:
                fpd = FlexPepDockingProtocol()
                fpd.apply(p)
            else:
                from pyrosetta.rosetta.core.kinematics import MoveMap  # type: ignore
                from pyrosetta.rosetta.protocols.minimization_packing import MinMover  # type: ignore
                mm2 = MoveMap()
                mm2.set_bb(True); mm2.set_chi(True); mm2.set_jump(True)
                full_min = MinMover()
                full_min.movemap(mm2)
                full_min.score_function(sfxn)
                full_min.min_type("dfpmin_armijo_nonmonotone")
                full_min.tolerance(0.1)
                full_min.apply(p)

            ddg = _score_interface_ddg(p, sfxn)
        except Exception as exc:
            logger.debug("nstruct %d 실패: %s", i, exc)
            continue

        scores.append(ddg)
        if ddg < best_ddg:
            best_ddg = ddg
            best_pose = p

    if not scores:
        raise RuntimeError("모든 nstruct 반복이 실패했습니다.")

    # 최적 구조 저장
    best_pdb: Optional[str] = None
    if output_dir and best_pose is not None:
        out_path = Path(output_dir) / "best_dock.pdb"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        best_pose.dump_pdb(str(out_path))
        best_pdb = str(out_path)

    # 양수 ddG는 "결합 안 됨" — 0.0으로 클램프 (off-target에 안 붙음 = 선택적)
    clamped_scores = [min(s, 0.0) for s in scores]
    best_ddg_clamped = min(clamped_scores) if clamped_scores else 0.0
    mean_ddg = sum(clamped_scores) / len(clamped_scores)
    return {
        "ddg": best_ddg_clamped,
        "mean_ddg": round(mean_ddg, 3),
        "nstruct_completed": len(scores),
        "nstruct_requested": nstruct,
        "scores": [round(s, 3) for s in scores],
        "best_pdb": best_pdb,
    }


# ---------------------------------------------------------------------------
# CLI 엔트리포인트
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="PyRosetta FlexPepDock off-target docking"
    )
    parser.add_argument("--receptor", required=True, help="수용체 구조 파일 (CIF/PDB)")
    parser.add_argument("--sequence", required=True, help="펩타이드 아미노산 서열")
    parser.add_argument("--nstruct", type=int, default=20, help="반복 도킹 횟수")
    parser.add_argument("--output-dir", default=None, help="최적 구조 저장 디렉토리")
    args = parser.parse_args()

    try:
        _init_pyrosetta()
        result = run_docking(
            receptor_path=args.receptor,
            sequence=args.sequence,
            nstruct=args.nstruct,
            output_dir=args.output_dir,
        )
        print(json.dumps(result), flush=True)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
