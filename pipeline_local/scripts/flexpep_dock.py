#!/usr/bin/env python3
"""
flexpep_dock.py  (pipeline_local wrapper)
=========================================
Worker CLI 호환 wrapper for FlexPepDock PyRosetta 도킹.

flexpepdock_worker.py 가 호출하는 CLI:
    conda run -n bio-tools python pipeline_local/scripts/flexpep_dock.py \\
        --receptor  <PDB or CIF>  \\
        --sequence  <14aa>        \\
        --output-prefix <prefix>  \\
        --cycles    <int>         \\
        --nstruct   <int>         \\
        --flex-pep-freedom <low|med|high> \\
        --ddg-cycle <int>

내부 동작:
  1. receptor 파일이 .cif면 PyRosetta로 .pdb 변환
  2. 14aa 시퀀스를 SST-14 reference complex에서 MutateResidue로 생성
     (reference 없으면 PDB string으로 peptide pose 빌드)
  3. FlexPepDockingProtocol으로 nstruct 앙상블 생성
  4. InterfaceAnalyzerMover ddG 계산
  5. stdout에 JSON 출력:
       {"dG_kcal_mol": float, "interface_score": float, "stub": false, ...}

AG_src/scripts/flexpep_dock.py 와의 관계:
  - AG_src 버전은 --input/--output/--protocol CLI를 사용 (step06_rosetta.py 호환)
  - 본 파일은 flexpepdock_worker.py 호환 CLI를 제공하고
    내부적으로 AG_src 버전의 PyRosetta 함수들을 import해서 재사용한다.

stdout: JSON only
stderr: 모든 PyRosetta 로그 및 진단 출력
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

# flake8 F821 false-positive 해소: PyRosetta는 conditional import (런타임
# `import pyrosetta`)로 사용되지만 type hint("pyrosetta.Pose")는 정적 분석
# 단계에서도 노출 필요. TYPE_CHECKING 블록으로 flake8에 모듈 존재 알림.
if TYPE_CHECKING:
    import pyrosetta  # noqa: F401

# ---------------------------------------------------------------------------
# 경로 설정
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parents[1]
_AG_SCRIPTS = _REPO_ROOT / "AgenticAI4SCIENCE_pyrosetta_track" / "repos" / "ai4sci-kaeri" / "AG_src" / "scripts"

# AG_src/scripts 를 sys.path에 추가 (AG_src flexpep_dock 함수 재사용)
if str(_AG_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_AG_SCRIPTS))


# ---------------------------------------------------------------------------
# FlexPepDock 파라미터 매핑
# ---------------------------------------------------------------------------

# flex-pep-freedom → PyRosetta 파라미터 맵
_FREEDOM_MAP: Dict[str, Dict[str, int]] = {
    "low":  {"cycles": 3,  "nstruct_multiplier": 1},
    "med":  {"cycles": 5,  "nstruct_multiplier": 1},
    "high": {"cycles": 10, "nstruct_multiplier": 2},
}

# SST-14 reference complex 탐색 경로 (우선순위 순)
_REFERENCE_SEARCH_PATHS: List[Path] = [
    _REPO_ROOT / "data" / "somatostatin_receptor" / "SSTR2_7XNA_complex.pdb",
    _REPO_ROOT / "runs_local" / "selectivity_demo_20260511" / "SSTR2_sst14_complex.pdb",
    _REPO_ROOT / "runs_local" / "alphafold_receptors" / "SSTR2_sst14_complex.pdb",
]


# ---------------------------------------------------------------------------
# PyRosetta 초기화
# ---------------------------------------------------------------------------

def init_pyrosetta(extra_options: str = "") -> None:
    """PyRosetta를 초기화한다 (stderr로 로그, stdout은 JSON 전용 보호)."""
    import pyrosetta
    base_opts = (
        "-mute all -ex1 -ex2aro -ignore_unrecognized_res"
        " -flexPepDocking:pep_refine"
        " -constraints:cst_fa_weight 1.0"
    )
    opts = f"{base_opts} {extra_options}".strip()
    pyrosetta.init(options=opts, silent=True)
    print("[wrapper] PyRosetta initialized", file=sys.stderr)


# ---------------------------------------------------------------------------
# CIF → PDB 변환
# ---------------------------------------------------------------------------

def convert_cif_to_pdb(cif_path: str, output_pdb: Optional[str] = None) -> str:
    """CIF 파일을 PyRosetta로 PDB로 변환한다.

    Args:
        cif_path:   입력 .cif 파일 경로.
        output_pdb: 출력 .pdb 파일 경로. None이면 동일 디렉토리에 저장.

    Returns:
        저장된 .pdb 파일 경로.
    """
    import pyrosetta

    cif_p = Path(cif_path)
    if output_pdb is None:
        output_pdb = str(cif_p.with_suffix(".pdb"))

    print(f"[wrapper] CIF→PDB 변환: {cif_path} → {output_pdb}", file=sys.stderr)

    # PyRosetta는 .mmcif/.cif 직접 로드 지원
    pose = pyrosetta.pose_from_file(str(cif_p))
    pose.dump_pdb(output_pdb)
    print(f"[wrapper] 변환 완료: {pose.total_residue()} residues", file=sys.stderr)
    return output_pdb


def resolve_receptor_pdb(receptor_path: str) -> str:
    """receptor_path가 .cif면 .pdb로 변환한 경로를 반환한다.

    .pdb이면 그대로 반환.
    변환된 파일은 동일 디렉토리에 <name>.pdb 로 저장 (이미 존재하면 재사용).
    """
    p = Path(receptor_path)
    if p.suffix.lower() in (".cif", ".mmcif"):
        pdb_path = p.with_suffix(".pdb")
        if not pdb_path.exists():
            convert_cif_to_pdb(str(p), str(pdb_path))
        else:
            print(f"[wrapper] PDB 캐시 재사용: {pdb_path}", file=sys.stderr)
        return str(pdb_path)
    return receptor_path


# ---------------------------------------------------------------------------
# Peptide Pose 생성
# ---------------------------------------------------------------------------

def _find_reference_complex() -> Optional[str]:
    """SST-14 reference complex PDB를 탐색한다."""
    for p in _REFERENCE_SEARCH_PATHS:
        if p.exists():
            print(f"[wrapper] Reference complex found: {p}", file=sys.stderr)
            return str(p)
    return None


def build_peptide_pose_from_sequence(
    sequence: str,
    receptor_pdb: str,
) -> "pyrosetta.Pose":
    """14aa 시퀀스로 receptor-peptide complex Pose를 빌드한다.

    우선순위:
    1. SST-14 reference complex + MutateResidue (backbone 보존)
    2. PyRosetta pose_from_sequence (확장 conformation) + append_pose

    Args:
        sequence:     14aa 1-letter 코드.
        receptor_pdb: 수용체 PDB 경로.

    Returns:
        FlexPepDock 준비된 complex Pose (peptide가 LAST chain).
    """
    import pyrosetta

    # AG_src/scripts/flexpep_dock.py의 함수 재사용 시도
    try:
        from flexpep_dock import (  # type: ignore[import]
            prepare_complex_by_mutation,
            reorder_peptide_last,
        )
        _ag_available = True
    except ImportError:
        _ag_available = False
        print("[wrapper] AG_src flexpep_dock 모듈 import 실패 — 내장 구현 사용", file=sys.stderr)

    ref_complex = _find_reference_complex()

    if _ag_available and ref_complex:
        print(f"[wrapper] MutateResidue 모드: reference={ref_complex}", file=sys.stderr)
        pose, resolved_chain = prepare_complex_by_mutation(
            ref_complex,
            sequence,
            peptide_chain=1,
        )
        pose = reorder_peptide_last(pose, resolved_chain)
        return pose

    # Fallback: receptor 로드 + 확장 conformation peptide append
    print("[wrapper] Fallback 모드: receptor + extended peptide", file=sys.stderr)
    return _build_complex_fallback(sequence, receptor_pdb)


def _build_complex_fallback(
    sequence: str,
    receptor_pdb: str,
) -> "pyrosetta.Pose":
    """Receptor PDB + 확장 conformation peptide를 합쳐 complex Pose를 반환한다.

    FlexPepDock의 pep_refine 모드에서는 초기 conformation이 실험 구조와
    달라도 허용된다 — refinement가 최적화함.
    """
    import pyrosetta
    from pyrosetta.rosetta.core.pose import append_pose_to_pose

    receptor_pose = pyrosetta.pose_from_pdb(receptor_pdb)
    pep_pose = pyrosetta.pose_from_sequence(sequence, res_type="fa_standard")

    # 확장 conformation 설정 (phi=-135, psi=135)
    for i in range(1, pep_pose.total_residue() + 1):
        pep_pose.set_phi(i, -135.0)
        pep_pose.set_psi(i, 135.0)
        pep_pose.set_omega(i, 180.0)

    print(
        f"[wrapper] receptor={receptor_pose.total_residue()} res, "
        f"peptide={pep_pose.total_residue()} res",
        file=sys.stderr,
    )

    # Peptide를 receptor의 LAST chain으로 append
    append_pose_to_pose(receptor_pose, pep_pose, new_chain=True)
    print(
        f"[wrapper] complex={receptor_pose.total_residue()} res, "
        f"{receptor_pose.num_chains()} chains",
        file=sys.stderr,
    )
    return receptor_pose


# ---------------------------------------------------------------------------
# 앙상블 도킹
# ---------------------------------------------------------------------------

def run_ensemble_docking(
    pose: "pyrosetta.Pose",
    output_prefix: str,
    nstruct: int,
    cycles: int,
) -> Tuple[List[str], List[float], List[float]]:
    """nstruct 반복으로 FlexPepDock 앙상블을 생성한다.

    Args:
        pose:          초기 complex Pose (peptide가 LAST chain).
        output_prefix: 출력 PDB prefix (예: /tmp/test/docked).
        nstruct:       앙상블 크기.
        cycles:        refinement cycles (PyRosetta에서 FlexPepDockingProtocol
                       의 apply 호출 횟수로 변환).

    Returns:
        (pdb_paths, ddg_values, interface_scores)
    """
    import pyrosetta

    # AG_src 함수 재사용 시도
    try:
        from flexpep_dock import (  # type: ignore[import]
            run_flexpep_refine_pose,
            compute_interface_ddg,
            compute_total_score,
        )
        _ag_available = True
    except ImportError:
        _ag_available = False

    Path(output_prefix).parent.mkdir(parents=True, exist_ok=True)

    pdb_paths: List[str] = []
    ddg_values: List[float] = []
    interface_scores: List[float] = []

    t0 = time.monotonic()

    for i in range(nstruct):
        output_pdb = f"{output_prefix}_{i:04d}.pdb"
        print(f"[wrapper] nstruct {i+1}/{nstruct} 시작", file=sys.stderr)

        # Pose 복사 (각 nstruct는 독립)
        working_pose = pose.clone()

        try:
            if _ag_available:
                refined_pose, _ = run_flexpep_refine_pose(working_pose, output_pdb)
                ddg = compute_interface_ddg(refined_pose)
                # interface_score = ddg (InterfaceAnalyzerMover.get_interface_dG() 값)
                # AG_src는 interface_score 키가 없으므로 ddg를 interface_score로도 사용
                interface_score = ddg
            else:
                refined_pose, ddg, interface_score = _run_flexpep_direct(
                    working_pose, output_pdb, cycles
                )
        except Exception as exc:
            print(f"[wrapper] nstruct {i+1} 실패: {exc}", file=sys.stderr)
            continue

        pdb_paths.append(output_pdb)
        ddg_values.append(float(ddg))
        interface_scores.append(float(interface_score))

        elapsed = time.monotonic() - t0
        print(
            f"[wrapper] nstruct {i+1}/{nstruct} 완료: ddg={ddg:.3f}, "
            f"interface={interface_score:.3f} ({elapsed:.1f}s)",
            file=sys.stderr,
        )

    return pdb_paths, ddg_values, interface_scores


def _run_flexpep_direct(
    pose: "pyrosetta.Pose",
    output_pdb: str,
    cycles: int,
) -> Tuple["pyrosetta.Pose", float, float]:
    """AG_src import 없이 직접 FlexPepDockingProtocol을 호출한다.

    Returns:
        (refined_pose, ddg, interface_score)
    """
    import pyrosetta
    from pyrosetta.rosetta.protocols.flexpep_docking import FlexPepDockingProtocol
    from pyrosetta.rosetta.protocols.analysis import InterfaceAnalyzerMover

    # Disulfide 감지 (SST-14 Cys3-Cys14)
    try:
        pose.conformation().detect_disulfides()
        print("[wrapper] 이황화결합 auto-detect 완료", file=sys.stderr)
    except Exception as exc:
        print(f"[wrapper] detect_disulfides 실패 ({exc}), 계속", file=sys.stderr)

    fpd = FlexPepDockingProtocol()
    fpd.apply(pose)

    pose.dump_pdb(output_pdb)

    # ddG 계산
    iam = InterfaceAnalyzerMover(1)
    iam.set_pack_input(True)
    iam.set_pack_separated(True)
    iam.apply(pose)
    ddg = iam.get_interface_dG()
    interface_score = ddg

    return pose, ddg, interface_score


# ---------------------------------------------------------------------------
# 최종 스코어 집계
# ---------------------------------------------------------------------------

def aggregate_scores(
    ddg_values: List[float],
    interface_scores: List[float],
) -> Tuple[float, float]:
    """앙상블 스코어를 집계한다.

    전략: 최저 ddg (가장 유리한 결합 에너지) 기준으로 best 구조 선택.

    Raises:
        RuntimeError: ddg_values 가 빈 리스트인 경우 (mock 금지 정책).
            모든 nstruct 가 InterfaceAnalyzer 단계에서 실패한 상황으로,
            silent 으로 0.0 반환하면 가짜 데이터가 Hard Cutoff 통과 가능.

    Returns:
        (best_dG_kcal_mol, best_interface_score)
    """
    if not ddg_values:
        raise RuntimeError(
            "aggregate_scores: ddg_values 빈 리스트 — "
            "모든 nstruct InterfaceAnalyzer 실패. "
            "silent 0.0 fallback 금지 (mock 정책). caller 가 stub:True 명시 처리 필요."
        )

    best_idx = ddg_values.index(min(ddg_values))
    return ddg_values[best_idx], interface_scores[best_idx]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="FlexPepDock wrapper — flexpepdock_worker.py 호환 CLI"
    )
    parser.add_argument(
        "--receptor", required=True,
        help="수용체 PDB 또는 CIF 파일 경로",
    )
    parser.add_argument(
        "--sequence", required=True,
        help="14aa 펩타이드 시퀀스 (1-letter code)",
    )
    parser.add_argument(
        "--output-prefix", required=True,
        help="출력 PDB 파일 prefix (예: /tmp/test/docked)",
    )
    parser.add_argument(
        "--cycles", type=int, default=10,
        help="FlexPepDock refinement cycles (default: 10)",
    )
    parser.add_argument(
        "--nstruct", type=int, default=50,
        help="앙상블 크기 — FlexPepDock 반복 횟수 (default: 50)",
    )
    parser.add_argument(
        "--flex-pep-freedom", default="med",
        choices=["low", "med", "high"],
        help="펩타이드 유연성 수준 (default: med)",
    )
    parser.add_argument(
        "--ddg-cycle", type=int, default=5,
        help="ddG 계산 반복 횟수 (default: 5, 현재 미사용 — nstruct로 앙상블 대체)",
    )
    args = parser.parse_args()

    # 입력 파일 존재 확인
    if not Path(args.receptor).exists():
        print(
            json.dumps({"error": f"receptor 파일 없음: {args.receptor}"}),
            file=sys.stderr,
        )
        sys.exit(1)

    t_total = time.monotonic()

    # 1. PyRosetta 초기화
    init_pyrosetta()

    # 2. CIF → PDB 변환 (필요시)
    receptor_pdb = resolve_receptor_pdb(args.receptor)
    print(f"[wrapper] receptor PDB: {receptor_pdb}", file=sys.stderr)

    # 3. cycles 파라미터 조정 (flex-pep-freedom 적용)
    freedom_params = _FREEDOM_MAP.get(args.flex_pep_freedom, _FREEDOM_MAP["med"])
    effective_cycles = max(args.cycles, freedom_params["cycles"])
    effective_nstruct = args.nstruct * freedom_params.get("nstruct_multiplier", 1)
    print(
        f"[wrapper] flex_pep_freedom={args.flex_pep_freedom}: "
        f"cycles={effective_cycles}, nstruct={effective_nstruct}",
        file=sys.stderr,
    )

    # 4. Complex Pose 빌드
    print(f"[wrapper] complex 빌드 중: sequence={args.sequence}", file=sys.stderr)
    complex_pose = build_peptide_pose_from_sequence(args.sequence, receptor_pdb)
    print(
        f"[wrapper] complex: {complex_pose.total_residue()} residues, "
        f"{complex_pose.num_chains()} chains",
        file=sys.stderr,
    )

    # 5. 앙상블 도킹
    pdb_paths, ddg_values, interface_scores = run_ensemble_docking(
        pose=complex_pose,
        output_prefix=args.output_prefix,
        nstruct=effective_nstruct,
        cycles=effective_cycles,
    )

    elapsed = time.monotonic() - t_total
    print(f"[wrapper] 앙상블 완료: {len(pdb_paths)}/{effective_nstruct} 성공 ({elapsed:.1f}s)", file=sys.stderr)

    if not pdb_paths:
        print(
            json.dumps({"error": "모든 nstruct 실패 — 도킹 결과 없음"}),
            file=sys.stderr,
        )
        sys.exit(1)

    # 6. PDB 는 있는데 ddg_values 가 빈 경우 — InterfaceAnalyzer 전부 실패 (mock 금지)
    if pdb_paths and not ddg_values:
        print(
            json.dumps({
                "error": (
                    f"PDB {len(pdb_paths)}개 생성됐으나 ddg_values 빈 리스트 — "
                    "InterfaceAnalyzer 전부 실패. silent 0.0 fallback 금지 (mock 정책)."
                ),
                "stub": True,
                "stub_reason": "interface_analyzer_failed_all_nstruct",
                "pdb_paths": pdb_paths,
                "nstruct_total": effective_nstruct,
            }),
            file=sys.stderr,
        )
        sys.exit(2)

    # 7. 스코어 집계
    best_dg, best_interface = aggregate_scores(ddg_values, interface_scores)
    avg_dg = sum(ddg_values) / len(ddg_values)
    avg_interface = sum(interface_scores) / len(interface_scores)

    # 8. stdout에 JSON 출력 (worker가 json.loads로 파싱)
    result = {
        "dG_kcal_mol": round(best_dg, 4),
        "interface_score": round(best_interface, 4),
        "ddg": round(best_dg, 4),  # AG_src 호환 alias
        "avg_dG_kcal_mol": round(avg_dg, 4),
        "avg_interface_score": round(avg_interface, 4),
        "nstruct_success": len(pdb_paths),
        "nstruct_total": effective_nstruct,
        "pdb_paths": pdb_paths,
        "elapsed_sec": round(elapsed, 1),
        "stub": False,
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
