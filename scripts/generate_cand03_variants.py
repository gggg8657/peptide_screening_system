"""Generate committed runs_local/cand03_variants/cand03_variants.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline_local.scripts.stability_predictor import CANDIDATE_8, batch_evaluate


OUTPUT_PATH = REPO_ROOT / "runs_local" / "cand03_variants" / "cand03_variants.json"

_PRIORITY = {
    "SST14_ref": "reference",
    "cand03": "baseline",
    "var12_dThr": "ncaa",
}

_RATIONALE = {
    "SST14_ref": "Parent SST14 reference sequence.",
    "cand03": "A1I baseline candidate for migration dashboard.",
    "var12_dThr": "D-Thr substitution candidate for NCAA comparison.",
}


def _variant_name(seq_id: str) -> str:
    if seq_id == "SST14_ref":
        return "SST14_ref (parent)"
    if seq_id == "cand03":
        return "cand03 (A1I)"
    if seq_id == "var12_dThr":
        return "var12_dThr (D-Thr)"
    return seq_id


def _fallback_variant(candidate: dict[str, Any]) -> dict[str, Any]:
    seq_id = str(candidate["seq_id"])
    return {
        "id": seq_id,
        "name": _variant_name(seq_id),
        "seq": str(candidate["sequence"]),
        "modifications": [str(item) for item in candidate.get("mods", [])],
        "hl_score": 0.0,
        "chymotrypsin_sites": 0,
        "trypsin_sites": 0,
        "nep_sites": 0,
        "priority": _PRIORITY.get(seq_id, "screening"),
        "rationale": _RATIONALE.get(seq_id, f"{seq_id} candidate from stability_predictor.CANDIDATE_8."),
    }


def _build_variants() -> list[dict[str, Any]]:
    variants = [_fallback_variant(candidate) for candidate in CANDIDATE_8]
    try:
        batch = batch_evaluate(
            [candidate["sequence"] for candidate in CANDIDATE_8],
            [candidate["seq_id"] for candidate in CANDIDATE_8],
            [candidate.get("mods", []) for candidate in CANDIDATE_8],
        )
    except Exception:
        return variants

    by_id = {item["id"]: item for item in variants}
    for result in batch.results:
        entry = by_id.get(result.seq_id)
        if entry is None:
            continue
        entry["hl_score"] = round(float(result.hl_score_heuristic), 2)
        entry["chymotrypsin_sites"] = len(result.protease_cleavage_sites.get("chymotrypsin", []))
        entry["trypsin_sites"] = len(result.protease_cleavage_sites.get("trypsin", []))
        entry["nep_sites"] = len(result.protease_cleavage_sites.get("nep", []))
    return variants


def main() -> int:
    payload = {
        "baseline": "cand03",
        "variants": _build_variants(),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
