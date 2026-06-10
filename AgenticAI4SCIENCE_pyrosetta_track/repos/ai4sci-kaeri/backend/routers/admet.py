"""ADMET, nephrotoxicity, and pharmacology batch endpoints."""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException

from backend.state import MAX_VALIDATION_BATCH

router = APIRouter()


def _compute_admet_single(sequence: str) -> dict:
    seq = sequence.upper().strip()
    if not seq or not re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWY]+", seq):
        raise HTTPException(status_code=400, detail=f"Invalid amino acid sequence: {sequence!r}")
    from backend.admet import compute_admet_full, merge_pepadmet_into_admet_results

    base = compute_admet_full(seq)
    merged = merge_pepadmet_into_admet_results([seq], [base])
    return merged[0]


@router.get("/admet/{sequence}")
def get_admet(sequence: str):
    return _compute_admet_single(sequence)


@router.post("/admet/batch")
def admet_batch(body: dict):
    sequences = body.get("sequences", [])
    if not isinstance(sequences, list) or not sequences:
        raise HTTPException(status_code=400, detail="sequences must be a non-empty array of strings")
    if len(sequences) > MAX_VALIDATION_BATCH:
        raise HTTPException(
            status_code=400,
            detail=f"Too many sequences ({len(sequences)}). Max batch size is {MAX_VALIDATION_BATCH}.",
        )
    from backend.admet import compute_admet_full, merge_pepadmet_into_admet_results

    upper: list[str] = []
    for s in sequences:
        seq = s.upper().strip() if isinstance(s, str) else ""
        if not seq or not re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWY]+", seq):
            raise HTTPException(status_code=400, detail=f"Invalid amino acid sequence: {s!r}")
        upper.append(seq)

    results = [compute_admet_full(s) for s in upper]
    results = merge_pepadmet_into_admet_results(upper, results)
    return {"results": results}


@router.post("/pharmacology/batch")
def pharmacology_batch(body: dict):
    sequences = body.get("sequences", [])
    reference = body.get("reference", "AGCKNFFWKTFTSC")
    if not isinstance(sequences, list) or not sequences:
        raise HTTPException(status_code=400, detail="sequences must be a non-empty array of strings")
    if len(sequences) > MAX_VALIDATION_BATCH:
        raise HTTPException(
            status_code=400,
            detail=f"Too many sequences ({len(sequences)}). Max batch size is {MAX_VALIDATION_BATCH}.",
        )
    from backend.pharmacology import compute_pharmacology
    results = [compute_pharmacology(s, reference) for s in sequences]
    return {"results": results}
