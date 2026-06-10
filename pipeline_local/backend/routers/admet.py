"""ADMET, 신독성, 약리학 배치 엔드포인트.

원본 backend.admet / backend.pharmacology 모듈을 그대로 재사용한다.

P1-4 (2026-05-13): 모든 응답에 confidence_grade 자동 주입.
  - /admet/*     → grade "C" (DLscore 포화 문제, M5-P3)
  - /pharmacology/batch → grade "B" (Biopython ProtParam in-silico)
  근거: pharmacology_guards.ENDPOINT_CONFIDENCE
"""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException

from pipeline_local.backend.state import MAX_VALIDATION_BATCH
from pipeline_local.scripts.pharmacology_guards import attach_confidence

router = APIRouter()


def _compute_admet_single(sequence: str) -> dict:
    """단일 서열 ADMET 계산. confidence_grade "C" 자동 주입."""
    seq = sequence.upper().strip()
    if not seq or not re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWY]+", seq):
        raise HTTPException(status_code=400, detail=f"유효하지 않은 아미노산 서열: {sequence!r}")
    from backend.admet import compute_admet_full
    raw = compute_admet_full(seq)
    return attach_confidence(raw, "/admet/{sequence}")


@router.get("/admet/{sequence}")
def get_admet(sequence: str):
    """단일 서열의 ADMET + 신독성 지표를 계산한다.

    ⚠️ confidence_grade "C": compute_admet DLscore 포화 문제 (M5-P3 §검증 필요).
    응답의 confidence_warnings 필드를 반드시 확인할 것.
    """
    return _compute_admet_single(sequence)


@router.post("/admet/batch")
def admet_batch(body: dict):
    """여러 서열의 ADMET 지표를 배치로 계산한다.

    ⚠️ confidence_grade "C": 각 항목의 confidence_grade 필드 확인 필수.
    """
    sequences = body.get("sequences", [])
    if not isinstance(sequences, list) or not sequences:
        raise HTTPException(status_code=400, detail="sequences 는 비어 있지 않은 배열이어야 합니다.")
    if len(sequences) > MAX_VALIDATION_BATCH:
        raise HTTPException(
            status_code=400,
            detail=f"배치 크기 초과 ({len(sequences)}). 최대 {MAX_VALIDATION_BATCH}개.",
        )
    results = [_compute_admet_single(s) for s in sequences]
    # 배치 응답에도 최고 등급(C) 요약 주입
    return attach_confidence(
        {"results": results},
        "/admet/batch",
    )


@router.post("/pharmacology/batch")
def pharmacology_batch(body: dict):
    """여러 서열의 약리학적 특성을 배치로 계산한다.

    ⚠️ confidence_grade "B": Biopython ProtParam 기반 in-silico 추정.
    D-아미노산 도입 후보는 Instability Index가 L-AA 기준으로 계산됨 (M5-P1).
    """
    sequences = body.get("sequences", [])
    reference = body.get("reference", "AGCKNFFWKTFTSC")
    if not isinstance(sequences, list) or not sequences:
        raise HTTPException(status_code=400, detail="sequences 는 비어 있지 않은 배열이어야 합니다.")
    if len(sequences) > MAX_VALIDATION_BATCH:
        raise HTTPException(
            status_code=400,
            detail=f"배치 크기 초과 ({len(sequences)}). 최대 {MAX_VALIDATION_BATCH}개.",
        )
    # 서열 사전 검증 — PharmaProperties 내부 ValueError → 400 변환
    for s in sequences:
        seq = s.upper().strip() if isinstance(s, str) else ""
        if not seq or not re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWY]+", seq):
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 아미노산 서열: {s!r}",
            )
    from backend.pharmacology import compute_pharmacology
    try:
        results = [compute_pharmacology(s, reference) for s in sequences]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return attach_confidence(
        {"results": results},
        "/pharmacology/batch",
    )
