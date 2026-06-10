from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, model_validator


class SeedMolecule(BaseModel):
    name: str
    smiles: str
    source: str = ""

    model_config = {"extra": "forbid"}


class PeptideVariant(BaseModel):
    name: str
    sequence: str
    description: str = ""

    model_config = {"extra": "forbid"}


class PocketConfig(BaseModel):
    complex_pdb: str
    ligand_chain: str = "A"
    receptor_chain: str = "B"
    cutoff_angstrom: float = 5.0

    model_config = {"extra": "forbid"}


class Arm1Config(BaseModel):
    enabled: bool = True
    seed_molecules: List[SeedMolecule]
    molmim_num_molecules: int = 10
    molmim_algorithm: str = "CMA-ES"
    molmim_property: str = "QED"
    molmim_min_similarity: float = 0.3
    top_k_for_docking: int = 15
    diffdock_num_poses: int = 5

    model_config = {"extra": "forbid"}


class Arm2Config(BaseModel):
    enabled: bool = True
    wildtype: str
    variants: List[PeptideVariant]
    use_pyrosetta: bool = True
    complex_pdb: str = ""
    peptide_chain: str = "B"
    relax_after_dock: bool = True
    disulfide_positions: List[int] = []
    pharmacophore_positions: List[int] = []

    model_config = {"extra": "forbid"}


class Arm3Config(BaseModel):
    enabled: bool = True
    num_designs: int = 5
    seqs_per_backbone: int = 4
    plddt_threshold: float = 70.0
    diffusion_steps: int = 50

    model_config = {"extra": "forbid"}


class ScoringWeights(BaseModel):
    qed: float = 0.15
    dock_confidence: float = 0.35
    delta_energy: float = 0.25
    plddt: float = 0.15
    diversity: float = 0.10

    model_config = {"extra": "forbid"}


class ScoringConfig(BaseModel):
    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    normalization: str = "minmax"
    epsilon: float = 1e-8

    model_config = {"extra": "forbid"}


class OutputConfig(BaseModel):
    root: str = "outputs/silo_a"
    manifest_name: str = "run_manifest.json"
    checkpoint_interval: int = 300

    model_config = {"extra": "forbid"}


class SiloAConfig(BaseModel):
    pipeline_name: str = "silo_a_sstr2_virtual_screening"
    config_version: str = "v1.0.0"
    seed: int = 20260220

    pocket: PocketConfig
    arm1: Arm1Config
    arm2: Arm2Config
    arm3: Arm3Config
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    model_config = {"extra": "forbid"}


def load_config(yaml_path: str | Path) -> SiloAConfig:
    text = Path(yaml_path).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("Config root must be a mapping")
    return SiloAConfig.model_validate(data)


def config_hash(cfg: SiloAConfig) -> str:
    canonical = yaml.dump(cfg.model_dump(), sort_keys=True)
    return sha256(canonical.encode()).hexdigest()
