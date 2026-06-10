"""Layer 1 serum half-life ensemble for L-AA peptides.

Layer 1 combines only wrappers that return an explicit half-life value in
hours. Tools that are missing, blocked, or return ranking/probability scores
are reported as unavailable instead of being converted into hours.
"""
from __future__ import annotations

import math
import re
from typing import Any, Callable, Dict, Optional

VALID_L_AA = set("ACDEFGHIKLMNPQRSTVWY")
DEFAULT_WEIGHTS: Dict[str, float] = {
    "plifepred": 0.552,      # PlifePred literature R2, if an hours wrapper exists.
    "hle_regression": 0.879, # Ezan 2024 albumin-binding subset R2.
    "pepadmet_hbm": 0.84,    # pepADMET human blood minimum reported R2.
}
CONFIDENCE_WEIGHT = {"P1": 1.0, "P2": 0.75, "P3": 0.5, "P4": 0.25}
GRADE_ORDER = {"P1": 1, "P2": 2, "P3": 3, "P4": 4, "UNAVAILABLE": 5}


def contains_d_amino_acid(sequence: str) -> bool:
    """Detect local D-AA notation used in this repository."""
    if any(ch.isalpha() and ch.islower() for ch in sequence):
        return True
    return bool(re.search(r"(^|[^A-Za-z])d[-_ ]?[A-Za-z]{1,3}", sequence, re.IGNORECASE))


def is_linear_l_aa_sequence(sequence: str) -> bool:
    return bool(sequence) and not contains_d_amino_acid(sequence) and all(
        aa in VALID_L_AA for aa in sequence
    )


def is_cyclic_or_dota_candidate(sequence: str) -> bool:
    text = sequence.lower()
    return (
        "cyclic" in text
        or "cyclo" in text
        or "c(" in text
        or "dota" in text
        or "dotaga" in text
        or sequence.upper().count("C") >= 2
    )


def _unavailable(reason: str, *, confidence: str = "UNAVAILABLE") -> Dict[str, Any]:
    return {
        "value": None,
        "confidence": confidence,
        "weight": 0.0,
        "unavailable": True,
        "reason": reason,
    }


