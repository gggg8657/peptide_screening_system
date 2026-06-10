from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from pipelines.shared.models import Modality, Silo, UnifiedCandidate

from .arms import Arm1SmallMolRunner, Arm2FlexPepRunner, Arm3DeNovoRunner, ArmRunner
from .clients import NimClientBundle
from .config import SiloAConfig, config_hash, load_config
from .models import ArmName, ArmResult, CandidateRecord, RunStatus
from .scoring import UnifiedScorer

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineResult:
    run_id: str
    config_hash: str
    arm_results: Dict[str, ArmResult]
    ranked_candidates: List[CandidateRecord]
    manifest: Dict[str, object]


class SiloAOrchestrator:
    def __init__(
        self,
        config_path: str,
        client_bundle: NimClientBundle,
        output_root: Path | None = None,
    ):
        self.config_path = config_path
        self.config = load_config(config_path)
        self.clients = client_bundle
        self.output_root = Path(output_root or self.config.output.root)
        self.scorer = UnifiedScorer(self.config.scoring)

    def _build_arms(self) -> List[ArmRunner]:
        return [Arm1SmallMolRunner(), Arm2FlexPepRunner(), Arm3DeNovoRunner()]

    def execute(self) -> PipelineResult:
        run_id = f"silo_a_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}"
        self.output_root.mkdir(parents=True, exist_ok=True)

        arm_results: Dict[str, ArmResult] = {}
        all_candidates: List[CandidateRecord] = []

        for arm in self._build_arms():
            try:
                result = arm.run(self.config, self.clients)
            except Exception as exc:
                logger.error("Arm %s failed during run: %s", arm.name.value, exc, exc_info=True)
                result = ArmResult(
                    arm=arm.name,
                    run_id=run_id,
                    status=RunStatus.FAILED,
                    started_at=datetime.now(timezone.utc),
                    finished_at=datetime.now(timezone.utc),
                    config_hash=config_hash(self.config),
                    errors=[f"{type(exc).__name__}: {exc}"],
                )
            arm_results[arm.name.value] = result
            all_candidates.extend(result.candidates)

        ranked = self.scorer.rank_candidates(all_candidates)

        manifest = {
            "run_id": run_id,
            "config_path": self.config_path,
            "config_hash": config_hash(self.config),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "arm_summary": {
                name: {
                    "status": r.status.value,
                    "candidates": len(r.candidates),
                    "errors": len(r.errors),
                }
                for name, r in arm_results.items()
            },
            "total_ranked": len(ranked),
        }

        manifest_path = self.output_root / self.config.output.manifest_name
        manifest_path.write_text(json.dumps(manifest, indent=2, default=str))

        return PipelineResult(
            run_id=run_id,
            config_hash=config_hash(self.config),
            arm_results=arm_results,
            ranked_candidates=ranked,
            manifest=manifest,
        )

    _ARM_TO_MODALITY = {
        ArmName.SMALL_MOL: Modality.SMALL_MOL,
        ArmName.FLEXPEP: Modality.PEPTIDE_VARIANT,
        ArmName.DENOVO: Modality.DE_NOVO,
    }

    @classmethod
    def to_unified(cls, result: PipelineResult) -> List[UnifiedCandidate]:
        """Convert Silo A ranked candidates to UnifiedCandidate for cross-silo comparison."""
        unified = []
        for i, cand in enumerate(result.ranked_candidates):
            modality = cls._ARM_TO_MODALITY.get(cand.arm, Modality.SMALL_MOL)

            raw_scores = dict(cand.features)
            if cand.score is not None:
                raw_scores["unified_score"] = cand.score

            bridge: Dict[str, float] = {}
            if "delta_energy" in cand.features:
                bridge["dg_est"] = cand.features["delta_energy"]
            if "dock_confidence" in cand.features:
                bridge["dg_est"] = bridge.get("dg_est", -cand.features["dock_confidence"] * 10)
            if "clash_score" in cand.features:
                bridge["clash"] = cand.features["clash_score"]
            if "plddt" in cand.features:
                bridge["stability"] = cand.features["plddt"] / 100.0
            bridge["feasibility"] = cand.features.get("qed", 0.5)

            confidence = cand.features.get("dock_success", 0.0)

            unified.append(UnifiedCandidate(
                id=f"silo_a_{i:04d}",
                silo=Silo.SILO_A,
                modality=modality,
                structure=cand.value,
                raw_scores=raw_scores,
                bridge_metrics=bridge,
                confidence=confidence,
                provenance={
                    "config_hash": result.config_hash,
                    "run_id": result.run_id,
                    "arm": cand.arm.value,
                    "source": cand.source,
                },
            ))
        return unified
