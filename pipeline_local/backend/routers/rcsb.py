"""RCSB PDB 서열 유사도 검색 엔드포인트.

원본 pyrosetta_flow.rcsb_sequence_search 모듈을 그대로 재사용한다.
"""
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
    """RCSB PDB에서 유사 펩타이드 서열을 검색한다.

    요청 바디:
        sequence:         str   — 1-letter 아미노산 서열
        identity_cutoff:  float — 최소 동일성 (0.0–1.0, 기본 0.4)
        max_results:      int   — 최대 결과 수 (기본 5)
    """
    if not _HAS_RCSB:
        raise HTTPException(status_code=503, detail="rcsb_sequence_search 모듈을 사용할 수 없습니다.")

    sequence = body.get("sequence", "").upper().strip()
    if not sequence or not re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWY]+", sequence):
        raise HTTPException(status_code=400, detail=f"유효하지 않은 아미노산 서열: {sequence!r}")
    if len(sequence) < 5:
        raise HTTPException(status_code=400, detail="서열이 너무 짧습니다 (최소 5 잔기).")

    identity_cutoff = float(body.get("identity_cutoff", 0.4))
    max_results     = int(body.get("max_results", 5))

    try:
        result = search_similar_peptides(
            sequence=sequence,
            identity_cutoff=identity_cutoff,
            max_results=max_results,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"RCSB API 오류: {exc}")

    hits = [
        {
            "pdb_id":     hit.pdb_id,
            "identifier": hit.identifier,
            "identity":   hit.sequence_identity,
            "evalue":     hit.evalue,
            "bitscore":   hit.bitscore,
        }
        for hit in result.hits
    ]
    return {"hits": hits, "total_count": result.total_count}
