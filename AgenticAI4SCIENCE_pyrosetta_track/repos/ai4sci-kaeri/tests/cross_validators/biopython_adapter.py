"""
Biopython ProteinAnalysis 교차 검증 어댑터
==========================================
ExPASy ProtParam 알고리즘의 로컬 구현체인 Biopython ProteinAnalysis를
사용하여 pharma_properties.py 결과를 교차 검증합니다.

검증 가능 메서드 (5개):
    - GRAVY (Kyte-Doolittle 1982)
    - Instability Index (Guruprasad 1990)
    - Isoelectric Point (pI)
    - Molecular Weight
    - Extinction Coefficient (ε₂₈₀)

패키지: biopython (pip install biopython)
"""

from __future__ import annotations

from typing import Dict, Optional

_AVAILABLE = False
try:
    from Bio.SeqUtils.ProtParam import ProteinAnalysis
    _AVAILABLE = True
except ImportError:
    pass


def is_available() -> bool:
    """Biopython ProteinAnalysis 사용 가능 여부."""
    return _AVAILABLE


def compute(sequence: str) -> Optional[Dict[str, float]]:
    """서열의 물리화학적 성질을 Biopython으로 계산합니다.

    Parameters
    ----------
    sequence : str
        표준 20종 아미노산 1문자 코드.

    Returns
    -------
    dict 또는 None
        패키지 미설치 시 None.
        설치 시 {gravy, instability_index, pi, mw, extinction_coeff_ss,
                 extinction_coeff_reduced} 딕셔너리.
    """
    if not _AVAILABLE:
        return None

    pa = ProteinAnalysis(sequence)

    # ε₂₈₀: (Cys가 모두 SS bond, Cys가 모두 환원) 두 값 반환
    ext_ss, ext_red = pa.molar_extinction_coefficient()

    return {
        "gravy": pa.gravy(),
        "instability_index": pa.instability_index(),
        "pi": pa.isoelectric_point(),
        "mw": pa.molecular_weight(),
        "extinction_coeff_ss": float(ext_ss),
        "extinction_coeff_reduced": float(ext_red),
    }
