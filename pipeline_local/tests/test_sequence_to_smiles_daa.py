from __future__ import annotations

import pytest

from pipeline_local.scripts.sequence_to_smiles_daa import (
    parse_sequence,
    sequence_to_smiles_daa,
)


SST14 = "AGCKNFFWKTFTSC"


def test_l_ala_smiles_uses_at_h() -> None:
    result = sequence_to_smiles_daa("A")
    assert result["smiles"] == "N[C@H](C)C(=O)O"
    assert result["daa_count"] == 0


def test_d_ala_smiles_uses_double_at_h() -> None:
    result = sequence_to_smiles_daa("a")
    assert result["smiles"] == "N[C@@H](C)C(=O)O"
    assert result["daa_count"] == 1


def test_sst14_standard_has_no_daa() -> None:
    result = sequence_to_smiles_daa(SST14)
    assert result["total_residues"] == 14
    assert result["daa_count"] == 0
    assert result["sequence"] == SST14


def test_octreotide_style_d_phe_detected_from_lowercase() -> None:
    result = sequence_to_smiles_daa("fCFwKTCT")
    assert result["daa_count"] == 2
    assert "N[C@@H](Cc1ccccc1)C(=O)" in result["smiles"]


def test_d_trp_single_residue() -> None:
    result = sequence_to_smiles_daa("w")
    assert result["smiles"] == "N[C@@H](Cc1c[nH]c2ccccc12)C(=O)O"
    assert result["daa_count"] == 1


def test_mixed_l_d_l_chain() -> None:
    result = sequence_to_smiles_daa("AfG")
    assert result["smiles"] == "N[C@H](C)C(=O)N[C@@H](Cc1ccccc1)C(=O)NCC(=O)O"
    assert result["daa_count"] == 1
    assert result["total_residues"] == 3


def test_length_14_peptide() -> None:
    result = sequence_to_smiles_daa("AGckNFFWKTFTSC")
    assert result["total_residues"] == 14
    assert result["daa_count"] == 2


def test_bracketed_d_cys_token() -> None:
    residues = parse_sequence("AG[D-Cys]K")
    assert [residue.code for residue in residues] == ["A", "G", "C", "K"]
    assert residues[2].is_d is True


def test_bracketed_d_phe_smiles() -> None:
    result = sequence_to_smiles_daa("A[D-Phe]G")
    assert "N[C@@H](Cc1ccccc1)C(=O)" in result["smiles"]
    assert result["daa_count"] == 1


def test_cys_disulfide_applied_for_sst14_pair() -> None:
    result = sequence_to_smiles_daa(SST14)
    assert result["smiles"].count("CS1") == 2
    assert any("disulfide" in warning for warning in result["warnings"])


def test_no_disulfide_option_leaves_free_cys_side_chains() -> None:
    result = sequence_to_smiles_daa("ACG", disulfide=False)
    assert "CS1" not in result["smiles"]
    assert "N[C@H](CS)C(=O)" in result["smiles"]


def test_rdkit_can_parse_generated_smiles() -> None:
    Chem = pytest.importorskip("rdkit.Chem")
    result = sequence_to_smiles_daa("AGckNFFWKTFTSC")
    mol = Chem.MolFromSmiles(result["smiles"])
    assert mol is not None


def test_empty_input_raises() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        sequence_to_smiles_daa("")


def test_invalid_amino_acid_raises() -> None:
    with pytest.raises(ValueError, match="invalid amino acid"):
        sequence_to_smiles_daa("AX")
