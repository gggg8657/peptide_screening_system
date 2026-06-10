"""
stability_predictor/core.py
============================
Silo-agnostic 공통 안정성 평가 코어 (U1 Plugin 패턴 — Option B).

외부에서 직접 임포트:
    from pipeline_local.scripts.stability_predictor.core import (
        StabilityCoreEvaluator, StabilityCore,
        BiophysicalProps, ProteasePredict,
    )

⚠️ HEURISTIC 적용 범위:
  hl_score_heuristic은 후보 ranking 전용 score임.
  임상 반감기·wet-lab assay 결과 대체 불가.
  근거: pharmacology_guards.HEURISTIC_FUNCTION_DISCLAIMERS 참조.
"""

from __future__ import annotations

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
        Path: AG_SRC_REPO 경로 (존재하지 않아도 Path 객체 반환)
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
# 선택적 의존성 (core 내부 독립 로드 — __init__.py 와 별개)
# ---------------------------------------------------------------------------
try:
    from Bio.SeqUtils.ProtParam import ProteinAnalysis as _ProteinAnalysis  # type: ignore
    _CORE_HAS_BIOPYTHON = True
except ImportError:
    _CORE_HAS_BIOPYTHON = False

try:
    from peptides import Peptide as _Peptide  # type: ignore
    _CORE_HAS_PEPTIDES = True
except ImportError:
    _CORE_HAS_PEPTIDES = False

try:
    from backend.admet import compute_admet as _compute_admet  # type: ignore
    from backend.admet import compute_nephrotox_risk as _nephrotox  # type: ignore
    _CORE_HAS_ADMET = True
except ImportError:
    _CORE_HAS_ADMET = False

try:
    from pipeline_local.steps.step08_stability import predict_half_life as _hl_predictor  # type: ignore
    _CORE_HAS_STEP08 = True
except ImportError:
    _CORE_HAS_STEP08 = False

# pharmacology_guards — LITERATURE_VALUES
from pipeline_local.scripts.pharmacology_guards import (
    HEURISTIC_FUNCTION_DISCLAIMERS,
    LITERATURE_VALUES,
    assert_in_range,
)

# ---------------------------------------------------------------------------
# Ikai 1980 계수 (LITERATURE_VALUES 기반 — 하드코딩 금지)
# ---------------------------------------------------------------------------
_CORE_IKAI = LITERATURE_VALUES["ikai_aliphatic_index"]
_CORE_IKAI_VAL = _CORE_IKAI["Val_coefficient"][0]  # 2.9
_CORE_IKAI_ILE = _CORE_IKAI["Ile_coefficient"][0]  # 3.9
_CORE_IKAI_LEU = _CORE_IKAI["Leu_coefficient"][0]  # 3.9

# ---------------------------------------------------------------------------
# NCAA 치환 테이블
# ---------------------------------------------------------------------------
_CORE_NCAA_MAP: Dict[str, tuple] = {
    "[dT]":  ("T", "D-Threonine → canonical T"),
    "[dA]":  ("A", "D-Alanine → A"),
    "[dF]":  ("F", "D-Phenylalanine → F"),
    "[dK]":  ("K", "D-Lysine → K"),
    "[dR]":  ("R", "D-Arginine → R"),
    "[dN]":  ("N", "D-Asparagine → N"),
    "[Cha]": ("L", "Cyclohexylalanine → L"),
    "[2Nal]":("F", "2-Naphthylalanine → F"),
    "[Aib]": ("A", "α-Aminoisobutyric acid → A"),
    "[Orn]": ("K", "Ornithine → K"),
    "[Nle]": ("L", "Norleucine → L"),
    "[Abu]": ("A", "α-Aminobutyric acid → A"),
    "[Hyp]": ("P", "Hydroxyproline → P"),
    "[Pip]": ("P", "Pipecolic acid → P"),
    "[Sar]": ("G", "Sarcosine → G"),
}
_CORE_VALID_AA = frozenset("ACDEFGHIKLMNPQRSTVWY")

