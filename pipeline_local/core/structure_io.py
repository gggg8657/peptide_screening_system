"""
structure_io.py
===============
구조 파일 I/O 유틸리티 — CIF/PDB 자동 감지 및 PyRosetta pose 로드

CIF (.cif, .mmcif) 와 PDB (.pdb) 형식을 투명하게 처리한다.
파이프라인 전 단계에서 단일 진입점(load_pose)을 통해 수용체 구조를 로드한다.

Public API:
    detect_format(path)       -> 'cif' | 'pdb'
    read_structure_text(path) -> str
    load_pose(path)           -> pyrosetta.Pose
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


# CIF 확장자 집합
_CIF_EXTENSIONS = frozenset({".cif", ".mmcif"})


def detect_format(path: str) -> str:
    """파일 확장자를 기반으로 구조 형식을 반환한다.

    Args:
        path: 구조 파일 경로

    Returns:
        'cif' (CIF/mmCIF 형식) 또는 'pdb' (PDB 형식)
    """
    suffix = Path(path).suffix.lower()
    return "cif" if suffix in _CIF_EXTENSIONS else "pdb"


def read_structure_text(path: str) -> str:
    """구조 파일을 텍스트로 읽어 반환한다.

    Args:
        path: 구조 파일 경로 (.cif, .mmcif, .pdb 모두 지원)

    Returns:
        파일 텍스트 내용 (UTF-8)
    """
    return Path(path).read_text(encoding="utf-8")


def _ensure_pyrosetta_init() -> None:
    """PyRosetta가 초기화되지 않은 경우 init()을 호출한다."""
    import pyrosetta  # type: ignore

    try:
        # init 여부 확인: 이미 초기화된 경우 rosetta.core가 활성화됨
        pyrosetta.rosetta.core.pose.Pose()
    except RuntimeError:
        # core::init 미호출 시 발생하는 에러 → init 실행
        pyrosetta.init("-mute all -ignore_unrecognized_res 1 -ignore_zero_occupancy false")
    except Exception:
        pass


def load_pose(path: str) -> Any:
    """CIF/PDB 형식을 자동 감지하여 PyRosetta Pose를 로드한다.

    PyRosetta의 pose_from_file()은 .cif/.pdb 확장자를 모두 지원한다.
    확장자가 .cif/.mmcif 이면 pose_from_file()을,
    그 외에는 pose_from_pdb()를 사용한다.

    Args:
        path: 구조 파일 경로

    Returns:
        pyrosetta.Pose 객체

    Raises:
        ImportError: PyRosetta 가 설치되지 않은 경우
        RuntimeError: 파일 로드 실패 시
    """
    _ensure_pyrosetta_init()
    fmt = detect_format(path)
    if fmt == "cif":
        # CIF/mmCIF: pose_from_file이 확장자 자동 감지 지원
        from pyrosetta import pose_from_file  # type: ignore
        return pose_from_file(path)
    # PDB: 표준 pose_from_pdb 사용
    from pyrosetta import pose_from_pdb  # type: ignore
    return pose_from_pdb(path)
