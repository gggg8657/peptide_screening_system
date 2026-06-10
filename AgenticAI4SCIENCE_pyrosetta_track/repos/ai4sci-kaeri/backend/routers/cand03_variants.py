"""cand03_variants catalog router backed by committed JSON data."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class Cand03Variant(BaseModel):
    id: str
    name: str
    seq: str
    modifications: list[str]
    hl_score: float
    chymotrypsin_sites: int
    trypsin_sites: int
    nep_sites: int
    priority: str
    rationale: str | None = None


class Cand03VariantsResponse(BaseModel):
    baseline: str
    variants: list[Cand03Variant]


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _variants_path() -> Path:
    return _workspace_root() / "runs_local" / "cand03_variants" / "cand03_variants.json"


def _fallback_payload() -> dict[str, Any]:
    return {
        "baseline": "cand03",
        "variants": [
            {
                "id": "SST14_ref",
                "name": "SST14_ref (parent)",
                "seq": "AGCKNFFWKTFTSC",
                "modifications": ["cyclization"],
                "hl_score": 0.0,
                "chymotrypsin_sites": 0,
                "trypsin_sites": 0,
                "nep_sites": 0,
                "priority": "reference",
                "rationale": "Parent peptide reference for cand03 lineage.",
            },
            {
                "id": "cand03",
                "name": "cand03 (A1I)",
                "seq": "AICKNFFWKTFTSC",
                "modifications": ["cyclization"],
                "hl_score": 0.0,
                "chymotrypsin_sites": 0,
                "trypsin_sites": 0,
                "nep_sites": 0,
                "priority": "baseline",
                "rationale": "Baseline migration candidate.",
            },
            {
                "id": "var12_dThr",
                "name": "var12_dThr (D-Thr)",
                "seq": "AICKNFFWKTFT[dT]C",
                "modifications": ["cyclization", "d_amino_acid"],
                "hl_score": 0.0,
                "chymotrypsin_sites": 0,
                "trypsin_sites": 0,
                "nep_sites": 0,
                "priority": "ncaa",
                "rationale": "NCAA variant placeholder when JSON is missing.",
            },
        ],
    }


def _load_payload() -> dict[str, Any]:
    path = _variants_path()
    if not path.exists():
        return _fallback_payload()
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _map_variant(raw: dict[str, Any]) -> Cand03Variant:
    return Cand03Variant(
        id=str(raw["id"]),
        name=str(raw.get("name", raw["id"])),
        seq=str(raw["seq"]),
        modifications=[str(item) for item in raw.get("modifications", [])],
        hl_score=float(raw.get("hl_score", 0.0)),
        chymotrypsin_sites=int(raw.get("chymotrypsin_sites", raw.get("chymo_sites", 0))),
        trypsin_sites=int(raw.get("trypsin_sites", raw.get("tryp_sites", 0))),
        nep_sites=int(raw.get("nep_sites", 0)),
        priority=str(raw.get("priority", "—")),
        rationale=raw.get("rationale"),
    )


@router.get("/cand03_variants/list", response_model=Cand03VariantsResponse)
def list_variants() -> Cand03VariantsResponse:
    payload = _load_payload()
    variants = [_map_variant(item) for item in payload.get("variants", [])]
    return Cand03VariantsResponse(
        baseline=str(payload.get("baseline", "cand03")),
        variants=variants,
    )


@router.get("/cand03_variants/{variant_id}", response_model=Cand03Variant)
def get_variant(variant_id: str) -> Cand03Variant:
    response = list_variants()
    for variant in response.variants:
        if variant.id == variant_id:
            return variant
    raise HTTPException(status_code=404, detail=f"variant {variant_id} not found")
