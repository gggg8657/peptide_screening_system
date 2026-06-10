"""
pharmacophore.py — SST-14/SSTR2 Pharmacophore Heuristics
=========================================================
SSTR2 방사성의약품 후보 펩타이드에 대한 두 boolean 필드를 sequence-level에서 판정한다.

**1차 데이터 소스**: runner.py → cluster_report._criteria_a/d → emitter.set_candidates()
**이 모듈 역할**: status._enrich_candidates()에서 상기 pipeline 값이 None일 때 fallback 계산

HEURISTIC 경고 (H-06 가드, VR-cycle-09):
  두 함수 모두 pre-wet-lab screening ranking signal.
  실제 Ki, 합성 수율, 방사화학 QC를 보장하지 않음.
  최종 후보 선정은 wet-lab assay(FACS, HPLC-RP) 필요.
  pharmacology_guards.HEURISTIC_FUNCTION_DISCLAIMERS 등록 참조.

FWKT 위치 정본 (Python 검증 기준):
  seq = "AGCKNFFWKTFTSC"
  seq[6:10] == "FWKT"  ← 유일하게 정확
  0-indexed: 6, 7, 8, 9
  1-indexed: Phe7-Trp8-Lys9-Thr10
  (주의: 일부 팀 문서의 "5-8", "Phe6" 등은 off-by-one 오류 — 이 파일이 정본)

reviewer-pharma 공식 정의 (2026-05-14):
  fwkt_contact:
    - FWKT pharmacophore: Phe7-Trp8-Lys9-Thr10 (0-idx 6-9)
    - SSTR2 pocket: TM3(Asp122), TM5(Asn276), TM6(Phe294,Trp291), TM7(Tyr316) [PDB 7T11]
    - 접촉 기준: ≤4.5 Å; Phase 1 fallback: "FWKT" substring OR ≥3/4 보존

  chelator_site_available (reviewer-pharma Condition A+B+C):
    - Condition A: N-terminus α-NH2 free (표준, 항상 True for linear peptide)
    - Condition B: Lys ε-NH2 존재 (대안)
    - Condition C: SS-bond Cys pair 유지 (chelator가 SS-bond 파괴 않아야 함)
    - Result: (A or B) AND C
    - SST-14: N-term(Ala) + K4,K8 + Cys3-Cys14 → True ✓

문헌 근거:
  - Patel YC (1999) Front Neuroendocrinol 20:157-198
  - Reubi JC et al. (2017) J Nucl Med 58:1017-1023
  - Krenning EP et al. (1992) Lancet 339:578-580
  - de Jong M et al. (2002) J Nucl Med 43:1650-1656
  - Maecke HR et al. (2005) J Nucl Med 46:151S-159S
  - Zhao X et al. (2022) Nature 605:204-209 [PDB 7T11 — SSTR2 cryo-EM + octreotide]
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# SST-14 기준 상수 (READ-ONLY)
# ---------------------------------------------------------------------------

# SST-14 wild-type 서열 (14-mer, Cys3-Cys14 SS bond)
_SST14_WT: str = "AGCKNFFWKTFTSC"

# FWKT pharmacophore 위치 (정본, Python 검증)
# seq = "AGCKNFFWKTFTSC"; seq[6:10] == "FWKT" → True
# 0-indexed: 6(F), 7(W), 8(K), 9(T)
# 1-indexed: 7(Phe7), 8(Trp8), 9(Lys9), 10(Thr10)
_FWKT_MOTIF: str = "FWKT"
_FWKT_0IDX_START: int = 6  # SST-14 기준 FWKT 시작 위치 (0-indexed)
_FWKT_LENGTH: int = 4

# SST-14 SS bond Cys 위치 (0-indexed: Cys3=2, Cys14=13)
_SST14_SS_CYS_0IDX: Tuple[int, int] = (2, 13)
_SS_BOND_MIN_CYS: int = 2  # SS bond 형성에 필요한 최소 Cys 수


# ---------------------------------------------------------------------------
# 1. FWKT pharmacophore contact 판정
# ---------------------------------------------------------------------------


def compute_fwkt_contact(
    candidate: Dict[str, Any],
    *,
    strict_position: bool = False,
    fwkt_start_0idx: int = _FWKT_0IDX_START,
    min_conserved: int = 3,
) -> Optional[bool]:
    """FWKT pharmacophore가 SSTR2 binding pocket과 접촉하는지 판정 (Phase 1 fallback).

    **1차 데이터 소스**: runner.py → cluster_report._criteria_a().fwkt_contact
    이 함수는 pipeline cluster 데이터가 None일 때 status._enrich_candidates()에서만 호출됨.

    reviewer-pharma 공식 정의 (Patel YC 1999 Front Neuroendocrinol; Reubi JC 2017):
    - FWKT 위치 (정본): SST-14 0-indexed 6-9 (seq[6:10] == "FWKT")
      1-indexed: Phe7-Trp8-Lys9-Thr10
    - SSTR2 pocket: TM3(Asp122), TM5(Asn276), TM6(Phe294,Trp291), TM7(Tyr316) [PDB 7T11]
    - 접촉 기준: ≤4.5 Å (엄격), ≤5.0 Å (완화 — PyRosetta 불확실성 허용)
    - 돌연변이 Ki 변화: Trp8→Ala ×100, Lys9→Ala ×50 (Reubi 2017)

    현재 구현 (Phase 1):
    - strict_position=False (기본): "FWKT" substring 어디서든 존재 → True
      (유연한 analogues 지원; 위치가 다를 가능성 허용)
    - strict_position=True: seq[fwkt_start_0idx:fwkt_start_0idx+4] 위치 확인
      + min_conserved 미만 보존 시 False (부분 보존 허용)

    Phase 2 경로 (pipeline에 구현됨):
    - cluster_report._fwkt_contact_maintained(): structural_rules.fwkt_pharmacophore.pass
    - runner.py → emitter → status.py 우선 사용

    VALIDATION_NEEDED: PDB 도킹 pose ≤4.5 Å 거리 기반 검증 미수행.
    confidence_grade: HEURISTIC (pharmacology_guards.HEURISTIC_FUNCTION_DISCLAIMERS 등록)

    Args:
        candidate: 후보 dict. 필수 키: "sequence" (str).
        strict_position: True이면 fwkt_start_0idx 위치에서만 확인.
        fwkt_start_0idx: strict 모드에서 FWKT 시작 위치 (기본=6, SST-14 기준).
        min_conserved: strict 모드에서 최소 보존 잔기 수 (기본=3; 4개 중 ≥3).

    Returns:
        True  — FWKT 모티프 보존
        False — FWKT 모티프 결실/변이
        None  — 서열 정보 없음
    """
    seq: Optional[str] = candidate.get("sequence")
    if not seq:
        return None
    seq_upper = seq.upper().strip()
    if not seq_upper:
        return None

    if strict_position:
        # Phase 2 예비 구현: 특정 위치에서 ≥min_conserved 잔기 보존 확인
        end = fwkt_start_0idx + _FWKT_LENGTH
        if len(seq_upper) < end:
            return False
        motif = seq_upper[fwkt_start_0idx:end]
        matches = sum(1 for a, b in zip(motif, _FWKT_MOTIF) if a == b)
        return matches >= min_conserved
    else:
        # Phase 1 (기본): FWKT substring 존재 여부 — flexible analogues 지원
        return _FWKT_MOTIF in seq_upper


# ---------------------------------------------------------------------------
# 2. Chelator site availability 판정 (reviewer-pharma Condition A+B+C)
# ---------------------------------------------------------------------------


def compute_chelator_site(
    sequence: str,
    ss_cys_0idx: Tuple[int, int] = _SST14_SS_CYS_0IDX,
) -> Optional[bool]:
    """DOTA chelator 부착 가능 site 존재 여부 판정 (Phase 1 fallback).

    **1차 데이터 소스**: runner.py → cluster_report._criteria_d().chelator_site_available
    이 함수는 pipeline cluster 데이터가 None일 때 (cluster A/B/C 후보 등) fallback으로 호출됨.

    reviewer-pharma 공식 알고리즘 (2026-05-14):

      Condition A: N-terminus α-NH2 free amine 존재
        - 일반 primary amine N-terminus → 항상 True
        - Pro N-terminus → secondary amine → DOTA-NHS 커플링 효율 저하
          (VALIDATION_NEEDED: ~10-20× 느림, screening 단계 False 처리 보수적)

      Condition B: Lys ε-NH2 존재 (Maecke HR 2005 J Nucl Med — K8 anchor)
        - SS-bond Cys 위치의 Lys는 제외하지 않음 (Lys는 SS-bond 관련 없음)
        - SS-bond Cys 위치(ss_cys_0idx)는 Cys thiol만 제외 (별도 Condition C)

      Condition C: SS-bond Cys pair 유지 (Krenning EP 1992 Lancet)
        - 서열에 Cys ≥ 2개 존재 → SS-bond 가능 → Cys thiol은 chelation 비대상
        - Cys < 2 → SS-bond 없음 → SSTR2 conformational 요구 미충족
          → chelation 자체는 가능하나 이 context에서는 False

      Result: (A OR B) AND C

    SST-14 검증:
      seq = "AGCKNFFWKTFTSC"
      A: N-term=A (non-Pro) → True
      B: K at idx 3 (K4), idx 8 (K9) → True
      C: C at idx 2, 13 → ≥2 Cys → True
      Result: (True OR True) AND True = True ✓

    pipeline 1차 소스와의 차이:
    - cluster_report._criteria_d(): n_strong ≥ 1 (H, C 잔기 기반)
      → SS-bond Cys가 n_strong에 포함될 수 있어 과대 계산 가능 (Phase 2 개선 예정)
    - 이 함수: N-term/Lys 기반 + SS-bond 보존 확인으로 더 정확

    VALIDATION_NEEDED: 합성 (MALDI-TOF, HPLC) + 방사화학 yield 검증 필요.
    confidence_grade: HEURISTIC (pharmacology_guards.HEURISTIC_FUNCTION_DISCLAIMERS 등록)

    Args:
        sequence: 1-letter 아미노산 서열 (대소문자 무관). 예: "AGCKNFFWKTFTSC"
        ss_cys_0idx: SS-bond를 형성하는 Cys 위치 (0-indexed). SST-14 기본: (2, 13).

    Returns:
        True  — DOTA 부착 가능 (N-term 또는 Lys + SS-bond 보존)
        False — 부착 불가 (Condition 미충족)
        None  — 서열 없음 (판정 불가)
    """
    if not sequence:
        return None
    seq = sequence.upper().strip()
    if not seq:
        return None

    # Condition C: SS-bond Cys pair 존재 (≥2 Cys in sequence)
    cys_positions: List[int] = [i for i, aa in enumerate(seq) if aa == "C"]
    ss_bond_maintained: bool = len(cys_positions) >= _SS_BOND_MIN_CYS

    # Condition A: N-terminus primary amine (non-Pro)
    n_term_free: bool = seq[0] != "P"

    # Condition B: Lys ε-amine (SS-bond와 무관 — Lys는 SS-bond에 참여 안 함)
    has_lys: bool = "K" in seq

    return (n_term_free or has_lys) and ss_bond_maintained


# ---------------------------------------------------------------------------
# 3. 복합 판정 (candidate dict 기반)
# ---------------------------------------------------------------------------


def compute_pharmacophore_fields(candidate: Dict[str, Any]) -> Dict[str, Optional[bool]]:
    """candidate dict로부터 두 pharmacophore 필드를 한번에 계산.

    Args:
        candidate: 후보 dict. "sequence" 키 필요.

    Returns:
        {"fwkt_contact": bool|None, "chelator_site_available": bool|None}
    """
    seq: Optional[str] = candidate.get("sequence")
    return {
        "fwkt_contact": compute_fwkt_contact(candidate),
        "chelator_site_available": compute_chelator_site(seq) if seq else None,
    }
