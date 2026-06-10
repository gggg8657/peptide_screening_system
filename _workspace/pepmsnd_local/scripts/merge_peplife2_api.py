"""Merge PEPlife2 REST JSON dumps by id (in pepmsnd_local workspace only)."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "data" / "peplife2_raw"


def main() -> None:
    seen: dict[str, dict] = {}
    for path in sorted(BASE.glob("api_*.json")):
        with path.open() as f:
            d = json.load(f)
        for row in d.get("data", []):
            rid = str(row.get("id", ""))
            if rid and rid not in seen:
                seen[rid] = row
    rows = list(seen.values())
    print("unique_ids", len(rows), file=sys.stderr)
    cnt = Counter(str(r.get("chiral") or "").strip() for r in rows)
    print("chiral_counts", dict(cnt), file=sys.stderr)
    daa = [
        r
        for r in rows
        if str(r.get("chiral", "")).strip().upper() == "D"
        or str(r.get("chiral", "")).lower().startswith("d")
    ]
    print("daa_chiral_field", len(daa), file=sys.stderr)
    low = [r for r in rows if r.get("seq") and re.search(r"[a-z]", r["seq"])]
    print("seq_lowercase_letters", len(low), file=sys.stderr)
    out = BASE / "peplife2_merged.json"
    with out.open("w") as f:
        json.dump({"count": len(rows), "data": rows}, f, indent=0)
    print("wrote", out)


if __name__ == "__main__":
    main()
