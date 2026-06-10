#!/usr/bin/env python3
"""One-off batch predict for Layer 3 report — run inside admet_ai_local conda env."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Quiet tqdm / Lightning progress (stdout must stay clean if piping JSON)
os.environ.setdefault("TQDM_DISABLE", "1")

import lightning.pytorch as pl

_orig_trainer_init = pl.Trainer.__init__


def _trainer_init_quiet(self, *args, **kwargs):
    kwargs.setdefault("enable_progress_bar", False)
    return _orig_trainer_init(self, *args, **kwargs)


pl.Trainer.__init__ = _trainer_init_quiet  # type: ignore[method-assign]

# Resolve bundled resources (editable install can mis-resolve importlib.resources)
import admet_ai.admet_model as _am

_PKG_ROOT = Path(_am.__file__).resolve().parent
_RESOURCES = _PKG_ROOT / "resources"
_MODELS = _RESOURCES / "models"
_DRUGBANK = _RESOURCES / "data" / "drugbank_approved.csv"


def main() -> None:
    from admet_ai.admet_model import ADMETModel

    t0 = time.time()
    model = ADMETModel(
        models_dir=_MODELS,
        drugbank_path=_DRUGBANK,
        num_workers=0,
    )
    init_s = round(time.time() - t0, 2)

    rows = []
    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t", 1)
        name = parts[0].strip()
        smi = parts[1].strip() if len(parts) > 1 else ""
        rec: dict = {"name": name, "smiles": smi[:500] + ("…" if len(smi) > 500 else "")}
        try:
            t1 = time.time()
            preds = model.predict(smiles=smi)
            rec["ok"] = True
            rec["predict_sec"] = round(time.time() - t1, 3)
            rec["n_endpoints"] = len(preds)
            rec["predictions"] = {k: (float(v) if hasattr(v, "real") else v) for k, v in preds.items()}
        except Exception as e:
            rec["ok"] = False
            rec["error"] = f"{type(e).__name__}: {e}"
        rows.append(rec)

    out = {
        "admet_ai_package": str(_PKG_ROOT),
        "model_init_sec": init_s,
        "results": rows,
    }
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if out_path:
        out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    else:
        json.dump(out, sys.stdout, indent=2, default=str)


if __name__ == "__main__":
    main()
