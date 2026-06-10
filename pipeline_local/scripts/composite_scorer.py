"""composite_scorer.py
=====================
복합 스코어링 모듈 — A-04 action item 구현.

WSS(Weighted Sum Score) + Pareto front(비지배 정렬) 기반 복합 스코어링 엔진.
Hard Cutoff 1차 필터 후 Soft Ranking을 통해 Tier S/A/B/FAIL 분류를 수행한다.

참고 문서:
    docs/meet_log/2026-04-06_action_items/A-04_composite_scoring.md
    pipeline_local/scripts/pharmacology_guards.py (Stage 5 가드 연동)
    pipeline_local/scoring/radiolysis_scorer.py (Radiolysis 연동)

Hard Cutoff 기준 (7단계 선별 체계 Step 1+3):
    dg_max       : None → soft mode (A-05 미완료 시 스킵), 기본값은 pharmacology_guards.py 참조
    selectivity_min : 100.0 (100× 이상)
    radiolysis_max  : 3 (민감 잔기 개수)
    admet_tox_max   : 0.3 (독성 확률)
    instability_max : 40.0 (Guruprasad 1990)

가중치 기본값 (합 = 1.0):
    dg              : 0.35
    selectivity     : 0.25
    half_life       : 0.20
    admet_safety    : 0.10  (= 1 - admet_tox)
    radiolysis_safety: 0.10  (= 1 - normalized(radiolysis_count))

Tier 분류 (7단계 선별 체계 Step 4):
    Tier S  : WSS 상위 20% AND Pareto rank 1 (Hard Cutoff 통과 전제)
    Tier A  : WSS 상위 20% XOR Pareto rank 1
    Tier B  : 나머지 Hard Cutoff 통과 후보
    FAIL    : Hard Cutoff 미통과

HEURISTIC 주의:
    WSS/Pareto 스코어는 ranking 도구이며 임상 binding affinity, Ki, ADMET 절대값을
    보장하지 않는다. ENDPOINT_CONFIDENCE.grade = "HEURISTIC" 참조.

Public API:
    CompositeScorer             — 메인 스코어링 클래스
    DEFAULT_WEIGHTS             — 기본 가중치 dict
    DEFAULT_HARD_CUTOFFS        — 기본 Hard Cutoff dict
    WARN_LOW_PASSRATE           — 통과율 5% 미만 경고 예외 클래스
    pareto_nondominated_sort()  — 독립 비지배 정렬 함수

회귀 테스트:
    pipeline_local/tests/test_composite_scorer.py (≥10개)
"""
from __future__ import annotations

import json
import logging
import math
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    import numpy as np
    _HAS_PANDAS = True
except ImportError:
    _HAS_PANDAS = False
    pd = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Stage 5 약리학 가드 연동
# ---------------------------------------------------------------------------
try:
    from pipeline_local.scripts.pharmacology_guards import (
        LITERATURE_VALUES,
        HEURISTIC_FUNCTION_DISCLAIMERS,
        ENDPOINT_CONFIDENCE,
    )
    _PHARMA_GUARDS_AVAILABLE = True
except ImportError:
    _PHARMA_GUARDS_AVAILABLE = False
    LITERATURE_VALUES = {}
    HEURISTIC_FUNCTION_DISCLAIMERS = {}
    ENDPOINT_CONFIDENCE = {}

# ---------------------------------------------------------------------------
# Radiolysis 스코어러 연동
# ---------------------------------------------------------------------------
try:
    from pipeline_local.scoring.radiolysis_scorer import (
        compute_radiolysis_score,
        HARD_CUTOFF_SENSITIVE_COUNT,
    )
    _RADIOLYSIS_AVAILABLE = True
except ImportError:
    _RADIOLYSIS_AVAILABLE = False
    HARD_CUTOFF_SENSITIVE_COUNT = 3

    def compute_radiolysis_score(
        sequence: str,
        ss_bond_positions: Tuple[int, ...] = (3, 14),
    ) -> Dict[str, object]:
        """fallback: radiolysis_scorer 미설치 시 빈 결과 반환."""
        return {"radiolysis_score": 0, "sensitive_count": 0, "ss_bond_intact": True, "details": {}}


# ---------------------------------------------------------------------------
# SST14 참조 ΔG (pharmacology_guards.py 연동)
# ---------------------------------------------------------------------------
def _get_sst14_ref_ddg() -> Optional[float]:
    """pharmacology_guards.LITERATURE_VALUES에서 SST14 레퍼런스 ΔG를 조회한다.

    Returns:
        float: REU 단위 레퍼런스 ΔG (-95.024 기본값), 조회 실패 시 None.
    """
    if not _PHARMA_GUARDS_AVAILABLE:
        return None
    try:
        entry = LITERATURE_VALUES.get("SST14_SSTR2_ref_ddg_boltz2", {})
        ref_tuple = entry.get("ref_ddg_reu")
        if ref_tuple is not None:
            return float(ref_tuple[0])
    except (KeyError, TypeError, IndexError):
        pass
    return None


# ---------------------------------------------------------------------------
# 기본값 상수
# ---------------------------------------------------------------------------

#: 기본 Hard Cutoff 값 (A-04 §Step 2)
DEFAULT_HARD_CUTOFFS: Dict[str, Optional[float]] = {
    "dg_max": None,          # None = A-05 미완료 → soft mode (경고 출력 후 스킵)
    "selectivity_min": 100.0, # SSTR2 vs off-targets 100× 이상
    "radiolysis_max": 3.0,    # 민감 잔기 개수 ≤ 3
    "admet_tox_max": 0.3,     # 독성 확률 ≤ 0.3
    "instability_max": 40.0,  # Guruprasad 1990 기준
}

