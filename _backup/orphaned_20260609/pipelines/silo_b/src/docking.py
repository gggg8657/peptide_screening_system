from __future__ import annotations

import math
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from .config import AMINO_ACIDS


@dataclass(frozen=True)
class DockingResult:
    sequence: str
    dg: float
    dsasa: float
    wall_time_s: float
    success: bool
    error_msg: str | None
    relaxed_dg: float | None = None
    clash_score: float | None = None
    interface_energy: float | None = None
    backbone_rmsd: float | None = None
    energy_components: dict | None = None


class DockingRunner(ABC):
    @abstractmethod
    def dock_candidate(self, sequence: str, receptor_pdb: str) -> DockingResult:
        raise NotImplementedError

    def dock_batch(self, sequences: list[str], receptor_pdb: str) -> list[DockingResult]:
        return [self.dock_candidate(sequence, receptor_pdb) for sequence in sequences]


class PyRosettaDockingRunner(DockingRunner):
    """Production docking via PyRosetta FlexPepDock.

    Requires a template complex PDB (receptor + reference peptide)
    to provide the initial pose for FlexPepDock refinement.
    """

    def __init__(
        self,
        complex_pdb_path: str,
        peptide_chain_idx: int = 1,
        timeout_sec: int = 15,
    ):
        try:
            import pyrosetta
        except ImportError:
            raise ImportError(
                "PyRosetta required for PyRosettaDockingRunner. "
                "Install: conda install -c https://conda.rosettacommons.org pyrosetta"
            )

        pyrosetta.init(extra_options="-mute all -ignore_unrecognized_res")
        self._pyrosetta = pyrosetta

        from pyrosetta import pose_from_pdb
        from pyrosetta.rosetta.core.scoring import get_score_function

        self._scorefxn = get_score_function()
        self._original_pose = pose_from_pdb(complex_pdb_path)
        self._original_score = self._scorefxn(self._original_pose)
        self._peptide_chain_idx = peptide_chain_idx
        self._timeout_sec = timeout_sec

    def dock_candidate(self, sequence: str, receptor_pdb: str) -> DockingResult:
        from pyrosetta.rosetta.protocols.flexpep_docking import FlexPepDockingProtocol
        from pyrosetta.rosetta.protocols.simple_moves import MutateResidue

        seq = sequence.upper()
        t0 = time.monotonic()

        try:
            pose = self._original_pose.clone()
            chain_begin = pose.chain_begin(self._peptide_chain_idx)
            chain_end = pose.chain_end(self._peptide_chain_idx)
            template_len = chain_end - chain_begin + 1

            if len(seq) != template_len:
                return DockingResult(
                    sequence=seq, dg=math.inf, dsasa=0.0,
                    wall_time_s=time.monotonic() - t0, success=False,
                    error_msg=f"length mismatch: got {len(seq)}, expected {template_len}",
                )

            for i, aa in enumerate(seq):
                res_idx = chain_begin + i
                if pose.residue(res_idx).name1() != aa:
                    MutateResidue(res_idx, aa).apply(pose)

            fpdock = FlexPepDockingProtocol()
            fpdock.apply(pose)

            total_score = self._scorefxn(pose)
            dg = total_score - self._original_score

            return DockingResult(
                sequence=seq, dg=round(dg, 4), dsasa=0.0,
                wall_time_s=round(time.monotonic() - t0, 3),
                success=True, error_msg=None,
            )
        except Exception as exc:
            return DockingResult(
                sequence=seq, dg=math.inf, dsasa=0.0,
                wall_time_s=time.monotonic() - t0,
                success=False, error_msg=str(exc),
            )


class MockDockingRunner(DockingRunner):
    """Synthetic, deterministic docking proxy for offline and unit-test execution.

    WARNING: All scores produced by this runner are fabricated heuristics.
    Do NOT use for production candidate evaluation. Use PyRosettaDockingRunner
    or an equivalent physics-based runner instead.
    """

    def _is_aa(self, aa: str) -> bool:
        return aa in AMINO_ACIDS

    def _invalid_reason(self, seq: str) -> str | None:
        for aa in seq.upper():
            if aa not in AMINO_ACIDS:
                return f"invalid_amino_acid:{aa}"
        return None

    def _count_motifs(self, sequence: str, motif: str) -> int:
        if not motif:
            return 0
        seq = sequence.upper()
        return sum(1 for i in range(len(seq) - len(motif) + 1) if seq[i : i + len(motif)] == motif)

    def dock_candidate(self, sequence: str, receptor_pdb: str) -> DockingResult:
        seq = sequence.upper()
        error = self._invalid_reason(seq)
        if error:
            return DockingResult(sequence=seq, dg=math.inf, dsasa=0.0, wall_time_s=0.0, success=False, error_msg=error)

        hydrophobic = set("AILMFWVY")
        hydrophobic_count = sum(1 for aa in seq if aa in hydrophobic)
        hydrophobic_ratio = hydrophobic_count / float(len(seq)) if seq else 0.0

        motif_ng = self._count_motifs(seq, "NG")
        motif_dg = self._count_motifs(seq, "DG")
        met_count = seq.count("M")

        dg = -6.0
        dg -= hydrophobic_ratio * 3.0
        dg -= motif_ng * 2.0
        dg -= motif_dg * 2.5
        dg -= 0.2 * met_count

        dsasa = 1.0 - (hydrophobic_ratio * 0.5 + 0.1 * motif_ng + 0.02 * met_count)
        dsasa = max(0.0, min(1.0, dsasa))
        wall_time_s = max(0.01, len(seq) * 0.003)
        return DockingResult(
            sequence=seq, dg=dg, dsasa=dsasa, wall_time_s=wall_time_s,
            success=True, error_msg=None,
        )

    def dock_batch(self, sequences: list[str], receptor_pdb: str) -> list[DockingResult]:
        return [self.dock_candidate(sequence, receptor_pdb) for sequence in sequences]
