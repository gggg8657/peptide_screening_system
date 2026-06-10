"""composite_scorer.py
======================
Top-K 후보 선정 복합 스코어링 체계 (A-04, KAERI-AIRL-MOM-2026-003).

파이프라인 처리 흐름:
    1. Hard Cutoff 필터 (5개 게이트 — 전원 통과 필수)
    2. Weighted Sum Score (WSS) 산출 (Hard Cutoff 통과 후보만)
    3. NSGA-II 기반 Pareto Front 계산 (후보 수 ≥ 50 시 활성)
    4. Tier 분류 (S / A / B / FAIL)

Hard Cutoff 기준:
    | 지표              | 기준                           | 키              |
    |------------------|-------------------------------|----------------|
    | ΔG SSTR2         | ≤ SST14 레퍼런스 (-95.024 REU) | candidate.ddg  |
    | 셀렉티비티 비율     | ≥ 100×                         | selectivity_ratio |
    | Radiolysis 민감잔기| ≤ 3개                          | (자동 계산)      |
    | ADMET 독성 확률    | ≤ 0.3                          | admet_tox      |
    | Instability Index | < 40                           | instability    |

WSS 가중치 (합계 = 1.0):
    ΔG (SSTR2)   : 0.35
    셀렉티비티     : 0.25
    반감기         : 0.20
    ADMET (비독성) : 0.10
    Radiolysis 안전성: 0.10

HEURISTIC 주의 (H-06 가드):
    - WSS 및 Pareto rank는 상대 순위 도구임. 임상 판단 대체 불가.
    - half_life 값은 heuristic ranking score (실측 PK 아님).
    - NSGA-II Pareto front는 후보 ≥ 50 시만 활성. 미만 시 WSS만 사용.
    - admet_tox: P1 pepADMET 결과 의존 — P1 미완료 시 input dict에서 제공.

pymoo 의존성:
    pymoo 미설치 시 Pareto front 계산을 건너뛰고 WSS만 사용한다.
    설치: pip install pymoo 또는 conda install -c conda-forge pymoo
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pipeline_local.scoring.radiolysis_scorer import (
    HARD_CUTOFF_SENSITIVE_COUNT,
    compute_radiolysis_score,
)
from pipeline_local.scripts.pharmacology_guards import LITERATURE_VALUES

# ---------------------------------------------------------------------------
# SST14 SSTR2 레퍼런스 ΔG (pharmacology_guards LITERATURE_VALUES에서 로드)
# H-01 가드: 직접 하드코딩 금지 — lookup table에서 가져옴.
# ---------------------------------------------------------------------------
_ref_entry = LITERATURE_VALUES["SST14_SSTR2_ref_ddg_boltz2"]["ref_ddg_reu"]
SST14_SSTR2_REF_DDG: float = float(_ref_entry[0])  # -95.024 REU

# ---------------------------------------------------------------------------
# WSS 가중치 (가중치 합 = 1.0 제약)
# ---------------------------------------------------------------------------
WSS_WEIGHTS: Dict[str, float] = {
    "ddg":         0.35,
    "selectivity": 0.25,
    "half_life":   0.20,
    "admet_tox":   0.10,
    "radiolysis":  0.10,
}

# 가중치 합 = 1.0 내부 검증
assert abs(sum(WSS_WEIGHTS.values()) - 1.0) < 1e-9, (
    f"WSS_WEIGHTS 합계 오류: {sum(WSS_WEIGHTS.values())} ≠ 1.0"
)

# ---------------------------------------------------------------------------
# Hard Cutoff 임계값 상수
# ---------------------------------------------------------------------------
HARD_CUTOFF_DDG: float = SST14_SSTR2_REF_DDG       # ≤ -95.024 REU
HARD_CUTOFF_SELECTIVITY: float = 100.0              # ≥ 100×
HARD_CUTOFF_RADIOLYSIS_COUNT: int = HARD_CUTOFF_SENSITIVE_COUNT  # ≤ 3
HARD_CUTOFF_ADMET_TOX: float = 0.3                 # ≤ 0.3
HARD_CUTOFF_INSTABILITY: float = 40.0              # < 40

# WSS Radiolysis 정규화 기준 최대값 (10 - count 가 [0, 1]에 매핑되도록)
_RADIOLYSIS_NORM_MAX: float = 10.0

# Pareto Front 활성화 최소 후보 수
PARETO_MIN_CANDIDATES: int = 50

# Tier 상위 20% 기준
WSS_TOP_FRACTION: float = 0.20


def enrich_candidates_from_wrappers(
    candidates: List[Dict[str, Any]],
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """P1 sprint wrapper enrichment helper.

    Implementation lives in pipeline_local.scripts.composite_scorer so the CLI
    and scoring entry points share identical D-AA guard and confidence metadata.
    """
    from pipeline_local.scripts.composite_scorer import (
        enrich_candidates_from_wrappers as _enrich,
    )

    return _enrich(candidates, **kwargs)

# ---------------------------------------------------------------------------
# pymoo 임포트 (optional)
# ---------------------------------------------------------------------------
try:
    import numpy as np  # type: ignore
    from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting  # type: ignore

    _PYMOO_AVAILABLE = True
except ImportError:
    _PYMOO_AVAILABLE = False
    try:
        import numpy as np  # type: ignore
        _NUMPY_AVAILABLE = True
    except ImportError:
        _NUMPY_AVAILABLE = False


# ---------------------------------------------------------------------------
# Tier 열거형
# ---------------------------------------------------------------------------
class Tier(str, Enum):
    """후보 Tier 분류.

    S:    WSS top 20% ∩ Pareto front — 합성 우선 추천
    A:    WSS top 20% XOR Pareto front — 2순위 검토
    B:    나머지 Hard Cutoff 통과 후보 — 보류
    FAIL: Hard Cutoff 미통과 — 탈락
    """
    S    = "TIER_S"
    A    = "TIER_A"
    B    = "TIER_B"
    FAIL = "TIER_FAIL"


# ---------------------------------------------------------------------------
# 결과 dataclass
# ---------------------------------------------------------------------------
@dataclass
class ScoringResult:
    """단일 후보의 스코어링 결과.

    Attributes:
        candidate_id:         후보 식별자
        passed_hard_cutoff:   Hard Cutoff 전원 통과 여부
        hard_cutoff_failures: 실패한 게이트 이름 목록
        wss:                  Weighted Sum Score [0, 1] (Hard Cutoff 미통과 시 None)
        is_pareto:            Pareto front 소속 여부 (Pareto 미계산 시 None)
        tier:                 Tier 분류 (S/A/B/FAIL)
        radiolysis_info:      compute_radiolysis_score() 반환 dict
        raw:                  원본 candidate dict (진단용)
        fallback_admet_tox:   ADMET wrapper 실패로 기존 입력값을 사용했는지 여부
        warnings:             명시적 경고 목록
    """
    candidate_id: str
    passed_hard_cutoff: bool
    hard_cutoff_failures: List[str]
    wss: Optional[float]
    is_pareto: Optional[bool]
    tier: Tier
    radiolysis_info: Dict[str, Any]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)
    fallback_admet_tox: bool = False
    warnings: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Hard Cutoff 적용
# ---------------------------------------------------------------------------
def apply_hard_cutoffs(
    candidate: Dict[str, Any],
    radiolysis_info: Dict[str, Any],
    ref_ddg: float = HARD_CUTOFF_DDG,
) -> Tuple[bool, List[str]]:
    """후보에 Hard Cutoff 5개 게이트를 적용한다.

    Args:
        candidate:       후보 dict. 필수 키:
                         ddg (float), selectivity_ratio (float),
                         admet_tox (float), instability (float)
        radiolysis_info: compute_radiolysis_score() 반환 dict
        ref_ddg:         ΔG Hard Cutoff 기준 (기본: SST14_SSTR2_REF_DDG)

    Returns:
        (passed: bool, failures: List[str])
        passed == True 이면 모든 게이트 통과.
        failures는 실패한 게이트 이름 목록.
    """
    failures: List[str] = []

    # Gate 1: ΔG SSTR2 ≤ SST14 레퍼런스
    ddg = float(candidate.get("ddg", 0.0))
    if ddg > ref_ddg:
        failures.append(
            f"ddg ({ddg:.3f} REU) > ref ({ref_ddg:.3f} REU)"
        )

    # Gate 2: 셀렉티비티 ≥ 100×
    sel = float(candidate.get("selectivity_ratio", 0.0))
    if sel < HARD_CUTOFF_SELECTIVITY:
        failures.append(
            f"selectivity_ratio ({sel:.1f}×) < {HARD_CUTOFF_SELECTIVITY}×"
        )

    # Gate 3: Radiolysis 민감 잔기 수 ≤ 3
    rad_count = int(radiolysis_info["sensitive_count"])
    if rad_count > HARD_CUTOFF_RADIOLYSIS_COUNT:
        failures.append(
            f"radiolysis sensitive_count ({rad_count}) > {HARD_CUTOFF_RADIOLYSIS_COUNT}"
        )

    # Gate 4: ADMET 독성 확률 ≤ 0.3
    admet = float(candidate.get("admet_tox", 1.0))
    if admet > HARD_CUTOFF_ADMET_TOX:
        failures.append(
            f"admet_tox ({admet:.3f}) > {HARD_CUTOFF_ADMET_TOX}"
        )

    # Gate 5: Instability Index < 40
    ii = float(candidate.get("instability", 100.0))
    if ii >= HARD_CUTOFF_INSTABILITY:
        failures.append(
            f"instability ({ii:.1f}) >= {HARD_CUTOFF_INSTABILITY}"
        )

    passed = len(failures) == 0
    return passed, failures


# ---------------------------------------------------------------------------
# WSS 정규화 헬퍼
# ---------------------------------------------------------------------------
def _minmax_normalize(values: List[float]) -> List[float]:
    """Min-Max 정규화 [0, 1].

    모든 값이 동일하면 0.5 반환 (division by zero 방지).
    """
    mn = min(values)
    mx = max(values)
    rng = mx - mn
    if rng < 1e-12:
        return [0.5] * len(values)
    return [(v - mn) / rng for v in values]


def compute_wss(
    candidates: List[Dict[str, Any]],
    radiolysis_infos: List[Dict[str, Any]],
) -> List[float]:
    """Hard Cutoff 통과 후보들의 Weighted Sum Score를 계산한다.

    WSS = 0.35·norm(-ΔG) + 0.25·norm(selectivity) + 0.20·norm(half_life)
          + 0.10·norm(1 - admet_tox) + 0.10·norm(10 - radiolysis_count)

    정규화: 후보군 내 min-max [0, 1].

    Args:
        candidates:       Hard Cutoff 통과 후보 dict 목록
        radiolysis_infos: 각 후보의 compute_radiolysis_score() 결과 (같은 순서)

    Returns:
        WSS 값 목록 (같은 순서, [0, 1])

    Raises:
        ValueError: candidates와 radiolysis_infos 길이가 다른 경우
    """
    if len(candidates) != len(radiolysis_infos):
        raise ValueError(
            f"candidates({len(candidates)})와 radiolysis_infos({len(radiolysis_infos)}) 길이 불일치"
        )
    if not candidates:
        return []

    # 각 차원 raw 값 추출
    neg_ddg_vals = [-float(c.get("ddg", 0.0)) for c in candidates]
    sel_vals     = [float(c.get("selectivity_ratio", 0.0)) for c in candidates]
    hl_vals      = [float(c.get("half_life", 0.0)) for c in candidates]
    # 1 - admet_tox: 낮은 독성 = 높은 값
    admet_inv    = [1.0 - float(c.get("admet_tox", 1.0)) for c in candidates]
    # 10 - radiolysis_count: 낮은 민감 잔기 수 = 높은 값
    rad_inv      = [
        _RADIOLYSIS_NORM_MAX - float(r["sensitive_count"]) for r in radiolysis_infos
    ]

    # Min-Max 정규화
    norm_ddg   = _minmax_normalize(neg_ddg_vals)
    norm_sel   = _minmax_normalize(sel_vals)
    norm_hl    = _minmax_normalize(hl_vals)
    norm_admet = _minmax_normalize(admet_inv)
    norm_rad   = _minmax_normalize(rad_inv)

    w = WSS_WEIGHTS
    wss_list = [
        w["ddg"]         * norm_ddg[i]
        + w["selectivity"] * norm_sel[i]
        + w["half_life"]   * norm_hl[i]
        + w["admet_tox"]   * norm_admet[i]
        + w["radiolysis"]  * norm_rad[i]
        for i in range(len(candidates))
    ]
    return wss_list


# ---------------------------------------------------------------------------
# Pareto Front 계산 (pymoo)
# ---------------------------------------------------------------------------
def _compute_pareto_front_indices(
    candidates: List[Dict[str, Any]],
    radiolysis_infos: List[Dict[str, Any]],
) -> Optional[List[int]]:
    """Non-Dominated (Pareto front) 인덱스를 반환한다.

    목적 함수 (최소화):
        [ddg, -selectivity_ratio, -half_life, admet_tox, radiolysis_count]
        (ddg는 이미 음수 — 더 작을수록 = 더 강한 결합 = 더 좋음)

    pymoo 미설치 시 None 반환.
    후보 수 < PARETO_MIN_CANDIDATES 시 None 반환.

    Args:
        candidates:       후보 dict 목록
        radiolysis_infos: 각 후보의 radiolysis 정보 (같은 순서)

    Returns:
        Pareto front 인덱스 목록 또는 None
    """
    if not _PYMOO_AVAILABLE:
        warnings.warn(
            "pymoo 미설치: Pareto front 계산 건너뜀. WSS만 사용합니다. "
            "설치: pip install pymoo",
            UserWarning,
            stacklevel=3,
        )
        return None

    if len(candidates) < PARETO_MIN_CANDIDATES:
        return None  # 후보 미달 — WSS만 사용 (경고 없음, 정상 분기)

    # 목적 함수 행렬 구성 (n × 5), 모두 최소화
    F = np.array([
        [
            float(c.get("ddg", 0.0)),                      # minimize ddg
            -float(c.get("selectivity_ratio", 0.0)),        # minimize -selectivity
            -float(c.get("half_life", 0.0)),                # minimize -half_life
            float(c.get("admet_tox", 1.0)),                 # minimize admet_tox
            float(r["sensitive_count"]),                    # minimize rad_count
        ]
        for c, r in zip(candidates, radiolysis_infos)
    ])

    nds = NonDominatedSorting()
    fronts = nds.do(F, n_stop_if_ranked=len(candidates))
    pareto_indices = list(fronts[0])
    return pareto_indices


# ---------------------------------------------------------------------------
# 메인 스코어링 함수
# ---------------------------------------------------------------------------
def score_candidates(
    candidates: List[Dict[str, Any]],
    ref_ddg: float = HARD_CUTOFF_DDG,
    ss_bond_positions: Tuple[int, ...] = (3, 14),
    *,
    enrich_from_wrappers: bool = False,
) -> List[ScoringResult]:
    """후보 목록에 복합 스코어링을 적용하여 Tier 분류 결과를 반환한다.

    처리 흐름:
        1. 각 후보에 Radiolysis score 계산
        2. Hard Cutoff 5개 게이트 적용
        3. 통과 후보에 WSS 계산
        4. 후보 ≥ 50 시 Pareto front 계산 (pymoo 필요)
        5. Tier 분류 (S/A/B/FAIL)

    Hard Cutoff 통과율 < 5% 시 경고 출력 (Critic Agent 플래그).

    Args:
        candidates:        후보 dict 목록. 각 dict 필수 키:
                           id (str), sequence (str), ddg (float),
                           selectivity_ratio (float), half_life (float),
                           admet_tox (float), instability (float)
        ref_ddg:           ΔG Hard Cutoff 기준값 (기본: SST14_SSTR2_REF_DDG)
        ss_bond_positions: Radiolysis 계산 시 SS bond 제외 위치 (1-indexed tuple)
        enrich_from_wrappers: True이면 P1 sprint wrappers로 sequence 기반
                              half_life/admet_tox를 보강한다. D-AA 후보는
                              wrapper 적용 없이 UNAVAILABLE metadata만 남긴다.

    Returns:
        List[ScoringResult] — 입력과 동일 순서

    Raises:
        ValueError: candidates가 비어 있는 경우
    """
    if not candidates:
        raise ValueError("candidates 목록이 비어 있습니다.")

    if enrich_from_wrappers:
        candidates = enrich_candidates_from_wrappers(candidates)

    n_total = len(candidates)

    # ------------------------------------------------------------------
    # Step 1: Radiolysis 점수 계산 (모든 후보)
    # ------------------------------------------------------------------
    radiolysis_infos: List[Dict[str, Any]] = []
    for cand in candidates:
        seq = str(cand.get("sequence", ""))
        rad = compute_radiolysis_score(seq, ss_bond_positions=ss_bond_positions)
        radiolysis_infos.append(rad)

    # ------------------------------------------------------------------
    # Step 2: Hard Cutoff 적용
    # ------------------------------------------------------------------
    pass_flags:    List[bool]       = []
    failure_lists: List[List[str]]  = []

    for cand, rad in zip(candidates, radiolysis_infos):
        passed, failures = apply_hard_cutoffs(cand, rad, ref_ddg=ref_ddg)
        pass_flags.append(passed)
        failure_lists.append(failures)

    # Hard Cutoff 통과 후보 수집 (원본 인덱스 보존)
    passed_indices = [i for i, p in enumerate(pass_flags) if p]
    passed_candidates   = [candidates[i]      for i in passed_indices]
    passed_rad_infos    = [radiolysis_infos[i] for i in passed_indices]

    # Critic Agent 플래그: 통과율 < 5%
    n_passed = len(passed_indices)
    if n_total >= 10 and n_passed / n_total < 0.05:
        warnings.warn(
            f"Hard Cutoff 통과율 {n_passed}/{n_total} ({n_passed/n_total:.1%}) < 5%. "
            "임계값 재검토가 필요할 수 있습니다 (Critic Agent 플래그).",
            UserWarning,
            stacklevel=2,
        )

    # ------------------------------------------------------------------
    # Step 3: WSS 계산 (Hard Cutoff 통과 후보만)
    # ------------------------------------------------------------------
    wss_list: List[float] = []
    if passed_candidates:
        wss_list = compute_wss(passed_candidates, passed_rad_infos)

    # WSS → 통과 후보 인덱스 매핑 dict {원본 idx: wss}
    wss_map: Dict[int, float] = {
        orig_idx: wss_list[rank]
        for rank, orig_idx in enumerate(passed_indices)
    }

    # ------------------------------------------------------------------
    # Step 4: Pareto Front 계산 (후보 ≥ 50 + pymoo 설치 시)
    # ------------------------------------------------------------------
    pareto_orig_indices: Optional[set] = None

    if n_passed >= PARETO_MIN_CANDIDATES:
        pareto_rel_indices = _compute_pareto_front_indices(
            passed_candidates, passed_rad_infos
        )
        if pareto_rel_indices is not None:
            # 상대 인덱스 → 원본 인덱스 변환
            pareto_orig_indices = {
                passed_indices[rel_i] for rel_i in pareto_rel_indices
            }

    # ------------------------------------------------------------------
    # Step 5: Tier 분류
    # ------------------------------------------------------------------
    # WSS top 20% 임계값 계산
    top20_threshold: Optional[float] = None
    if wss_list:
        sorted_wss = sorted(wss_list, reverse=True)
        top20_count = max(1, int(len(sorted_wss) * WSS_TOP_FRACTION))
        # 상위 20% 경계값 (이상 값이 top 20%)
        top20_threshold = sorted_wss[top20_count - 1]

    results: List[ScoringResult] = []
    for orig_idx, cand in enumerate(candidates):
        cand_id = str(cand.get("id", f"cand_{orig_idx}"))
        passed  = pass_flags[orig_idx]
        rad_info = radiolysis_infos[orig_idx]
        failures = failure_lists[orig_idx]
        fallback_admet_tox = bool(cand.get("fallback_admet_tox", False))
        result_warnings = [
            str(w) for w in cand.get("warnings", [])
        ] if isinstance(cand.get("warnings"), list) else []

        if not passed:
            # Hard Cutoff 탈락
            results.append(ScoringResult(
                candidate_id         = cand_id,
                passed_hard_cutoff   = False,
                hard_cutoff_failures = failures,
                wss                  = None,
                is_pareto            = None,
                tier                 = Tier.FAIL,
                radiolysis_info      = rad_info,
                raw                  = cand,
                fallback_admet_tox   = fallback_admet_tox,
                warnings             = result_warnings,
            ))
            continue

        wss_val = wss_map[orig_idx]

        # Pareto 소속 여부
        is_pareto: Optional[bool]
        if pareto_orig_indices is not None:
            is_pareto = orig_idx in pareto_orig_indices
        else:
            is_pareto = None

        # Tier 결정
        in_top20 = top20_threshold is not None and wss_val >= top20_threshold

        if pareto_orig_indices is None:
            # Pareto 미계산 (후보 < 50 or pymoo 없음): WSS top 20% = Tier-S
            tier = Tier.S if in_top20 else Tier.B
        else:
            # Pareto 계산 완료: XOR 로직
            in_pareto = is_pareto is True
            if in_top20 and in_pareto:
                tier = Tier.S
            elif in_top20 or in_pareto:
                tier = Tier.A
            else:
                tier = Tier.B

        results.append(ScoringResult(
            candidate_id         = cand_id,
            passed_hard_cutoff   = True,
            hard_cutoff_failures = [],
            wss                  = wss_val,
            is_pareto            = is_pareto,
            tier                 = tier,
            radiolysis_info      = rad_info,
            raw                  = cand,
            fallback_admet_tox   = fallback_admet_tox,
            warnings             = result_warnings,
        ))

    return results
