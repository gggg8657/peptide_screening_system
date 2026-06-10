"""
Pyteomics 교차 검증 어댑터
==========================
질량분석(Mass Spectrometry) 기반 프로테오믹스 도구인 Pyteomics를 사용하여
MW, pI, Charge, Protease Sites를 교차 검증합니다.

특장점:
    - MW: 동위원소 수준 고정밀 질량 계산 (monoisotopic/average 선택 가능)
    - Protease Sites: Trypsin, Chymotrypsin, Pepsin 등 주요 프로테아제
      절단 규칙이 내장되어 있어, 우리 count_protease_sites()를 검증할 수 있는
      유일한 프로그래밍 도구입니다.

검증 가능 메서드 (4개):
    - Molecular Weight (고정밀)
    - Isoelectric Point (pI)
    - Net Charge (pH 7.4)
    - Protease Cleavage Sites (trypsin, chymotrypsin)

패키지: pyteomics (pip install pyteomics)
"""

from __future__ import annotations

from typing import Dict, List, Optional

_AVAILABLE = False
try:
    from pyteomics import mass, electrochem, parser
    _AVAILABLE = True
except ImportError:
    pass


def is_available() -> bool:
    """Pyteomics 사용 가능 여부."""
    return _AVAILABLE


def compute(sequence: str, ph: float = 7.4) -> Optional[Dict]:
    """서열의 물리화학적 성질을 Pyteomics로 계산합니다.

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

    result: Dict = {}

    # MW (평균 동위원소 질량)
    try:
        result["mw"] = mass.calculate_mass(sequence=sequence, average=True)
    except Exception:
        result["mw"] = None

    # pI
    try:
        result["pi"] = electrochem.pI(sequence)
    except Exception:
        result["pi"] = None

    # Net Charge at pH
    try:
        result["net_charge"] = electrochem.charge(sequence, ph)
    except Exception:
        result["net_charge"] = None

    # Protease Cleavage Sites
    result["protease_sites"] = {}
    for enzyme_name in ("trypsin", "chymotrypsin low specificity"):
        try:
            rule = parser.expasy_rules.get(enzyme_name)
            if rule:
                fragments = parser.cleave(sequence, rule)
                # 절단 횟수 = 조각 수 - 1
                result["protease_sites"][enzyme_name] = len(fragments) - 1
        except Exception:
            result["protease_sites"][enzyme_name] = None

    return result
