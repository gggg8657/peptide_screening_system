"""
stability_predictor/silo_b_evaluator.py
=========================================
Silo B 전용 안정성 평가 — SST-14 변이 후보 특화.

Silo B: PyRosetta FlexPepDock 기반 SST-14 변이 생성 파이프라인
- SST14 (AGCKNFFWKTFTSC) 대비 mutation_count 추적
- FWKT pharmacophore (위치 7-10, 1-indexed) 보존 여부 검사
- SAR 일관성 점수 (pharmacophore + charge 기반 heuristic)
- SST-14 baseline 대비 biophysical 변화량

Usage:
    from pipeline_local.scripts.stability_predictor.core import StabilityCoreEvaluator
    from pipeline_local.scripts.stability_predictor.silo_b_evaluator import (
        SiloBStabilityEvaluator, SiloBStabilityResult,
    )

    core_eval = StabilityCoreEvaluator()
    evaluator = SiloBStabilityEvaluator(core_eval)
    result = evaluator.evaluate("AICKNFFWKTFTSC", seq_id="cand03")

⚠️ HEURISTIC — SAR consistency score, HL score 등은 후보 ranking 전용.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pipeline_local.scripts.stability_predictor.core import (
    StabilityCore,
    StabilityCoreEvaluator,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SST-14 레퍼런스 상수
# ---------------------------------------------------------------------------
SST14_SEQUENCE = "AGCKNFFWKTFTSC"

# FWKT pharmacophore — SST-14 에서 수용체 결합에 핵심적인 잔기 (1-indexed)
# A=1,G=2,C=3,K=4,N=5,F=6,F=7,W=8,K=9,T=10,F=11,T=12,S=13,C=14
# FWKT = F@7, W@8, K@9, T@10
PHARMACOPHORE_POSITIONS = (7, 8, 9, 10)
PHARMACOPHORE_RESIDUES  = ("F", "W", "K", "T")   # 1-indexed 위치별 기대 잔기


# ---------------------------------------------------------------------------
# 데이터클래스
# ---------------------------------------------------------------------------

@dataclass
class SiloBStabilityExtras:
    """Silo B (SST-14 변이) 전용 추가 지표.

    ⚠️ sar_consistency_score는 HEURISTIC ranking용 — 실험적 결합력 절대값 아님.
    """
    mutation_count: int                         # SST-14 대비 치환 개수
    fwkt_conservation: bool                     # FWKT pharmacophore 4잔기 전체 보존 여부
    fwkt_partial_conservation: float            # 보존된 pharmacophore 잔기 비율 (0.0-1.0)
    sar_consistency_score: float                # [0.0-1.0] HEURISTIC SAR 일치도
    sst14_baseline_diff: Dict[str, float]       # biophysical 지표의 SST-14 대비 변화량

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mutation_count": self.mutation_count,
            "fwkt_conservation": self.fwkt_conservation,
            "fwkt_partial_conservation": round(self.fwkt_partial_conservation, 3),
            "sar_consistency_score": round(self.sar_consistency_score, 4),
            "sst14_baseline_diff": {k: round(v, 4) for k, v in self.sst14_baseline_diff.items()},
        }


@dataclass
class SiloBStabilityResult:
    """Silo B 안정성 평가 통합 결과.

    core: Silo-agnostic 물리화학 지표 (StabilityCore)
    extras: Silo B 전용 SAR / mutation 지표 (SiloBStabilityExtras)
    """
    core: StabilityCore
    extras: SiloBStabilityExtras
    silo: str = field(default="B")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "silo": self.silo,
            "core": self.core.to_dict(),
            "extras": self.extras.to_dict(),
        }

    # 자주 쓰는 core 속성 직접 접근 편의 프로퍼티
    @property
    def seq_id(self) -> str:
        return self.core.seq_id

    @property
    def sequence(self) -> str:
        return self.core.sequence

    @property
    def canonical_sequence(self) -> str:
        return self.core.canonical_sequence

    @property
    def is_stable(self) -> bool:
        return self.core.is_stable_biopython


# ---------------------------------------------------------------------------
# SiloBStabilityEvaluator
# ---------------------------------------------------------------------------

class SiloBStabilityEvaluator:
    """Silo B (SST-14 변이) 전용 안정성 평가기.

    Dependency Injection 패턴 — StabilityCoreEvaluator를 주입받아 사용.

    Usage:
        core_eval = StabilityCoreEvaluator()
        evaluator = SiloBStabilityEvaluator(core_eval)
        result = evaluator.evaluate("AICKNFFWKTFTSC", seq_id="cand03")

    Args:
        core_eval: StabilityCoreEvaluator 인스턴스
        reference: SST-14 레퍼런스 서열 (기본: AGCKNFFWKTFTSC)
    """

    def __init__(
        self,
        core_eval: StabilityCoreEvaluator,
        reference: str = SST14_SEQUENCE,
    ) -> None:
        self._core_eval = core_eval
        self._reference = reference
        self._ref_core: Optional[StabilityCore] = None   # lazy 계산

    def _get_ref_core(self) -> StabilityCore:
        """SST-14 baseline core (lazy, 최초 1회 계산)."""
        if self._ref_core is None:
            try:
                self._ref_core = self._core_eval.evaluate(
                    self._reference, seq_id="SST14_ref"
                )
            except Exception as e:
                logger.warning("[silo_b] SST14 baseline 계산 실패: %s", e)
                # fallback — 빈 core
                from pipeline_local.scripts.stability_predictor.core import (
                    BiophysicalProps, ProteasePredict,
                )
                self._ref_core = StabilityCore(
                    seq_id="SST14_ref", sequence=self._reference,
                    canonical_sequence=self._reference,
                    biophysical=BiophysicalProps(
                        mw=1637.9, gravy=-0.48, instability_index=30.65,
                        pi=8.2, boman=None, charge_ph74=None, aliphatic_index=35.0,
                    ),
                    protease=ProteasePredict(trypsin=[4, 9], chymotrypsin=[6, 7, 8, 11], nep=[1, 6]),
                    admet={}, nephrotox_risk="Unknown",
                    hl_score_heuristic=0.0, hl_warnings=[], ncaa_warnings=[],
                )
        return self._ref_core

    def evaluate(
        self,
        sequence: str,
        seq_id: str = "",
        modifications: Optional[List[str]] = None,
    ) -> SiloBStabilityResult:
        """단일 Silo B 후보 안정성 평가.

        Args:
            sequence: 후보 서열 (NCAA 포함 가능)
            seq_id: 후보 ID
            modifications: step08에 전달할 modification 목록

        Returns:
            SiloBStabilityResult (core + extras)
        """
        core = self._core_eval.evaluate(sequence, seq_id=seq_id, modifications=modifications)
        extras = self._compute_extras(core)
        return SiloBStabilityResult(core=core, extras=extras)

    def _compute_extras(self, core: StabilityCore) -> SiloBStabilityExtras:
        """Silo B 전용 지표 계산."""
        cand_seq = core.canonical_sequence
        mut_count = self._count_mutations(cand_seq, self._reference)
        fwkt_full, fwkt_partial = self._check_fwkt(cand_seq)
        sar_score = self._sar_consistency_score(core, fwkt_partial)
        baseline_diff = self._baseline_diff(core)
        return SiloBStabilityExtras(
            mutation_count=mut_count,
            fwkt_conservation=fwkt_full,
            fwkt_partial_conservation=fwkt_partial,
            sar_consistency_score=sar_score,
            sst14_baseline_diff=baseline_diff,
        )

    def _count_mutations(self, seq: str, ref: str) -> int:
        """참조 서열 대비 치환 개수 (길이 다르면 max 길이 기준)."""
        max_len = max(len(seq), len(ref))
        count = 0
        for i in range(max_len):
            aa_cand = seq[i] if i < len(seq) else "-"
            aa_ref  = ref[i] if i < len(ref) else "-"
            if aa_cand != aa_ref:
                count += 1
        return count

    def _check_fwkt(self, seq: str) -> tuple:
        """FWKT pharmacophore 보존 여부.

        Returns:
            (is_fully_conserved: bool, partial_ratio: float)
        """
        conserved = 0
        for pos, expected in zip(PHARMACOPHORE_POSITIONS, PHARMACOPHORE_RESIDUES):
            idx = pos - 1  # 0-indexed
            if idx < len(seq) and seq[idx] == expected:
                conserved += 1
        partial = conserved / len(PHARMACOPHORE_POSITIONS)
        return (partial == 1.0, partial)

    def _sar_consistency_score(
        self, core: StabilityCore, fwkt_partial: float
    ) -> float:
        """HEURISTIC SAR 일관성 점수 [0.0-1.0].

        구성:
          - FWKT pharmacophore 보존율 (가중치 0.6)
          - 순 전하 양성 여부 (가중치 0.4) — SSTR2 음성 결합 포켓과 친화성
          ⚠️ 이 점수는 heuristic ranking 전용 — 실험적 결합력 절대값 아님.
        """
        # Pharmacophore 보존 기여
        fwkt_contrib = fwkt_partial * 0.6

        # 순 전하 기여: SST14 전형적 양성 (net charge ~ +1-2)
        charge_contrib = 0.0
        if core.biophysical.charge_ph74 is not None:
            ch = core.biophysical.charge_ph74
            if ch > 0:
                # 양성이면 최대 기여, 과도한 양성은 부분 감소
                charge_contrib = min(ch / 2.0, 1.0) * 0.4
        else:
            # peptides.py 없는 경우 GRAVY로 대체 heuristic
            charge_contrib = 0.2  # 중간값 부여

        return round(min(fwkt_contrib + charge_contrib, 1.0), 4)

    def _baseline_diff(self, core: StabilityCore) -> Dict[str, float]:
        """SST-14 baseline 대비 biophysical 변화량."""
        ref = self._get_ref_core()
        b = core.biophysical
        rb = ref.biophysical

        diff: Dict[str, float] = {
            "mw_diff": b.mw - rb.mw,
            "gravy_diff": b.gravy - rb.gravy,
            "aliphatic_diff": b.aliphatic_index - rb.aliphatic_index,
        }

        # instability_index: NaN 있으면 None 표시
        if not math.isnan(b.instability_index) and not math.isnan(rb.instability_index):
            diff["instability_diff"] = b.instability_index - rb.instability_index
        else:
            diff["instability_diff"] = float("nan")

        return diff