#: 기본 가중치 (합 = 1.0, A-04 §Step 3 방식 A)
DEFAULT_WEIGHTS: Dict[str, float] = {
    "dg": 0.35,
    "selectivity": 0.25,
    "half_life": 0.20,
    "admet_safety": 0.10,    # = 1 - admet_tox
    "radiolysis_safety": 0.10,  # = 1 - normalized(radiolysis_count)
}

#: Hard Cutoff 통과율 경고 임계값 (5% 미만 시 WARN_LOW_PASSRATE 발생)
LOW_PASSRATE_THRESHOLD: float = 0.05

#: Tier 분류 기준 — WSS 상위 N% 경계
TIER_TOP_PERCENTILE: float = 0.20  # 상위 20%

UNAVAILABLE_GRADE = "UNAVAILABLE"
ADMET_FALLBACK_WARNING = (
    "admet_tox_wrapper_failed: fallback value used (REAL_MEASUREMENT_MISSING)"
)

#: PRST mismatch fix (2026-05-26) — pepADMET retrained vs ADMET-AI raw 값 차이가
#: ADMET_DIVERGENCE_THRESHOLD (0.4) 이상이면 OOD 의심 — 한 값을 강제로 채택하지
#: 않고 양쪽 값을 보존하고 warning 으로 정직 노출.
#:
#: 사례: PRST-001~004 pepADMET=1.00 (재훈련 OOD), ADMET-AI raw=0.10~0.25 (낮은 위험)
#: → 둘 다 0.75 이상 차이 → ADMET_DIVERGENCE_HIGH 발생, 추가 검증 권고.
ADMET_DIVERGENCE_THRESHOLD: float = 0.4
ADMET_DIVERGENCE_WARNING_FMT = (
    "admet_divergence_high: pepadmet={pepadmet_tox:.3f} vs admet_ai={admet_ai_tox:.3f} "
    "(|Δ|={delta:.3f} > {threshold:.2f}) — OOD suspect, additional validation required"
)


# ---------------------------------------------------------------------------
# 예외 클래스
# ---------------------------------------------------------------------------

class WARN_LOW_PASSRATE(RuntimeError):
    """Hard Cutoff 통과율이 LOW_PASSRATE_THRESHOLD (5%) 미만일 때 발생.

    임계값 재검토 권고 메시지를 포함한다.
    """


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------

@dataclass
class ScoringInput:
    """CompositeScorer.score() 단일 후보 입력 표준 형식."""
    candidate_id: str
    sequence: str = ""
    dg: float = 0.0
    selectivity: float = 0.0
    half_life: float = 0.0
    admet_tox: float = 0.5       # 기본값: 보수적 (불명 시 0.5)
    radiolysis_count: int = 0    # 민감 잔기 개수
    instability_index: float = 0.0
    # 선택적 필드
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ScoringInput":
        """dict → ScoringInput 변환. 누락 필드는 기본값 처리."""
        known = {
            "candidate_id", "sequence", "dg", "selectivity",
            "half_life", "admet_tox", "radiolysis_count", "instability_index",
        }
        extra = {k: v for k, v in d.items() if k not in known}
        return cls(
            candidate_id=str(d.get("candidate_id", "unknown")),
            sequence=str(d.get("sequence", "")),
            dg=float(d.get("dg", 0.0)),
            selectivity=float(d.get("selectivity", 0.0)),
            half_life=float(d.get("half_life", 0.0)),
            admet_tox=float(d.get("admet_tox", 0.5)),
            radiolysis_count=int(d.get("radiolysis_count", 0)),
            instability_index=float(d.get("instability_index", 0.0)),
            extra=extra,
        )


@dataclass
class ScoringResult:
    """단일 후보 복합 스코어링 결과."""
    candidate_id: str
    dg: float
    selectivity: float
    half_life: float
    admet_tox: float
    radiolysis_count: int
    instability_index: float
    # Hard Cutoff 결과
    hard_cutoff_pass: bool
    hard_cutoff_failures: List[str]  # 실패한 cutoff 항목 목록
    # Soft Ranking 결과
    wss: float                       # Weighted Sum Score [0, 1]
    pareto_rank: int                 # 1 = Pareto-optimal, 0 = FAIL 또는 미계산
    # Tier 분류
    tier: str                        # "S" | "A" | "B" | "FAIL"
    # 기여도 분해
    explain: Dict[str, float]        # {metric: weighted_contribution}
    # P1 sprint wrapper enrichment metadata
    halflife_confidence_grade: str = ""
    admet_confidence_grade: str = ""
    smiles: str = ""
    enrichment_status: str = ""
    enrichment_notes: List[str] = field(default_factory=list)
    fallback_admet_tox: bool = False
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """dict 변환 (CSV/JSON 저장용)."""
        return {
            "candidate_id": self.candidate_id,
            "dg": self.dg,
            "selectivity": self.selectivity,
            "half_life": self.half_life,
            "admet_tox": self.admet_tox,
            "radiolysis_count": self.radiolysis_count,
            "instability_index": self.instability_index,
            "hard_cutoff_pass": self.hard_cutoff_pass,
            "hard_cutoff_failures": ";".join(self.hard_cutoff_failures),
            "wss": self.wss,
            "pareto_rank": self.pareto_rank,
            "tier": self.tier,
            "explain_json": json.dumps(self.explain, ensure_ascii=False),
            "halflife_confidence_grade": self.halflife_confidence_grade,
            "admet_confidence_grade": self.admet_confidence_grade,
            "smiles": self.smiles,
            "enrichment_status": self.enrichment_status,
            "enrichment_notes": ";".join(self.enrichment_notes),
            "fallback_admet_tox": self.fallback_admet_tox,
            "warnings": ";".join(self.warnings),
        }


