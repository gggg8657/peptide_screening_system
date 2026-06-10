"""Peptide Design Utilities — Cys/disulfide detection & design position generation.

서열에서 Cys 위치를 자동 탐지하고, 이황화결합(disulfide bond) 잔기를 제외한
design positions 리스트를 생성하는 유틸리티.

Usage (standalone):
    python scripts/peptide_design_utils.py AGCKNFFWKTFTSC

Usage (import):
    from scripts.peptide_design_utils import (
        find_cys_positions,
        get_design_positions,
        validate_design_positions,
    )

    seq = "AGCKNFFWKTFTSC"
    cys_pos = find_cys_positions(seq)
    # => [3, 14]
    design_pos = get_design_positions(seq)
    # => [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
"""

from __future__ import annotations

from typing import List, Optional, Set


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def find_cys_positions(sequence: str, one_indexed: bool = True) -> List[int]:
    """Find all Cysteine (C) positions in a peptide sequence.

    Parameters
    ----------
    sequence : str
        Amino acid sequence in 1-letter code.
    one_indexed : bool, default True
        If True, return 1-indexed positions (biology convention).
        If False, return 0-indexed positions (Python convention).

    Returns
    -------
    List[int]
        Sorted list of Cys positions.

    Examples
    --------
    >>> find_cys_positions("AGCKNFFWKTFTSC")
    [3, 14]
    >>> find_cys_positions("AGCKNFFWKTFTSC", one_indexed=False)
    [2, 13]
    """
    offset = 1 if one_indexed else 0
    return [i + offset for i, aa in enumerate(sequence) if aa == "C"]


def get_design_positions(
    sequence: str,
    frozen_residues: Optional[Set[str]] = None,
    one_indexed: bool = True,
) -> List[int]:
    """Get designable positions = all positions EXCEPT frozen residues.

    By default, Cysteine (C) is the only frozen residue type.
    Additional residue types can be frozen via `frozen_residues`.

    Parameters
    ----------
    sequence : str
        Amino acid sequence in 1-letter code.
    frozen_residues : set of str, optional
        1-letter codes of residue types to exclude from design.
        Default: {"C"} (Cysteine only).
    one_indexed : bool, default True
        If True, return 1-indexed positions.

    Returns
    -------
    List[int]
        Sorted list of designable positions.

    Examples
    --------
    >>> get_design_positions("AGCKNFFWKTFTSC")
    [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    >>> get_design_positions("AGCKNFFWKTFTSC", frozen_residues={"C", "G"})
    [1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    """
    if frozen_residues is None:
        frozen_residues = {"C"}
    offset = 1 if one_indexed else 0
    return [
        i + offset
        for i, aa in enumerate(sequence)
        if aa not in frozen_residues
    ]


def validate_design_positions(
    sequence: str,
    design_positions: List[int],
    one_indexed: bool = True,
) -> dict:
    """Validate design positions against the actual sequence.

    Checks for:
    - Positions out of range
    - Cys positions incorrectly included in design positions
    - Non-Cys positions incorrectly excluded from design positions

    Parameters
    ----------
    sequence : str
        Amino acid sequence in 1-letter code.
    design_positions : list of int
        List of design positions to validate.
    one_indexed : bool, default True
        Whether positions are 1-indexed.

    Returns
    -------
    dict with keys:
        valid : bool
        cys_positions : list of int (actual Cys positions)
        design_positions : list of int (input)
        correct_design_positions : list of int (what it should be)
        errors : list of str (error messages)
        warnings : list of str (warning messages)
    """
    offset = 1 if one_indexed else 0
    seq_len = len(sequence)
    max_pos = seq_len + offset - (0 if one_indexed else 1)
    min_pos = offset

    cys_pos = set(find_cys_positions(sequence, one_indexed))
    correct_design = set(get_design_positions(sequence, one_indexed=one_indexed))
    dp_set = set(design_positions)

    errors = []
    warnings = []

    # Check out-of-range
    for p in design_positions:
        if p < min_pos or p > max_pos:
            errors.append(
                f"Position {p} is out of range "
                f"[{min_pos}, {max_pos}] for sequence of length {seq_len}"
            )

    # Check Cys positions included in design
    cys_in_design = cys_pos & dp_set
    if cys_in_design:
        idx = "1-indexed" if one_indexed else "0-indexed"
        for pos in sorted(cys_in_design):
            errors.append(
                f"Cys at position {pos} ({idx}) is included in design_positions — "
                "this will break disulfide bonds"
            )

    # Check non-Cys positions excluded from design
    missing = correct_design - dp_set
    if missing:
        for pos in sorted(missing):
            aa = sequence[pos - offset]
            warnings.append(
                f"Position {pos} ({aa}) is non-Cys but excluded from design_positions"
            )

    # Extra positions that shouldn't be there
    extra = dp_set - correct_design
    for pos in sorted(extra):
        if pos not in cys_pos and min_pos <= pos <= max_pos:
            warnings.append(
                f"Position {pos} is in design_positions but not in expected set"
            )

    return {
        "valid": len(errors) == 0,
        "cys_positions": sorted(cys_pos),
        "design_positions": sorted(dp_set),
        "correct_design_positions": sorted(correct_design),
        "errors": errors,
        "warnings": warnings,
    }