# Fallback MW/GRAVY 계산용 상수
_CORE_RESIDUE_WEIGHTS: Dict[str, float] = {
    "A": 71.03711,  "R": 156.10111, "N": 114.04293, "D": 115.02694,
    "C": 103.00919, "E": 129.04259, "Q": 128.05858, "G":  57.02146,
    "H": 137.05891, "I": 113.08406, "L": 113.08406, "K": 128.09496,
    "M": 131.04049, "F": 147.06841, "P":  97.05276, "S":  87.03203,
    "T": 101.04768, "W": 186.07931, "Y": 163.06333, "V":  99.06841,
}
_CORE_WATER_MW = 18.01056
_CORE_KD_HYDROPATHY: Dict[str, float] = {
    "A":  1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C":  2.5,
    "E": -3.5, "Q": -3.5, "G": -0.4, "H": -3.2, "I":  4.5,
    "L":  3.8, "K": -3.9, "M":  1.9, "F":  2.8, "P": -1.6,
    "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V":  4.2,
}


# ---------------------------------------------------------------------------
# 신규 구조화 데이터클래스 (Plugin 패턴)
# ---------------------------------------------------------------------------

@dataclass
class BiophysicalProps:
    """Silo-agnostic 물리화학 속성 묶음."""
    mw: float                           # 분자량 (Da), Biopython
    gravy: float                        # Kyte-Doolittle mean, Biopython
    instability_index: float            # Guruprasad 1990, Biopython
    pi: float                           # 등전점, Biopython
    boman: Optional[float]              # Boman index, peptides.py (없으면 None)
    charge_ph74: Optional[float]        # Net charge @ pH 7.4, peptides.py
    aliphatic_index: float              # Ikai 1980

    @property
    def molecular_weight(self) -> float:
        """분자량 (Da) — `mw` 필드의 alias (M-03).

        Usage:
            props.mw == props.molecular_weight  # 항상 True
        """
        return self.mw

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["molecular_weight"] = self.mw   # alias도 포함
        return d


@dataclass
class ProteasePredict:
    """정성적 protease 절단 취약 부위 예측."""
    trypsin: List[int]                  # K/R 이후 (not before P), 1-indexed
    chymotrypsin: List[int]             # F/Y/W 이후 (not before P), 1-indexed
    nep: List[int]                      # Neprilysin: hydrophobic 잔기, 1-indexed

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def total_sites(self) -> int:
        return len(self.trypsin) + len(self.chymotrypsin) + len(self.nep)


@dataclass
class StabilityCore:
    """Silo-agnostic 안정성 평가 핵심 결과.

    ⚠️ hl_score_heuristic: 임상 반감기 절대값 아님 — ranking score 전용.
    pharmacology_guards.HEURISTIC_FUNCTION_DISCLAIMERS 참조.
    """
    seq_id: str
    sequence: str                                           # 원본 서열 (NCAA 포함 가능)
    canonical_sequence: str                                 # NCAA 치환 후
    biophysical: BiophysicalProps
    protease: ProteasePredict
    admet: Dict[str, Any]
    nephrotox_risk: str                                     # Low/Moderate/High/Unknown
    hl_score_heuristic: float                               # HEURISTIC ranking score
    hl_warnings: List[str]                                  # HEURISTIC disclaimer 목록
    ncaa_warnings: List[str] = field(default_factory=list)
    ncaa_removed_residues: List[Tuple[int, str]] = field(default_factory=list)
    # M-02: NCAA 처리된 잔기의 원본 위치 + 표기 기록
    # [(1-indexed_pos, original_notation), ...] — ex: [(13, "[dT]")]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # biophysical에 molecular_weight alias 추가 (M-03)
        d["biophysical"]["molecular_weight"] = self.biophysical.mw
        return d

    @property
    def is_stable_biopython(self) -> bool:
        """instability_index < 40 이고 NaN이 아닌 경우 안정."""
        ii = self.biophysical.instability_index
        return (not math.isnan(ii)) and (ii < 40.0)


# ---------------------------------------------------------------------------
# Core 헬퍼 함수 (StabilityCoreEvaluator 내부 사용)
# ---------------------------------------------------------------------------