# ---------------------------------------------------------------------------
# P1 sprint wrapper enrichment
# ---------------------------------------------------------------------------

_D_AA_TOKEN_RE = re.compile(r"(^|[^A-Za-z])d[-_ ]?[A-Za-z]{1,3}", re.IGNORECASE)


def contains_d_amino_acid(sequence: str) -> bool:
    """D-AA 표기를 감지한다.

    정책:
      - lowercase 1-letter residue는 D-AA shorthand로 취급한다.
      - "d-" / "D-" 토큰은 D-AA 표기로 취급한다.
    """
    if any(ch.isalpha() and ch.islower() for ch in sequence):
        return True
    return bool(_D_AA_TOKEN_RE.search(sequence))


def _endpoint_confidence(endpoint_key: str, default_grade: str) -> Dict[str, Any]:
    if _PHARMA_GUARDS_AVAILABLE:
        info = ENDPOINT_CONFIDENCE.get(endpoint_key)
        if info:
            return dict(info)
    return {"grade": default_grade, "warnings": [], "source": "P1 sprint wrapper"}


def _extract_halflife_score(result: Dict[str, Any]) -> Optional[float]:
    for key in ("halflife_score", "half_life_score", "plifepred2_score"):
        value = result.get(key)
        if value is not None:
            return float(value)
    plife = result.get("plifepred2")
    if isinstance(plife, dict) and plife.get("plifepred2_score") is not None:
        return float(plife["plifepred2_score"])
    return None


def _finite_or_none(value: Any) -> Optional[float]:
    if value is None:
        return None
    score = float(value)
    if not math.isfinite(score):
        return None
    return score


def _extract_admet_tox(result: Dict[str, Any]) -> Optional[float]:
    for key in ("admet_tox", "toxicity_probability", "toxicity_score", "tox_score"):
        value = result.get(key)
        if value is not None:
            return _finite_or_none(value)

    pepadmet = result.get("pepadmet")
    if isinstance(pepadmet, dict):
        for key in ("admet_tox", "toxicity_probability", "toxicity_score"):
            value = pepadmet.get(key)
            if value is not None:
                return _finite_or_none(value)

    # Current P1 wrapper usually falls back to modlamp descriptors. Convert
    # descriptors to a conservative triage proxy so the scorer can proceed.
    desc = result.get("modlamp_descriptors")
    if isinstance(desc, dict) and "error" not in desc:
        instability = desc.get("instability_index")
        boman = desc.get("boman_index")
        hydrophobic = desc.get("hydrophobic_ratio")
        tox = 0.12
        if instability is not None:
            tox += max(0.0, min(0.12, (float(instability) - 30.0) / 100.0))
        if boman is not None:
            tox += max(0.0, min(0.08, (float(boman) - 1.0) / 25.0))
        if hydrophobic is not None:
            tox += max(0.0, min(0.05, (float(hydrophobic) - 0.45) / 4.0))
        return max(0.0, min(1.0, tox))

    return None


def _check_admet_divergence(result: Dict[str, Any]) -> Optional[str]:
    """PRST mismatch guard (2026-05-26) — pepADMET retrained vs ADMET-AI raw 값
    차이가 ADMET_DIVERGENCE_THRESHOLD 이상이면 warning 문자열 반환.

    탐지 source:
      - pepadmet 결과 → result["pepadmet"]["admet_tox"] 또는 result["pepadmet_tox"]
      - ADMET-AI 결과 → result["admet_ai"]["admet_tox"] 또는 result["admet_ai_tox"]

    한 쪽이라도 없으면 None 반환 (divergence 판정 불가).
    """
    if not isinstance(result, dict):
        return None

    def _read_source(d: Any, key: str = "admet_tox") -> Optional[float]:
        if isinstance(d, dict):
            value = d.get(key) or d.get("toxicity_probability") or d.get("toxicity_score")
            return _finite_or_none(value)
        return _finite_or_none(d)

    pepadmet_tox = _read_source(result.get("pepadmet"))
    if pepadmet_tox is None:
        pepadmet_tox = _finite_or_none(result.get("pepadmet_tox"))

    admet_ai_tox = _read_source(result.get("admet_ai"))
    if admet_ai_tox is None:
        admet_ai_tox = _finite_or_none(result.get("admet_ai_tox"))

    if pepadmet_tox is None or admet_ai_tox is None:
        return None

    delta = abs(pepadmet_tox - admet_ai_tox)
    if delta >= ADMET_DIVERGENCE_THRESHOLD:
        return ADMET_DIVERGENCE_WARNING_FMT.format(
            pepadmet_tox=pepadmet_tox,
            admet_ai_tox=admet_ai_tox,
            delta=delta,
            threshold=ADMET_DIVERGENCE_THRESHOLD,
        )
    return None


def _candidate_id(candidate: Dict[str, Any], index: int) -> str:
    return str(candidate.get("candidate_id") or candidate.get("id") or f"cand_{index}")


def _coerce_notes(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, tuple):
        return [str(v) for v in value]
    if isinstance(value, str):
        return [value] if value else []
    return []


def _append_warning(candidate: Dict[str, Any], notes: List[str], message: str) -> None:
    if message not in notes:
        notes.append(message)
    warning_list = _coerce_notes(candidate.get("warnings"))
    if message not in warning_list:
        warning_list.append(message)
    candidate["warnings"] = warning_list
    candidate["fallback_admet_tox"] = True
    logger.warning("%s: %s", _candidate_id(candidate, -1), message)


