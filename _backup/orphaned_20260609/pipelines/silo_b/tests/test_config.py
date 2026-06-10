from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from pipelines.silo_b.src.config import MutationConfig, config_hash, load_config


CFG_PATH = Path("pipelines/silo_b/configs/sst14_mutation_default.yaml")


def test_load_default_config() -> None:
    config = load_config(CFG_PATH)
    assert isinstance(config, MutationConfig)
    assert config.sequence_metadata.peptide.name == "SST-14"


def test_config_hash_deterministic() -> None:
    config1 = load_config(CFG_PATH)
    config2 = load_config(CFG_PATH)
    assert config_hash(config1) == config_hash(config2)


def test_frozen_positions_validated() -> None:
    config = load_config(CFG_PATH)
    assert sorted(config.sequence_metadata.chain_info.cysteine_positions) == [3, 14]
    assert config.constraints.frozen_positions == [3, 14]


def test_pharmacophore_positions() -> None:
    config = load_config(CFG_PATH)
    assert config.sequence_metadata.pharmacophore.positions == [7, 8, 9, 10]
    assert config.sequence_metadata.pharmacophore.residues[7] == "F"
    assert config.sequence_metadata.pharmacophore.residues[8] == "W"
    assert config.sequence_metadata.pharmacophore.residues[9] == "K"
    assert config.sequence_metadata.pharmacophore.residues[10] == "T"


def test_invalid_yaml_rejected(tmp_path: Path) -> None:
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text(
        "pipeline_name: bad\n"
        "config_version: v1\n"
        "schema_version: 1\n"
        "created_utc: now\n"
        "seed: 1\n"
        "sequence_metadata: {}\n"
    )
    with pytest.raises(ValidationError):
        load_config(invalid_yaml)
