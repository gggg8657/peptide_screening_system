"""D-AA aware peptide sequence to SMILES utility.

This module intentionally avoids ``RDKit.MolFromSequence`` because RDKit's
sequence parser accepts the standard uppercase protein alphabet and drops
mixed D-amino-acid training examples such as ``AGckNFFWKTFTSC``.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Iterable


AA_3_TO_1: dict[str, str] = {
    "Ala": "A",
    "Arg": "R",
    "Asn": "N",
    "Asp": "D",
    "Cys": "C",
    "Gln": "Q",
    "Glu": "E",
    "Gly": "G",
    "His": "H",
    "Ile": "I",
    "Leu": "L",
    "Lys": "K",
    "Met": "M",
    "Phe": "F",
    "Pro": "P",
    "Ser": "S",
    "Thr": "T",
    "Trp": "W",
    "Tyr": "Y",
    "Val": "V",
}

AA_1_TO_3: dict[str, str] = {value: key for key, value in AA_3_TO_1.items()}
VALID_AA = set(AA_1_TO_3)

# Side chain fragments attached as the alpha-carbon branch.
SIDE_CHAINS: dict[str, str | None] = {
    "A": "C",
    "R": "CCCNC(=N)N",
    "N": "CC(=O)N",
    "D": "CC(=O)O",
    "C": "CS",
    "Q": "CCC(=O)N",
    "E": "CCC(=O)O",
    "G": None,
    "H": "Cc1cnc[nH]1",
    "I": "C(C)CC",
    "L": "CC(C)C",
    "K": "CCCCN",
    "M": "CCSC",
    "F": "Cc1ccccc1",
    "P": None,
    "S": "CO",
    "T": "C(O)C",
    "W": "Cc1c[nH]c2ccccc12",
    "Y": "Cc1ccc(O)cc1",
    "V": "C(C)C",
}


@dataclass(frozen=True)
class Residue:
    code: str
    is_d: bool
    source: str


def parse_sequence(sequence: str) -> list[Residue]:
    """Parse uppercase L-AA, lowercase D-AA, and bracketed D-AA tokens."""
    if not sequence or not sequence.strip():
        raise ValueError("sequence must not be empty")

    residues: list[Residue] = []
    i = 0
    raw = sequence.strip()
    while i < len(raw):
        char = raw[i]
        if char.isspace() or char in "-_":
            i += 1
            continue

        if char == "[":
            end = raw.find("]", i + 1)
            if end == -1:
                raise ValueError(f"unterminated bracket token at position {i + 1}")
            token = raw[i + 1 : end]
            residues.append(_parse_bracket_token(token))
            i = end + 1
            continue

        if char.isalpha() and len(char) == 1:
            code = char.upper()
            if code not in VALID_AA:
                raise ValueError(f"invalid amino acid '{char}' at position {i + 1}")
            residues.append(Residue(code=code, is_d=char.islower(), source=char))
            i += 1
            continue

        raise ValueError(f"invalid sequence token '{char}' at position {i + 1}")

    if not residues:
        raise ValueError("sequence must contain at least one residue")
    return residues


def sequence_to_smiles_daa(sequence: str, *, disulfide: bool = True) -> dict[str, object]:
    """Convert a mixed L/D peptide sequence into a linear peptide SMILES.

    L residues use ``N[C@H](side)C(=O)`` and D residues use
    ``N[C@@H](side)C(=O)``. Gly is emitted without a chiral center. When
    ``disulfide`` is true, the first two Cys residues are connected as a
    simple S-S ring closure.
    """
    residues = parse_sequence(sequence)
    warnings: list[str] = []
    cys_indices = [idx for idx, residue in enumerate(residues) if residue.code == "C"]
    disulfide_pair = set(cys_indices[:2]) if disulfide and len(cys_indices) >= 2 else set()

    if disulfide_pair:
        warnings.append(
            "Cys disulfide applied between the first two Cys residues as an S-S ring closure."
        )
    elif len(cys_indices) == 1:
        warnings.append("Single Cys residue detected; disulfide bond not applied.")

    if len(cys_indices) > 2:
        warnings.append("More than two Cys residues detected; only the first pair was linked.")

    fragments = [
        _residue_fragment(residue, is_terminal=(idx == len(residues) - 1), cys_ring=(idx in disulfide_pair))
        for idx, residue in enumerate(residues)
    ]
    smiles = "".join(fragments)

    return {
        "sequence": sequence,
        "smiles": smiles,
        "daa_count": sum(1 for residue in residues if residue.is_d and residue.code != "G"),
        "total_residues": len(residues),
        "warnings": warnings,
    }


def _parse_bracket_token(token: str) -> Residue:
    parts = token.split("-", 1)
    if len(parts) != 2 or parts[0] not in {"D", "L"}:
        raise ValueError(f"unsupported bracket token '[{token}]'; expected [D-Phe] or [L-Phe]")

    stereo, aa_name = parts
    normalized = aa_name[:1].upper() + aa_name[1:].lower()
    code = AA_3_TO_1.get(normalized)
    if code is None:
        raise ValueError(f"unsupported amino acid in bracket token '[{token}]'")
    return Residue(code=code, is_d=(stereo == "D"), source=f"[{token}]")


def _residue_fragment(residue: Residue, *, is_terminal: bool, cys_ring: bool) -> str:
    suffix = "C(=O)O" if is_terminal else "C(=O)"

    if residue.code == "G":
        return f"NCC(=O){'O' if is_terminal else ''}"

    if residue.code == "P":
        alpha_tag = "@@H" if residue.is_d else "@H"
        return f"N1CCC[C{alpha_tag}]1{suffix}"

    side_chain = "CS1" if residue.code == "C" and cys_ring else SIDE_CHAINS[residue.code]
    alpha_tag = "@@H" if residue.is_d else "@H"
    return f"N[C{alpha_tag}]({side_chain}){suffix}"


def convert_many(sequences: Iterable[str]) -> list[dict[str, object]]:
    return [sequence_to_smiles_daa(sequence) for sequence in sequences]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate D-AA aware peptide SMILES.")
    parser.add_argument("--sequence", required=True, help="Peptide sequence, e.g. AGckNFFWKTFTSC")
    parser.add_argument(
        "--no-disulfide",
        action="store_true",
        help="Do not auto-link the first two Cys residues with an S-S bond.",
    )
    args = parser.parse_args()

    result = sequence_to_smiles_daa(args.sequence, disulfide=not args.no_disulfide)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
