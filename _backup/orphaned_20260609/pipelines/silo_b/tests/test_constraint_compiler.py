from pathlib import Path

from pipelines.silo_b.src.config import load_config
from pipelines.silo_b.src.constraint_compiler import ConstraintCompiler

CFG_PATH = Path("pipelines/silo_b/configs/sst14_mutation_default.yaml")


def _make_mutable_variant() -> str:
    return "AGCKNFFWKTFTSC"


def test_design_space_size() -> None:
    compiler = ConstraintCompiler(load_config(CFG_PATH))
    compiler.compile()
    assert compiler.compute_design_space_size() == 19**7 * 18  # 7 positions×19 AA + pos11×18 AA


def test_mutable_positions() -> None:
    compiler = ConstraintCompiler(load_config(CFG_PATH))
    compiler.compile()
    assert compiler.get_mutable_positions() == [1, 2, 4, 5, 6, 11, 12, 13]


def test_validate_wildtype() -> None:
    compiler = ConstraintCompiler(load_config(CFG_PATH))
    compiler.compile()
    result = compiler.validate_sequence(_make_mutable_variant())
    assert result.valid
    assert not result.hard_violations
    assert result.penalty_score == 0.0


def test_validate_cys_violation() -> None:
    compiler = ConstraintCompiler(load_config(CFG_PATH))
    compiler.compile()
    seq = list(_make_mutable_variant())
    seq[2] = "A"
    mutated = "".join(seq)
    result = compiler.validate_sequence(mutated)
    assert not result.valid
    assert any("pos_3" in violation for violation in result.hard_violations)


def test_validate_pharmacophore_violation() -> None:
    compiler = ConstraintCompiler(load_config(CFG_PATH))
    compiler.compile()
    seq = list(_make_mutable_variant())
    seq[6] = "A"  # pos7
    mutated = "".join(seq)
    result = compiler.validate_sequence(mutated)
    assert not result.valid
    assert any("pharmacophore" in violation for violation in result.hard_violations)


def test_pairwise_hydrophobic_guard() -> None:
    compiler = ConstraintCompiler(load_config(CFG_PATH))
    compiler.compile()
    seq = list(_make_mutable_variant())
    seq[4] = "F"  # pos5
    seq[5] = "F"  # pos6
    mutated = "".join(seq)
    result = compiler.validate_sequence(mutated)
    assert not result.valid
    assert any("pairwise_hard" in violation for violation in result.hard_violations)