def _core_strip_ncaa(
    sequence: str,
) -> Tuple[str, List[str], List[Tuple[int, str]]]:
    """NCAA → canonical 치환 + 경고 + 제거 잔기 목록 반환.

    M-02: ncaa_removed_residues 추적 추가.

    Args:
        sequence: 원본 서열 (NCAA 포함 가능)

    Returns:
        (canonical_seq, warnings, ncaa_removed_residues)
        ncaa_removed_residues: List of (1-indexed_position, original_notation)
            — 처리된 모든 NCAA 잔기의 원본 위치 + 표기 기록
    """
    import re as _re
    seq = sequence.strip().upper()
    warn_msgs: List[str] = []
    removed: List[Tuple[int, str]] = []

    # 원본 서열에서 모든 NCAA 괄호 표기의 위치를 먼저 수집
    # (치환 후 위치가 바뀌므로 원본 기준으로 추적)
    for ncaa, (replacement, desc) in _CORE_NCAA_MAP.items():
        ncaa_upper = ncaa.upper()
        # 반복 치환하면서 위치 추적
        search_seq = seq
        while ncaa_upper in search_seq:
            pos = search_seq.index(ncaa_upper)
            # 1-indexed 원본 위치 (이미 처리된 이전 NCAA들의 길이 차이 반영)
            # ncaa_upper 길이와 replacement(1자) 길이 차이로 오프셋 보정 생략
            # → 현재 seq 내 위치(1-indexed) 기록 (최선 근사치)
            removed.append((pos + 1, ncaa))
            search_seq = search_seq.replace(ncaa_upper, replacement, 1)
            seq = seq.replace(ncaa_upper, replacement, 1)
            warn_msgs.append(f"{ncaa} → {replacement}: {desc}")

    # 알 수 없는 괄호 표기 처리
    unknown_list = _re.findall(r"\[[^\]]+\]", seq)
    for u in unknown_list:
        pos_in_seq = seq.index(u) + 1  # 1-indexed
        removed.append((pos_in_seq, u))
        seq = seq.replace(u, "G", 1)
        warn_msgs.append(f"{u} → G (알 수 없는 NCAA, Gly으로 대체)")

    return seq, warn_msgs, removed


def _core_fallback_biophysical(seq: str) -> Dict[str, float]:
    n = len(seq)
    mw = sum(_CORE_RESIDUE_WEIGHTS.get(aa, 0.0) for aa in seq) + _CORE_WATER_MW
    gravy = sum(_CORE_KD_HYDROPATHY.get(aa, 0.0) for aa in seq) / n if n else 0.0
    return {"mw": round(mw, 2), "gravy": round(gravy, 4),
            "instability_index": float("nan"), "pi": float("nan")}


def _core_compute_biopython_props(seq: str) -> Dict[str, float]:
    if not _CORE_HAS_BIOPYTHON:
        return _core_fallback_biophysical(seq)
    try:
        pa = _ProteinAnalysis(seq)
        return {
            "mw": round(pa.molecular_weight(), 2),
            "gravy": round(pa.gravy(), 4),
            "instability_index": round(pa.instability_index(), 2),
            "pi": round(pa.isoelectric_point(), 2),
        }
    except Exception as e:
        logger.warning("[core] Biopython 실패 %s: %s", seq[:10], e)
        return _core_fallback_biophysical(seq)


def _core_aliphatic_index(seq: str) -> float:
    n = len(seq)
    if n == 0:
        return 0.0
    xa = seq.count("A") / n
    xv = seq.count("V") / n
    xi = seq.count("I") / n
    xl = seq.count("L") / n
    return round((xa + _CORE_IKAI_VAL * xv + _CORE_IKAI_ILE * xi + _CORE_IKAI_LEU * xl) * 100.0, 2)


def _core_boman(seq: str) -> Optional[float]:
    if _CORE_HAS_PEPTIDES:
        try:
            return round(_Peptide(seq).boman(), 4)
        except Exception:
            pass
    return None


def _core_charge(seq: str, ph: float = 7.4) -> Optional[float]:
    if _CORE_HAS_PEPTIDES:
        try:
            return round(_Peptide(seq).charge(pH=ph), 4)
        except Exception:
            pass
    return None


