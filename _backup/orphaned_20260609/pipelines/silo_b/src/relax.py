from __future__ import annotations

import math
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class RelaxResult:
    sequence: str
    relaxed_dg: float          # ΔG = E(bound) − E(peptide) − E(receptor)
    clash_score: float         # fa_rep component; lower = fewer clashes
    interface_energy: float    # interface_delta_X from InterfaceAnalyzerMover
    backbone_rmsd: float       # Cα RMSD vs pre-relax pose
    wall_time_s: float
    success: bool
    error_msg: Optional[str]
    components: Dict[str, float]


class ComplexRelaxer(ABC):
    """Post-dock complex relaxation interface.

    After docking places the peptide, relaxation resolves steric clashes and
    yields a physically meaningful binding ΔG via the three-body decomposition:
        ΔG_bind = E(complex) − E(peptide_alone) − E(receptor_alone)
    """

    @abstractmethod
    def relax(self, sequence: str, docked_pose_tag: str) -> RelaxResult:
        raise NotImplementedError


class PyRosettaComplexRelaxer(ComplexRelaxer):
    """Constrained FastRelax on the docked complex using PyRosetta.

    Protocol:
      1. Apply coordinate constraints to preserve disulfide and pharmacophore
      2. FastRelax with ref2015 score function
      3. Three-body ΔG decomposition
      4. Measure interface energy via InterfaceAnalyzerMover
    """

    def __init__(
        self,
        complex_pdb_path: str,
        peptide_chain: str = "B",
        disulfide_positions: tuple[int, int] = (3, 14),
        pharmacophore_positions: tuple[int, ...] = (7, 8, 9, 10),
        coord_constraint_sd: float = 0.5,
    ):
        try:
            import pyrosetta
        except ImportError:
            raise ImportError(
                "PyRosetta required. "
                "Install: conda install -c https://conda.rosettacommons.org pyrosetta"
            )

        pyrosetta.init(extra_options="-mute all -ignore_unrecognized_res")
        self._pyrosetta = pyrosetta

        from pyrosetta import pose_from_pdb
        from pyrosetta.rosetta.core.scoring import get_score_function

        self._scorefxn = get_score_function()
        self._template_pose = pose_from_pdb(complex_pdb_path)
        self._peptide_chain = peptide_chain
        self._disulfide_positions = disulfide_positions
        self._pharmacophore_positions = pharmacophore_positions
        self._coord_cst_sd = coord_constraint_sd

    def _find_chain_id(self, pose) -> int:
        from pyrosetta.rosetta.core.pose import get_chain_id_from_chain
        return get_chain_id_from_chain(self._peptide_chain, pose)

    def _add_coordinate_constraints(self, pose, chain_id: int) -> None:
        from pyrosetta.rosetta.core.scoring.constraints import (
            CoordinateConstraint,
        )
        from pyrosetta.rosetta.core.scoring.func import HarmonicFunc
        from pyrosetta.rosetta.core.id import AtomID

        chain_begin = pose.chain_begin(chain_id)
        func = HarmonicFunc(0.0, self._coord_cst_sd)

        constrained_local = set(self._disulfide_positions) | set(self._pharmacophore_positions)
        anchor_atom = AtomID(1, 1)

        for local_pos in constrained_local:
            res_idx = chain_begin + local_pos - 1
            if res_idx > pose.total_residue():
                continue
            ca_idx = pose.residue(res_idx).atom_index("CA")
            target = pose.residue(res_idx).xyz("CA")
            cst = CoordinateConstraint(
                AtomID(ca_idx, res_idx), anchor_atom, target, func
            )
            pose.add_constraint(cst)

        from pyrosetta.rosetta.core.scoring import ScoreType
        self._scorefxn.set_weight(ScoreType.coordinate_constraint, 1.0)

    def _fast_relax(self, pose) -> None:
        from pyrosetta.rosetta.protocols.relax import FastRelax

        relax = FastRelax()
        relax.set_scorefxn(self._scorefxn)
        relax.constrain_relax_to_start_coords(True)
        relax.apply(pose)

    def _compute_three_body_dg(self, pose, chain_id: int) -> tuple[float, float, float, float]:
        """ΔG_bind = E(complex) − E(peptide) − E(receptor)"""
        from pyrosetta.rosetta.protocols.rigid import RigidBodyTransMover

        e_complex = self._scorefxn(pose)

        separated = pose.clone()
        jump_id = cyclic_jump = 1
        for j in range(1, separated.num_jump() + 1):
            up_res = separated.fold_tree().upstream_jump_residue(j)
            down_res = separated.fold_tree().downstream_jump_residue(j)
            if (separated.chain(up_res) != separated.chain(down_res)):
                jump_id = j
                break

        trans = RigidBodyTransMover(separated, jump_id)
        trans.step_size(500.0)
        trans.apply(separated)

        e_separated = self._scorefxn(separated)

        chain_begin = pose.chain_begin(chain_id)
        chain_end = pose.chain_end(chain_id)

        pep_only = pose.clone()
        rec_only = pose.clone()

        e_pep = 0.0
        e_rec = 0.0
        try:
            from pyrosetta.rosetta.protocols.grafting import (
                return_region,
            )
            pep_pose = return_region(pose.clone(), chain_begin, chain_end)
            e_pep = self._scorefxn(pep_pose)

            if chain_begin > 1:
                rec_pose = return_region(pose.clone(), 1, chain_begin - 1)
                if chain_end < pose.total_residue():
                    from pyrosetta.rosetta.protocols.grafting import (
                        insert_pose_into_pose,
                    )
                    tail = return_region(pose.clone(), chain_end + 1, pose.total_residue())
                    insert_pose_into_pose(rec_pose, tail, rec_pose.total_residue())
                e_rec = self._scorefxn(rec_pose)
            else:
                e_rec = e_separated - e_pep
        except Exception:
            e_rec = e_separated - e_pep

        dg_bind = e_complex - e_pep - e_rec
        return dg_bind, e_complex, e_pep, e_rec

    def _compute_interface_energy(self, pose, chain_id: int) -> float:
        try:
            from pyrosetta.rosetta.protocols.analysis import InterfaceAnalyzerMover

            iam = InterfaceAnalyzerMover()
            iam.set_scorefunction(self._scorefxn)
            iam.set_compute_interface_delta_hbond_unsat(True)
            iam.apply(pose)
            return pose.scores.get("dG_separated", 0.0)
        except Exception:
            return 0.0

    def _compute_clash_score(self, pose) -> float:
        from pyrosetta.rosetta.core.scoring import ScoreType
        self._scorefxn(pose)
        return pose.energies().total_energies()[ScoreType.fa_rep]

    def _compute_backbone_rmsd(self, pose, reference) -> float:
        from pyrosetta.rosetta.core.scoring import CA_rmsd
        return CA_rmsd(pose, reference)

    def relax(self, sequence: str, docked_pose_tag: str) -> RelaxResult:
        from pyrosetta.rosetta.protocols.simple_moves import MutateResidue

        t0 = time.monotonic()
        seq = sequence.upper()

        try:
            pose = self._template_pose.clone()
            chain_id = self._find_chain_id(pose)
            chain_begin = pose.chain_begin(chain_id)
            chain_end = pose.chain_end(chain_id)
            template_len = chain_end - chain_begin + 1

            if len(seq) != template_len:
                return RelaxResult(
                    sequence=seq, relaxed_dg=math.inf, clash_score=math.inf,
                    interface_energy=0.0, backbone_rmsd=math.inf,
                    wall_time_s=time.monotonic() - t0, success=False,
                    error_msg=f"length mismatch: {len(seq)} vs {template_len}",
                    components={},
                )

            for i, aa in enumerate(seq):
                res_idx = chain_begin + i
                if pose.residue(res_idx).name1() != aa:
                    MutateResidue(res_idx, aa).apply(pose)

            pre_relax = pose.clone()

            self._add_coordinate_constraints(pose, chain_id)
            self._fast_relax(pose)

            dg_bind, e_complex, e_pep, e_rec = self._compute_three_body_dg(pose, chain_id)
            interface_e = self._compute_interface_energy(pose, chain_id)
            clash = self._compute_clash_score(pose)
            rmsd = self._compute_backbone_rmsd(pose, pre_relax)

            return RelaxResult(
                sequence=seq,
                relaxed_dg=round(dg_bind, 4),
                clash_score=round(clash, 4),
                interface_energy=round(interface_e, 4),
                backbone_rmsd=round(rmsd, 4),
                wall_time_s=round(time.monotonic() - t0, 3),
                success=True,
                error_msg=None,
                components={
                    "e_complex": round(e_complex, 2),
                    "e_peptide": round(e_pep, 2),
                    "e_receptor": round(e_rec, 2),
                    "dg_bind": round(dg_bind, 2),
                },
            )
        except Exception as exc:
            return RelaxResult(
                sequence=seq, relaxed_dg=math.inf, clash_score=math.inf,
                interface_energy=0.0, backbone_rmsd=math.inf,
                wall_time_s=time.monotonic() - t0, success=False,
                error_msg=str(exc), components={},
            )


