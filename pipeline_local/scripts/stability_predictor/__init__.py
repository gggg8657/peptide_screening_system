"""
stability_predictor/__init__.py
=================================
SSTR2 펩타이드 바인더 후보의 안정성 통합 평가 패키지 (U1 — Plugin 패턴).

## 패키지 구조
    core.py             — BiophysicalProps, ProteasePredict, StabilityCore, StabilityCoreEvaluator
    silo_a_evaluator.py — Silo A (de novo) 전용 평가
    silo_b_evaluator.py — Silo B (SST-14 변이) 전용 평가
    combined_report.py  — silo 결과 병합 + 정렬

## 신규 Plugin API (Option B)
    from pipeline_local.scripts.stability_predictor import (
        StabilityCoreEvaluator,
        SiloBStabilityEvaluator,
        SiloAStabilityEvaluator,
        combine_silos,
    )

    core_eval = StabilityCoreEvaluator()
    silo_b    = SiloBStabilityEvaluator(core_eval)
    result    = silo_b.evaluate("AICKNFFWKTFTSC", seq_id="cand03")

## 하위호환 API (기존 router / 테스트 호환)
    compute_stability(sequence, seq_id, modifications) -> StabilityResult
    batch_evaluate(sequences, seq_ids, modifications) -> BatchStabilityResult
    to_markdown_table(results) -> str
    CANDIDATE_8, run_candidate8_batch(output_dir)

⚠️ HEURISTIC 명세 (pharmacology_guards.HEURISTIC_FUNCTION_DISCLAIMERS 참조):
  compute_stability / batch_evaluate 출력은 후보 ranking score.
  임상 반감기 절대값 보고, wet-lab assay 대체 용도 불가.

지원 도구 (자동 탐지):
  - Biopython ProtParam  → MW, GRAVY, instability_index, pI
  - peptides.py 0.5.0   → boman, aliphatic_index, charge(pH=7.4)
    ⚠️ peptides.py 0.5.0에는 gravy() 없음 — Biopython gravy() 사용
  - backend.admet        → compute_admet, nephrotox_risk
  - step08_stability     → hl_score_heuristic

비표준 아미노산(NCAA) 지원:
  [dT]=D-Thr, [Cha]=CHA, [2Nal]=2Nal 표기 처리 후 warning 자동 부착.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sys
import warnings as _warnings_module
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# M-04: sys.path 변이 함수 스코프로 분리
# ---------------------------------------------------------------------------

def _ensure_ag_src_on_path() -> Path:
    """AG_SRC_REPO를 sys.path에 추가. M-04: 함수 스코프 내 sys.path 변이.

    Returns:
        Path: AG_SRC_REPO 경로
    """
    ag_src = Path(os.environ.get(
        "AG_SRC_REPO",
        str(Path(__file__).resolve().parent.parent.parent.parent
            / "AgenticAI4SCIENCE_pyrosetta_track" / "repos" / "ai4sci-kaeri"),
    ))
    if ag_src.exists() and str(ag_src) not in sys.path:
        sys.path.insert(0, str(ag_src))
    return ag_src


# 패키지 로드 시 1회 실행 (backend.admet 임포트 전 경로 보장)
_ensure_ag_src_on_path()

# ---------------------------------------------------------------------------
# 선택적 의존성 (이 모듈 수준 flag — 하위호환 patch 경로 유지용)
# ---------------------------------------------------------------------------

try:
    from Bio.SeqUtils.ProtParam import ProteinAnalysis as _ProteinAnalysis
    _HAS_BIOPYTHON = True
except ImportError:
    _HAS_BIOPYTHON = False
    logger.info("[stability] Biopython 없음 — MW/GRAVY/instability/pI fallback 사용")

try:
    from peptides import Peptide as _Peptide  # type: ignore[import]
    _HAS_PEPTIDES = True
except ImportError:
    _HAS_PEPTIDES = False
    logger.info("[stability] peptides.py 없음 — Boman/aliphatic fallback 사용")

try:
    from backend.admet import compute_admet, compute_nephrotox_risk  # type: ignore[import]
    _HAS_ADMET = True
except ImportError:
    _HAS_ADMET = False
    logger.info("[stability] backend.admet 없음 — ADMET 스킵")

try:
    from pipeline_local.steps.step08_stability import predict_half_life as _hl_predictor
    _HAS_STEP08 = True
except ImportError:
    _HAS_STEP08 = False
    logger.info("[stability] step08_stability 없음 — hl_score_heuristic 스킵")

# pharmacology_guards
from pipeline_local.scripts.pharmacology_guards import (
    HEURISTIC_FUNCTION_DISCLAIMERS,
    LITERATURE_VALUES,
    SCALE_RANGES,
    assert_in_range,
)

# ---------------------------------------------------------------------------
# Ikai 1980 계수 (LITERATURE_VALUES 기반)
# ---------------------------------------------------------------------------
_IKAI = LITERATURE_VALUES["ikai_aliphatic_index"]
_IKAI_VAL = _IKAI["Val_coefficient"][0]   # 2.9
_IKAI_ILE = _IKAI["Ile_coefficient"][0]   # 3.9
_IKAI_LEU = _IKAI["Leu_coefficient"][0]   # 3.9

# ---------------------------------------------------------------------------
# NCAA 치환 테이블
# ---------------------------------------------------------------------------
_NCAA_MAP: Dict[str, Tuple[str, str]] = {
    "[dT]":  ("T", "D-Threonine → canonical T (chirality 무시)"),
    "[dA]":  ("A", "D-Alanine → A"),
    "[dF]":  ("F", "D-Phenylalanine → F"),
    "[dK]":  ("K", "D-Lysine → K"),
    "[dR]":  ("R", "D-Arginine → R"),
    "[dN]":  ("N", "D-Asparagine → N"),
    "[Cha]": ("L", "Cyclohexylalanine → L (aliphatic 유사체)"),
    "[2Nal]":("F", "2-Naphthylalanine → F (aromatic 유사체)"),
    "[Aib]": ("A", "α-Aminoisobutyric acid → A"),
    "[Orn]": ("K", "Ornithine → K (same sidechain charge)"),
    "[Nle]": ("L", "Norleucine → L"),
    "[Abu]": ("A", "α-Aminobutyric acid → A"),
    "[Hyp]": ("P", "Hydroxyproline → P"),
    "[Pip]": ("P", "Pipecolic acid → P"),
    "[Sar]": ("G", "Sarcosine → G"),
}

_VALID_AA = frozenset("ACDEFGHIKLMNPQRSTVWY")

# ---------------------------------------------------------------------------
# Protease 절단 규칙 헬퍼
# ---------------------------------------------------------------------------

def _find_protease_sites(seq: str) -> Dict[str, List[int]]:
    """정성적 protease 절단 취약 부위 예측.

    Args:
        seq: 대문자 canonical 아미노산 서열

    Returns:
        {"trypsin": [pos, ...], "chymotrypsin": [pos, ...], "nep": [pos, ...]}
        positions: 1-indexed, 해당 잔기 이후 절단 위치

    ⚠️ 정성적 vulnerability ranking — kcat/Km 정량 아님.
    """
    sites: Dict[str, List[int]] = {"trypsin": [], "chymotrypsin": [], "nep": []}
    n = len(seq)
    for i, aa in enumerate(seq):
        nxt = seq[i + 1] if i + 1 < n else ""
        if aa in ("K", "R") and nxt != "P":
            sites["trypsin"].append(i + 1)
        if aa in ("F", "Y", "W") and nxt != "P":
            sites["chymotrypsin"].append(i + 1)
        if aa in ("F", "L", "V", "A", "I") and i > 0:
            sites["nep"].append(i + 1)
    return sites


# ---------------------------------------------------------------------------
# Biopython fallback
# ---------------------------------------------------------------------------

_RESIDUE_WEIGHTS: Dict[str, float] = {
    "A": 71.03711,  "R": 156.10111, "N": 114.04293, "D": 115.02694,
    "C": 103.00919, "E": 129.04259, "Q": 128.05858, "G":  57.02146,
    "H": 137.05891, "I": 113.08406, "L": 113.08406, "K": 128.09496,
    "M": 131.04049, "F": 147.06841, "P":  97.05276, "S":  87.03203,
    "T": 101.04768, "W": 186.07931, "Y": 163.06333, "V":  99.06841,
}
_WATER_MW = 18.01056

_KD_HYDROPATHY: Dict[str, float] = {
    "A":  1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C":  2.5,
    "E": -3.5, "Q": -3.5, "G": -0.4, "H": -3.2, "I":  4.5,
    "L":  3.8, "K": -3.9, "M":  1.9, "F":  2.8, "P": -1.6,
    "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V":  4.2,
}


def _fallback_biophysical(seq: str) -> Dict[str, float]:
    """Biopython 없을 때 간소화 MW + GRAVY 계산."""
    n = len(seq)
    mw = sum(_RESIDUE_WEIGHTS.get(aa, 0.0) for aa in seq) + _WATER_MW
    gravy = sum(_KD_HYDROPATHY.get(aa, 0.0) for aa in seq) / n if n else 0.0
    return {
        "mw": round(mw, 2),
        "gravy": round(gravy, 4),
        "instability_index": float("nan"),
        "pi": float("nan"),
    }


def _compute_biopython_props(seq: str) -> Dict[str, float]:
    """Biopython ProteinAnalysis를 이용한 물리화학 속성 계산.

    ⚠️ peptides.py 0.5.0에는 gravy() 없음 — Biopython gravy() 전용.
    """
    if not _HAS_BIOPYTHON:
        return _fallback_biophysical(seq)
    try:
        pa = _ProteinAnalysis(seq)
        return {
            "mw": round(pa.molecular_weight(), 2),
            "gravy": round(pa.gravy(), 4),
            "instability_index": round(pa.instability_index(), 2),
            "pi": round(pa.isoelectric_point(), 2),
        }
    except Exception as e:
        logger.warning("[stability] Biopython 계산 실패 %s: %s — fallback", seq[:10], e)
        return _fallback_biophysical(seq)


def _compute_aliphatic_index(seq: str) -> float:
    """Ikai 1980 Aliphatic Index.

    AI = (X_Ala + 2.9·X_Val + 3.9·(X_Ile + X_Leu)) × 100
    계수: pharmacology_guards.LITERATURE_VALUES["ikai_aliphatic_index"] 기반.
    """
    n = len(seq)
    if n == 0:
        return 0.0
    xa = seq.count("A") / n
    xv = seq.count("V") / n
    xi = seq.count("I") / n
    xl = seq.count("L") / n
    return round((xa + _IKAI_VAL * xv + _IKAI_ILE * xi + _IKAI_LEU * xl) * 100.0, 2)


def _compute_boman(seq: str) -> Optional[float]:
    """Boman index (peptides.py). 없으면 None."""
    if _HAS_PEPTIDES:
        try:
            return round(_Peptide(seq).boman(), 4)
        except Exception as e:
            logger.debug("[stability] peptides Boman 실패: %s", e)
    return None


def _compute_charge(seq: str, ph: float = 7.4) -> Optional[float]:
    """Net charge @ pH (peptides.py). 없으면 None."""
    if _HAS_PEPTIDES:
        try:
            return round(_Peptide(seq).charge(pH=ph), 4)
        except Exception as e:
            logger.debug("[stability] peptides charge 실패: %s", e)
    return None


# ---------------------------------------------------------------------------
# 하위호환 데이터클래스 (router + test 호환)
# ---------------------------------------------------------------------------

@dataclass
class StabilityResult:
    """단일 후보의 통합 안정성 평가 결과 (하위호환 플랫 구조).

    ⚠️ hl_score_heuristic: ranking score. 임상 반감기 절대값 아님.
    pharmacology_guards.HEURISTIC_FUNCTION_DISCLAIMERS 참조.
    """
    seq_id: str
    sequence: str
    canonical_sequence: str
    mw: float
    gravy: float
    instability_index: float
    pi: float
    boman: Optional[float]
    charge_ph74: Optional[float]
    aliphatic_index: float
    protease_cleavage_sites: Dict[str, List[int]]
    admet_score: Dict[str, Any]
    nephrotox_risk: str
    hl_score_heuristic: float
    hl_warnings: List[str]
    ncaa_warnings: List[str] = field(default_factory=list)
    # Default-valued fields (backwards-compat: 기존 positional 호출자가 깨지지 않도록)
    is_unstable: bool = False                       # II > 40 → True (Guruprasad 1990, __post_init__에서 자동 설정)
    stability_class: str = "stable"                 # "unstable" if II > 40 else "stable"
    surrogate_panel: Dict[str, Any] = field(default_factory=dict)
    agreement_profile: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # instability_index 기반 자동 도출 (생성자가 명시값 주지 않은 경우 갱신)
        if self.instability_index > 40.0:
            self.is_unstable = True
            self.stability_class = "unstable"
        else:
            self.is_unstable = False
            self.stability_class = "stable"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "StabilityResult":
        return cls(**d)


@dataclass
class BatchStabilityResult:
    """Batch 안정성 평가 결과."""
    results: List[StabilityResult]
    n_total: int
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "results": [r.to_dict() for r in self.results],
            "n_total": self.n_total,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "BatchStabilityResult":
        return cls(
            results=[StabilityResult.from_dict(r) for r in d["results"]],
            n_total=d["n_total"],
            summary=d["summary"],
        )


# ---------------------------------------------------------------------------
# NCAA 처리 (하위호환 public API)
# ---------------------------------------------------------------------------

def strip_ncaa(sequence: str) -> Tuple[str, List[str]]:
    """비표준 아미노산 표기를 canonical 서열로 변환.

    M-01: NCAA 치환 발생 시 returned warnings 리스트와 함께
    Python warnings.warn() 도 병행 발행. 라이브러리 소비자가
    -W error::UserWarning 으로 치환을 오류로 격상시킬 수 있음.

    Args:
        sequence: 원본 서열 (예: "AICKNFFWKTFT[dT]C")

    Returns:
        (canonical_seq, warnings)
    """
    import re
    seq = sequence.strip().upper()
    warn_list: List[str] = []
    for ncaa, (replacement, desc) in _NCAA_MAP.items():
        while ncaa.upper() in seq:
            seq = seq.replace(ncaa.upper(), replacement, 1)
            msg = f"{ncaa} → {replacement}: {desc}"
            warn_list.append(msg)
            # M-01: Python 경고 채널에도 발행
            _warnings_module.warn(
                f"[stability_predictor] NCAA 치환: {msg}",
                UserWarning,
                stacklevel=2,
            )
    unknown = re.findall(r"\[[^\]]+\]", seq)
    for u in unknown:
        seq = seq.replace(u, "G")
        msg = f"{u} → G (알 수 없는 NCAA, Gly으로 대체)"
        warn_list.append(msg)
        # M-01: 알 수 없는 NCAA — 더 높은 stacklevel로 경고
        _warnings_module.warn(
            f"[stability_predictor] 알 수 없는 NCAA 치환: {msg}",
            UserWarning,
            stacklevel=2,
        )
    return seq, warn_list


def _build_surrogate_panel(
    *,
    sequence: str,
    canonical_sequence: str,
    modifications: List[str],
    mw: float,
    gravy: float,
    instability_index: float,
    pi: float,
    boman: Optional[float],
    charge_ph74: Optional[float],
    aliphatic_index: float,
    protease_sites: Dict[str, List[int]],
    admet_score: Dict[str, Any],
    nephrotox_risk: str,
    hl_score: float,
    hl_warnings: List[str],
    ncaa_warnings: List[str],
) -> Dict[str, Any]:
    """독립 surrogate 출력을 JSON sidecar 구조로 정리."""
    site_counts = {name: len(pos) for name, pos in protease_sites.items()}
    total_sites = sum(site_counts.values())
    return {
        "tool_availability": {
            "biopython": _HAS_BIOPYTHON,
            "peptides_py": _HAS_PEPTIDES,
            "backend_admet": _HAS_ADMET,
            "step08_half_life": _HAS_STEP08,
        },
        "input_normalization": {
            "original_sequence": sequence,
            "canonical_sequence": canonical_sequence,
            "modifications": modifications,
            "ncaa_warnings": ncaa_warnings,
        },
        "biophysical": {
            "mw": mw,
            "gravy": gravy,
            "instability_index": instability_index,
            "pi": pi,
            "boman": boman,
            "charge_ph74": charge_ph74,
            "aliphatic_index": aliphatic_index,
        },
        "protease": {
            "cleavage_sites": protease_sites,
            "site_counts": site_counts,
            "total_sites": total_sites,
        },
        "admet": {
            "score": admet_score,
            "nephrotox_risk": nephrotox_risk,
        },
        "half_life": {
            "internal_step08": {
                "available": _HAS_STEP08,
                "score": hl_score,
                "score_kind": "heuristic_ranking",
                "warnings": hl_warnings,
            }
        },
    }


def _build_agreement_profile(
    *,
    instability_index: float,
    protease_sites: Dict[str, List[int]],
    nephrotox_risk: str,
    hl_score: float,
) -> Dict[str, Any]:
    """현재 surrogate들 간의 합의/불일치 상태를 경량 규칙으로 계산."""
    total_sites = sum(len(v) for v in protease_sites.values())
    if math.isnan(instability_index):
        biophysical_class = "unknown"
    elif instability_index > 40.0:
        biophysical_class = "unstable"
    else:
        biophysical_class = "stable"

    if total_sites <= 2:
        protease_burden = "low"
    elif total_sites <= 5:
        protease_burden = "moderate"
    else:
        protease_burden = "high"

    nephrotox_norm = str(nephrotox_risk).strip().lower()
    if nephrotox_norm in {"low", "medium", "high"}:
        admet_signal = nephrotox_norm
    else:
        admet_signal = "unknown"

    half_life_signal = "supportive" if hl_score > 0 else "missing"
    flags: List[str] = []
    if biophysical_class == "stable" and protease_burden == "low" and hl_score > 0:
        consensus_bucket = "stable_supportive"
    elif biophysical_class == "unstable" and protease_burden == "high":
        consensus_bucket = "unstable_risk"
    else:
        consensus_bucket = "mixed"

    if biophysical_class == "stable" and protease_burden == "high":
        flags.append("biophysical_vs_protease_disagreement")
    if biophysical_class == "unstable" and hl_score > 0:
        flags.append("instability_vs_half_life_disagreement")
    if admet_signal == "high":
        flags.append("nephrotox_high_risk")
    if hl_score <= 0:
        flags.append("half_life_signal_missing")

    return {
        "biophysical_class": biophysical_class,
        "protease_burden": protease_burden,
        "admet_signal": admet_signal,
        "half_life_signal": half_life_signal,
        "consensus_bucket": consensus_bucket,
        "flags": flags,
    }


# ---------------------------------------------------------------------------
# 핵심 계산 함수 (하위호환 public API)
# ---------------------------------------------------------------------------

def compute_stability(
    sequence: str,
    seq_id: str = "",
    modifications: Optional[List[str]] = None,
) -> StabilityResult:
    """단일 후보의 통합 안정성 평가 (하위호환 API).

    ⚠️ HEURISTIC — 임상 반감기 절대값 아님. 후보 ranking용.
    pharmacology_guards.HEURISTIC_FUNCTION_DISCLAIMERS
    ["pipeline_local.scripts.stability_predictor.compute_stability"] 참조.

    Args:
        sequence: 아미노산 서열 (NCAA 포함 가능)
        seq_id: 후보 식별자
        modifications: modification 목록

    Returns:
        StabilityResult (플랫 구조, 하위호환)
    """
    if not sequence or not str(sequence).strip():
        raise ValueError(
            f"빈 서열은 허용되지 않습니다: {sequence!r}. "
            "유효한 아미노산 1-letter 코드 문자열을 전달하세요."
        )

    if not seq_id:
        seq_id = sequence[:6]
    mods = modifications or []

    # NCAA 처리
    canonical, ncaa_warnings = strip_ncaa(sequence)
    canonical_clean = "".join(aa for aa in canonical if aa in _VALID_AA)
    if len(canonical_clean) != len(canonical):
        ncaa_warnings.append(f"{len(canonical) - len(canonical_clean)}개 알 수 없는 잔기 제거됨")
    canonical = canonical_clean

    # Biopython 속성
    bio_props = _compute_biopython_props(canonical)
    mw = bio_props["mw"]
    gravy = bio_props["gravy"]
    instability_index = bio_props["instability_index"]
    pi = bio_props["pi"]

    # 범위 가드
    try:
        assert_in_range(mw, "molecular_weight_peptide_da", seq_id)
    except (ValueError, AssertionError, KeyError) as e:
        logger.warning("[stability] MW 범위 경고 %s: %s", seq_id, e)
    try:
        if not math.isnan(gravy):
            assert_in_range(gravy, "kyte_doolittle_mean", seq_id)
    except (ValueError, AssertionError, KeyError) as e:
        logger.warning("[stability] GRAVY 범위 경고 %s: %s", seq_id, e)

    aliphatic_index = _compute_aliphatic_index(canonical)
    boman = _compute_boman(canonical)
    charge_ph74 = _compute_charge(canonical, ph=7.4)
    protease_sites = _find_protease_sites(canonical)

    # ADMET
    admet_score: Dict[str, Any] = {}
    nephrotox_risk = "Unknown"
    if _HAS_ADMET:
        try:
            admet_score = compute_admet(canonical)
            nephrotox_dict = compute_nephrotox_risk(canonical)
            nephrotox_risk = nephrotox_dict.get("risk_level", "Unknown")
        except Exception as e:
            logger.warning("[stability] ADMET 계산 실패 %s: %s", seq_id, e)

    # Heuristic HL score
    hl_score: float = 0.0
    if _HAS_STEP08:
        try:
            hl_score = _hl_predictor(canonical, mods)
        except Exception as e:
            logger.warning("[stability] hl_score 계산 실패 %s: %s", seq_id, e)

    # HEURISTIC disclaimer
    hl_warnings: List[str] = []
    disc = HEURISTIC_FUNCTION_DISCLAIMERS.get(
        "pipeline_local.scripts.stability_predictor.compute_stability", {}
    )
    if disc:
        hl_warnings.append(
            f"[HEURISTIC] {disc.get('actual_meaning', '')}. "
            f"한계: {disc.get('limitations', '')}. "
            f"유효 용도: {disc.get('valid_use', '')}"
        )

    surrogate_panel = _build_surrogate_panel(
        sequence=sequence,
        canonical_sequence=canonical,
        modifications=mods,
        mw=mw,
        gravy=gravy,
        instability_index=instability_index,
        pi=pi,
        boman=boman,
        charge_ph74=charge_ph74,
        aliphatic_index=aliphatic_index,
        protease_sites=protease_sites,
        admet_score=admet_score,
        nephrotox_risk=nephrotox_risk,
        hl_score=hl_score,
        hl_warnings=hl_warnings,
        ncaa_warnings=ncaa_warnings,
    )
    agreement_profile = _build_agreement_profile(
        instability_index=instability_index,
        protease_sites=protease_sites,
        nephrotox_risk=nephrotox_risk,
        hl_score=hl_score,
    )

    return StabilityResult(
        seq_id=seq_id,
        sequence=sequence,
        canonical_sequence=canonical,
        mw=mw,
        gravy=gravy,
        instability_index=instability_index,
        pi=pi,
        boman=boman,
        charge_ph74=charge_ph74,
        aliphatic_index=aliphatic_index,
        protease_cleavage_sites=protease_sites,
        admet_score=admet_score,
        nephrotox_risk=nephrotox_risk,
        hl_score_heuristic=hl_score,
        hl_warnings=hl_warnings,
        ncaa_warnings=ncaa_warnings,
        surrogate_panel=surrogate_panel,
        agreement_profile=agreement_profile,
    )


def batch_evaluate(
    sequences: List[str],
    seq_ids: Optional[List[str]] = None,
    modifications: Optional[List[List[str]]] = None,
) -> BatchStabilityResult:
    """후보 서열 list의 일괄 안정성 평가 (하위호환 API).

    ⚠️ HEURISTIC — pharmacology_guards.HEURISTIC_FUNCTION_DISCLAIMERS 참조.
    """
    ids = seq_ids or [f"seq_{i}" for i in range(len(sequences))]
    mods_list = modifications or [[] for _ in sequences]

    results: List[StabilityResult] = []
    for i, seq in enumerate(sequences):
        sid = ids[i] if i < len(ids) else f"seq_{i}"
        m = mods_list[i] if i < len(mods_list) else []
        r = compute_stability(seq, seq_id=sid, modifications=m)
        results.append(r)
        logger.info(
            "[stability] %s: MW=%.0f GRAVY=%.2f instab=%.1f HL=%.1f",
            sid, r.mw, r.gravy,
            r.instability_index if not math.isnan(r.instability_index) else -1,
            r.hl_score_heuristic,
        )

    valid_instab = [r.instability_index for r in results if not math.isnan(r.instability_index)]
    valid_hl = [r.hl_score_heuristic for r in results if r.hl_score_heuristic > 0]
    consensus_counts: Dict[str, int] = {}
    for r in results:
        bucket = r.agreement_profile.get("consensus_bucket", "unknown")
        consensus_counts[bucket] = consensus_counts.get(bucket, 0) + 1
    summary: Dict[str, Any] = {
        "n_total": len(results),
        "n_stable_biopython": sum(
            1 for r in results
            if not math.isnan(r.instability_index) and r.instability_index < 40.0
        ),
        "mean_mw": round(sum(r.mw for r in results) / len(results), 2) if results else 0.0,
        "mean_gravy": round(sum(r.gravy for r in results) / len(results), 4) if results else 0.0,
        "mean_instability": round(sum(valid_instab) / len(valid_instab), 2) if valid_instab else None,
        "mean_hl_score": round(sum(valid_hl) / len(valid_hl), 2) if valid_hl else None,
        "heuristic_disclaimer": "hl_score_heuristic은 임상 반감기 절대값이 아닌 ranking score임",
        "surrogate_panel_summary": {
            "consensus_bucket_counts": consensus_counts,
            "tools_present": {
                "biopython": _HAS_BIOPYTHON,
                "peptides_py": _HAS_PEPTIDES,
                "backend_admet": _HAS_ADMET,
                "step08_half_life": _HAS_STEP08,
            },
        },
    }

    return BatchStabilityResult(results=results, n_total=len(results), summary=summary)


# ---------------------------------------------------------------------------
# Markdown 표
# ---------------------------------------------------------------------------

def to_markdown_table(results: List[StabilityResult]) -> str:
    """StabilityResult 목록을 Markdown 표로 변환."""
    headers = [
        "seq_id", "sequence", "MW (Da)", "GRAVY",
        "Instab.", "pI", "Boman", "Aliphatic",
        "HL score*", "Nephrotox", "Tryp sites", "Chymo sites",
    ]
    rows = []
    for r in results:
        instab_str = f"{r.instability_index:.1f}" if not math.isnan(r.instability_index) else "N/A"
        pi_str = f"{r.pi:.2f}" if not math.isnan(r.pi) else "N/A"
        boman_str = f"{r.boman:.2f}" if r.boman is not None else "N/A"
        rows.append([
            r.seq_id,
            r.sequence[:14] + ("…" if len(r.sequence) > 14 else ""),
            f"{r.mw:.0f}",
            f"{r.gravy:.2f}",
            instab_str,
            pi_str,
            boman_str,
            f"{r.aliphatic_index:.1f}",
            f"{r.hl_score_heuristic:.1f}",
            r.nephrotox_risk,
            str(r.protease_cleavage_sites.get("trypsin", [])),
            str(r.protease_cleavage_sites.get("chymotrypsin", [])),
        ])
    widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(len(headers))]
    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    header_line = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    data_lines = [
        "| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)) + " |"
        for row in rows
    ]
    lines = [header_line, sep] + data_lines
    lines.append("")
    lines.append("\\* hl_score_heuristic = ranking score (NOT clinical half-life). HEURISTIC 신뢰등급.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 본 프로젝트 8 후보 (Silo B 출신 — SiloBStabilityEvaluator 사용)
# ---------------------------------------------------------------------------

CANDIDATE_8: List[Dict[str, Any]] = [
    {"seq_id": "SST14_ref",  "sequence": "AGCKNFFWKTFTSC",       "mods": ["cyclization"]},
    {"seq_id": "cand03",     "sequence": "AICKNFFWKTFTSC",        "mods": ["cyclization"]},
    {"seq_id": "T3_1",       "sequence": "ILCKKFFWKTFTSC",        "mods": ["cyclization"]},
    {"seq_id": "T3_2",       "sequence": "IGCWWFFWKTFTSC",        "mods": ["cyclization"]},
    {"seq_id": "T3_3",       "sequence": "AGCKNDFWKTLTSC",        "mods": ["cyclization"]},
    {"seq_id": "T3_4",       "sequence": "QTCKNFFWKTFTSC",        "mods": ["cyclization"]},
    {"seq_id": "T3_5",       "sequence": "AGCKWEFWKTLTSC",        "mods": ["cyclization"]},
    {"seq_id": "var12_dThr", "sequence": "AICKNFFWKTFT[dT]C",    "mods": ["cyclization", "d_amino_acid"]},
]


def run_candidate8_batch(output_dir: Path) -> BatchStabilityResult:
    """8 후보 배치 평가 및 결과 저장 (하위호환 API).

    Args:
        output_dir: 저장 디렉토리

    Returns:
        BatchStabilityResult (플랫 구조)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    seqs = [c["sequence"] for c in CANDIDATE_8]
    ids = [c["seq_id"] for c in CANDIDATE_8]
    mods = [c["mods"] for c in CANDIDATE_8]

    result = batch_evaluate(seqs, ids, mods)

    out_json = output_dir / "batch_8_candidates.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
    logger.info("[stability] 8 후보 결과 저장: %s", out_json)

    out_md = output_dir / "batch_8_candidates.md"
    out_md.write_text(
        "# Stability Predictor — 8 후보 평가 결과\n\n"
        "> ⚠️ hl_score_heuristic은 ranking score (NOT clinical half-life)\n\n"
        + to_markdown_table(result.results) + "\n",
        encoding="utf-8",
    )
    logger.info("[stability] Markdown 저장: %s", out_md)

    return result


