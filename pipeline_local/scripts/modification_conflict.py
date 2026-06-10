"""modification_conflict.py
==========================
Chemical and structural conflict checker for peptide modifications.

펩타이드 modification 조합의 화학적·구조적 충돌을 탐지하는 체커.
SST-14 (AGCKNFFWKTFTSC) 기반 SSTR2 바인더 최적화 파이프라인에서
step08_stability.py 가 제안하는 modification 조합의 사전 검증에 사용.

규칙 근거 출처:
  - Knudsen 2019: Knudsen LB, Lau J (2019) "The Discovery and Development of
    Liraglutide and Semaglutide." Front Endocrinol 10:155. doi:10.3389/fendo.2019.00155
  - DOTATATE 화학: Reubi JC et al. (2000) "Somatostatin receptor sst1-sst5
    expression in normal and neoplastic human tissues using receptor autoradiography
    with subtype-selective ligands." Eur J Nucl Med 28:836-846.
  - Merrifield 화학: Merrifield RB (1963) "Solid Phase Peptide Synthesis."
    J Am Chem Soc 85:2149-2154. (Gly 키랄성 기술)

Public API:
    Conflict      — 충돌 정보를 담는 dataclass
    check_conflicts(sequence, modifications) -> list[Conflict]
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 데이터클래스
# ---------------------------------------------------------------------------

@dataclass
class Conflict:
    """단일 충돌 결과.

    Attributes:
        severity:      충돌 심각도 ("ERROR" | "WARNING")
        rule_id:       규칙 식별자 (예: "C-01")
        description:   사람 친화적 설명 (한국어)
        mods_involved: 충돌에 관여한 modification 인덱스 (0-based, input 리스트 기준)
        suggestion:    권장 수정 방향
    """

    severity: str
    rule_id: str
    description: str
    mods_involved: Tuple[int, ...]
    suggestion: str


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _get_residue(sequence: str, position: int) -> Optional[str]:
    """1-indexed position에서 1-letter 아미노산 코드를 반환.

    Args:
        sequence: 아미노산 서열 (대문자, 1-letter code)
        position: 1-indexed 위치

    Returns:
        1-letter code (str) 또는 범위 밖이면 None
    """
    idx = position - 1
    if idx < 0 or idx >= len(sequence):
        return None
    return sequence[idx]


def _find_cys_pairs(sequence: str) -> List[Tuple[int, int]]:
    """시퀀스에서 이황화결합(SS bond) 가능한 Cys 쌍 위치를 탐지.

    최소 4잔기 간격을 가진 Cys 쌍만 반환 (step08_stability.py 기준 일치).
    반환값은 0-based 인덱스 쌍.

    근거: DOTATATE Cys3-Cys14 SS bond topology
          Reubi 2000; Baker & Squire 2005 Chem Biol 12:103

    Args:
        sequence: 아미노산 서열 (대문자)

    Returns:
        (i, j) 쌍의 리스트 (0-based, i < j, j - i >= 4)
    """
    cys_indices = [i for i, aa in enumerate(sequence) if aa == "C"]
    pairs: List[Tuple[int, int]] = []
    for i in range(len(cys_indices)):
        for j in range(i + 1, len(cys_indices)):
            if (cys_indices[j] - cys_indices[i]) >= 4:
                pairs.append((cys_indices[i], cys_indices[j]))
    return pairs


# ---------------------------------------------------------------------------
# 규칙 함수들
# ---------------------------------------------------------------------------

def _rule_c01_same_position_fatty_peg(
    sequence: str,
    modifications: List[dict],
) -> List[Conflict]:
    """C-01: 동일 position에 fatty_acid + pegylation 동시 부착 불가.

    화학적 근거: Lys 측쇄 ε-amine(ε-NH2)은 단일 친핵성 부위이므로
    NHS-ester 활성화된 지방산과 PEG 링커 중 하나만 결합 가능.
    두 개의 acylation 시약이 경쟁적으로 반응하나 단일 아민에는 모노-치환만 허용.

    출처: Knudsen & Lau 2019 Front Endocrinol 10:155 — 세마글루타이드
          C18 지방산의 K26 ε-NH2 단일 결합 전략 설명.
    """
    conflicts: List[Conflict] = []
    # position → (mod_type, index) 맵 구축
    position_map: dict = {}
    for idx, mod in enumerate(modifications):
        pos = mod.get("position")
        mtype = mod.get("mod_type", "")
        if pos is None:
            continue
        if pos not in position_map:
            position_map[pos] = []
        position_map[pos].append((mtype, idx))

    for pos, entries in position_map.items():
        fatty_entries = [(mt, i) for mt, i in entries if mt == "fatty_acid"]
        peg_entries = [(mt, i) for mt, i in entries if mt == "pegylation"]
        if fatty_entries and peg_entries:
            involved = [i for _, i in fatty_entries] + [i for _, i in peg_entries]
            aa = _get_residue(sequence, pos) or "?"
            conflicts.append(Conflict(
                severity="ERROR",
                rule_id="C-01",
                description=(
                    f"position {pos}({aa})에 fatty_acid와 pegylation이 동시에 지정됨. "
                    "Lys ε-NH2는 단일 acylation 부위로 두 수식기가 경쟁 반응."
                ),
                mods_involved=tuple(sorted(set(involved))),
                suggestion=(
                    f"fatty_acid 또는 pegylation 중 하나만 position {pos}에 적용. "
                    "PEG는 N-말단(position 1)이나 다른 Lys에 이동 권장."
                ),
            ))
    return conflicts


def _rule_c02_fatty_acid_non_lys(
    sequence: str,
    modifications: List[dict],
) -> List[Conflict]:
    """C-02: fatty_acid를 Lys(K)가 아닌 비-N-terminal 위치에 적용.

    화학적 근거: C18 지방산 NHS-ester 아실화는 Lys ε-NH2 또는 N-term α-NH2
    에만 선택적으로 일어난다. 다른 측쇄(Ser, Thr OH기 등)는 생리적 pH에서
    반응성이 극히 낮아 실질적으로 부위-선택적이지 않음.

    N-terminal(position 1)은 α-NH2 아실화로 허용 (Merrifield chemistry).
    Lys(K) 위치는 허용.
    그 외 위치는 ERROR.

    출처: Knudsen & Lau 2019 Front Endocrinol 10:155 — 세마글루타이드 K26 선택성.
    """
    conflicts: List[Conflict] = []
    for idx, mod in enumerate(modifications):
        if mod.get("mod_type") != "fatty_acid":
            continue
        pos = mod.get("position")
        if pos is None:
            continue
        aa = _get_residue(sequence, pos)
        if aa is None:
            continue  # C-06에서 별도 처리
        # N-terminal(pos==1) 또는 Lys(K)이면 허용
        if pos == 1 or aa == "K":
            continue
        conflicts.append(Conflict(
            severity="ERROR",
            rule_id="C-02",
            description=(
                f"fatty_acid를 {aa}{pos}에 적용 시도. "
                "지방산 NHS-ester 아실화는 Lys(ε-NH2) 또는 N-terminal(α-NH2)에만 선택적."
            ),
            mods_involved=(idx,),
            suggestion=(
                f"fatty_acid를 Lys(K) 잔기 또는 N-terminal(position 1)로 이동. "
                f"현재 서열의 Lys 위치: "
                f"{[i+1 for i, r in enumerate(sequence) if r == 'K'] or '없음'}."
            ),
        ))
    return conflicts


def _rule_c03_d_amino_on_gly(
    sequence: str,
    modifications: List[dict],
) -> List[Conflict]:
    """C-03: d_amino_acid를 Gly(G) 위치에 적용 — no-op WARNING.

    화학적 근거: Glycine은 α-탄소에 수소 두 개를 가지는 유일한 아미노산으로
    입체이성질 중심(chiral center)이 없다. 따라서 D-Gly과 L-Gly은 동일한
    화합물이며 치환이 안정성/약동학에 실질적 효과 없음.

    출처: Merrifield RB (1963) J Am Chem Soc 85:2149 (Gly 비키랄성 기본 화학).
    """
    conflicts: List[Conflict] = []
    for idx, mod in enumerate(modifications):
        if mod.get("mod_type") != "d_amino_acid":
            continue
        pos = mod.get("position")
        if pos is None:
            continue
        aa = _get_residue(sequence, pos)
        if aa == "G":
            conflicts.append(Conflict(
                severity="WARNING",
                rule_id="C-03",
                description=(
                    f"d_amino_acid를 Gly{pos}에 적용. "
                    "Gly은 키랄 중심이 없어 D-Gly = L-Gly — 안정성 효과 없음(no-op)."
                ),
                mods_involved=(idx,),
                suggestion=(
                    "Gly 위치의 D-아미노산 치환은 제거하고, "
                    "프로테아제 취약성이 높은 인접 잔기(K, R, F, W)를 D-form으로 치환 권장."
                ),
            ))
    return conflicts


def _rule_c04_d_amino_on_cys_ss(
    sequence: str,
    modifications: List[dict],
) -> List[Conflict]:
    """C-04: d_amino_acid를 Cys-Cys SS bond 위치에 적용 — SS 토폴로지 손상 ERROR.

    구조적 근거: SST-14의 Cys3-Cys14 이황화결합은 생물활성 환형 구조의
    핵심. Cys를 D-Cys로 치환하면 측쇄 χ1 이면각이 변화하여 SS bond
    형성 기하가 왜곡되고, SSTR2 결합에 필수인 β-turn 구조가 손상될 수 있음.
    Veber 1978 실측 결과 D-Cys 치환 시 활성 ~10× 감소. reviewer-chemistry +
    reviewer-pharma 교차 검증으로 ERROR로 격상 결정 (Phase 5 A-3).

    출처: Reubi JC et al. (2000) Eur J Nucl Med 28:836 — DOTATATE SS topology.
          Veber DF et al. (1978) "Conformationally restricted bicyclic analogs of
          somatostatin." PNAS 75:2636 — Cys D/L 치환 활성 ~10× 감소 실측.
          Pellegrini & Mierke (1999) Biopolymers 51:208 — somatostatin β-turn.
    """
    conflicts: List[Conflict] = []
    # 서열 내 Cys 쌍 탐지 (SS bond 예측 위치)
    cys_pairs = _find_cys_pairs(sequence)
    ss_positions_0based = set()
    for i, j in cys_pairs:
        ss_positions_0based.add(i)
        ss_positions_0based.add(j)

    for idx, mod in enumerate(modifications):
        if mod.get("mod_type") != "d_amino_acid":
            continue
        pos = mod.get("position")
        if pos is None:
            continue
        aa = _get_residue(sequence, pos)
        if aa == "C" and (pos - 1) in ss_positions_0based:
            conflicts.append(Conflict(
                severity="ERROR",
                rule_id="C-04",
                description=(
                    f"d_amino_acid를 Cys{pos}에 적용. "
                    "이 Cys는 SS bond 쌍에 포함되어 있어 D-Cys 치환 시 "
                    "이황화결합 기하 왜곡 및 SSTR2 결합 β-turn 손상. "
                    "Veber 1978 실측: D-Cys 치환 → 활성 ~10× 감소."
                ),
                mods_involved=(idx,),
                suggestion=(
                    "SS bond를 유지하려면 Cys 위치의 D-아미노산 치환을 제거. "
                    "프로테아제 저항이 목적이라면 SS bond 비참여 잔기에 D-form 적용 권장."
                ),
            ))
    return conflicts


def _rule_c05_duplicate_cyclization(
    sequence: str,
    modifications: List[dict],
) -> List[Conflict]:
    """C-05: 자연 Cys-Cys SS bond가 존재하는데 cyclization modification을 추가 시도.

    화학적 근거: 서열 내 Cys 쌍이 존재하면 산화 조건에서 자발적으로
    이황화결합이 형성되어 환형이 된다(DOTATATE 구조). 이 상태에서
    또다른 cyclization을 적용하면 (1) 중복 비용 발생, (2) 두 번째 고리화가
    SS bond 포함 잔기와 반응할 경우 입체 충돌.

    출처: Reubi 2000 DOTATATE SS bond topology.
    """
    conflicts: List[Conflict] = []
    cys_pairs = _find_cys_pairs(sequence)
    has_natural_cyclization = len(cys_pairs) > 0

    if not has_natural_cyclization:
        return conflicts

    cyc_indices = [
        idx for idx, mod in enumerate(modifications)
        if mod.get("mod_type") == "cyclization"
    ]
    if cyc_indices:
        cys_positions_1based = [
            (i + 1, j + 1) for i, j in cys_pairs
        ]
        conflicts.append(Conflict(
            severity="WARNING",
            rule_id="C-05",
            description=(
                f"시퀀스 내 Cys-Cys 쌍 {cys_positions_1based}에 의한 자연 고리화가 "
                "이미 존재하는데 cyclization modification이 추가로 지정됨 — 중복."
            ),
            mods_involved=tuple(cyc_indices),
            suggestion=(
                "자연 SS bond(Cys-Cys)가 있으므로 별도 cyclization modification은 제거. "
                "추가 고리화가 필요하다면 비-SS bond 방식(lactam, head-to-tail)을 별도 명시."
            ),
        ))
    return conflicts


def _rule_c06_out_of_range_position(
    sequence: str,
    modifications: List[dict],
) -> List[Conflict]:
    """C-06: position이 시퀀스 길이 범위 밖 — INDEX_ERROR.

    1-indexed position이 1 미만이거나 len(sequence) 초과인 경우.

    출처: 기본 배열 인덱스 유효성 (language-agnostic).
    """
    conflicts: List[Conflict] = []
    seq_len = len(sequence)

    for idx, mod in enumerate(modifications):
        pos = mod.get("position")
        if pos is None:
            continue
        # 정수 여부 확인 (bool은 int 서브클래스이므로 명시적 제외)
        if not isinstance(pos, int) or isinstance(pos, bool):
            conflicts.append(Conflict(
                severity="ERROR",
                rule_id="C-06",
                description=(
                    f"modification[{idx}] position={pos!r}이 정수가 아님. "
                    "position은 1-indexed 정수여야 함."
                ),
                mods_involved=(idx,),
                suggestion="position을 1 이상의 정수로 지정.",
            ))
            continue
        if pos < 1 or pos > seq_len:
            conflicts.append(Conflict(
                severity="ERROR",
                rule_id="C-06",
                description=(
                    f"modification[{idx}] position={pos}이 서열 범위 밖. "
                    f"서열 길이={seq_len}, 허용 범위=[1, {seq_len}]."
                ),
                mods_involved=(idx,),
                suggestion=(
                    f"position을 1~{seq_len} 범위 내로 조정. "
                    f"현재 서열: {sequence}"
                ),
            ))
    return conflicts


# ---------------------------------------------------------------------------
# C-07~C-10 추가 규칙 (Phase 5 A-7 — reviewer-chemistry 권고)
# ---------------------------------------------------------------------------
# §검증 필요: C-07 (DOTA chelator 이중 결합)은 현재 mod_type 어휘에 "dota_conjugation"
# 이 부재하여 구현 불가. step08_stability.py 어휘 확장 RFC 완료 후 도입 예정.


def _rule_c07_dota_double_conjugation(
    sequence: str,
    modifications: List[dict],
) -> List[Conflict]:
    """C-07: DOTA chelator는 펩타이드당 1개만 결합 가능 (stoichiometry).

    DOTA(1,4,7,10-tetraazacyclododecane-1,4,7,10-tetraacetic acid)는 theranostic
    라벨링에 사용되는 macrocyclic chelator로 한 분자가 1개의 metal isotope
    (68Ga, 177Lu, 90Y 등)와 결합한다. 펩타이드에 DOTA를 2개 이상 부착하면:
      - radioisotope stoichiometry 손상 (specific activity 예측 불가)
      - 결합 위치 경쟁으로 합성 효율 저하
      - chelator 간 입체 충돌 가능성

    근거: Reubi JC et al. (2000) Eur J Nucl Med 28:836 — DOTATATE 라벨링 화학;
          Wadas TJ et al. (2010) Chem Rev 110:2858 — DOTA stoichiometry 원칙.

    적용 mod_type: "dota", "dota_conjugation", "DOTA" (case-insensitive).

    severity: ERROR — radiotherapeutic 적용 불가.
    """
    conflicts: List[Conflict] = []
    dota_indices = [
        i for i, mod in enumerate(modifications)
        if str(mod.get("mod_type", "")).lower() in ("dota", "dota_conjugation")
    ]
    if len(dota_indices) >= 2:
        conflicts.append(Conflict(
            severity="ERROR",
            rule_id="C-07",
            description=(
                f"DOTA chelator가 {len(dota_indices)}개 지정됨 "
                f"(modification 인덱스 {dota_indices}). DOTA는 펩타이드당 "
                f"1개만 부착 가능 (metal isotope binding stoichiometry — 68Ga/177Lu/90Y)."
            ),
            mods_involved=tuple(dota_indices),
            suggestion=(
                "DOTA conjugation은 1개로 제한하세요. 다중 라벨링이 필요하면 "
                "다른 chelator(NOTA, DOTAGA)를 추가로 사용하되 각각 단일성 보장."
            ),
        ))
    return conflicts


def _rule_c08_double_dcys_on_ss_pair(
    sequence: str,
    modifications: List[dict],
) -> List[Conflict]:
    """C-08: SS bond 양쪽 Cys에 동시 d_amino_acid 적용 — D,D-cystine geometry ERROR.

    화학적 근거: SS pair의 두 Cys를 모두 D-Cys로 치환하면 D,D-cystine이 형성될 수
    있으나, SST-14 β-turn topology와 incompatible(거울상 구조). 더불어 한쪽 D-Cys
    (C-04)보다 더 큰 구조적 왜곡을 초래하므로 별도 ERROR로 분리.

    출처: Mosberg HI et al. (1983) "Constrained analogs of enkephalin containing
          D,D-cystine." PNAS 80:5871 — D,D-cystine bicyclic 구조 비호환성.
          Veber DF et al. (1978) PNAS 75:2636 — SST-14 Cys D/L 치환 활성 감소.
    """
    conflicts: List[Conflict] = []
    cys_pairs = _find_cys_pairs(sequence)
    if not cys_pairs:
        return conflicts

    # SS bond 위치 별로 d_amino_acid mod 인덱스 수집
    for cys_i_0, cys_j_0 in cys_pairs:
        pos_i = cys_i_0 + 1  # 1-indexed
        pos_j = cys_j_0 + 1
        d_on_i = [
            idx for idx, m in enumerate(modifications)
            if m.get("mod_type") == "d_amino_acid" and m.get("position") == pos_i
        ]
        d_on_j = [
            idx for idx, m in enumerate(modifications)
            if m.get("mod_type") == "d_amino_acid" and m.get("position") == pos_j
        ]
        if d_on_i and d_on_j:
            involved = tuple(sorted(d_on_i + d_on_j))
            conflicts.append(Conflict(
                severity="ERROR",
                rule_id="C-08",
                description=(
                    f"SS bond 쌍 Cys{pos_i}-Cys{pos_j} 양쪽에 d_amino_acid 동시 지정. "
                    "D,D-cystine 형성 시 SST-14 β-turn topology와 incompatible."
                ),
                mods_involved=involved,
                suggestion=(
                    "두 Cys 중 하나의 D-아미노산 치환만 허용하거나, "
                    "SS bond 비참여 잔기에 D-form 적용 권장."
                ),
            ))
    return conflicts


def _rule_c09_lactam_cyclization_nterm_mod(
    sequence: str,
    modifications: List[dict],
) -> List[Conflict]:
    """C-09: head-to-tail cyclization(lactam) + N-terminal modification 충돌 ERROR.

    화학적 근거: head-to-tail lactam cyclization은 N-term α-NH2를 C-term α-COOH와
    amide bond로 소비. 이후 N-term에 fatty_acid/pegylation을 시도하면 결합할
    1차 아민이 없음.

    출처: Davies JS (2003) "The cyclization of peptides and depsipeptides."
          J Pept Sci 9:471-501 — head-to-tail cyclic peptide N-term 비가용성.
          Knudsen & Lau 2019 Front Endocrinol 10:155 — N-term acylation 화학.
    """
    conflicts: List[Conflict] = []
    # cyclization이 있는지 확인 (mod_type == "cyclization")
    cyc_mods = [
        (idx, m) for idx, m in enumerate(modifications)
        if m.get("mod_type") == "cyclization"
    ]
    if not cyc_mods:
        return conflicts

    # N-terminal modification: position=1 의 fatty_acid 또는 pegylation
    nterm_mods = [
        (idx, m) for idx, m in enumerate(modifications)
        if m.get("position") == 1
        and m.get("mod_type") in ("fatty_acid", "pegylation")
    ]
    if not nterm_mods:
        return conflicts

    cyc_indices = tuple(idx for idx, _ in cyc_mods)
    nterm_indices = tuple(idx for idx, _ in nterm_mods)
    involved = tuple(sorted(set(cyc_indices + nterm_indices)))

    conflicts.append(Conflict(
        severity="ERROR",
        rule_id="C-09",
        description=(
            "cyclization(head-to-tail)과 N-terminal(position=1) fatty_acid/pegylation 동시 지정. "
            "cyclization이 N-term α-NH2를 소비하여 acylation 부위 없음."
        ),
        mods_involved=involved,
        suggestion=(
            "cyclization과 N-terminal acylation 중 하나만 선택. "
            "cyclization을 유지하려면 N-term mod를 제거. "
            "N-term acylation이 목적이면 cyclization을 제거."
        ),
    ))
    return conflicts


def _rule_c10_substitution_and_damino_same_position(
    sequence: str,
    modifications: List[dict],
) -> List[Conflict]:
    """C-10: 동일 position에 substitution + d_amino_acid 동시 지정 — 의미 충돌 ERROR.

    화학적 근거: substitution은 잔기 자체를 다른 아미노산으로 교체 (예: K→Orn),
    d_amino_acid는 키랄성만 D로 바꿈. 같은 position에 둘 다 지정되면
    (1) 의미 모호(substituted 결과 잔기의 D form인가?),
    (2) SPPS SOP에서 발주할 Fmoc 빌딩블록 결정 불가.

    출처: (pipeline schema 무결성 — 외부 문헌 불필요).
    """
    conflicts: List[Conflict] = []
    # position → (mod_type, idx) 맵
    position_map: dict = {}
    for idx, mod in enumerate(modifications):
        pos = mod.get("position")
        if pos is None:
            continue
        position_map.setdefault(pos, []).append((mod.get("mod_type", ""), idx))

    for pos, entries in position_map.items():
        sub_entries = [(mt, i) for mt, i in entries if mt == "substitution"]
        d_entries = [(mt, i) for mt, i in entries if mt == "d_amino_acid"]
        if sub_entries and d_entries:
            involved = tuple(sorted(
                set([i for _, i in sub_entries] + [i for _, i in d_entries])
            ))
            aa = _get_residue(sequence, pos) or "?"
            conflicts.append(Conflict(
                severity="ERROR",
                rule_id="C-10",
                description=(
                    f"position {pos}({aa})에 substitution과 d_amino_acid 동시 지정. "
                    "substitution(잔기 교체)과 d_amino_acid(키랄 변환)의 의미가 충돌 — "
                    "발주 Fmoc 빌딩블록 결정 불가."
                ),
                mods_involved=involved,
                suggestion=(
                    "substitution(잔기 교체) 또는 d_amino_acid(D-form 키랄 변환) 중 하나만 선택. "
                    "D-치환 잔기(예: D-Orn)를 원한다면 substitution의 target 필드에 명시."
                ),
            ))
    return conflicts


# ---------------------------------------------------------------------------
# 규칙 레지스트리
# ---------------------------------------------------------------------------

# 각 규칙 함수의 타입: (sequence, modifications) -> list[Conflict]
_RuleFunc = Callable[[str, List[dict]], List[Conflict]]

_RULES: List[Tuple[str, _RuleFunc]] = [
    # C-06을 첫 번째로 배치 — 범위/타입 유효성을 선행 차단하여
    # 다른 규칙이 비-int position으로 TypeError를 일으키지 않게 함 (A-6).
    ("C-06", _rule_c06_out_of_range_position),
    ("C-01", _rule_c01_same_position_fatty_peg),
    ("C-02", _rule_c02_fatty_acid_non_lys),
    ("C-03", _rule_c03_d_amino_on_gly),
    ("C-04", _rule_c04_d_amino_on_cys_ss),
    ("C-05", _rule_c05_duplicate_cyclization),
    # Phase 5 A-7 추가 규칙
    # VR-cycle-01 closure (Stage 8g): C-07 DOTA chelator stoichiometry 추가
    ("C-07", _rule_c07_dota_double_conjugation),
    ("C-08", _rule_c08_double_dcys_on_ss_pair),
    ("C-09", _rule_c09_lactam_cyclization_nterm_mod),
    ("C-10", _rule_c10_substitution_and_damino_same_position),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_conflicts(
    sequence: str,
    modifications: List[dict],
) -> List[Conflict]:
    """주어진 시퀀스와 modification 조합에서 화학적·구조적 충돌을 탐지.

    모든 등록 규칙(_RULES)을 순서대로 적용하고 발견된 충돌을 반환.
    ERROR는 반드시 수정 필요, WARNING은 검토 권장.

    Args:
        sequence:      아미노산 서열 (1-letter code, 대문자 자동 변환)
        modifications: modification 딕셔너리 리스트.
                       각 dict 필수 키:
                         "mod_type" (str): "fatty_acid" | "pegylation" |
                                           "d_amino_acid" | "cyclization" |
                                           "substitution"
                         "position" (int): 1-indexed 잔기 번호
                       선택 키: 추가 파라미터 (규칙에 따라 무시될 수 있음)

    Returns:
        Conflict 리스트. 비어 있으면 충돌 없음.
        rule_id 오름차순(C-01 → C-06) 정렬.

    Example:
        >>> seq = "AGCKNFFWKTFTSC"
        >>> mods = [{"mod_type": "fatty_acid", "position": 4},
        ...         {"mod_type": "pegylation", "position": 4}]
        >>> conflicts = check_conflicts(seq, mods)
        >>> assert len(conflicts) == 1
        >>> assert conflicts[0].rule_id == "C-01"
        >>> assert conflicts[0].severity == "ERROR"
    """
    seq = sequence.upper()
    all_conflicts: List[Conflict] = []

    # A-6: C-06(범위/타입 검사)을 먼저 실행하여 유효하지 않은 position을 가진 mod를
    # 이후 규칙에서 제외시킴 — 비-int position이 다른 규칙에서 TypeError를 유발하지 않도록.
    c06_conflicts = _rule_c06_out_of_range_position(seq, modifications)
    all_conflicts.extend(c06_conflicts)
    # C-06 ERROR가 발생한 mod 인덱스 수집 → 이후 규칙 실행 시 제거
    invalid_mod_indices = set()
    for cf in c06_conflicts:
        if cf.severity == "ERROR":
            invalid_mod_indices.update(cf.mods_involved)

    # 유효한 modification만 이후 규칙에 전달
    filtered_mods = [
        m for i, m in enumerate(modifications)
        if i not in invalid_mod_indices
    ]

    for rule_id, rule_fn in _RULES:
        if rule_fn is _rule_c06_out_of_range_position:
            # 이미 위에서 실행됨 — 건너뜀
            continue
        try:
            found = rule_fn(seq, filtered_mods)
            # filtered_mods의 인덱스를 원래 modifications 인덱스로 매핑
            valid_indices = [
                i for i in range(len(modifications))
                if i not in invalid_mod_indices
            ]
            remapped: List[Conflict] = []
            for cf in found:
                remapped_involved = tuple(
                    valid_indices[fi] for fi in cf.mods_involved
                    if fi < len(valid_indices)
                )
                remapped.append(Conflict(
                    severity=cf.severity,
                    rule_id=cf.rule_id,
                    description=cf.description,
                    mods_involved=remapped_involved,
                    suggestion=cf.suggestion,
                ))
            all_conflicts.extend(remapped)
        except Exception as exc:  # noqa: BLE001
            # 예외를 삼키지 않고 호출자가 인식할 수 있는 Conflict로 승격 (A-1).
            # C-99 = INTERNAL_ERROR 예약 rule_id.
            logger.error("규칙 %s 실행 중 예외 발생: %s", rule_id, exc)
            all_conflicts.append(Conflict(
                severity="ERROR",
                rule_id="C-99",
                description=(
                    f"규칙 {rule_id} 실행 중 내부 예외 발생: {exc!r}. "
                    "입력값(position 타입 등)을 확인하세요."
                ),
                mods_involved=(),
                suggestion="modification 입력 스키마를 검증 후 재시도.",
            ))

    # rule_id 기준 정렬 (C-01 < C-02 < ... < C-06)
    all_conflicts.sort(key=lambda c: c.rule_id)

    n_errors = sum(1 for c in all_conflicts if c.severity == "ERROR")
    n_warnings = sum(1 for c in all_conflicts if c.severity == "WARNING")
    logger.info(
        "check_conflicts: seq=%s, mods=%d개 → ERROR %d, WARNING %d",
        sequence[:8] + ("..." if len(sequence) > 8 else ""),
        len(modifications),
        n_errors,
        n_warnings,
    )

    return all_conflicts