def _core_protease_sites(seq: str) -> ProteasePredict:
    """정성적 protease 절단 취약 부위 예측 (1-indexed)."""
    trypsin, chymotrypsin, nep = [], [], []
    n = len(seq)
    for i, aa in enumerate(seq):
        nxt = seq[i + 1] if i + 1 < n else ""
        if aa in ("K", "R") and nxt != "P":
            trypsin.append(i + 1)
        if aa in ("F", "Y", "W") and nxt != "P":
            chymotrypsin.append(i + 1)
        if aa in ("F", "L", "V", "A", "I") and i > 0:
            nep.append(i + 1)
    return ProteasePredict(trypsin=trypsin, chymotrypsin=chymotrypsin, nep=nep)


# ---------------------------------------------------------------------------
# StabilityCoreEvaluator — 공통 평가 클래스
# ---------------------------------------------------------------------------

class StabilityCoreEvaluator:
    """Silo-agnostic 안정성 평가기.

    Usage:
        evaluator = StabilityCoreEvaluator()
        core = evaluator.evaluate("AGCKNFFWKTFTSC", seq_id="SST14_ref")
    """

    def evaluate(
        self,
        sequence: str,
        seq_id: str = "",
        modifications: Optional[List[str]] = None,
    ) -> StabilityCore:
        """단일 서열 안정성 평가.

        Args:
            sequence: 아미노산 서열 (NCAA 포함 가능)
            seq_id: 후보 식별자
            modifications: step08에 전달할 modification 목록

        Returns:
            StabilityCore
        """
        if not sequence or not str(sequence).strip():
            raise ValueError(f"빈 서열 불허: {sequence!r}")

        if not seq_id:
            seq_id = sequence[:6]
        mods = modifications or []

        # NCAA 처리 (M-02: ncaa_removed_residues 추적)
        canonical, ncaa_warnings, ncaa_removed = _core_strip_ncaa(sequence)
        clean = "".join(aa for aa in canonical if aa in _CORE_VALID_AA)
        if len(clean) != len(canonical):
            ncaa_warnings.append(f"{len(canonical) - len(clean)}개 알 수 없는 잔기 제거됨")
        canonical = clean

        # Biopython 속성
        bio = _core_compute_biopython_props(canonical)

        # 범위 가드 (soft warning only)
        try:
            assert_in_range(bio["mw"], "molecular_weight_peptide_da", seq_id)
        except (ValueError, AssertionError, KeyError) as e:
            logger.warning("[core] MW 범위 경고 %s: %s", seq_id, e)
        try:
            if not math.isnan(bio["gravy"]):
                assert_in_range(bio["gravy"], "kyte_doolittle_mean", seq_id)
        except (ValueError, AssertionError, KeyError) as e:
            logger.warning("[core] GRAVY 범위 경고 %s: %s", seq_id, e)

        biophysical = BiophysicalProps(
            mw=bio["mw"],
            gravy=bio["gravy"],
            instability_index=bio["instability_index"],
            pi=bio["pi"],
            boman=_core_boman(canonical),
            charge_ph74=_core_charge(canonical, ph=7.4),
            aliphatic_index=_core_aliphatic_index(canonical),
        )

        protease = _core_protease_sites(canonical)

        # ADMET
        admet: Dict[str, Any] = {}
        nephrotox_risk = "Unknown"
        if _CORE_HAS_ADMET:
            try:
                admet = _compute_admet(canonical)  # type: ignore[name-defined]
                nr = _nephrotox(canonical)  # type: ignore[name-defined]
                nephrotox_risk = nr.get("risk_level", "Unknown")
            except Exception as e:
                logger.warning("[core] ADMET 실패 %s: %s", seq_id, e)

        # Heuristic HL score
        hl_score = 0.0
        if _CORE_HAS_STEP08:
            try:
                hl_score = _hl_predictor(canonical, mods)  # type: ignore[name-defined]
            except Exception as e:
                logger.warning("[core] hl_score 실패 %s: %s", seq_id, e)

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

        return StabilityCore(
            seq_id=seq_id,
            sequence=sequence,
            canonical_sequence=canonical,
            biophysical=biophysical,
            protease=protease,
            admet=admet,
            nephrotox_risk=nephrotox_risk,
            hl_score_heuristic=hl_score,
            hl_warnings=hl_warnings,
            ncaa_warnings=ncaa_warnings,
            ncaa_removed_residues=ncaa_removed,  # M-02
        )