def run_candidate8_batch_silo_b(output_dir: Path):
    """8 후보 SiloBStabilityEvaluator 기반 평가 및 결과 저장.

    Plugin 패턴 신규 API — SiloBStabilityResult 목록 반환.
    기존 run_candidate8_batch (플랫) 와 병행 제공.

    Returns:
        List[SiloBStabilityResult]
    """
    from pipeline_local.scripts.stability_predictor.core import StabilityCoreEvaluator
    from pipeline_local.scripts.stability_predictor.silo_b_evaluator import SiloBStabilityEvaluator

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    core_eval = StabilityCoreEvaluator()
    evaluator = SiloBStabilityEvaluator(core_eval)

    results = []
    for cand in CANDIDATE_8:
        r = evaluator.evaluate(
            cand["sequence"],
            seq_id=cand["seq_id"],
            modifications=cand.get("mods", []),
        )
        results.append(r)
        logger.info(
            "[silo_b] %s: MW=%.0f mut=%d FWKT=%s",
            r.seq_id, r.core.biophysical.mw,
            r.extras.mutation_count, r.extras.fwkt_conservation,
        )

    out_json = output_dir / "batch_8_candidates_silo_b.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in results], f, indent=2, ensure_ascii=False)
    logger.info("[stability] Silo B 8 후보 결과 저장: %s", out_json)

    return results


