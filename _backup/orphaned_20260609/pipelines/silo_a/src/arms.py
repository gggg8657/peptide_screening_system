from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Protocol

from .clients import NimClientBundle
from .config import SiloAConfig, config_hash
from .models import ArmName, ArmResult, CandidateRecord, RunStatus


class ArmRunner(ABC):
    name: ArmName

    @abstractmethod
    def run(self, config: SiloAConfig, clients: NimClientBundle) -> ArmResult:
        raise NotImplementedError

    def _make_run_id(self) -> str:
        return f"{self.name.value}_{uuid.uuid4().hex[:8]}"


class Arm1SmallMolRunner(ArmRunner):
    name = ArmName.SMALL_MOL

    def run(self, config: SiloAConfig, clients: NimClientBundle) -> ArmResult:
        cfg = config.arm1
        run_id = self._make_run_id()
        started = datetime.utcnow()
        candidates = []
        warnings = []
        errors = []

        if not cfg.enabled:
            return ArmResult(
                arm=self.name, run_id=run_id, status=RunStatus.SKIPPED,
                started_at=started, finished_at=datetime.utcnow(),
                config_hash=config_hash(config),
            )

        for seed in cfg.seed_molecules:
            try:
                mols = clients.molmim.generate(
                    smi=seed.smiles,
                    num_molecules=cfg.molmim_num_molecules,
                    algorithm=cfg.molmim_algorithm,
                    property_name=cfg.molmim_property,
                    min_similarity=cfg.molmim_min_similarity,
                )
                for mol in mols:
                    if not isinstance(mol, dict):
                        continue
                    smiles = mol.get("sample", mol.get("smiles", ""))
                    qed = float(mol.get("score", 0.0))
                    candidates.append(CandidateRecord(
                        candidate_id=uuid.uuid4().hex[:12],
                        arm=self.name, value=smiles,
                        source=seed.name,
                        features={"qed": qed},
                    ))
            except Exception as exc:
                errors.append(f"MolMIM({seed.name}): {exc}")

        candidates.sort(key=lambda c: c.features.get("qed", 0.0), reverse=True)
        top = candidates[:cfg.top_k_for_docking]

        docked = []
        for c in top:
            try:
                result = clients.diffdock.dock_smiles(
                    protein_pdb_path=config.pocket.complex_pdb,
                    smiles=c.value,
                    num_poses=cfg.diffdock_num_poses,
                )
                confidence = float(result.get("confidence", 0.0)) if isinstance(result, dict) else 0.0
                docked.append(CandidateRecord(
                    candidate_id=c.candidate_id, arm=self.name,
                    value=c.value, source=c.source,
                    features={**c.features, "dock_confidence": confidence, "dock_success": 1.0},
                ))
            except Exception as exc:
                errors.append(f"DiffDock({c.candidate_id}): {exc}")
                docked.append(CandidateRecord(
                    candidate_id=c.candidate_id, arm=self.name,
                    value=c.value, source=c.source,
                    features={**c.features, "dock_confidence": 0.0, "dock_success": 0.0},
                ))

        status = RunStatus.SUCCESS if not errors else RunStatus.PARTIAL
        return ArmResult(
            arm=self.name, run_id=run_id, status=status,
            started_at=started, finished_at=datetime.utcnow(),
            config_hash=config_hash(config),
            candidates=docked, errors=errors, warnings=warnings,
            features={"total_generated": float(len(candidates)), "total_docked": float(len(docked))},
        )


