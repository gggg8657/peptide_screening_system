"""radiolysis_scorer.py
======================
방사선 분해(Radiolysis) 민감도 점수 산출 모듈.

177Lu 방사선에 의한 펩타이드 분해에 취약한 잔기를 정량화한다.

서호성 박사 제안 민감도 등급 (A-04, KAERI-AIRL-MOM-2026-003):
    C, M: 최고 민감도 (3점/개)
    F, Y, W: 높은 민감도 (2점/개)
    P, H, L: 낮은 민감도 (1점/개)

Hard Cutoff 기준: sensitive_count ≤ 3 (잔기 개수 기준, 점수 합 아님)

Cys3-Cys14 SS bond 예외:
    SST-14 핵심 고리화 결합(Cys3-Cys14)은 치환 불가 구조 → 스코어 산출 시 제외.
    ss_bond_intact 플래그로 SS bond 보존 여부를 별도 관리한다.

HEURISTIC 주의:
    이 모듈의 점수는 계산 기반 대리 지표(proxy)이며 실험적 RCP(Radiochemical Purity) 값을
    대체하지 않는다. 최종 확인은 177Lu 표지 후 72시간 HPLC RCP ≥ 90% 기준으로 수행한다.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 잔기별 Radiolysis 민감도 점수 (서호성 박사 제안, A-04)
# 키: 1글자 아미노산 코드, 값: 점수
# ---------------------------------------------------------------------------
RADIOLYSIS_SENSITIVITY: Dict[str, int] = {
    "C": 3,  # Cysteine — 최고 민감도 (산화 후 β-mercaptoethanol 방출)
    "M": 3,  # Methionine — 최고 민감도 (황 산화)
    "F": 2,  # Phenylalanine — 높음 (방향족 고리 산화)
    "Y": 2,  # Tyrosine — 높음 (방향족 하이드록실 라디칼 반응)
    "W": 2,  # Tryptophan — 높음 (인돌 고리 산화)
    "P": 1,  # Proline — 낮음 (고리 구조 라디칼 취약)
    "H": 1,  # Histidine — 낮음 (이미다졸 산화)
    "L": 1,  # Leucine — 낮음 (지방족 라디칼 취약)
}

# Hard Cutoff 임계값: 민감 잔기 개수 ≤ 3 (A-04 §Step 2)
HARD_CUTOFF_SENSITIVE_COUNT: int = 3


def compute_radiolysis_score(
    sequence: str,
    ss_bond_positions: Tuple[int, ...] = (3, 14),
) -> Dict[str, object]:
    """서열의 Radiolysis 민감도 점수를 산출한다.

    SS bond 위치의 Cys 잔기는 핵심 고리화 결합으로 치환 불가 → 점수 계산 제외.
    SS bond 양쪽 위치 모두 Cys인 경우 ss_bond_intact = True.

    Args:
        sequence:          아미노산 서열 (1글자 코드, 대소문자 무관)
        ss_bond_positions: SS bond를 형성하는 Cys 위치 (1-indexed 정수 tuple).
                           기본값: (3, 14) — SST-14 Cys3-Cys14.

    Returns:
        dict:
            "radiolysis_score": int   — 총 점수 합 (SS bond Cys 제외)
            "sensitive_count":  int   — 민감 잔기 개수 (SS bond Cys 제외)
            "ss_bond_intact":   bool  — SS bond 위치 모두 Cys 여부
            "details":          dict  — 잔기 코드별 카운트 {"W": 1, "F": 2, ...}

    Raises:
        ValueError: sequence가 빈 문자열인 경우
    """
    if not sequence:
        raise ValueError("sequence는 빈 문자열일 수 없습니다.")

    seq = sequence.upper()
    n = len(seq)

    # 0-indexed SS bond 위치 집합 (유효 범위만 포함)
    ss_idx_0: frozenset[int] = frozenset(
        pos - 1 for pos in ss_bond_positions if 1 <= pos <= n
    )

    # SS bond 보존 여부: 지정 위치가 모두 Cys
    ss_bond_intact: bool = all(seq[i] == "C" for i in ss_idx_0 if i < n)

    # 점수 누적 (SS bond 위치의 Cys는 제외)
    total_score: int = 0
    count: int = 0
    details: Dict[str, int] = {}

    for i, aa in enumerate(seq):
        # SS bond 위치 Cys → 제외
        if i in ss_idx_0 and aa == "C":
            continue
        score = RADIOLYSIS_SENSITIVITY.get(aa, 0)
        if score > 0:
            total_score += score
            count += 1
            details[aa] = details.get(aa, 0) + 1

    return {
        "radiolysis_score": total_score,
        "sensitive_count": count,
        "ss_bond_intact": ss_bond_intact,
        "details": details,
    }


def passes_hard_cutoff(radiolysis_result: Dict[str, object]) -> bool:
    """Radiolysis Hard Cutoff 통과 여부를 반환한다.

    기준: sensitive_count ≤ HARD_CUTOFF_SENSITIVE_COUNT (= 3)

    Args:
        radiolysis_result: compute_radiolysis_score() 반환값

    Returns:
        True if passes Hard Cutoff, False otherwise
    """
    return int(radiolysis_result["sensitive_count"]) <= HARD_CUTOFF_SENSITIVE_COUNT