def enrich_candidates_from_wrappers(
    candidates: List[Dict[str, Any]],
    *,
    use_plifepred2: bool = True,
    use_modlamp_fallback: bool = True,
    check_pepadmet_web: bool = False,
) -> List[Dict[str, Any]]:
    """P1 sprint wrappers로 half_life/admet_tox 입력을 보강한다.

    D-AA가 감지된 후보는 wrapper 적용을 금지하고 confidence grade를
    UNAVAILABLE로 남긴다.
    """
    from pipeline_local.scripts.predict_admet_pepadmet import predict_admet
    from pipeline_local.scripts.predict_halflife_pepmsnd import predict_halflife
    from pipeline_local.scripts.sequence_to_smiles import sequence_to_linear_smiles

    halflife_conf = _endpoint_confidence("halflife_plifepred2", "P4")
    admet_conf = _endpoint_confidence("admet_pepadmet", "P1")

    enriched: List[Dict[str, Any]] = []
    for idx, candidate in enumerate(candidates):
        c = dict(candidate)
        seq = str(c.get("sequence", ""))
        cid = _candidate_id(c, idx)
        notes = _coerce_notes(c.get("enrichment_notes"))
        c["fallback_admet_tox"] = bool(c.get("fallback_admet_tox", False))
        c["warnings"] = _coerce_notes(c.get("warnings"))

        if contains_d_amino_acid(seq):
            notes.append("D-AA detected; halflife/admet wrappers skipped")
            c.update({
                "halflife_confidence_grade": UNAVAILABLE_GRADE,
                "admet_confidence_grade": UNAVAILABLE_GRADE,
                "enrichment_status": UNAVAILABLE_GRADE,
                "enrichment_notes": notes,
            })
            enriched.append(c)
            continue

        try:
            smiles_result = sequence_to_linear_smiles(seq)
            c["smiles"] = smiles_result.get("smiles", "")
            notes.extend(str(w) for w in smiles_result.get("warnings", []))
        except Exception as exc:
            notes.append(f"sequence_to_smiles failed: {exc}")

        try:
            hl_result = predict_halflife(
                seq,
                seq_id=cid,
                use_plifepred2=use_plifepred2,
                use_pepmsnd_web=False,
            )
            c["halflife_wrapper_result"] = hl_result
            hl_score = _extract_halflife_score(hl_result)
            if hl_score is not None:
                c["halflife_score"] = hl_score
                c["half_life"] = hl_score
            else:
                notes.append("halflife wrapper returned no score")
            c["halflife_confidence_grade"] = str(
                hl_result.get("final_confidence_grade")
                or halflife_conf.get("grade")
                or "P4"
            )
        except Exception as exc:
            notes.append(f"halflife wrapper failed: {exc}")
            c["halflife_confidence_grade"] = UNAVAILABLE_GRADE

        try:
            admet_result = predict_admet(
                seq,
                seq_id=cid,
                use_modlamp_fallback=use_modlamp_fallback,
                check_pepadmet_web=check_pepadmet_web,
            )
            c["admet_wrapper_result"] = admet_result
            admet_tox = _extract_admet_tox(admet_result)
            if admet_tox is not None:
                c["admet_tox"] = admet_tox
            else:
                notes.append("admet wrapper returned no toxicity score")
                _append_warning(c, notes, ADMET_FALLBACK_WARNING)
            c["admet_confidence_grade"] = str(
                admet_result.get("final_confidence_grade")
                or admet_conf.get("grade")
                or "P2"
            )
        except Exception as exc:
            notes.append(f"admet wrapper failed: {exc}")
            _append_warning(c, notes, ADMET_FALLBACK_WARNING)
            c["admet_confidence_grade"] = UNAVAILABLE_GRADE

        # PRST mismatch guard (2026-05-26):
        # pepADMET retrained 와 ADMET-AI raw 값 차이가 크면 OOD 의심 — warning
        # 으로 정직 노출. 후보 자체를 차단하지는 않음 (사용자가 추가 검증 결정).
        divergence_msg = _check_admet_divergence(c.get("admet_wrapper_result", {}))
        if divergence_msg:
            notes.append(divergence_msg)
            warning_list = _coerce_notes(c.get("warnings"))
            if divergence_msg not in warning_list:
                warning_list.append(divergence_msg)
            c["warnings"] = warning_list
            c["admet_divergence_high"] = True

        c["enrichment_status"] = "ENRICHED"
        c["enrichment_notes"] = notes
        enriched.append(c)

    return enriched


# ---------------------------------------------------------------------------
# 비지배 정렬 (Pareto Front)
# ---------------------------------------------------------------------------

def pareto_nondominated_sort(
    objectives: List[List[float]],
) -> List[int]:
    """목적 함수 벡터 집합에 대해 비지배 정렬을 수행한다.

    모든 목적 함수는 **최소화** 방향을 가정한다.
    (더 작은 값 = 더 좋음)

    구현: O(n²M) 단순 비지배 검사 (n = 후보 수, M = 목적 함수 수).
    pymoo 미설치 환경을 위한 독립 구현.

    Args:
        objectives: 목적 함수 값 리스트. shape = (n_candidates, n_objectives).
                    각 행이 한 후보의 목적 함수 벡터.

    Returns:
        각 후보의 비지배 순위 (1 = Pareto-optimal, 2 = 2nd front, ...).
        길이 = len(objectives).
    """
    n = len(objectives)
    if n == 0:
        return []

    ranks = [0] * n
    domination_count = [0] * n   # i를 지배하는 솔루션 수
    dominated_solutions: List[List[int]] = [[] for _ in range(n)]  # i가 지배하는 솔루션 목록

    # 지배 관계 계산
    for i in range(n):
        for j in range(i + 1, n):
            if _dominates(objectives[i], objectives[j]):
                dominated_solutions[i].append(j)
                domination_count[j] += 1
            elif _dominates(objectives[j], objectives[i]):
                dominated_solutions[j].append(i)
                domination_count[i] += 1

    # Front 1 식별
    current_front = [i for i in range(n) if domination_count[i] == 0]
    front_rank = 1
    while current_front:
        for i in current_front:
            ranks[i] = front_rank
        next_front = []
        for i in current_front:
            for j in dominated_solutions[i]:
                domination_count[j] -= 1
                if domination_count[j] == 0:
                    next_front.append(j)
        current_front = next_front
        front_rank += 1

    return ranks