class Arm2FlexPepRunner(ArmRunner):
    name = ArmName.FLEXPEP

    def run(self, config: SiloAConfig, clients: NimClientBundle) -> ArmResult:
        cfg = config.arm2
        run_id = self._make_run_id()
        started = datetime.utcnow()
        candidates = []
        errors = []
        warnings = []

        if not cfg.enabled:
            return ArmResult(
                arm=self.name, run_id=run_id, status=RunStatus.SKIPPED,
                started_at=started, finished_at=datetime.utcnow(),
                config_hash=config_hash(config),
            )

        docking_runner = None
        complex_relaxer = None

        if cfg.use_pyrosetta and cfg.complex_pdb:
            try:
                from pipelines.silo_b.src.docking import PyRosettaDockingRunner
                docking_runner = PyRosettaDockingRunner(
                    complex_pdb_path=cfg.complex_pdb,
                )
            except ImportError:
                warnings.append("PyRosetta not available for docking, using sequence analysis only")
            except Exception as exc:
                errors.append(f"Failed to init PyRosettaDockingRunner: {exc}")

            if docking_runner and cfg.relax_after_dock:
                try:
                    from pipelines.silo_b.src.relax import PyRosettaComplexRelaxer
                    complex_relaxer = PyRosettaComplexRelaxer(
                        complex_pdb_path=cfg.complex_pdb,
                        peptide_chain=cfg.peptide_chain,
                        disulfide_positions=tuple(cfg.disulfide_positions),
                        pharmacophore_positions=tuple(cfg.pharmacophore_positions),
                    )
                except Exception as exc:
                    warnings.append(f"Complex relaxer unavailable, skipping relax: {exc}")
        elif cfg.use_pyrosetta and not cfg.complex_pdb:
            warnings.append("complex_pdb not set; PyRosetta docking disabled")

        for variant in cfg.variants:
            if len(variant.sequence) != len(cfg.wildtype):
                errors.append(
                    f"Length mismatch: {variant.name} "
                    f"({len(variant.sequence)}) != wildtype ({len(cfg.wildtype)})"
                )
                continue

            mutations = [
                f"{wt}{i+1}{mt}"
                for i, (wt, mt) in enumerate(zip(cfg.wildtype, variant.sequence))
                if wt != mt
            ]

            features: dict[str, float] = {"mutation_count": float(len(mutations))}

            if docking_runner:
                dock_result = docking_runner.dock_candidate(
                    variant.sequence, receptor_pdb=cfg.complex_pdb
                )
                features["delta_energy"] = dock_result.dg if dock_result.success else 0.0
                features["dock_success"] = 1.0 if dock_result.success else 0.0
                features["dock_wall_time"] = dock_result.wall_time_s

                if dock_result.success and complex_relaxer:
                    relax_result = complex_relaxer.relax(variant.sequence, docked_pose_tag="")
                    if relax_result.success:
                        features["delta_energy"] = relax_result.relaxed_dg
                        features["clash_score"] = relax_result.clash_score
                        features["interface_energy"] = relax_result.interface_energy
                        features["backbone_rmsd"] = relax_result.backbone_rmsd
                        features["relax_wall_time"] = relax_result.wall_time_s
                    else:
                        warnings.append(f"Relax failed for {variant.name}: {relax_result.error_msg}")
                elif not dock_result.success:
                    warnings.append(f"Docking failed for {variant.name}: {dock_result.error_msg}")
            else:
                features["dock_success"] = 0.0

            candidates.append(CandidateRecord(
                candidate_id=uuid.uuid4().hex[:12],
                arm=self.name, value=variant.sequence,
                source=variant.name, features=features,
            ))

        status = RunStatus.SUCCESS if not errors else RunStatus.PARTIAL
        return ArmResult(
            arm=self.name, run_id=run_id, status=status,
            started_at=started, finished_at=datetime.utcnow(),
            config_hash=config_hash(config),
            candidates=candidates, errors=errors, warnings=warnings,
        )


class Arm3DeNovoRunner(ArmRunner):
    name = ArmName.DENOVO

    def run(self, config: SiloAConfig, clients: NimClientBundle) -> ArmResult:
        cfg = config.arm3
        run_id = self._make_run_id()
        started = datetime.utcnow()
        candidates = []
        errors = []

        if not cfg.enabled:
            return ArmResult(
                arm=self.name, run_id=run_id, status=RunStatus.SKIPPED,
                started_at=started, finished_at=datetime.utcnow(),
                config_hash=config_hash(config),
            )

        backbones = []
        for i in range(cfg.num_designs):
            try:
                result = clients.rfdiffusion.design_binder(
                    pdb_path=config.pocket.complex_pdb,
                    contigs="B1-369/0 10-30",
                    hotspot_res=[],
                    diffusion_steps=cfg.diffusion_steps,
                    random_seed=config.seed + i,
                )
                pdb = result.get("output_pdb", "")
                if pdb:
                    backbones.append((i, pdb))
            except Exception as exc:
                errors.append(f"RFdiffusion(design_{i}): {exc}")

        designed_seqs = []
        for idx, pdb_content in backbones:
            try:
                result = clients.proteinmpnn.predict(
                    input_pdb=pdb_content,
                    num_seq_per_target=cfg.seqs_per_backbone,
                    sampling_temp=0.2,
                )
                sequences = []
                if isinstance(result, dict):
                    raw = result.get("sequences", result.get("output", ""))
                    if isinstance(raw, str):
                        entries = clients.proteinmpnn.parse_fasta(raw)
                        sequences = [e["sequence"] for e in entries]
                    elif isinstance(raw, list):
                        sequences = raw
                for j, seq in enumerate(sequences):
                    designed_seqs.append((idx, j, seq))
            except Exception as exc:
                errors.append(f"ProteinMPNN(bb_{idx}): {exc}")

        for bb_idx, seq_idx, seq in designed_seqs:
            try:
                result = clients.esmfold.predict(seq)
                plddt = None
                if isinstance(result, dict):
                    plddt = result.get("mean_plddt", result.get("plddt"))
                if isinstance(plddt, (list, tuple)):
                    plddt = sum(plddt) / len(plddt) if plddt else 0.0
                if plddt is None:
                    continue
                plddt = float(plddt)

                if plddt >= cfg.plddt_threshold:
                    candidates.append(CandidateRecord(
                        candidate_id=uuid.uuid4().hex[:12],
                        arm=self.name, value=seq,
                        source=f"bb{bb_idx:02d}_seq{seq_idx}",
                        features={"plddt": plddt},
                    ))
            except Exception as exc:
                errors.append(f"ESMFold(bb{bb_idx}_seq{seq_idx}): {exc}")

        status = RunStatus.SUCCESS if not errors else RunStatus.PARTIAL
        return ArmResult(
            arm=self.name, run_id=run_id, status=status,
            started_at=started, finished_at=datetime.utcnow(),
            config_hash=config_hash(config),
            candidates=candidates, errors=errors,
            features={"backbones": float(len(backbones)), "designed_seqs": float(len(designed_seqs))},
        )
