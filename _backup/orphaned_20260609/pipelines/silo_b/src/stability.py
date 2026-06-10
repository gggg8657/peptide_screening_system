from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict


# Kyte-Doolittle hydropathy index
_HYDROPATHY: Dict[str, float] = {
    "A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5,
    "E": -3.5, "Q": -3.5, "G": -0.4, "H": -3.2, "I": 4.5,
    "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8, "P": -1.6,
    "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2,
}

# Beta-turn propensity (Levitt, 1978) — relevant for cyclic peptides like SST-14
_TURN_PROPENSITY: Dict[str, float] = {
    "A": 0.66, "R": 0.95, "N": 1.56, "D": 1.46, "C": 1.19,
    "E": 0.74, "Q": 0.98, "G": 1.56, "H": 0.95, "I": 0.47,
    "L": 0.59, "K": 1.01, "M": 0.60, "F": 0.60, "P": 1.52,
    "S": 1.43, "T": 0.96, "W": 0.96, "Y": 1.14, "V": 0.50,
}


@dataclass(frozen=True)
class StabilityScore:
    score: float
    components: Dict[str, float]


class StabilityEstimator(ABC):
    @abstractmethod
    def estimate(self, sequence: str, template_sequence: str) -> StabilityScore:
        raise NotImplementedError


class SequenceStabilityEstimator(StabilityEstimator):
    """Heuristic stability estimator based on physicochemical properties.

    Compares the mutant sequence against the template using:
    1. Hydropathy deviation from template (amphipathic balance)
    2. Charge balance preservation
    3. Proline burden (disrupts beta-turns in cyclic peptides)
    4. Glycine excess (structural flexibility penalty)
    5. Template conservation (fewer mutations = safer)
    """

    def estimate(self, sequence: str, template_sequence: str) -> StabilityScore:
        seq = sequence.upper()
        tmpl = template_sequence.upper()

        hydro_score = self._hydropathy_similarity(seq, tmpl)
        charge_score = self._charge_balance(seq, tmpl)
        pro_score = self._proline_penalty(seq, tmpl)
        gly_score = self._glycine_penalty(seq)
        conservation_score = self._conservation(seq, tmpl)

        score = (
            0.30 * hydro_score
            + 0.20 * charge_score
            + 0.15 * pro_score
            + 0.15 * gly_score
            + 0.20 * conservation_score
        )

        return StabilityScore(
            score=round(max(0.0, min(1.0, score)), 4),
            components={
                "hydropathy": round(hydro_score, 4),
                "charge_balance": round(charge_score, 4),
                "proline": round(pro_score, 4),
                "glycine": round(gly_score, 4),
                "conservation": round(conservation_score, 4),
            },
        )

    @staticmethod
    def _hydropathy_similarity(seq: str, tmpl: str) -> float:
        mean_h = sum(_HYDROPATHY.get(aa, 0.0) for aa in seq) / max(len(seq), 1)
        tmpl_h = sum(_HYDROPATHY.get(aa, 0.0) for aa in tmpl) / max(len(tmpl), 1)
        deviation = abs(mean_h - tmpl_h) / 9.0
        return max(0.0, 1.0 - deviation)

    @staticmethod
    def _charge_balance(seq: str, tmpl: str) -> float:
        net = lambda s: sum(1 for aa in s if aa in "KRH") - sum(1 for aa in s if aa in "DE")
        delta = abs(net(seq) - net(tmpl)) / max(len(seq), 1)
        return max(0.0, 1.0 - delta * 2.0)

    @staticmethod
    def _proline_penalty(seq: str, tmpl: str) -> float:
        excess = max(0, seq.count("P") - tmpl.count("P") - 1)
        return max(0.0, 1.0 - excess * 0.15)

    @staticmethod
    def _glycine_penalty(seq: str) -> float:
        ratio = seq.count("G") / max(len(seq), 1)
        return max(0.0, 1.0 - max(0.0, ratio - 0.15) * 3.0)

    @staticmethod
    def _conservation(seq: str, tmpl: str) -> float:
        if len(seq) != len(tmpl):
            return 0.0
        mutations = sum(a != b for a, b in zip(seq, tmpl))
        return max(0.0, 1.0 - (mutations / max(len(seq), 1)) * 0.5)


class PyRosettaStabilityEstimator(StabilityEstimator):
    """Stability via PyRosetta FastRelax + ddG scoring.

    Relaxes both the template and each mutant peptide independently,
    then computes the folding ddG. Lower ddG = more stable mutation.
    """

    def __init__(self, template_pdb_path: str):
        try:
            import pyrosetta
        except ImportError:
            raise ImportError("PyRosetta required for PyRosettaStabilityEstimator")

        pyrosetta.init(extra_options="-mute all -ignore_unrecognized_res")

        from pyrosetta import pose_from_pdb
        from pyrosetta.rosetta.core.scoring import get_score_function
        from pyrosetta.rosetta.protocols.relax import FastRelax

        self._scorefxn = get_score_function()
        self._template_pose = pose_from_pdb(template_pdb_path)

        relax = FastRelax()
        relax.set_scorefxn(self._scorefxn)
        relax.apply(self._template_pose)
        self._template_score = self._scorefxn(self._template_pose)

    def estimate(self, sequence: str, template_sequence: str) -> StabilityScore:
        from pyrosetta.rosetta.protocols.simple_moves import MutateResidue
        from pyrosetta.rosetta.protocols.relax import FastRelax

        seq = sequence.upper()
        pose = self._template_pose.clone()

        try:
            for i, aa in enumerate(seq):
                res_idx = i + 1
                if pose.residue(res_idx).name1() != aa:
                    MutateResidue(res_idx, aa).apply(pose)

            relax = FastRelax()
            relax.set_scorefxn(self._scorefxn)
            relax.apply(pose)

            mutant_score = self._scorefxn(pose)
            ddg = mutant_score - self._template_score

            normalized = 1.0 / (1.0 + math.exp(ddg / 5.0))

            return StabilityScore(
                score=round(normalized, 4),
                components={
                    "ddg_reu": round(ddg, 2),
                    "template_reu": round(self._template_score, 2),
                    "mutant_reu": round(mutant_score, 2),
                },
            )
        except Exception as exc:
            return StabilityScore(score=0.0, components={"error": str(exc)})
