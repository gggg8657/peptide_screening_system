"""
modlAMP 교차 검증 어댑터
========================
AMP(항균 펩타이드) descriptor 계산 패키지인 modlAMP을 사용하여
pharma_properties.py와 독립적으로 동일 메서드를 교차 검증합니다.

peptides PyPI와 **완전히 다른 코드베이스**이므로,
3자 교차 검증(우리/peptides/modlAMP) 구성에 핵심입니다.

검증 가능 메서드 (8개):
    - GRAVY (Kyte-Doolittle)
    - Boman Index
    - Instability Index
    - Aliphatic Index
    - Isoelectric Point (pI)
    - Hydrophobic Moment (μH)
    - Molecular Weight
    - Net Charge (pH 7.4)

패키지: modlamp (pip install modlamp)
"""

from __future__ import annotations

from typing import Dict, Optional

_AVAILABLE = False
try:
    from modlamp.descriptors import GlobalDescriptor, PeptideDescriptor
    _AVAILABLE = True
except ImportError:
    pass


def is_available() -> bool:
    """modlAMP 사용 가능 여부."""
    return _AVAILABLE


def compute(sequence: str, ph: float = 7.4) -> Optional[Dict[str, float]]:
    """서열의 물리화학적 성질을 modlAMP으로 계산합니다.

    Parameters
    ----------
    sequence : str
        표준 20종 아미노산 1문자 코드.
    ph : float
        Net charge 계산 pH (기본 7.4).

    Returns
    -------
    dict 또는 None
        패키지 미설치 시 None.
    """
    if not _AVAILABLE:
        return None

    # GlobalDescriptor: 단일 서열을 리스트로 감싸서 전달
    gd = GlobalDescriptor([sequence])

    result: Dict[str, float] = {}

    # MW
    gd.calculate_MW()
    result["mw"] = float(gd.descriptor[0][0])

    # pI
    gd.isoelectric_point()
    result["pi"] = float(gd.descriptor[0][0])

    # Instability Index
    gd.instability_index()
    result["instability_index"] = float(gd.descriptor[0][0])

    # Aliphatic Index
    gd.aliphatic_index()
    result["aliphatic_index"] = float(gd.descriptor[0][0])

    # Boman Index
    gd.boman_index()
    result["boman_index"] = float(gd.descriptor[0][0])

    # Net Charge at pH
    gd.calculate_charge(ph=ph)
    result["net_charge"] = float(gd.descriptor[0][0])

    # GRAVY (Kyte-Doolittle 스케일)
    pd = PeptideDescriptor([sequence], scalename="KyteDoolittle")
    pd.calculate_global()
    result["gravy"] = float(pd.descriptor[0][0])

    # Hydrophobic Moment (α-helix, angle=100°, window=min(11, len))
    pd_moment = PeptideDescriptor([sequence], scalename="Eisenberg")
    window = min(11, len(sequence))
    pd_moment.calculate_moment(window=window)
    result["hydrophobic_moment"] = float(pd_moment.descriptor[0][0])

    return result
