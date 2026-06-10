"""Cluster classification endpoint — A~E 5등급 후보 분류."""
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/cluster/classify")
def cluster_classify(body: dict):
    """후보 리스트를 A~E 클러스터로 분류."""
    try:
        from pyrosetta_flow.cluster_report import batch_classify
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="cluster_report module not available",
        )

    candidates = body.get("candidates", [])
    if not candidates:
        raise HTTPException(status_code=400, detail="candidates list is empty")

    try:
        result = batch_classify(candidates)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Classification error: {exc}")

    return result
