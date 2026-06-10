"""ADMET-AI Layer 3 wrapper.

This wrapper intentionally treats ADMET-AI as an external, learned model.
It does not train or calibrate any model locally, and it always marks peptide
and DOTA use as extrapolative for decision-making.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


ADMET_AI_EXTRAPOLATION_WARNING = (
    "ADMET-AI is a learned small-molecule ADMET model; PRST peptides, cyclic "
    "peptides, and DOTA/radiometal conjugates are outside the validated "
    "decision domain. Use raw endpoint outputs for triage only; do not use as "
    "a clinical or wet-lab decision substitute."
)


def _to_builtin(value: Any) -> Any:
    """Convert common numpy/pandas scalars and containers to JSON-like values."""
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, dict):
        return {str(k): _to_builtin(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_builtin(v) for v in value]
    return value


def _local_admet_ai_resources() -> dict[str, Path]:
    """Return isolated ADMET-AI resource paths when the local clone exists."""
    repo_root = Path(__file__).resolve().parents[2]
    pkg_root = repo_root / "_workspace" / "admet_ai_local" / "admet_ai" / "admet_ai"
    return {
        "models_dir": pkg_root / "resources" / "models",
        "drugbank_path": pkg_root / "resources" / "data" / "drugbank_approved.csv",
    }


def predict_admet_layer3(smiles: str, *, has_dota: bool = False) -> dict[str, Any]:
    """Run ADMET-AI on a SMILES string and attach mandatory H-06/OOD guards.

    Returns the external model's raw endpoint dictionary under ``predictions``.
    If ADMET-AI is unavailable or inference fails, this function reports the
    provider error and leaves ``predictions`` empty rather than fabricating
    endpoint values.
    """
    result: dict[str, Any] = {
        "tool": "ADMET-AI",
        "layer": 3,
        "smiles": smiles,
        "has_dota": bool(has_dota),
        "extrapolation_warning": True,
        "h06_guard": True,
        "recommended_for_decision": False,
        "warnings": [ADMET_AI_EXTRAPOLATION_WARNING],
        "predictions": {},
    }

    if has_dota:
        result["warnings"].append(
            "DOTA/radiometal-chelator conjugates are explicitly treated as OOD."
        )

    if not smiles or not isinstance(smiles, str):
        result["ok"] = False
        result["error"] = "empty_or_invalid_smiles"
        return result

    try:
        from admet_ai import ADMETModel
    except Exception as exc:
        result["ok"] = False
        result["error"] = f"admet_ai_import_failed: {type(exc).__name__}: {exc}"
        return result

    try:
        resources = _local_admet_ai_resources()
        kwargs: dict[str, Any] = {"num_workers": 0}
        if resources["models_dir"].exists() and resources["drugbank_path"].exists():
            kwargs.update(resources)

        model = ADMETModel(**kwargs)
        predictions = model.predict(smiles=smiles)
    except Exception as exc:
        result["ok"] = False
        result["error"] = f"admet_ai_predict_failed: {type(exc).__name__}: {exc}"
        return result

    result["ok"] = True
    result["predictions"] = _to_builtin(dict(predictions))
    result["n_endpoints"] = len(result["predictions"])
    return result