# ---------------------------------------------------------------------------
# Plugin 패턴 신규 클래스 — 통합 export
# ---------------------------------------------------------------------------

from pipeline_local.scripts.stability_predictor.core import (  # noqa: E402
    BiophysicalProps,
    ProteasePredict,
    StabilityCore,
    StabilityCoreEvaluator,
)
from pipeline_local.scripts.stability_predictor.silo_a_evaluator import (  # noqa: E402
    SiloAStabilityEvaluator,
    SiloAStabilityExtras,
    SiloAStabilityResult,
)
from pipeline_local.scripts.stability_predictor.silo_b_evaluator import (  # noqa: E402
    SiloBStabilityEvaluator,
    SiloBStabilityExtras,
    SiloBStabilityResult,
    SST14_SEQUENCE,
    PHARMACOPHORE_POSITIONS,
    PHARMACOPHORE_RESIDUES,
)
from pipeline_local.scripts.stability_predictor.combined_report import (  # noqa: E402
    combine_silos,
)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="SSTR2 후보 펩타이드 안정성 통합 평가 (HEURISTIC ranking only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "예시:\n"
            "  python -m pipeline_local.scripts.stability_predictor \\\n"
            "    --sequences AGCKNFFWKTFTSC AICKNFFWKTFTSC \\\n"
            "    --output runs_local/stability/results.json\n\n"
            "  python -m pipeline_local.scripts.stability_predictor --batch8\n\n"
            "  python -m pipeline_local.scripts.stability_predictor --batch8 --silo-b"
        ),
    )
    parser.add_argument("--sequences", nargs="+", help="평가할 아미노산 서열 목록")
    parser.add_argument("--seq-ids", nargs="+", help="각 서열의 ID (선택)")
    parser.add_argument("--modifications", nargs="+", help="적용된 modification")
    parser.add_argument("--input-json", type=Path, help="입력 JSON 파일")
    parser.add_argument("--output", type=Path, help="결과 JSON 파일 경로")
    parser.add_argument("--output-json", type=Path, help="결과 JSON 파일 경로 (--output 별칭)")
    parser.add_argument("--output-dir", type=Path, default=Path("runs_local/stability"),
                        help="결과 저장 디렉토리 (기본: runs_local/stability)")
    parser.add_argument("--batch8", action="store_true", help="8 후보 자동 평가")
    parser.add_argument("--silo-b", action="store_true",
                        help="Plugin 패턴 SiloBStabilityEvaluator 사용 (--batch8과 함께)")
    parser.add_argument("--markdown", action="store_true", help="Markdown 표 함께 출력")
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = _build_parser()
    args = parser.parse_args()

    output_path = args.output or args.output_json

    if args.batch8:
        if args.silo_b:
            results = run_candidate8_batch_silo_b(args.output_dir)
            print(f"\n[완료] {len(results)}개 후보 (Silo B) 평가 완료")
            print(f"  결과: {args.output_dir}/batch_8_candidates_silo_b.json")
        else:
            result = run_candidate8_batch(args.output_dir)
            print(f"\n[완료] {result.n_total}개 후보 평가 완료")
            print(f"  결과: {args.output_dir}/batch_8_candidates.json")
            if args.markdown:
                print("\n" + to_markdown_table(result.results))
        return

    sequences: List[str] = []
    seq_ids: Optional[List[str]] = None

    if args.input_json:
        with open(args.input_json, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    sequences.append(item)
                elif isinstance(item, dict):
                    sequences.append(item.get("sequence", item.get("seq", "")))
                    if seq_ids is None:
                        seq_ids = []
                    seq_ids.append(item.get("seq_id", item.get("id", f"seq_{len(sequences)-1}")))
        elif isinstance(data, dict):
            sequences = data.get("sequences", [])
            seq_ids = data.get("seq_ids")
    elif args.sequences:
        sequences = args.sequences
        seq_ids = args.seq_ids
    else:
        parser.print_help()
        return

    if not sequences:
        print("ERROR: 서열이 없습니다.")
        return

    mods = [args.modifications or [] for _ in sequences]
    result = batch_evaluate(sequences, seq_ids, mods)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"[완료] {result.n_total}개 결과 저장: {output_path}")
    else:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))

    if args.markdown:
        print("\n" + to_markdown_table(result.results))


if __name__ == "__main__":
    main()
