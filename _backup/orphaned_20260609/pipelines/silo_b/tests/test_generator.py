from pathlib import Path

import pytest
from pipelines.silo_b.src.config import load_config
from pipelines.silo_b.src.constraint_compiler import ConstraintCompiler
from pipelines.silo_b.src.generator import MutantGenerator
import yaml


def _small_config(path: Path, position_options: dict[int, list[str]], low_space_threshold: int = 8) -> Path:
    cfg = {
        "pipeline_name": "test_silo_b_generator",
        "config_version": "test",
        "schema_version": 1,
        "created_utc": "2026-02-20T00:00:00Z",
        "seed": 20260220,
        "sequence_metadata": {
            "peptide": {
                "name": "TEST",
                "template_sequence": "ACDEFG",
                "length": 6,
                "chain_id": "A",
                "n_terminal_modification": "free_amino",
                "c_terminal_modification": "free_carboxyl",
                "source": "unit_test",
            },
            "receptor": {
                "name": "REC",
                "organism": "human",
                "uniprot": "X0",
                "sequence_length": 100,
                "binding_mode_hint": "pocket",
            },
            "disulfides": [],
            "chain_info": {"cysteine_positions": [], "cysteine_locked": False},
            "pharmacophore": {"motif_name": "", "positions": [], "residues": {}, "mode": "none"},
        },
        "constraints": {
            "frozen_positions": [2],
            "per_position_allowed_aas": {
                1: ["A", "G"],
                2: ["C"],
                3: ["D", "E"],
                4: ["E"],
                5: ["W"],
                6: ["G"],
            },
            "pairwise_rules": [],
            "pharmacophore": {"require_positions": [], "required_residues": {}, "preserve_geometry": False, "max_sidechain_shift_rmsd_ao": 1.0},
        },
        "generator": {
            "strategy": {
                "primary": "ga_bo",
                "fallback": {
                    "low_space_threshold": low_space_threshold,
                    "low_density_threshold": 0.5,
                    "fallback_primary": "sampling",
                    "fallback_secondary": "sampling",
                },
            },
            "budget": {
                "total_candidates": 16,
                "adaptive_rounds": 1,
                "per_round_max": 16,
                "approach_b_allocation_ratio": 0.5,
                "approach_a_allocation_ratio": 0.5,
            },
            "diversity_policy": {
                "min_hamming_distance": 1,
                "max_seq_identity": 0.95,
                "ngram_diversity_weight": 0.1,
                "cluster_before_docking": False,
                "cluster_max_size": 256,
            },
            "mutation": {
                "mutation_rate": 0.30,
                "mutation_mode": "position_uniform",
                "preserve_motif": True,
            },
            "approach_b": {"enabled": False, "docking_timeout_sec": 10, "batch_size": 4, "max_fail_retries": 1, "api": {"provider": "", "endpoint_env": ""}},
            "approach_a": {"enabled": False, "trigger": {"gate2_pass_top_k": 1, "min_docking_z": -1.0, "min_diversity_gap": 0.1}, "timeout_sec_per_candidate": 10, "batch_size": 1},
        },
        "validation": {
            "drugability_filters": {
                "enabled": True,
                "max_molecular_weight": 2000,
                "min_logp": -1.0,
                "max_logp": 5.0,
                "max_positive_charge": 5,
                "min_topology_stability_score": 0.0,
                "max_hydrophobic_fragment_ratio": 1.0,
            },
            "structure": {
                "require_disulfide_geometry": False,
                "max_steric_clash": 0.5,
                "max_backbone_rmsd_to_template": 5.0,
            },
            "dedupe": {
                "enabled": True,
                "sequence_identity_threshold": 0.5,
                "keep_top_by_identity": 1,
                "torsion_fingerprint_kl_threshold": 0.0,
                "near_neighbour_window": 1,
            },
        },
        "scoring": {
            "primary": {
                "docking_delta_g": {"weight": 0.45, "goal": "minimize", "clip": {"min": -10.0, "max": 0.0}},
                "stability": {"weight": 0.20, "goal": "maximize", "source": "pRosetta", "clip": {"min": -10.0, "max": 10.0}},
            },
            "auxiliary": {
                "druggability": {"weight": 0.15, "goal": "maximize", "source": "rule", "clip": {"min": 0.0, "max": 1.0}},
                "diversity": {"weight": 0.10, "goal": "maximize", "source": "hamming", "clip": {"min": 0.0, "max": 1.0}},
                "hil_confidence": {"weight": 0.10, "goal": "maximize", "source": "hil", "clip": {"min": 0.0, "max": 1.0}},
            },
            "penalties": {"hard_violation": 2.0, "soft_violation_per_rule": 0.5, "duplicate_penalty": 0.1},
            "normalization": {"method": "minmax", "epsilon": 1e-8},
        },
        "orchestration": {
            "batch_size": {"generation": 16, "docking": 4, "approach_a": 1},
            "adaptive_steps": 1,
            "stop_criteria": {"min_candidates_for_gate2": 1, "min_gate2_ratio": 0.1, "max_wallclock_hours": 1},
            "hil_gates": {
                "gate_1": {"enabled": True},
                "gate_2": {"enabled": True},
                "gate_3": {"enabled": True},
            },
            "seed_lineage": {"base_seed": 20260220, "stage_seeds": {}},
            "output": {
                "manifest_path": "outputs/manifest.json",
                "candidates_path": "outputs/candidates",
                "logs_path": "outputs/logs",
                "checkpoint_interval": 100,
            },
        },
    }
    cfg["constraints"]["per_position_allowed_aas"].update(position_options)
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return path


def test_enumerate_small_space(tmp_path: Path) -> None:
    cfg_path = _small_config(tmp_path / "small.yaml", {})
    compiler = ConstraintCompiler(load_config(cfg_path))
    compiled = compiler.compile()
    generator = MutantGenerator(compiled, load_config(cfg_path))

    all_variants = generator.enumerate_all()
    assert len(all_variants) == 4
    assert len(set(all_variants)) == 4
    assert all(compiler.validate_sequence(v).valid for v in all_variants)


def test_sample_diverse(tmp_path: Path) -> None:
    cfg_path = _small_config(tmp_path / "sample.yaml", {})
    cfg = load_config(cfg_path)
    compiler = ConstraintCompiler(cfg)
    compiled = compiler.compile()
    generator = MutantGenerator(compiled, cfg)

    candidates = generator.sample_diverse(3, seed=12345)
    assert len(candidates) == 3
    assert len(set(candidates)) == 3
    assert all(len(c) == len(cfg.sequence_metadata.peptide.template_sequence) for c in candidates)
    assert all(compiler.validate_sequence(c).valid for c in candidates)


def test_strategy_selection(tmp_path: Path) -> None:
    cfg_path = _small_config(
        tmp_path / "strategy_small.yaml",
        position_options={1: ["A"], 5: ["Y"]},
        low_space_threshold=10,
    )
    cfg_small = load_config(cfg_path)
    generator_small = MutantGenerator(ConstraintCompiler(cfg_small).compile(), cfg_small)
    assert generator_small.strategy == MutantGenerator.STRATEGY_ENUMERATE

    cfg_path_large = _small_config(
        tmp_path / "strategy_large.yaml",
        position_options={1: ["A", "G", "N"], 3: ["D", "E", "K"], 5: ["W", "Y", "L"]},
        low_space_threshold=4,
    )
    cfg_large = load_config(cfg_path_large)
    generator_large = MutantGenerator(ConstraintCompiler(cfg_large).compile(), cfg_large)
    assert generator_large.strategy == MutantGenerator.STRATEGY_SAMPLE