def _dominates(a: List[float], b: List[float]) -> bool:
    """a가 b를 지배하는지 확인 (최소화 기준).

    Returns:
        True if a dominates b (a is at least as good in all objectives
        and strictly better in at least one).
    """
    at_least_as_good = all(ai <= bi for ai, bi in zip(a, b))
    strictly_better = any(ai < bi for ai, bi in zip(a, b))
    return at_least_as_good and strictly_better


# ---------------------------------------------------------------------------
# 메인 스코어링 클래스
# ---------------------------------------------------------------------------

class CompositeScorer:
    """복합 스코어링 엔진 (WSS + Pareto front + Tier 분류).

    사용 예::

        scorer = CompositeScorer()
        results_df = scorer.score(candidates)  # list[dict] → DataFrame
        tier_s = results_df[results_df["tier"] == "S"]

    가중치/Hard Cutoff 외부 주입::

        scorer = CompositeScorer(
            weights={"dg": 0.4, "selectivity": 0.3, "half_life": 0.15,
                     "admet_safety": 0.1, "radiolysis_safety": 0.05},
            hard_cutoffs={"dg_max": -10.0, "selectivity_min": 50.0},
        )
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        hard_cutoffs: Optional[Dict[str, Optional[float]]] = None,
        *,
        use_sst14_ref_dg: bool = True,
    ) -> None:
        """CompositeScorer 초기화.

        Args:
            weights:       가중치 dict. None이면 DEFAULT_WEIGHTS 사용.
                           합 = 1.0이어야 한다 (허용 오차 1e-6).
            hard_cutoffs:  Hard Cutoff dict. None이면 DEFAULT_HARD_CUTOFFS 사용.
                           dg_max=None이면 soft mode (dg Hard Cutoff 스킵).
            use_sst14_ref_dg: True이면 pharmacology_guards에서 SST14 ref ΔG를
                              자동 조회하여 dg_max에 적용 (hard_cutoffs["dg_max"]가
                              None인 경우에만).
        """
        # 가중치 설정 및 검증
        self.weights: Dict[str, float] = dict(DEFAULT_WEIGHTS)
        if weights is not None:
            self.weights.update(weights)
        self._validate_weights()

        # Hard Cutoff 설정
        self.hard_cutoffs: Dict[str, Optional[float]] = dict(DEFAULT_HARD_CUTOFFS)
        if hard_cutoffs is not None:
            self.hard_cutoffs.update(hard_cutoffs)

        # A-05 연동: pharmacology_guards에서 SST14 ref ΔG 자동 조회
        if use_sst14_ref_dg and self.hard_cutoffs.get("dg_max") is None:
            ref_dg = _get_sst14_ref_ddg()
            if ref_dg is not None:
                self.hard_cutoffs["dg_max"] = ref_dg
                logger.info(
                    "SST14 ref ΔG 자동 적용: dg_max = %.3f REU (pharmacology_guards.py)",
                    ref_dg,
                )
            else:
                logger.warning(
                    "SST14 ref ΔG 조회 실패 (A-05 미완료). dg Hard Cutoff 스킵 (soft mode)."
                )

        # 스코어 이후 결과 캐시 (explain() 지원)
        self._last_results: List[ScoringResult] = []

    def _validate_weights(self) -> None:
        """가중치 합 = 1.0 검증."""
        total = sum(self.weights.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"가중치 합이 1.0이 아닙니다: {total:.6f}. "
                f"weights = {self.weights}"
            )

    # ------------------------------------------------------------------
    # Hard Cutoff 검사
    # ------------------------------------------------------------------

    def _check_hard_cutoffs(
        self,
        candidate: ScoringInput,
    ) -> Tuple[bool, List[str]]:
        """Hard Cutoff 통과 여부를 반환한다.

        Args:
            candidate: 검사 대상 ScoringInput.

        Returns:
            (pass: bool, failures: list[str])
            failures는 실패한 cutoff 항목 이름 목록 (통과 시 빈 리스트).
        """
        failures: List[str] = []
        cutoffs = self.hard_cutoffs

        # 1. ΔG (SSTR2 결합) — dg_max=None이면 soft mode (스킵)
        dg_max = cutoffs.get("dg_max")
        if dg_max is not None:
            if candidate.dg > dg_max:
                failures.append(
                    f"dg_fail(dg={candidate.dg:.3f} > dg_max={dg_max:.3f})"
                )
        else:
            logger.debug("dg Hard Cutoff 스킵 (soft mode): candidate_id=%s", candidate.candidate_id)

        # 2. 선택성 (SSTR2 vs off-targets)
        sel_min = cutoffs.get("selectivity_min")
        if sel_min is not None:
            if candidate.selectivity < sel_min:
                failures.append(
                    f"selectivity_fail(sel={candidate.selectivity:.1f} < min={sel_min:.1f})"
                )

        # 3. Radiolysis 민감 잔기 수
        rad_max = cutoffs.get("radiolysis_max")
        if rad_max is not None:
            if candidate.radiolysis_count > int(rad_max):
                failures.append(
                    f"radiolysis_fail(count={candidate.radiolysis_count} > max={int(rad_max)})"
                )

        # 4. ADMET 독성 확률
        admet_max = cutoffs.get("admet_tox_max")
        if admet_max is not None:
            if candidate.admet_tox > admet_max:
                failures.append(
                    f"admet_fail(tox={candidate.admet_tox:.3f} > max={admet_max:.3f})"
                )

        # 5. Instability Index (Guruprasad 1990)
        inst_max = cutoffs.get("instability_max")
        if inst_max is not None:
            if candidate.instability_index >= inst_max:
                failures.append(
                    f"instability_fail(ii={candidate.instability_index:.1f} >= max={inst_max:.1f})"
                )

        return (len(failures) == 0, failures)

    # ------------------------------------------------------------------
    # 정규화
    # ------------------------------------------------------------------

    @staticmethod
    def _minmax_normalize(
        values: List[float],
        invert: bool = False,
    ) -> List[float]:
        """min-max 정규화 → [0, 1] 스케일링.

        Args:
            values: 정규화 대상 값 목록.
            invert: True이면 정규화 후 1-x 변환 (lower=better 지표에 사용).

        Returns:
            정규화된 값 목록. min==max이면 모두 1.0 반환.
        """
        if not values:
            return []
        vmin = min(values)
        vmax = max(values)
        if abs(vmax - vmin) < 1e-10:
            return [1.0] * len(values)  # 모든 값이 동일한 경우

        normalized = [(v - vmin) / (vmax - vmin) for v in values]
        if invert:
            normalized = [1.0 - v for v in normalized]
        return normalized

    # ------------------------------------------------------------------
    # WSS 계산
    # ------------------------------------------------------------------

    def _compute_wss(
        self,
        inputs: List[ScoringInput],
    ) -> List[Dict[str, float]]:
        """Hard Cutoff 통과 후보 집합에 대해 WSS를 계산한다.

        Args:
            inputs: Hard Cutoff 통과 후보 목록 (전체 후보가 아닌 통과 후보만).

        Returns:
            각 후보의 WSS 및 기여도 분해 dict 목록.
            순서는 inputs와 동일.
        """
        if not inputs:
            return []

        n = len(inputs)

        # 각 지표 값 추출
        dg_vals       = [c.dg for c in inputs]
        sel_vals      = [c.selectivity for c in inputs]
        hl_vals       = [c.half_life for c in inputs]
        admet_vals    = [c.admet_tox for c in inputs]
        rad_vals      = [float(c.radiolysis_count) for c in inputs]

        # 정규화
        # dg: 낮을수록 좋으므로 invert=True
        dg_norm       = self._minmax_normalize(dg_vals, invert=True)
        # selectivity: 높을수록 좋으므로 invert=False
        sel_norm      = self._minmax_normalize(sel_vals, invert=False)
        # half_life: 높을수록 좋으므로 invert=False
        hl_norm       = self._minmax_normalize(hl_vals, invert=False)
        # admet_tox: 낮을수록 좋으므로 invert=True → admet_safety = 1 - normalized(tox)
        admet_norm    = self._minmax_normalize(admet_vals, invert=True)
        # radiolysis_count: 낮을수록 좋으므로 invert=True → radiolysis_safety
        rad_norm      = self._minmax_normalize(rad_vals, invert=True)

        w = self.weights
        results = []
        for i in range(n):
            contrib = {
                "dg": w["dg"] * dg_norm[i],
                "selectivity": w["selectivity"] * sel_norm[i],
                "half_life": w["half_life"] * hl_norm[i],
                "admet_safety": w["admet_safety"] * admet_norm[i],
                "radiolysis_safety": w["radiolysis_safety"] * rad_norm[i],
            }
            wss = sum(contrib.values())
            contrib["wss_total"] = wss
            results.append(contrib)

        return results

    # ------------------------------------------------------------------
    # 메인 진입점
    # ------------------------------------------------------------------

    def score(
        self,
        candidates: List[Dict[str, Any]],
        *,
        enrich_from_wrappers: bool = False,
    ) -> "pd.DataFrame":
        """복합 스코어링 실행 → DataFrame 반환.

        Args:
            candidates: 후보 list[dict]. 각 dict는 ScoringInput.from_dict() 형식.
                        필수 필드: candidate_id.
                        선택 필드 (누락 시 기본값 적용):
                            dg, selectivity, half_life, admet_tox,
                            radiolysis_count, instability_index
            enrich_from_wrappers: True이면 P1 sprint wrappers로 half_life/admet_tox
                                  및 confidence metadata를 보강한다.

        Returns:
            pd.DataFrame, columns:
                candidate_id, dg, selectivity, half_life, admet_tox,
                radiolysis_count, instability_index,
                hard_cutoff_pass, hard_cutoff_failures,
                wss, pareto_rank, tier, explain_json

        Raises:
            WARN_LOW_PASSRATE: Hard Cutoff 통과율 < 5% 시.
            ImportError: pandas/numpy 미설치 시.
        """
        if not _HAS_PANDAS:
            raise ImportError(
                "composite_scorer.score()는 pandas가 필요합니다. "
                "pip install pandas numpy"
            )

        if not candidates:
            logger.warning("빈 후보 목록. 빈 DataFrame 반환.")
            return pd.DataFrame()

        if enrich_from_wrappers:
            candidates = enrich_candidates_from_wrappers(candidates)

        # dict → ScoringInput 변환
        inputs = [ScoringInput.from_dict(c) for c in candidates]
        n_total = len(inputs)

        # Hard Cutoff 1차 필터
        hc_results: List[Tuple[bool, List[str]]] = [
            self._check_hard_cutoffs(c) for c in inputs
        ]

        passed_idx  = [i for i, (p, _) in enumerate(hc_results) if p]
        failed_idx  = [i for i, (p, _) in enumerate(hc_results) if not p]
        n_passed = len(passed_idx)

        logger.info(
            "Hard Cutoff 결과: %d/%d 통과 (%.1f%%)",
            n_passed, n_total, 100.0 * n_passed / n_total if n_total else 0,
        )

        # 통과율 5% 미만 경고
        if n_total > 0 and (n_passed / n_total) < LOW_PASSRATE_THRESHOLD:
            msg = (
                f"Hard Cutoff 통과율 {100.*n_passed/n_total:.1f}% < "
                f"{100.*LOW_PASSRATE_THRESHOLD:.0f}%. "
                f"Hard Cutoff 임계값 재검토 권고. "
                f"현재 cutoffs: {self.hard_cutoffs}"
            )
            logger.warning(msg)
            raise WARN_LOW_PASSRATE(msg)

        # ------------------------------------------------------------------
        # WSS 계산 (Hard Cutoff 통과 후보만)
        # ------------------------------------------------------------------
        passed_inputs = [inputs[i] for i in passed_idx]

        wss_data: List[Dict[str, float]] = []
        if passed_inputs:
            wss_data = self._compute_wss(passed_inputs)

        # ------------------------------------------------------------------
        # Pareto Front (후보 수 ≥ 2일 때 계산, 10 미만 시 경고)
        # ------------------------------------------------------------------
        pareto_ranks_passed = [0] * n_passed

        if n_passed >= 2:
            if n_passed < 10:
                logger.warning(
                    "Hard Cutoff 통과 후보 수 %d < 10. "
                    "Pareto front 계산은 수행하나 신뢰도 낮음.",
                    n_passed,
                )
            # 목적 함수 (최소화 방향으로 변환)
            # 원래 값: dg(낮을수록 좋음=그대로), selectivity(높을수록 좋음=-x),
            #         half_life(높을수록 좋음=-x), admet_tox(낮을수록 좋음=그대로),
            #         radiolysis_count(낮을수록 좋음=그대로)
            objectives = []
            for c in passed_inputs:
                objectives.append([
                    c.dg,                       # 최소화 (낮을수록 좋음)
                    -c.selectivity,             # 최소화 (높을수록 좋음 → 부호 반전)
                    -c.half_life,               # 최소화 (높을수록 좋음 → 부호 반전)
                    c.admet_tox,                # 최소화 (낮을수록 좋음)
                    float(c.radiolysis_count),  # 최소화 (낮을수록 좋음)
                ])
            pareto_ranks_passed = pareto_nondominated_sort(objectives)
        elif n_passed == 1:
            pareto_ranks_passed = [1]
            logger.warning("Hard Cutoff 통과 후보가 1개. Pareto front = [1] (단일 솔루션).")

        # ------------------------------------------------------------------
        # Tier 분류
        # ------------------------------------------------------------------
        if passed_inputs:
            wss_values = [d["wss_total"] for d in wss_data]
            # 상위 20% 경계값
            top_k = max(1, int(n_passed * TIER_TOP_PERCENTILE))
            sorted_wss = sorted(wss_values, reverse=True)
            top_threshold = sorted_wss[top_k - 1]
        else:
            wss_values = []
            top_threshold = float("inf")

        # ------------------------------------------------------------------
        # 결과 조합
        # ------------------------------------------------------------------
        all_results: List[ScoringResult] = []

        # Hard Cutoff 통과 후보
        for rank_idx, orig_idx in enumerate(passed_idx):
            c = inputs[orig_idx]
            wss_val = wss_data[rank_idx]["wss_total"] if wss_data else 0.0
            p_rank  = pareto_ranks_passed[rank_idx] if pareto_ranks_passed else 0
            explain = {k: v for k, v in wss_data[rank_idx].items() if k != "wss_total"} if wss_data else {}

            # Tier 분류 로직 (A-04 §Step 3 최종 순위 결정)
            is_top20 = wss_val >= top_threshold
            is_pareto = p_rank == 1

            if is_top20 and is_pareto:
                tier = "S"
            elif is_top20 or is_pareto:
                tier = "A"
            else:
                tier = "B"

            all_results.append(ScoringResult(
                candidate_id=c.candidate_id,
                dg=c.dg,
                selectivity=c.selectivity,
                half_life=c.half_life,
                admet_tox=c.admet_tox,
                radiolysis_count=c.radiolysis_count,
                instability_index=c.instability_index,
                hard_cutoff_pass=True,
                hard_cutoff_failures=[],
                wss=wss_val,
                pareto_rank=p_rank,
                tier=tier,
                explain=explain,
                halflife_confidence_grade=str(c.extra.get("halflife_confidence_grade", "")),
                admet_confidence_grade=str(c.extra.get("admet_confidence_grade", "")),
                smiles=str(c.extra.get("smiles", "")),
                enrichment_status=str(c.extra.get("enrichment_status", "")),
                enrichment_notes=_coerce_notes(c.extra.get("enrichment_notes")),
                fallback_admet_tox=bool(c.extra.get("fallback_admet_tox", False)),
                warnings=_coerce_notes(c.extra.get("warnings")),
            ))

        # Hard Cutoff 실패 후보
        for orig_idx in failed_idx:
            c = inputs[orig_idx]
            _, failures = hc_results[orig_idx]
            all_results.append(ScoringResult(
                candidate_id=c.candidate_id,
                dg=c.dg,
                selectivity=c.selectivity,
                half_life=c.half_life,
                admet_tox=c.admet_tox,
                radiolysis_count=c.radiolysis_count,
                instability_index=c.instability_index,
                hard_cutoff_pass=False,
                hard_cutoff_failures=failures,
                wss=0.0,
                pareto_rank=0,
                tier="FAIL",
                explain={},
                halflife_confidence_grade=str(c.extra.get("halflife_confidence_grade", "")),
                admet_confidence_grade=str(c.extra.get("admet_confidence_grade", "")),
                smiles=str(c.extra.get("smiles", "")),
                enrichment_status=str(c.extra.get("enrichment_status", "")),
                enrichment_notes=_coerce_notes(c.extra.get("enrichment_notes")),
                fallback_admet_tox=bool(c.extra.get("fallback_admet_tox", False)),
                warnings=_coerce_notes(c.extra.get("warnings")),
            ))

        # 캐시 저장 (explain() 지원)
        self._last_results = all_results

        # DataFrame 생성
        rows = [r.to_dict() for r in all_results]
        df = pd.DataFrame(rows)

        # 정렬: Tier → WSS 내림차순
        tier_order = {"S": 0, "A": 1, "B": 2, "FAIL": 3}
        if not df.empty:
            df["_tier_order"] = df["tier"].map(tier_order)
            df = df.sort_values(["_tier_order", "wss"], ascending=[True, False])
            df = df.drop(columns=["_tier_order"]).reset_index(drop=True)

        logger.info(
            "Tier 분류 결과: S=%d, A=%d, B=%d, FAIL=%d",
            (df["tier"] == "S").sum() if not df.empty else 0,
            (df["tier"] == "A").sum() if not df.empty else 0,
            (df["tier"] == "B").sum() if not df.empty else 0,
            (df["tier"] == "FAIL").sum() if not df.empty else 0,
        )

        return df

    # ------------------------------------------------------------------
    # Pareto Front (독립 API)
    # ------------------------------------------------------------------

    def pareto_front(
        self,
        candidates: "pd.DataFrame",
    ) -> "pd.DataFrame":
        """Hard Cutoff 통과 후보 DataFrame에서 Pareto front (rank=1) 추출.

        Args:
            candidates: score() 반환 DataFrame (또는 동일 형식).

        Returns:
            pareto_rank == 1인 행 필터링 DataFrame.
        """
        if not _HAS_PANDAS:
            raise ImportError("pandas 필요")
        if "pareto_rank" not in candidates.columns:
            raise ValueError("'pareto_rank' 컬럼이 없습니다. score() 결과를 입력하세요.")
        return candidates[candidates["pareto_rank"] == 1].copy()

    # ------------------------------------------------------------------
    # 기여도 분해 (explain)
    # ------------------------------------------------------------------

    def explain(self, candidate_id: str) -> Dict[str, Any]:
        """마지막 score() 결과에서 특정 후보의 스코어 기여도를 반환한다.

        Args:
            candidate_id: 조회할 후보 ID.

        Returns:
            {
                "candidate_id": str,
                "tier": str,
                "wss": float,
                "pareto_rank": int,
                "hard_cutoff_pass": bool,
                "hard_cutoff_failures": list[str],
                "contributions": {metric: weighted_contribution},
                "weights_used": dict,
                "cutoffs_used": dict,
            }

        Raises:
            KeyError: candidate_id를 찾을 수 없을 때.
        """
        for r in self._last_results:
            if r.candidate_id == candidate_id:
                return {
                    "candidate_id": r.candidate_id,
                    "tier": r.tier,
                    "wss": r.wss,
                    "pareto_rank": r.pareto_rank,
                    "hard_cutoff_pass": r.hard_cutoff_pass,
                    "hard_cutoff_failures": r.hard_cutoff_failures,
                    "contributions": r.explain,
                    "weights_used": dict(self.weights),
                    "cutoffs_used": dict(self.hard_cutoffs),
                }
        raise KeyError(
            f"candidate_id={candidate_id!r} 를 마지막 score() 결과에서 찾을 수 없습니다."
        )

    # ------------------------------------------------------------------
    # 결과 저장
    # ------------------------------------------------------------------

    def save_results(
        self,
        df: "pd.DataFrame",
        output_dir: Optional[str] = None,
    ) -> Dict[str, str]:
        """Tier별 CSV 파일 및 통합 CSV를 저장한다.

        저장 경로:
            {output_dir}/tier_s_candidates.csv
            {output_dir}/tier_a_candidates.csv
            {output_dir}/tier_b_candidates.csv
            {output_dir}/hard_cutoff_pass.csv
            {output_dir}/all_candidates.csv

        Args:
            df:         score() 반환 DataFrame.
            output_dir: 저장 디렉토리. None이면 runs_local/final_candidates/ 사용.

        Returns:
            저장된 파일 경로 dict.
        """
        if not _HAS_PANDAS:
            raise ImportError("pandas 필요")

        if output_dir is None:
            # 기본 경로: 레포지토리 루트 / runs_local / final_candidates
            _script_dir = Path(__file__).resolve().parent
            _repo_root = _script_dir.parent.parent
            output_dir = str(_repo_root / "runs_local" / "final_candidates")

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        saved: Dict[str, str] = {}

        # 전체
        all_path = out / "all_candidates.csv"
        df.to_csv(all_path, index=False, encoding="utf-8-sig")
        saved["all"] = str(all_path)

        # Hard Cutoff 통과
        if "hard_cutoff_pass" in df.columns:
            passed_df = df[df["hard_cutoff_pass"]]
            hc_path = out / "hard_cutoff_pass.csv"
            passed_df.to_csv(hc_path, index=False, encoding="utf-8-sig")
            saved["hard_cutoff_pass"] = str(hc_path)

        # Tier별
        for tier in ["S", "A", "B"]:
            tier_df = df[df["tier"] == tier]
            tier_path = out / f"tier_{tier.lower()}_candidates.csv"
            tier_df.to_csv(tier_path, index=False, encoding="utf-8-sig")
            saved[f"tier_{tier}"] = str(tier_path)

        logger.info("결과 저장 완료: %s", output_dir)
        return saved
