from __future__ import annotations


def test_run_approach_b_uses_reference_peptide_sequence_when_seed_missing():
    from pipeline_local.steps.step03b_blosum_mutation import run_approach_b

    result = run_approach_b(
        {
            "reference_peptide": {"sequence": "VVVVVVVVVVVVVV"},
            "approach_b": {
                "fixed_positions": {3: "V", 7: "V", 8: "V", 9: "V", 10: "V", 14: "V"},
                "max_variants": 0,
            },
        }
    )

    assert result.seed_sequence == "VVVVVVVVVVVVVV"
