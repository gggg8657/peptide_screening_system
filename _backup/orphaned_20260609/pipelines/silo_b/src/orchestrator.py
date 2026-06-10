from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Dict, List

logger = logging.getLogger(__name__)

from pipelines.shared.models import Modality, Silo, UnifiedCandidate

from .config import load_config
from .constraint_compiler import ConstraintCompiler, ValidationResult
from .docking import DockingResult, DockingRunner, MockDockingRunner
from .filters import DrugabilityFilter
from .gates import DefaultHILGate, Gate1Report, Gate2Report, Gate3Report, HILGate
from .generator import MutantGenerator
from .relax import ComplexRelaxer, MockComplexRelaxer, RelaxResult
from .scoring import MultiObjectiveScorer
from .stability import SequenceStabilityEstimator, StabilityEstimator


@dataclass(frozen=True)
class OrchestratorResult:
    total_generated: int
    filtered_count: int
    scored_count: int
    top_candidates: List[dict]
    manifest: Dict[str, object]


class SiloBOrchestrator:
    def __init__(
        self,
        config_path: str,
        docking_runner: DockingRunner | None = None,
        gate_impl: HILGate | None = None,
        stability_estimator: StabilityEstimator | None = None,
        complex_relaxer: ComplexRelaxer | None = None,
    ):
        self.config_path = config_path
        self.config = load_config(config_path)
        if docking_runner is None:
            logger.warning("No DockingRunner provided — using MockDockingRunner. Results will be synthetic.")
        self.docking_runner = docking_runner or MockDockingRunner()
        self.gates = gate_impl or DefaultHILGate()
        self.stability_estimator = stability_estimator or SequenceStabilityEstimator()
        self.complex_relaxer = complex_relaxer or MockComplexRelaxer()
        self.validator = ConstraintCompiler(self.config)
        self.compiled = self.validator.compile()

    def _validate_candidates(self, candidates: List[str]) -> List[ValidationResult]:
        return [self.validator.validate_sequence(candidate) for candidate in candidates]

    def _run_docking(self, sequences: List[str]) -> List[DockingResult]:
        receptor_cfg = self.config.sequence_metadata.receptor
        receptor_pdb = getattr(receptor_cfg, "pdb_path", None) or receptor_cfg.name
        if receptor_pdb == receptor_cfg.name:
            logger.warning("No receptor PDB path configured — using receptor name '%s' as fallback", receptor_pdb)
        return self.docking_runner.dock_batch(sequences, receptor_pdb=receptor_pdb)

    def _run_relax(self, dock_results: List[DockingResult]) -> List[DockingResult]:
        """Apply post-dock complex relaxation and enrich DockingResult with
        three-body ΔG and structural quality metrics."""
        enriched = []
        for dr in dock_results:
            if not dr.success:
                enriched.append(dr)
                continue
            relax = self.complex_relaxer.relax(dr.sequence, docked_pose_tag="")
            if relax.success:
                enriched.append(DockingResult(
                    sequence=dr.sequence,
                    dg=dr.dg,
                    dsasa=dr.dsasa,
                    wall_time_s=dr.wall_time_s + relax.wall_time_s,
                    success=True,
                    error_msg=None,
                    relaxed_dg=relax.relaxed_dg,
                    clash_score=relax.clash_score,
                    interface_energy=relax.interface_energy,
                    backbone_rmsd=relax.backbone_rmsd,
                    energy_components=relax.components,
                ))
            else:
                enriched.append(dr)
        return enriched

    def _compute_hil_confidence(
        self,
        validation: ValidationResult,
        dock_result: DockingResult,
        druggability: float,
        diversity: float,
    ) -> float:
        score = 1.0
        score -= len(validation.hard_violations) * 0.3
        score -= len(validation.soft_violations) * 0.1
        if not dock_result.success:
            score -= 0.4
        score -= max(0.0, 0.5 - druggability) * 0.2
        score -= max(0.0, 0.3 - diversity) * 0.2
        return round(max(0.0, min(1.0, score)), 4)

    def _diversity_metric(self, sequence: str, existing: List[str]) -> float:
        if not sequence:
            return 0.0
        if not existing:
            return 1.0
        seq_len = len(sequence)
        distances = []
        for previous in existing:
            if len(previous) != seq_len:
                continue
            distance = sum(a != b for a, b in zip(sequence, previous))
            distances.append(distance / float(seq_len))
        return min(distances) if distances else 1.0

    def run(self) -> OrchestratorResult:
        generator = MutantGenerator(self.compiled, self.config)
        seed = int(self.config.orchestration.seed_lineage.stage_seeds.get("candidate_generation", self.config.seed))
        total_target = int(self.config.generator.budget.total_candidates)
        total_target = min(total_target, max(1, self.compiled.design_space_size))

        generated = generator.sample_diverse(total_target, seed=seed)
        validation = self._validate_candidates(generated)
        filterer = DrugabilityFilter()

        filtered: List[str] = []
        filter_results = []
        for candidate, valid in zip(generated, validation):
            filter_result = filterer.filter_candidate(candidate)
            filter_results.append(filter_result)
            if not valid.valid:
                continue
            if filter_result.passed:
                filtered.append(candidate)

        gate1: Gate1Report = self.gates.gate_1_review(generated, filter_results)
        if not self.gates.request_approval(gate1):
            return OrchestratorResult(
                total_generated=len(generated),
                filtered_count=0,
                scored_count=0,
                top_candidates=[],
                manifest={"gate1": asdict(gate1)},
            )

        docking_results = self._run_docking(filtered)
        docking_results = self._run_relax(docking_results)

        scorer = MultiObjectiveScorer(self.config.scoring)
        scored: List[dict] = []
        template_seq = self.config.sequence_metadata.peptide.template_sequence
        for candidate, dock_result in zip(filtered, docking_results):
            valid = self.validator.validate_sequence(candidate)
            if not valid.valid:
                continue

            stability_result = self.stability_estimator.estimate(candidate, template_seq)
            diversity = self._diversity_metric(candidate, [item["sequence"] for item in scored])
            druggability = 1.0 - filterer.check_aggregation_prone(candidate)
            hil_confidence = self._compute_hil_confidence(
                valid, dock_result, druggability, diversity,
            )

            effective_dg = dock_result.relaxed_dg if dock_result.relaxed_dg is not None else dock_result.dg

            scored_candidate: dict = {
                "sequence": candidate,
                "dg": effective_dg,
                "dg_raw": dock_result.dg,
                "dg_relaxed": dock_result.relaxed_dg,
                "clash_score": dock_result.clash_score,
                "interface_energy": dock_result.interface_energy,
                "backbone_rmsd": dock_result.backbone_rmsd,
                "energy_components": dock_result.energy_components,
                "stability": stability_result.score,
                "stability_components": stability_result.components,
                "druggability": druggability,
                "diversity": diversity,
                "hil_confidence": hil_confidence,
                "hard_violations": valid.hard_violations,
                "soft_violations": valid.soft_violations,
                "docking_result": dock_result,
                "docking_success": dock_result.success,
            }
            scored_candidate["score"] = scorer.score_candidate(
                dg=scored_candidate["dg"],
                stability=scored_candidate["stability"],
                druggability=scored_candidate["druggability"],
                diversity=scored_candidate["diversity"],
                hil_confidence=scored_candidate["hil_confidence"],
                hard_violations=valid.hard_violations,
                soft_violations=valid.soft_violations,
            )
            scored.append(scored_candidate)

        ranked = scorer.rank_candidates(scored)
        gate2: Gate2Report = self.gates.gate_2_review(ranked)
        if not self.gates.request_approval(gate2):
            return OrchestratorResult(
                total_generated=len(generated),
                filtered_count=len(filtered),
                scored_count=len(ranked),
                top_candidates=[],
                manifest={"gate1": asdict(gate1), "gate2": asdict(gate2)},
            )

        refined = ranked[: max(1, min(3, len(ranked)))]
        gate3 = self.gates.gate_3_review(refined)
        if not self.gates.request_approval(gate3):
            return OrchestratorResult(
                total_generated=len(generated),
                filtered_count=len(filtered),
                scored_count=len(ranked),
                top_candidates=[],
                manifest={"gate1": asdict(gate1), "gate2": asdict(gate2), "gate3": asdict(gate3)},
            )

        manifest: Dict[str, object] = {
            "config_path": self.config_path,
            "stage_counts": {
                "generated": len(generated),
                "filtered": len(filtered),
                "scored": len(ranked),
            },
            "gate1": asdict(gate1),
            "gate2": asdict(gate2),
            "gate3": asdict(gate3),
            "generator_strategy": generator.strategy,
        }
        return OrchestratorResult(
            total_generated=len(generated),
            filtered_count=len(filtered),
            scored_count=len(ranked),
            top_candidates=refined,
            manifest=manifest,
        )

    @staticmethod
    def to_unified(result: OrchestratorResult, config_hash: str = "") -> List[UnifiedCandidate]:
        """Convert Silo B top candidates to UnifiedCandidate for cross-silo comparison."""
        unified = []
        for i, cand in enumerate(result.top_candidates):
            raw_scores = {
                "dg": float(cand.get("dg", 0.0)),
                "stability": float(cand.get("stability", 0.0)),
                "druggability": float(cand.get("druggability", 0.0)),
                "diversity": float(cand.get("diversity", 0.0)),
                "hil_confidence": float(cand.get("hil_confidence", 0.0)),
                "score": float(cand.get("score", 0.0)),
            }

            bridge: Dict[str, float] = {}
            if cand.get("dg_relaxed") is not None:
                bridge["dg_est"] = float(cand["dg_relaxed"])
            else:
                bridge["dg_est"] = float(cand.get("dg", 0.0))
            if cand.get("clash_score") is not None:
                bridge["clash"] = float(cand["clash_score"])
            bridge["stability"] = float(cand.get("stability", 0.0))
            bridge["feasibility"] = float(cand.get("druggability", 0.0))

            confidence = float(cand.get("hil_confidence", 0.0))

            unified.append(UnifiedCandidate(
                id=f"silo_b_{i:04d}",
                silo=Silo.SILO_B,
                modality=Modality.SST14_MUTANT,
                structure=cand.get("sequence", ""),
                raw_scores=raw_scores,
                bridge_metrics=bridge,
                confidence=confidence,
                provenance={
                    "config_hash": config_hash,
                    "gate_status": "gate3_passed",
                },
            ))
        return unified