def _coerce_hours_prediction(raw: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
    """Accept only explicit hour-valued wrapper outputs."""
    if raw.get("unavailable"):
        return _unavailable(
            str(raw.get("reason", "wrapper unavailable")),
            confidence=str(raw.get("confidence", "UNAVAILABLE")),
        )
    if raw.get("error"):
        return _unavailable(str(raw["error"]), confidence=str(raw.get("confidence", "UNAVAILABLE")))

    unit = str(raw.get("unit") or raw.get("value_unit") or raw.get("halflife_unit") or "").lower()
    value = (
        raw.get("value")
        if raw.get("value") is not None
        else raw.get("predicted_hours", raw.get("halflife_hours", raw.get("half_life_hours")))
    )
    if value is None:
        return _unavailable(f"{tool_name} wrapper returned no half-life value in hours")
    if unit and "hour" not in unit and unit != "h":
        return _unavailable(f"{tool_name} output unit is not hours: {unit}")

    try:
        hours = float(value)
    except (TypeError, ValueError):
        return _unavailable(f"{tool_name} half-life value is not numeric: {value!r}")
    if not math.isfinite(hours) or hours < 0:
        return _unavailable(f"{tool_name} half-life value is outside valid range: {value!r}")

    confidence = str(raw.get("confidence") or raw.get("confidence_grade") or "P4")
    return {
        "value": hours,
        "confidence": confidence,
        "weight": 0.0,
        "raw": raw,
    }


def _predict_plifepred(sequence: str) -> Dict[str, Any]:
    """Call available PlifePred wrapper if it returns explicit hours."""
    try:
        from pipeline_local.scripts.predict_halflife_pepmsnd import predict_halflife_plifepred
    except Exception as exc:
        return _unavailable(f"PlifePred wrapper import failed: {exc}")

    result = predict_halflife_plifepred(sequence)
    hours = result.get("predicted_hours")
    if hours is None:
        return _unavailable(
            "PlifePred2 rank only, hours unavailable",
            confidence=str(result.get("confidence_grade", "P4")),
        )
    return {
        "value": hours,
        "unit": "hours",
        "confidence": str(result.get("absolute_confidence") or result.get("confidence_grade") or "P4"),
        "raw": result,
    }


def _predict_hle_regression(sequence: str) -> Dict[str, Any]:
    try:
        from pipeline_local.scripts.predict_halflife_pepmsnd import predict_halflife_hle_regression
    except Exception as exc:
        return _unavailable(f"HLE regression wrapper import failed: {exc}", confidence="P4")

    result = predict_halflife_hle_regression(sequence)
    hours = result.get("predicted_hours")
    if hours is None:
        return _unavailable(
            str(result.get("reason", "HLE regression hours unavailable")),
            confidence=str(result.get("absolute_confidence") or result.get("confidence") or "P4"),
        )
    return {
        "value": hours,
        "unit": "hours",
        "confidence": str(result.get("absolute_confidence") or result.get("confidence") or "P4"),
        "raw": result,
    }


def _predict_pepadmet_hbm(sequence: str) -> Dict[str, Any]:
    try:
        from pipeline_local.scripts.predict_admet_pepadmet import check_pepadmet_web_access
    except Exception as exc:
        return _unavailable(f"pepADMET wrapper import failed: {exc}", confidence="P1")

    status = check_pepadmet_web_access()
    if not status.get("reachable"):
        return _unavailable(
            f"pepADMET HBM web unavailable: HTTP {status.get('http_status')}",
            confidence="P1",
        )
    return _unavailable(
        "pepADMET HBM web is reachable, but automated result parsing is not implemented",
        confidence="P1",
    )


def _absolute_confidence(predictions: Dict[str, Dict[str, Any]]) -> str:
    used = [p for p in predictions.values() if not p.get("unavailable")]
    if not used:
        return "UNAVAILABLE"
    return max((str(p.get("confidence", "P4")) for p in used), key=lambda g: GRADE_ORDER.get(g, 4))


def compute_layer1_halflife(
    sequence: str,
    *,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Compute Layer 1 weighted serum half-life for a single L-AA peptide."""
    configured_weights = dict(DEFAULT_WEIGHTS)
    if weights:
        configured_weights.update(weights)

    predictions: Dict[str, Dict[str, Any]] = {
        "plifepred": _unavailable("not called"),
        "hle_regression": _unavailable("not called"),
        "pepadmet_hbm": _unavailable("not called"),
    }
    warnings = [
        "H-06 HEURISTIC: Layer 1 ensemble is for first-pass ranking only; wet-lab serum stability assay is required."
    ]

    if not is_linear_l_aa_sequence(sequence) or is_cyclic_or_dota_candidate(sequence):
        reason = "Layer 1 supports only linear standard L-AA sequences; route D-AA/cyclic/DOTA candidates to Layer 2/3"
        for name in predictions:
            predictions[name] = _unavailable(reason)
        return {
            "ensemble_halflife_hours": None,
            "individual_predictions": predictions,
            "ensemble_method": "weighted_average",
            "tools_used": [],
            "tools_unavailable": list(predictions),
            "absolute_confidence": "UNAVAILABLE",
            "recommended": False,
            "unavailable": True,
            "warnings": warnings + [reason],
        }

    callers: Dict[str, Callable[[str], Dict[str, Any]]] = {
        "plifepred": _predict_plifepred,
        "hle_regression": _predict_hle_regression,
        "pepadmet_hbm": _predict_pepadmet_hbm,
    }
    for name, caller in callers.items():
        try:
            predictions[name] = _coerce_hours_prediction(caller(sequence), name)
        except Exception as exc:
            predictions[name] = _unavailable(f"{name} wrapper failed: {exc}")

    tools_used = [name for name, pred in predictions.items() if not pred.get("unavailable")]
    tools_unavailable = [name for name in predictions if name not in tools_used]
    if not tools_used:
        return {
            "ensemble_halflife_hours": None,
            "individual_predictions": predictions,
            "ensemble_method": "weighted_average",
            "tools_used": [],
            "tools_unavailable": tools_unavailable,
            "absolute_confidence": "UNAVAILABLE",
            "recommended": True,
            "unavailable": True,
            "warnings": warnings + ["No Layer 1 tool returned explicit half-life hours."],
        }

    raw_weights: Dict[str, float] = {}
    for name in tools_used:
        pred = predictions[name]
        grade = str(pred.get("confidence", "P4"))
        raw_weights[name] = float(configured_weights.get(name, 1.0)) * CONFIDENCE_WEIGHT.get(grade, 0.25)

    total_weight = sum(raw_weights.values())
    if total_weight <= 0:
        return {
            "ensemble_halflife_hours": None,
            "individual_predictions": predictions,
            "ensemble_method": "weighted_average",
            "tools_used": tools_used,
            "tools_unavailable": tools_unavailable,
            "absolute_confidence": "UNAVAILABLE",
            "recommended": True,
            "unavailable": True,
            "warnings": warnings + ["Layer 1 weights sum to zero."],
        }

    for name, raw_weight in raw_weights.items():
        predictions[name]["weight"] = raw_weight / total_weight

    ensemble = sum(
        float(predictions[name]["value"]) * float(predictions[name]["weight"])
        for name in tools_used
    )
    return {
        "ensemble_halflife_hours": ensemble,
        "individual_predictions": predictions,
        "ensemble_method": "weighted_average",
        "tools_used": tools_used,
        "tools_unavailable": tools_unavailable,
        "absolute_confidence": _absolute_confidence(predictions),
        "recommended": True,
        "unavailable": False,
        "warnings": warnings,
    }
