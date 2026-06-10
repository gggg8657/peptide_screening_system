"""
peptides PyPI 교차 검증 어댑터
==============================
기존 test_pharma_vs_peptides_pkg.py에서 사용하던 peptides 패키지를
통일된 어댑터 인터페이스로 래핑합니다.

검증 가능 메서드 (8개):
    - GRAVY, Boman Index, Instability Index, Aliphatic Index
    - pI, Hydrophobic Moment, Net Charge, MW

패키지: peptides (pip install peptides)
"""

from __future__ import annotations

from typing import Dict, Optional

_AVAILABLE = False
try:
    import peptides as _peptides_pkg
    _AVAILABLE = True
except ImportError:
    pass


def is_available() -> bool:
    """peptides 패키지 사용 가능 여부."""
    return _AVAILABLE


def compute(sequence: str, ph: float = 7.4) -> Optional[Dict[str, float]]:
    """서열의 물리화학적 성질을 peptides 패키지로 계산합니다.

    Returns
    -------
    dict 또는 None
        패키지 미설치 시 None.
    """
    if not _AVAILABLE:
        return None

    pep = _peptides_pkg.Peptide(sequence)
    window = min(11, len(sequence))

    return {
        "gravy": pep.hydrophobicity(scale="KyteDoolittle"),
        "boman_index": pep.boman(),
        "instability_index": pep.instability_index(),
        "aliphatic_index": pep.aliphatic_index(),
        "pi": pep.isoelectric_point(pKscale="Lehninger"),
        "hydrophobic_moment": float(pep.hydrophobic_moment(window=window, angle=100)),
        "net_charge": pep.charge(pH=ph, pKscale="Lehninger"),
        "mw": pep.molecular_weight(average="expasy"),
    }
