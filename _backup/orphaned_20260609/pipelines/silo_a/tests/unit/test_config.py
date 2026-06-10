from pathlib import Path

import pytest
from pydantic import ValidationError

from pipelines.silo_a.src.config import SiloAConfig, config_hash, load_config

CFG_PATH = Path("pipelines/silo_a/configs/sstr2_a_default.yaml")


def test_load_default_config() -> None:
    cfg = load_config(CFG_PATH)
    assert isinstance(cfg, SiloAConfig)
    assert cfg.pipeline_name == "silo_a_sstr2_virtual_screening"


def test_config_hash_deterministic() -> None:
    h1 = config_hash(load_config(CFG_PATH))
    h2 = config_hash(load_config(CFG_PATH))
    assert h1 == h2


def test_arm1_seed_molecules() -> None:
    cfg = load_config(CFG_PATH)
    assert len(cfg.arm1.seed_molecules) >= 3
    names = {m.name for m in cfg.arm1.seed_molecules}
    assert "Paltusotine" in names


def test_arm2_variants() -> None:
    cfg = load_config(CFG_PATH)
    assert cfg.arm2.wildtype == "AGCKNFFWKTFTSC"
    assert len(cfg.arm2.variants) >= 10
    for v in cfg.arm2.variants:
        assert len(v.sequence) == 14


def test_arm3_plddt_threshold() -> None:
    cfg = load_config(CFG_PATH)
    assert cfg.arm3.plddt_threshold >= 70.0


def test_scoring_weights_sum_to_one() -> None:
    cfg = load_config(CFG_PATH)
    w = cfg.scoring.weights
    total = w.qed + w.dock_confidence + w.delta_energy + w.plddt + w.diversity
    assert abs(total - 1.0) < 1e-6
