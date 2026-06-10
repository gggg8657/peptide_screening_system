"""RCSB PDB sequence similarity search endpoint."""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException

router = APIRouter()

try:
    from pyrosetta_flow.rcsb_sequence_search import search_similar_peptides
    _HAS_RCSB = True
except ImportError:
    _HAS_RCSB = False


@router.post("/rcsb-search")
def rcsb_search(body: dict):
    """Search RCSB PDB for similar peptide sequences.

    Request body:
        sequence: str — amino acid sequence (1-letter code)
        identity_cutoff: float — min identity (0.0–1.0, default 0.4)
        max_results: int — max hits to return (default 5)

    Returns:
        {"hits": [{"pdb_id", "identifier", "identity", "evalue", "bitscore"}, ...]}
    """
    if not _HAS_RCSB:
        raise HTTPException(status_code=503, detail="rcsb_sequence_search module not available")

    sequence = body.get("sequence", "").upper().strip()
    if not sequence or not re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWY]+", sequence):
        raise HTTPException(status_code=400, detail=f"Invalid amino acid sequence: {sequence!r}")
    if len(sequence) < 5:
        raise HTTPException(status_code=400, detail="Sequence too short (min 5 residues)")

    identity_cutoff = float(body.get("identity_cutoff", 0.4))
    max_results = int(body.get("max_results", 5))

    try:
        result = search_similar_peptides(
            sequence=sequence,
            identity_cutoff=identity_cutoff,
            max_results=max_results,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"RCSB API error: {exc}")

    hits = [
        {
            "pdb_id": hit.pdb_id,
            "identifier": hit.identifier,
            "identity": hit.sequence_identity,
            "evalue": hit.evalue,
            "bitscore": hit.bitscore,
        }
        for hit in result.hits
    ]
    return {"hits": hits, "total_count": result.total_count}
