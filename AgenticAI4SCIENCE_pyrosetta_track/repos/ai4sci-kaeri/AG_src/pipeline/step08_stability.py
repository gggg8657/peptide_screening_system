"""
step08_stability.py
===================
Step 08: GLP-1 기반 반감기 예측 및 안정성 개선 전략 제안
        (Blood Stability Prediction & Modification Strategy)

GLP-1 수용체 작용제(세마글루타이드, 리라글루타이드)의 장기 반감기 달성 전략을 참고하여
SSTR2 펩타이드 바인더 후보물질의 혈중 안정성을 예측하고 최적화한다.

Scientific basis (GLP-1 agonist 반감기 연장 메커니즘):
  - 지방산 아실화(fatty acid acylation): C16-C18 지방산이 알부민 결합을 통해 신장 청소율 감소
  - PEG화(PEGylation): 고분자량 PEG가 신장 여과를 차단하고 수력역학적 반경 증가
  - D-아미노산 치환: L-아미노산 선택적인 프로테아제에 대한 저항성 획득
  - 백본 고리화(backbone cyclization): DOTATATE(Cys3-Cys14 이황화결합)처럼 엔도펩티다제 접근 차단
  - 프로테아제 취약 잔기 치환: Arg/Lys(트립신 부위), Met(산화 취약)을 내성 아미노산으로 교체

Reference sequence: DOTATATE = "AGCKNFFWKTFTSC" (14-aa 고리형 펩타이드)
Target half-life: 144-240 hours (6-10 days)

Public API:
    predict_half_life(sequence, modifications)              -> float (hours)
    suggest_modifications(sequence, target_half_life_hours) -> list[ModificationSuggestion]
    evaluate_stability(candidates, config)                  -> list[StabilityResult]
    apply_stability_gate(results, min_half_life_hours)      -> (passed, failed)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 아미노산 물리화학적 특성 테이블
# ---------------------------------------------------------------------------

# 프로테아제 취약성 점수 (높을수록 취약): 혈중 프로테아제 기질 우선순위
# 근거: 트립신/키모트립신/엘라스타제 절단 선호도 기반
_PROTEASE_VULNERABILITY: Dict[str, float] = {
    "R": 3.0,   # 아르지닌: 트립신 절단 부위 (가장 취약)
    "K": 2.5,   # 라이신: 트립신 절단 부위
    "F": 2.0,   # 페닐알라닌: 키모트립신 절단 부위
    "Y": 1.8,   # 타이로신: 키모트립신 절단 부위
    "W": 1.5,   # 트립토판: 키모트립신 절단 부위
    "L": 1.2,   # 류신: 엘라스타제 절단 부위
    "A": 0.8,   # 알라닌: 엘라스타제 절단 부위
    "V": 0.6,   # 발린: 엘라스타제 절단 부위 (낮음)
    "G": 0.4,   # 글리신: 일반적으로 절단 부위 아님
    "P": 0.1,   # 프롤린: 프로테아제 저항성 (이미다졸 고리로 인한 입체장애)
    "M": 0.5,   # 메티오닌: 직접 절단 아니나 산화로 취약해짐
    "S": 0.6,
    "T": 0.6,
    "C": 0.3,   # 시스테인: 이황화결합 형성 시 안정화
    "N": 0.5,
    "Q": 0.5,
    "D": 0.4,
    "E": 0.4,
    "H": 0.9,
    "I": 0.7,
}

# D-아미노산으로 치환 추천되는 L-아미노산 표기 (D-Xaa 표기)
_D_AMINO_ACID_MAP: Dict[str, str] = {
    "R": "D-Arg", "K": "D-Lys", "F": "D-Phe", "Y": "D-Tyr",
    "L": "D-Leu", "A": "D-Ala", "V": "D-Val", "I": "D-Ile",
    "N": "D-Asn", "Q": "D-Gln", "S": "D-Ser", "T": "D-Thr",
    "E": "D-Glu", "D": "D-Asp", "H": "D-His", "M": "D-Met",
    "W": "D-Trp", "G": "Gly",   # Gly은 키랄중심 없으므로 D/L 동일
    "C": "D-Cys",
}

# 산화 취약 잔기
_OXIDATION_PRONE: frozenset = frozenset({"M", "C", "W", "H"})

# 프로테아제 절단 페널티가 높은 잔기
_HIGH_VULNERABILITY: frozenset = frozenset({"R", "K", "F", "Y"})

# ---------------------------------------------------------------------------
# 기본 반감기 계산 파라미터 (GLP-1 약동학 데이터 기반)
# ---------------------------------------------------------------------------

# 선형 펩타이드 기본 반감기: 2-4시간 (혈중 프로테아제 환경)
_BASE_HALF_LIFE_HOURS = 3.0

# 수정(modification) 보너스 — suggest_modifications 의 우선순위/예상증가량 표시용 (additive, 레거시)
_MODIFICATION_BONUS: Dict[str, float] = {
    "fatty_acid":    120.0,   # C18 지방산: 알부민 결합으로 세마글루타이드 168h 달성
    "pegylation":    96.0,    # PEG20kDa: 신장 청소율 감소 (PEGylated exenatide 기준)
    "d_amino_acid":  48.0,    # D-아미노산 1개당: 해당 절단 부위 프로테아제 저항성
    "cyclization":   24.0,    # 고리화: 엑소펩티다제 및 엔도펩티다제 부분 차단
    "substitution":  12.0,    # 프로테아제 취약 잔기 교체 (Arg→Aib, Lys→Orn 등)
}

# ── 2026-06-09 재보정 (log-multiplicative 모델) ──────────────────────────────
# 기존 additive 모델은 cyclization +24h 가 사이클릭/SS 펩타이드(SST-14 등)를 과대예측
# (벤치마크: SST-14 16.6h vs 실제 ~0.05h, plain Spearman=-0.5 순위 역전).
# log10 곱셈 모델로 교체: 고리화는 완만한 배수, fatty_acid(알부민결합)가 장반감기 주도,
# 프로테아제 취약성이 단반감기 스프레드. 문헌 t½ 8종 벤치마크에서 Spearman 0.86(all)/0.50(plain),
# SST-14 0.04h 로 교정. 검증: tests/test_halflife_benchmark.py.
_HL_BASE_HOURS = 0.05            # 짧은 선형 펩타이드 혈중 baseline (~3 min)
_HL_PROTEO_K = 0.32             # avg vulnerability 계수 (log10)
_HL_CLEAVE_K = 0.06             # dipeptide 절단부위 계수
_HL_TERM_K = 0.15               # 말단 exopeptidase 계수
_MODIFICATION_LOG_MULT: Dict[str, float] = {
    "fatty_acid":    math.log10(2800.0),  # C16-18 알부민 결합 → 신장청소 회피
    "pegylation":    math.log10(2200.0),  # PEG 신장청소 차단
    "d_amino_acid":  math.log10(35.0),    # 절단부위 프로테아제 저항
    "cyclization":   math.log10(1.8),     # 이황화/고리화: 완만한 안정화 (혈중 t½ 주도 아님)
    "substitution":  math.log10(4.0),
}

# 잔기별 페널티 (노출된 취약 잔기당)
_EXPOSED_ARG_LYS_PENALTY = -12.0    # 트립신 절단 부위 per Arg/Lys
_EXPOSED_MET_PENALTY = -8.0         # 산화 취약 per Met

# ---------------------------------------------------------------------------
# 데이터클래스 정의
# ---------------------------------------------------------------------------


@dataclass
class ModificationSuggestion:
    """단일 화학적 수정(modification) 제안.

    Attributes:
        mod_type:            수정 유형 ("fatty_acid" | "pegylation" | "d_amino_acid" | "substitution")
        position:            아미노산 위치 (1-indexed)
        original:            원래 잔기 (1-letter code)
        proposed:            제안된 수정 표기 (예: "D-Arg", "C18-fatty-acid-at-K10")
        half_life_gain_hours: 이 수정으로 예상되는 반감기 증가량 (시간)
        rationale:           과학적 근거 설명
    """
    mod_type: str
    position: int
    original: str
    proposed: str
    half_life_gain_hours: float
    rationale: str


@dataclass
class StabilityResult:
    """단일 후보물질의 안정성 평가 결과.

    Attributes:
        candidate_id:          후보 식별자
        sequence:              아미노산 서열 (1-letter code)
        base_half_life_hours:  수정 전 예측 반감기 (시간)
        modifications:         권장 수정 목록
        modified_half_life_hours: 모든 권장 수정 적용 후 예측 반감기 (시간)
        target_met:            목표 반감기(기본 144h) 달성 여부
        score:                 0-1 안정성 점수 (높을수록 안정)
    """
    candidate_id: str
    sequence: str
    base_half_life_hours: float
    modifications: List[ModificationSuggestion]
    modified_half_life_hours: float
    target_met: bool
    score: float


@dataclass
class StabilityReport:
    """전체 안정성 평가 보고서.

    Attributes:
        results:       각 후보물질의 StabilityResult 목록
        n_passed:      목표 반감기를 달성한 후보 수
        n_failed:      목표 반감기 미달성 후보 수
        min_half_life: 평가에 사용된 최소 반감기 기준 (시간)
    """
    results: List[StabilityResult]
    n_passed: int
    n_failed: int
    min_half_life: float


# ---------------------------------------------------------------------------
# 핵심 기능 함수
# ---------------------------------------------------------------------------


def predict_half_life(
    sequence: str,
    modifications: List[str],
) -> float:
    """펩타이드 서열과 적용된 수정(modification) 목록으로 반감기를 예측한다.

    GLP-1 약동학 모델 기반 반감기 예측:
      1) 아미노산 조성에서 기본 프로테아제 취약성 점수 계산
      2) 취약 잔기(Arg/Lys/Met) 노출 페널티 적용
      3) 기존 구조적 특성(DOTATATE-like 고리화) 반영
      4) 적용된 modification 보너스 합산

    Args:
        sequence:      아미노산 서열 (1-letter code, 대문자)
        modifications: 이미 적용된 modification 유형 목록
                       예: ["fatty_acid", "d_amino_acid", "cyclization"]

    Returns:
        예측 반감기 (시간, float)

    Scientific note:
        세마글루타이드(C18 지방산 + 링커): 혈중 반감기 ~168h
        리라글루타이드(C16 지방산): 혈중 반감기 ~13h
        DOTATATE(고리형 + SST 유사체): 혈중 반감기 ~1.5h (신장 분비로 짧음)
    """
    seq = sequence.upper()
    if not seq:
        logger.warning("빈 서열이 입력되었습니다. 기본 반감기를 반환합니다.")
        return _BASE_HALF_LIFE_HOURS

    # === 2026-06-09 재보정: log10 곱셈 모델 (벤치마크 검증) ===================
    # log10(t½) = log10(base) - proteolysis_penalty + Σ modification_log_mult
    #   - base: 짧은 선형 펩타이드 혈중 baseline
    #   - proteolysis_penalty: avg 취약성 + dipeptide 절단부위 + 말단 exopeptidase (음수↑=짧음)
    #   - modification: 곱셈(log 합) — fatty_acid(알부민결합) 장반감기 주도, cyclization 은 완만

    # 1) 프로테아제 취약성 (단반감기 스프레드)
    avg_vulnerability = sum(_PROTEASE_VULNERABILITY.get(aa, 0.5) for aa in seq) / len(seq)
    n_arg_lys = seq.count("R") + seq.count("K")  # (로그용)
    n_met = seq.count("M")                        # (로그용)
    n_term_vuln = _PROTEASE_VULNERABILITY.get(seq[0], 0.5)
    c_term_vuln = _PROTEASE_VULNERABILITY.get(seq[-1], 0.5)
    cleavage_sites = 0.0
    for i in range(len(seq) - 1):
        if seq[i] in ("K", "R") and seq[i + 1] != "P":   # Pro은 절단 억제 (트립신)
            cleavage_sites += 1.0
        elif seq[i] in ("F", "Y", "W") and seq[i + 1] != "P":  # 키모트립신
            cleavage_sites += 0.5
    proteo_log = -(
        _HL_PROTEO_K * (avg_vulnerability - 0.8)
        + _HL_CLEAVE_K * cleavage_sites
        + _HL_TERM_K * ((n_term_vuln + c_term_vuln) / 2.0 - 0.8)
    )

    # 2) 고리화 자동 감지 (Cys 쌍, ≥4 간격) → 완만한 log 배수
    cys_indices = [i for i, aa in enumerate(seq) if aa == "C"]
    has_cyclization_in_seq = (
        len(seq) >= 6 and len(cys_indices) >= 2 and (cys_indices[-1] - cys_indices[0]) >= 4
    )
    mod_log = _MODIFICATION_LOG_MULT["cyclization"] if has_cyclization_in_seq else 0.0

    # 3) 외부 modification (곱셈, log 합). fatty_acid/PEG 가 장반감기 주도.
    for mod in (m.lower() for m in modifications):
        if mod in _MODIFICATION_LOG_MULT:
            mod_log += _MODIFICATION_LOG_MULT[mod]
        elif "d_amino" in mod or "d-amino" in mod:
            mod_log += _MODIFICATION_LOG_MULT["d_amino_acid"]
        elif "fatty" in mod or "acyl" in mod:
            mod_log += _MODIFICATION_LOG_MULT["fatty_acid"]
        elif "peg" in mod:
            mod_log += _MODIFICATION_LOG_MULT["pegylation"]

    # 4) 최종 (log10 → 선형, 합리적 범위 클램프)
    log_hl = math.log10(_HL_BASE_HOURS) + proteo_log + mod_log
    final_hl = max(0.02, min(10.0 ** log_hl, 1.0e4))

    logger.debug(
        "반감기(재보정 logmult): seq=%s avg_vuln=%.2f cleave=%.1f proteo_log=%.2f mod_log=%.2f final=%.3fh",
        sequence[:8] + "...", avg_vulnerability, cleavage_sites, proteo_log, mod_log, final_hl,
    )
    return round(final_hl, 3)


def suggest_modifications(
    sequence: str,
    target_half_life_hours: float = 168.0,
) -> List[ModificationSuggestion]:
    """목표 반감기 달성을 위한 화학적 수정을 우선순위 순으로 제안한다.

    GLP-1 전략 우선순위:
      1) 지방산 아실화 (fatty acid acylation) - 최우선: 세마글루타이드처럼 +120h
      2) PEG화 (PEGylation) - 차선: 신장 청소율 차단 +96h
      3) D-아미노산 치환 - 프로테아제 취약 위치에 적용 (+48h per site)
      4) 잔기 치환 - 프로테아제 절단 부위를 내성 잔기로 교체 (+12h per site)

    Args:
        sequence:              아미노산 서열 (1-letter code, 대문자)
        target_half_life_hours: 목표 반감기 (기본값: 168h = 7일, GLP-1 목표치)

    Returns:
        ModificationSuggestion 리스트 (예상 반감기 증가 내림차순 정렬)

    Scientific note:
        세마글루타이드: C18 이중산 지방산 + PEG 링커 → 168h 반감기
        목표 범위: 144-240h (6-10일) per KAERI SSTR2 프로젝트 요구사항
    """
    seq = sequence.upper()
    suggestions: List[ModificationSuggestion] = []

    # 현재 기본 반감기 계산
    current_hl = predict_half_life(seq, [])

    # 이미 고리화되어 있는지 확인 (Cys 쌍 기반: DOTATATE Cys3-Cys14 또는 Approach B Cys3-Cys13)
    cys_idx = [i for i, aa in enumerate(seq) if aa == "C"]
    is_cyclic = (
        len(seq) >= 6
        and len(cys_idx) >= 2
        and (cys_idx[-1] - cys_idx[0]) >= 4
    )

    remaining_gap = target_half_life_hours - current_hl

    # --- 우선순위 1: 지방산 아실화 ---
    # Lys 잔기가 있으면 해당 위치에 C18 지방산 부착 (세마글루타이드 전략)
    # Lys 없으면 C-말단에 부착 제안
    lys_positions = [i + 1 for i, aa in enumerate(seq) if aa == "K"]
    fatty_acid_pos = lys_positions[0] if lys_positions else len(seq)
    fatty_acid_orig = seq[fatty_acid_pos - 1] if lys_positions else seq[-1]

    suggestions.append(ModificationSuggestion(
        mod_type="fatty_acid",
        position=fatty_acid_pos,
        original=fatty_acid_orig,
        proposed=f"C18-fatty-acid-at-{fatty_acid_orig}{fatty_acid_pos}",
        half_life_gain_hours=_MODIFICATION_BONUS["fatty_acid"],
        rationale=(
            f"C18 지방산(옥타데칸산) {fatty_acid_orig}{fatty_acid_pos}에 부착: "
            "알부민(HSA) 결합으로 신장 여과 차단. "
            "세마글루타이드 동일 전략 → 혈중 반감기 168h 달성."
        ),
    ))

    # --- 우선순위 2: PEG화 ---
    # N-말단 또는 라이신 잔기에 PEG20kDa 부착
    peg_pos = 1  # N-말단 기본
    peg_orig = seq[0]
    if lys_positions and len(lys_positions) > 1:
        peg_pos = lys_positions[-1]  # 지방산과 다른 Lys 위치 사용
        peg_orig = seq[peg_pos - 1]

    suggestions.append(ModificationSuggestion(
        mod_type="pegylation",
        position=peg_pos,
        original=peg_orig,
        proposed=f"PEG20kDa-at-pos{peg_pos}",
        half_life_gain_hours=_MODIFICATION_BONUS["pegylation"],
        rationale=(
            f"PEG(20kDa) {peg_orig}{peg_pos}에 부착: "
            "수력역학적 반경 증가로 신장 사구체 여과 차단, "
            "단백분해효소 접근 입체 차단. "
            "PEGylated exenatide 기준 반감기 2-3배 연장."
        ),
    ))

    # --- 우선순위 3: D-아미노산 치환 (프로테아제 취약 위치) ---
    # 취약성 점수 높은 상위 잔기를 D-form으로 치환
    vulnerability_ranked = sorted(
        [(i + 1, aa, _PROTEASE_VULNERABILITY.get(aa, 0.5))
         for i, aa in enumerate(seq)
         if aa in _HIGH_VULNERABILITY and aa != "C"],  # Cys는 이황화결합 보존
        key=lambda x: -x[2],  # 취약성 내림차순
    )

    # 최대 3개 위치까지 D-아미노산 제안
    for pos, aa, vuln_score in vulnerability_ranked[:3]:
        d_form = _D_AMINO_ACID_MAP.get(aa, f"D-{aa}")
        suggestions.append(ModificationSuggestion(
            mod_type="d_amino_acid",
            position=pos,
            original=aa,
            proposed=d_form,
            half_life_gain_hours=_MODIFICATION_BONUS["d_amino_acid"],
            rationale=(
                f"{aa}{pos} → {d_form} 치환: "
                f"L-아미노산 선택적 프로테아제(취약성={vuln_score:.1f}) 저항성 획득. "
                "DOTATATE의 D-Phe1처럼 키모트립신 절단 차단."
            ),
        ))

    # --- 우선순위 4: 프로테아제 취약 잔기 치환 ---
    # 남은 Arg/Lys을 Aib(α-aminoisobutyric acid) 또는 Orn으로 치환
    substitution_candidates = [
        (i + 1, aa) for i, aa in enumerate(seq)
        if aa in ("R", "K") and (i + 1) != fatty_acid_pos
    ]
    for pos, aa in substitution_candidates[:2]:
        substitute = "Aib" if aa == "R" else "Orn"
        suggestions.append(ModificationSuggestion(
            mod_type="substitution",
            position=pos,
            original=aa,
            proposed=substitute,
            half_life_gain_hours=_MODIFICATION_BONUS["substitution"],
            rationale=(
                f"{aa}{pos} → {substitute} 치환: "
                "트립신 절단 부위(Arg/Lys-X) 제거. "
                f"{'Aib는 α-메틸기로 입체적 프로테아제 차단' if aa == 'R' else 'Orn은 측쇄 아민 보존하면서 트립신 절단 약화'}."
            ),
        ))

    # 결과를 예상 반감기 증가량 내림차순 정렬
    suggestions.sort(key=lambda s: -s.half_life_gain_hours)

    logger.info(
        "수정 제안 완료: seq=%s, 현재 반감기=%.1fh, 목표=%.1fh, 제안 수=%d",
        sequence[:8] + "...",
        current_hl,
        target_half_life_hours,
        len(suggestions),
    )
    return suggestions


def _compute_stability_score(
    base_hl: float,
    modified_hl: float,
    target_hl: float = 144.0,
) -> float:
    """안정성 점수(0-1)를 계산한다.

    점수 계산 방식:
      - 목표 반감기의 50% 미달: 선형 증가 (0 -> 0.5)
      - 목표 달성: sigmoid 함수로 0.5 -> 1.0 전환
      - 목표의 2배 초과: 1.0 상한

    Args:
        base_hl:     수정 전 반감기 (시간)
        modified_hl: 수정 후 반감기 (시간)
        target_hl:   목표 반감기 (시간)

    Returns:
        0.0 - 1.0 사이의 안정성 점수
    """
    if modified_hl <= 0:
        return 0.0

    # sigmoid 기반 점수: 목표치에서 0.5, 목표 2배에서 ~0.88
    # k=0.02는 기울기 조절 (144h 목표 시 합리적 분리)
    k = 0.02
    midpoint = target_hl
    score = 1.0 / (1.0 + math.exp(-k * (modified_hl - midpoint)))

    return round(min(1.0, max(0.0, score)), 4)


def evaluate_stability(
    candidates: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None,
) -> List[StabilityResult]:
    """후보물질 목록에 대해 안정성을 평가하고 수정을 제안한다.

    각 후보물질에 대해:
      1) 현재 서열의 기본 반감기 예측
      2) 목표 반감기 달성을 위한 수정 제안
      3) 수정 후 반감기 예측
      4) 안정성 점수 계산

    Args:
        candidates: 후보물질 딕셔너리 목록
                    필수 키: "candidate_id" (str), "sequence" (str)
                    선택 키: "modifications" (list[str])
        config:     파이프라인 설정 딕셔너리
                    선택 키: "stability.target_half_life_hours" (float, 기본값: 168.0)
                             "stability.min_half_life_hours" (float, 기본값: 144.0)

    Returns:
        StabilityResult 목록 (modified_half_life_hours 내림차순 정렬)
    """
    cfg = config or {}
    stability_cfg = cfg.get("stability", {})
    target_hl = float(stability_cfg.get("target_half_life_hours", 168.0))
    min_hl = float(stability_cfg.get("min_half_life_hours", 144.0))

    results: List[StabilityResult] = []

    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id", "unknown"))
        sequence = str(candidate.get("sequence", "")).upper()
        existing_mods = list(candidate.get("modifications", []))

        if not sequence:
            logger.warning("후보 %s: 서열 없음, 건너뜀", candidate_id)
            continue

        # 기본 반감기 (기존 modification 적용)
        base_hl = predict_half_life(sequence, existing_mods)

        # 추가 수정 제안
        suggestions = suggest_modifications(sequence, target_hl)

        # 제안된 수정 모두 적용 시 반감기 계산
        all_mod_types = existing_mods + [s.mod_type for s in suggestions]
        modified_hl = predict_half_life(sequence, all_mod_types)

        target_met = modified_hl >= min_hl
        score = _compute_stability_score(base_hl, modified_hl, min_hl)

        results.append(StabilityResult(
            candidate_id=candidate_id,
            sequence=sequence,
            base_half_life_hours=base_hl,
            modifications=suggestions,
            modified_half_life_hours=modified_hl,
            target_met=target_met,
            score=score,
        ))

        logger.info(
            "[Step08] %s: 기본=%.1fh -> 수정후=%.1fh (목표 %s, 점수=%.3f)",
            candidate_id,
            base_hl,
            modified_hl,
            "달성" if target_met else "미달",
            score,
        )

    # modified_half_life_hours 내림차순 정렬
    results.sort(key=lambda r: -r.modified_half_life_hours)
    return results


def apply_stability_gate(
    results: List[StabilityResult],
    min_half_life_hours: float = 144.0,
) -> Tuple[List[StabilityResult], List[StabilityResult]]:
    """안정성 게이트를 적용하여 후보물질을 통과/실패로 분류한다.

    게이트 기준:
      modified_half_life_hours >= min_half_life_hours (기본: 144h = 6일)

    Args:
        results:              evaluate_stability()의 StabilityResult 목록
        min_half_life_hours:  최소 반감기 기준 (시간, 기본값: 144h)

    Returns:
        (passed, failed) 튜플:
          - passed: 게이트 통과 후보 목록 (안정성 점수 내림차순)
          - failed: 게이트 실패 후보 목록

    Scientific note:
        목표 반감기 144-240h (6-10일) = KAERI SSTR2 임상 요구사항
        GLP-1 기준: 세마글루타이드 168h, 리라글루타이드 13h
        최소 기준 144h는 DOTATATE 후속체 임상 데이터(Sandostatin LAR ~14일) 보수적 절충
    """
    passed = [r for r in results if r.modified_half_life_hours >= min_half_life_hours]
    failed = [r for r in results if r.modified_half_life_hours < min_half_life_hours]

    logger.info(
        "[Step08] 안정성 게이트(%.0fh): %d/%d 통과",
        min_half_life_hours,
        len(passed),
        len(results),
    )
    return passed, failed


# ---------------------------------------------------------------------------
# 편의 함수: 파이프라인 통합용
# ---------------------------------------------------------------------------


def run_stability_evaluation(
    candidates: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None,
) -> StabilityReport:
    """파이프라인 통합용 래퍼: 평가 + 게이트 적용 + 보고서 생성.

    Args:
        candidates: 후보물질 딕셔너리 목록
        config:     파이프라인 설정 딕셔너리

    Returns:
        StabilityReport (전체 결과 + 통계)
    """
    cfg = config or {}
    stability_cfg = cfg.get("stability", {})
    min_hl = float(stability_cfg.get("min_half_life_hours", 144.0))

    results = evaluate_stability(candidates, config)
    passed, failed = apply_stability_gate(results, min_hl)

    return StabilityReport(
        results=results,
        n_passed=len(passed),
        n_failed=len(failed),
        min_half_life=min_hl,
    )
