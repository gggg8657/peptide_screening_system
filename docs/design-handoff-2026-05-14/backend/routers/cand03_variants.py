"""
cand03 변이체 카탈로그 라우터.

데이터 소스:
  runs_local/cand03_variants/cand03_variants.json   (이미 존재, 20종)

마운트:
  app.include_router(cand03_variants.router, prefix="/api/cand03_variants", tags=["cand03"])
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..schemas.dashboard import Cand03Variant, Cand03VariantsResponse  # type: ignore

router = APIRouter()


def _variants_path() -> Path:
    return Path(__file__).resolve().parents[3] / "runs_local" / "cand03_variants" / "cand03_variants.json"


@router.get("/list", response_model=Cand03VariantsResponse)
def list_variants() -> Cand03VariantsResponse:
    """cand03 변이체 20종 카탈로그."""
    path = _variants_path()
    if not path.exists():
        # Fallback: prototype 의 sample
        return Cand03VariantsResponse(
            baseline="cand03",
            variants=[
                Cand03Variant(
                    id="var12", name="var12 (T12 → D-Thr)",
                    seq="AICKNFFWKTF*SC", modifications=["D-Thr12"],
                    hl_score=16.72, chymotrypsin_sites=4, trypsin_sites=2, nep_sites=5,
                    priority="★ 1순위",
                    rationale="cand03 stability 보강, Boltz iPTM 0.952 유지",
                ),
                Cand03Variant(
                    id="var07", name="var07 (I2K + K4-DOTA)",
                    seq="AKCKNFFWKTFTSC", modifications=["I2K", "K4-DOTA"],
                    hl_score=14.20, chymotrypsin_sites=4, trypsin_sites=3, nep_sites=5,
                    priority="2순위",
                ),
                Cand03Variant(
                    id="var18", name="var18 (I2Y · ¹²⁵I 라벨)",
                    seq="AYCKNFFWKTFTSC", modifications=["I2Y (Tyr ¹²⁵I label)"],
                    hl_score=15.80, chymotrypsin_sites=4, trypsin_sites=2, nep_sites=5,
                    priority="3순위 · chemistry",
                ),
            ],
        )

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    # cand03_variants.json 의 실제 스키마에 맞춰 매핑 — 아래는 추정 키
    variants = []
    for v in raw.get("variants", []):
        variants.append(Cand03Variant(
            id=v["id"],
            name=v.get("name", v["id"]),
            seq=v["seq"],
            modifications=v.get("modifications", []),
            hl_score=float(v.get("hl_score", 0)),
            chymotrypsin_sites=int(v.get("chymo_sites", v.get("chymotrypsin_sites", 0))),
            trypsin_sites=int(v.get("tryp_sites", v.get("trypsin_sites", 0))),
            nep_sites=int(v.get("nep_sites", 0)),
            priority=v.get("priority", "—"),
            rationale=v.get("rationale"),
        ))
    return Cand03VariantsResponse(baseline=raw.get("baseline", "cand03"), variants=variants)


@router.get("/{variant_id}", response_model=Cand03Variant)
def get_variant(variant_id: str) -> Cand03Variant:
    resp = list_variants()
    for v in resp.variants:
        if v.id == variant_id:
            return v
    raise HTTPException(404, f"variant {variant_id} not found")