class MockComplexRelaxer(ComplexRelaxer):
    """Deterministic mock for testing. Produces synthetic but structurally
    plausible values based on sequence composition.

    WARNING: All values are fabricated heuristics for testing only.
    """

    def relax(self, sequence: str, docked_pose_tag: str) -> RelaxResult:
        seq = sequence.upper()
        t0 = time.monotonic()

        hydrophobic = set("AILMFWY")
        h_ratio = sum(1 for aa in seq if aa in hydrophobic) / max(len(seq), 1)

        dg = -8.0 - h_ratio * 4.0
        clash = max(0.0, (1.0 - h_ratio) * 15.0)
        interface_e = dg * 0.6
        rmsd = 0.3 + h_ratio * 0.5

        return RelaxResult(
            sequence=seq,
            relaxed_dg=round(dg, 4),
            clash_score=round(clash, 4),
            interface_energy=round(interface_e, 4),
            backbone_rmsd=round(rmsd, 4),
            wall_time_s=round(time.monotonic() - t0, 6),
            success=True,
            error_msg=None,
            components={
                "e_complex": round(dg * 2, 2),
                "e_peptide": round(-dg * 0.5, 2),
                "e_receptor": round(-dg * 0.5, 2),
                "dg_bind": round(dg, 2),
            },
        )