def format_design_pos_string(positions: List[int], sep: str = ",") -> str:
    """Format design positions as a comma-separated string.

    Parameters
    ----------
    positions : list of int
    sep : str, default ","

    Returns
    -------
    str
        e.g. "1,2,4,5,6,7,8,9,10,11,12,13"
    """
    return sep.join(str(p) for p in sorted(positions))


def summarize_sequence(sequence: str) -> dict:
    """Generate a complete summary of a peptide sequence for design.

    Parameters
    ----------
    sequence : str
        Amino acid sequence in 1-letter code.

    Returns
    -------
    dict with keys:
        sequence, length, cys_positions, cys_count,
        design_positions, design_count, design_pos_string,
        frozen_positions, frozen_residues
    """
    cys_pos = find_cys_positions(sequence)
    design_pos = get_design_positions(sequence)

    return {
        "sequence": sequence,
        "length": len(sequence),
        "cys_positions": cys_pos,
        "cys_count": len(cys_pos),
        "design_positions": design_pos,
        "design_count": len(design_pos),
        "design_pos_string": format_design_pos_string(design_pos),
        "frozen_positions": cys_pos,
        "frozen_residues": {sequence[p - 1]: p for p in cys_pos},
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """CLI entrypoint."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python peptide_design_utils.py <SEQUENCE> [--validate POS1,POS2,...]")
        print("Example: python peptide_design_utils.py AGCKNFFWKTFTSC")
        print("Example: python peptide_design_utils.py AGCKNFFWKTFTSC --validate 1,2,4,5,6,7,8,9,10,11,12,14")
        sys.exit(1)

    sequence = sys.argv[1].upper()

    # Validate mode
    if "--validate" in sys.argv:
        idx = sys.argv.index("--validate")
        if idx + 1 < len(sys.argv):
            positions = [int(x) for x in sys.argv[idx + 1].split(",")]
            result = validate_design_positions(sequence, positions)
            print(f"\nSequence: {sequence} ({len(sequence)} residues)")
            print(f"Cys positions: {result['cys_positions']}")
            print(f"Input design positions: {result['design_positions']}")
            print(f"Correct design positions: {result['correct_design_positions']}")
            print(f"Valid: {result['valid']}")
            if result["errors"]:
                print("\nERRORS:")
                for e in result["errors"]:
                    print(f"  ✗ {e}")
            if result["warnings"]:
                print("\nWARNINGS:")
                for w in result["warnings"]:
                    print(f"  ⚠ {w}")
            sys.exit(0 if result["valid"] else 1)

    # Summary mode
    summary = summarize_sequence(sequence)
    print(f"\n{'='*60}")
    print(f"Peptide Design Summary")
    print(f"{'='*60}")
    print(f"  Sequence:          {summary['sequence']}")
    print(f"  Length:             {summary['length']} residues")
    print(f"  Cys positions:     {summary['cys_positions']} (frozen)")
    print(f"  Design positions:  {summary['design_positions']}")
    print(f"  Design count:      {summary['design_count']} / {summary['length']}")
    print(f"  Design string:     {summary['design_pos_string']}")
    print(f"{'='*60}")

    # Also validate the old hardcoded positions if applicable
    old_positions = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14]
    if len(sequence) == 14:
        print(f"\n--- Validation of old hardcoded positions {old_positions} ---")
        result = validate_design_positions(sequence, old_positions)
        if not result["valid"]:
            print("  ✗ OLD POSITIONS ARE INCORRECT:")
            for e in result["errors"]:
                print(f"    ✗ {e}")
        if result["warnings"]:
            for w in result["warnings"]:
                print(f"    ⚠ {w}")


if __name__ == "__main__":
    main()
