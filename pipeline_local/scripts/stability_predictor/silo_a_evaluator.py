"""
stability_predictor/silo_a_evaluator.py
=========================================
Silo A 전용 안정성 평가 — 3-Arm NIM de novo 후보 특화.

Silo A: ESMFold / ProteinMPNN 기반 de novo 후보 생성 파이프라인
- archives 대비 backbone novelty (시퀀스 유사도 기반 heuristic)
- ESMFold pLDDT (step04 출력) 통합
- SPPS 합성 가능성 간이 평가

Usage:
    from pipeline_local.scripts.stability_predictor.core import StabilityCoreEvaluator
    from pipeline_local.scripts.stability_predictor.silo_a_evaluator import (
        SiloAStabilityEvaluator, SiloAStabilityResult,
    )

    core_eval = StabilityCoreEvaluator()
    evaluator = SiloAStabilityEvaluator(core_eval)
    result = evaluator.evaluate(
        "MYVNOVELSEQ", seq_id="novel_01",
        esmfold_plddt=82.5,
        archive_sequences=["AGCKNFFWKTFTSC", ...],
    )

⚠️ HEURISTIC — backbone_novelty, sar_synthesizability는 ranking 전용.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pipeline_local.scripts.stability_predictor.core import (
    StabilityCore,
    StabilityCoreEvaluator,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SPPS 합성 취약 잔기 (solid-phase peptide synthesis 관점)
# ---------------------------------------------------------------------------
_SPPS_DIFFICULT_AAS = frozenset("WPM")     # Trp/Pro 카플링 저효율, Met 산화
_SPPS_AGGREGATION_PRONE = frozenset("VI")  # β-sheet 집합 경향 (연속 시 문제)


# ---------------------------------------------------------------------------
# 데이터클래스
# ---------------------------------------------------------------------------

@dataclass
class SiloAStabilityExtras:
    """Silo A (de novo) 전용 추가 지표.

    ⚠️ backbone_novelty, de_novo_synthesizability: HEURISTIC ranking 전용.
    """
    backbone_novelty: Optional[float]           # archives 대비 최소 identity 역수 (0-1)
    esmfold_plddt_mean: Optional[float]          # step04 ESMFold pLDDT 평균 (없으면 None)
    de_novo_synthesizability: str               # "Favorable" / "Moderate" / "Difficult"
    spps_difficult_count: int                   # SPPS 취약 잔기 개수

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backbone_novelty": (
                round(self.backbone_novelty, 4) if self.backbone_novelty is not None else None
            ),
            "esmfold_plddt_mean": (
                round(self.esmfold_plddt_mean, 2) if self.esmfold_plddt_mean is not None else None
            ),
            "de_novo_synthesizability": self.de_novo_synthesizability,
            "spps_difficult_count": self.spps_difficult_count,
        }


@dataclass
class SiloAStabilityResult:
    """Silo A 안정성 평가 통합 결과."""
    core: StabilityCore
    extras: SiloAStabilityExtras
    silo: str = field(default="A")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "silo": self.silo,
            "core": self.core.to_dict(),
            "extras": self.extras.to_dict(),
        }

    @property
    def seq_id(self) -> str:
        return self.core.seq_id

    @property
    def sequence(self) -> str:
        return self.core.sequence

    @property
    def is_stable(self) -> bool:
        return self.core.is_stable_biopython


# ---------------------------------------------------------------------------
# SiloAStabilityEvaluator
# ---------------------------------------------------------------------------

class SiloAStabilityEvaluator:
    """Silo A (de novo) 전용 안정성 평가기.

    Dependency Injection 패턴 — StabilityCoreEvaluator를 주입받아 사용.

    Args:
        core_eval: StabilityCoreEvaluator 인스턴스
    """

    def __init__(self, core_eval: StabilityCoreEvaluator) -> None:
        self._core_eval = core_eval

    def evaluate(
        self,
        sequence: str,
        seq_id: str = "",
        modifications: Optional[List[str]] = None,
        esmfold_plddt: Optional[float] = None,
        archive_sequences: Optional[List[str]] = None,
    ) -> SiloAStabilityResult:
        """단일 Silo A 후보 안정성 평가.

        Args:
            sequence: 후보 서열
            seq_id: 후보 ID
            modifications: step08에 전달할 modification 목록
            esmfold_plddt: step04 ESMFold pLDDT 평균 (없으면 None)
            archive_sequences: archives 서열 목록 (novelty 계산용)

        Returns:
            SiloAStabilityResult
        """
        core = self._core_eval.evaluate(
            sequence, seq_id=seq_id, modifications=modifications
        )
        extras = self._compute_extras(
            core, esmfold_plddt=esmfold_plddt, archives=archive_sequences or []
        )
        return SiloAStabilityResult(core=core, extras=extras)

    def _compute_extras(
        self,
        core: StabilityCore,
        esmfold_plddt: Optional[float],
        archives: List[str],
    ) -> SiloAStabilityExtras:
        canonical = core.canonical_sequence
        novelty = self._compute_novelty(canonical, archives) if archives else None
        synth = self._spps_check(canonical)
        difficult = sum(1 for aa in canonical if aa in _SPPS_DIFFICULT_AAS)
        return SiloAStabilityExtras(
            backbone_novelty=novelty,
            esmfold_plddt_mean=esmfold_plddt,
            de_novo_synthesizability=synth,
            spps_difficult_count=difficult,
        )

    def _compute_novelty(self, seq: str, archives: List[str]) -> float:
        """archives 서열 목록 대비 최대 sequence identity 역수.

        novelty = 1 - max_identity
        max_identity = max(identity(seq, arch) for arch in archives)
        identity(a, b) = n_matching / min(len(a), len(b))

        ⚠️ HEURISTIC — 단순 문자 일치율 기반. 구조 novelty 보장 아님.
        """
        if not archives:
            return 1.0
        max_id = 0.0
        for arch in archives:
            common = min(len(seq), len(arch))
            if common == 0:
                continue
            matches = sum(1 for a, b in zip(seq, arch) if a == b)
            max_id = max(max_id, matches / common)
        return round(1.0 - max_id, 4)

    def _spps_check(self, seq: str) -> str:
        """SPPS 합성 가능성 간이 평가.

        기준:
        - Difficult: W/P/M 잔기 ≥3 또는 연속 V/I ≥3
        - Moderate: W/P/M 잔기 1-2
        - Favorable: 없음

        ⚠️ HEURISTIC — 실제 카플링 효율 측정 아님.
        """
        difficult_count = sum(1 for aa in seq if aa in _SPPS_DIFFICULT_AAS)

        # 연속 V/I 패턴 확인
        max_vi_run = 0
        current_vi = 0
        for aa in seq:
            if aa in _SPPS_AGGREGATION_PRONE:
                current_vi += 1
                max_vi_run = max(max_vi_run, current_vi)
            else:
                current_vi = 0

        if difficult_count >= 3 or max_vi_run >= 3:
            return "Difficult"
        elif difficult_count >= 1:
            return "Moderate"
        else:
            return "Favorable"
