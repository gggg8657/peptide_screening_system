from pathlib import Path

import yaml
import pytest

from pipelines.silo_b.src.config import load_config
from pipelines.silo_b.src.scoring import MultiObjectiveScorer


def _scoring_config(path: Path) -> object:
    cfg = {
        "pipeline_name": "test_silo_b_scoring",
        "config_version": "test",
        "schema_version": 1,
        "created_utc": "2026-02-20T00:00:00Z",
        "seed": 1,
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
            "frozen_positions": [],
            "per_position_allowed_aas": {1: ["A"]},
            "pairwise_rules": [],
            "pharmacophore": {"require_positions": [], "required_residues": {}, "preserve_geometry": False, "max_sidechain_shift_rmsd_ao": 1.0},
        },
        "generator": {
            "strategy": {
                "primary": "ga_bo",
                "fallback": {
                    "low_space_threshold": 10,
                    "low_density_threshold": 0.5,
                    "fallback_primary": "sampling",
                    "fallback_secondary": "sampling",
                },
            },
            "budget": {
                "total_candidates": 1,
                "adaptive_rounds": 1,
                "per_round_max": 1,
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
            "mutation": {"mutation_rate": 0.3, "mutation_mode": "position_uniform", "preserve_motif": True},
            "approach_b": {"enabled": False, "docking_timeout_sec": 10, "batch_size": 1, "max_fail_retries": 1, "api": {"provider": "", "endpoint_env": ""}},
            "approach_a": {"enabled": False, "trigger": {"gate2_pass_top_k": 1, "min_docking_z": -1.0, "min_diversity_gap": 0.1}, "timeout_sec_per_candidate": 10, "batch_size": 1},
        },
        "validation": {
            "drugability_filters": {"enabled": True, "max_molecular_weight": 2000, "min_logp": -1.0, "max_logp": 5.0, "max_positive_charge": 5, "min_topology_stability_score": 0.0, "max_hydrophobic_fragment_ratio": 1.0},
            "structure": {"require_disulfide_geometry": False, "max_steric_clash": 0.5, "max_backbone_rmsd_to_template": 5.0},
            "dedupe": {"enabled": True, "sequence_identity_threshold": 0.5, "keep_top_by_identity": 1, "torsion_fingerprint_kl_threshold": 0.0, "near_neighbour_window": 1},
        },
        "scoring": {
            "primary": {
                "docking_delta_g": {"weight": 0.5, "goal": "minimize", "clip": {"min": -10.0, "max": 0.0}},
                "stability": {"weight": 0.2, "goal": "maximize", "source": "pRosetta", "clip": {"min": 0.0, "max": 10.0}},
            },
            "auxiliary": {
                "druggability": {"weight": 0.15, "goal": "maximize", "source": "rule", "clip": {"min": 0.0, "max": 1.0}},
                "diversity": {"weight": 0.1, "goal": "maximize", "source": "hamming", "clip": {"min": 0.0, "max": 1.0}},
                "hil_confidence": {"weight": 0.05, "goal": "maximize", "source": "hil", "clip": {"min": 0.0, "max": 1.0}},
            },
            "penalties": {"hard_violation": 10.0, "soft_violation_per_rule": 1.0, "duplicate_penalty": 0.0},
            "normalization": {"method": "minmax", "epsilon": 1e-8},
        },
        "orchestration": {
            "batch_size": {"generation": 1, "docking": 1, "approach_a": 1},
            "adaptive_steps": 1,
            "stop_criteria": {"min_candidates_for_gate2": 1, "min_gate2_ratio": 0.1, "max_wallclock_hours": 1},
            "hil_gates": {"gate_1": {"enabled": True}, "gate_2": {"enabled": True}, "gate_3": {"enabled": True}},
            "seed_lineage": {"base_seed": 1, "stage_seeds": {}},
            "output": {"manifest_path": "outputs/manifest.json", "candidates_path": "outputs/candidates", "logs_path": "outputs/logs", "checkpoint_interval": 100},
        },
    }
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return load_config(path)


def test_normalize(tmp_path: Path) -> None:
    cfg = _scoring_config(tmp_path / "scoring.yaml")
    scorer = MultiObjectiveScorer(cfg.scoring)
    assert scorer.normalize(5.0, 0.0, 10.0) == pytest.approx(0.5)
    assert scorer.normalize(-5.0, -10.0, 0.0) == pytest.approx(0.5)
    assert scorer.normalize(-11.0, -10.0, 0.0) == pytest.approx(0.0)
    assert scorer.normalize(11.0, -10.0, 0.0) == pytest.approx(1.0)


def test_score_candidate(tmp_path: Path) -> None:
    cfg = _scoring_config(tmp_path / "scoring.yaml")
    scorer = MultiObjectiveScorer(cfg.scoring)
    score = scorer.score_candidate(
        dg=-5.0,
        stability=8.0,
        druggability=0.6,
        diversity=0.8,
        hil_confidence=0.3,
        hard_violations=1,
        soft_violations=1,
    )
    expected = (
        0.5 * 0.5
        + 0.2 * 0.8
        + 0.15 * 0.6
        + 0.1 * 0.8
        + 0.05 * 0.3
        - 10.0
        - 1.0
    )
    assert score == pytest.approx(expected)


def test_rank_candidates(tmp_path: Path) -> None:
    cfg = _scoring_config(tmp_path / "scoring.yaml")
    scorer = MultiObjectiveScorer(cfg.scoring)
    candidates = [
        {"sequence": "AAA", "dg": -1.0, "stability": 5.0, "druggability": 0.8, "diversity": 0.2, "hil_confidence": 0.4, "hard_violations": 0, "soft_violations": 0},
        {"sequence": "CCC", "dg": -5.0, "stability": 2.0, "druggability": 0.2, "diversity": 0.9, "hil_confidence": 0.6, "hard_violations": 0, "soft_violations": 0},
    ]
    ranked = scorer.rank_candidates(candidates)
    assert len(ranked) == 2
    assert ranked[0]["sequence"] == "CCC"
    assert ranked[1]["sequence"] == "AAA"
