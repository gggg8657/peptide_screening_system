"""
Unified Validation Engine
==========================
Combines pharmacological property checks + statistical reliability checks
into a single validation pass with user-selectable criteria and thresholds.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.pharmacology import compute_pharmacology
from backend.admet import compute_nephrotox_risk

# ── Default criteria definitions ──────────────────────────────────────────────

CRITERIA_REGISTRY: dict[str, dict[str, Any]] = {
    # ── Pharmacological ──────────────────────────────────────────────────────
    "gravy": {
        "label": "GRAVY (소수성)",
        "group": "pharmacological",
        "description": "Kyte-Doolittle 평균 소수성. 과도한 양수 → 간 흡수 증가.",
        "default_enabled": True,
        "threshold": {"min": -2.0, "max": 1.0},
        "unit": "",
    },
    "boman_index": {
        "label": "Boman Index (단백질 결합력)",
        "group": "pharmacological",
        "description": "수용체 결합 잠재력. GPCR 리간드는 ≥2.48 kcal/mol 필요.",
        "default_enabled": True,
        "threshold": {"min": 2.48},
        "unit": "kcal/mol",
    },
    "instability_index": {
        "label": "Instability Index (안정성)",
        "group": "pharmacological",
        "description": "Guruprasad dipeptide 안정성 예측. <40 = 안정.",
        "default_enabled": True,
        "threshold": {"max": 40.0},
        "unit": "",
    },
    "aliphatic_index": {
        "label": "Aliphatic Index (지방족 지수)",
        "group": "pharmacological",
        "description": "지방족 측쇄 상대 부피. 높으면 응집/수용성 저하.",
        "default_enabled": False,
        "threshold": {"max": 150.0},
        "unit": "",
    },
    "isoelectric_point": {
        "label": "pI (등전점)",
        "group": "pharmacological",
        "description": "순전하=0인 pH. 극단적 pI → 비특이적 조직 흡수.",
        "default_enabled": True,
        "threshold": {"min": 4.0, "max": 10.0},
        "unit": "",
    },
    "extinction_coefficient": {
        "label": "ε₂₈₀ (몰 흡광계수)",
        "group": "pharmacological",
        "description": "UV280 정량 가능 여부. 0이면 UV 정량 불가.",
        "default_enabled": False,
        "threshold": {"min": 1000},
        "unit": "M⁻¹cm⁻¹",
    },
    "n_end_rule": {
        "label": "N-end Rule (세포내 반감기)",
        "group": "pharmacological",
        "description": "N-말단 잔기에 의한 유비퀴틴-프로테아좀 분해 예측 반감기.",
        "default_enabled": True,
        "threshold": {"min": 2.0},
        "unit": "hours",
    },
    "hydrophobic_moment": {
        "label": "μH (소수성 모멘트)",
        "group": "pharmacological",
        "description": "양친매성 정도. 높으면 비특이적 막 결합 위험.",
        "default_enabled": False,
        "threshold": {"max": 0.6},
        "unit": "",
    },
    "wimley_white": {
        "label": "Wimley-White (막 상호작용)",
        "group": "pharmacological",
        "description": "Water→membrane ΔG. 음수 = 막 선호, 양수 = 수상 선호.",
        "default_enabled": False,
        "threshold": {"min": -5.0},
        "unit": "kcal/mol",
    },
    "protease_sites": {
        "label": "Protease Sites (절단 부위)",
        "group": "pharmacological",
        "description": "주요 프로테아제 절단 부위 총합. native 대비 Δ≤+2.",
        "default_enabled": True,
        "threshold": {"max_delta_vs_native": 2},
        "unit": "sites",
    },
    "charge_ph_profile": {
        "label": "Charge vs pH (전하 프로파일)",
        "group": "pharmacological",
        "description": "pH 7.4 / 6.5 (종양)에서의 순전하 비교.",
        "default_enabled": False,
        "threshold": {"max_abs_charge_ph74": 5.0},
        "unit": "",
    },
    "blosum62": {
        "label": "BLOSUM62 (변이 보존성)",
        "group": "pharmacological",
        "description": "변이의 진화적 보존성. 평균 점수 < -2 → 비보존적.",
        "default_enabled": False,
        "threshold": {"min_avg_score": -2.0},
        "unit": "",
    },
    "metal_coordination": {
        "label": "Metal Coordination (금속 배위)",
        "group": "radiopharmaceutical",
        "description": "강한 금속 배위 잔기. ≥2 → 킬레이터 간섭 위험.",
        "default_enabled": True,
        "threshold": {"max_strong": 1},
        "unit": "",
    },
    "nephrotox": {
        "label": "Nephrotox (신독성)",
        "group": "radiopharmaceutical",
        "description": "양이온 잔기에 의한 신장 재흡수 위험. High = 불합격.",
        "default_enabled": True,
        "threshold": {"max_risk_level": "Moderate"},
        "unit": "",
    },
    # ── Statistical reliability ──────────────────────────────────────────────
    "rank_stability": {
        "label": "Rank Stability (순위 안정성)",
        "group": "statistical",
        "description": "복수 반복에서 top-k 순위 출현 빈도.",
        "default_enabled": True,
        "threshold": {"min_appearances": 2},
        "unit": "",
    },
    "score_consistency": {
        "label": "Score Consistency (점수 일관성)",
        "group": "statistical",
        "description": "ddG 변동계수(CV). 높으면 불안정.",
        "default_enabled": True,
        "threshold": {"max_cv": 0.5},
        "unit": "",
    },
    "no_dominance": {
        "label": "No Dominance (독점 검출)",
        "group": "statistical",
        "description": "단일 후보가 전체 순위를 독점하는지 검사.",
        "default_enabled": True,
        "threshold": {},
        "unit": "",
    },
}

# ── Preset configurations ────────────────────────────────────────────────────

PRESETS: dict[str, dict[str, Any]] = {
    "prrt_radiopharmaceutical": {
        "label": "PRRT 방사성의약품",
        "description": "신독성, 금속 배위, 소수성, 결합력, 프로테아제 안정성 중심",
        "criteria": [
            "gravy", "boman_index", "instability_index", "isoelectric_point",
            "n_end_rule", "protease_sites", "nephrotox", "metal_coordination",
            "rank_stability", "score_consistency", "no_dominance",
        ],
    },
    "general_peptide": {
        "label": "일반 펩타이드",
        "description": "기본 물성 + 안정성 + 통계 신뢰성",
        "criteria": [
            "gravy", "instability_index", "aliphatic_index", "isoelectric_point",
            "protease_sites", "rank_stability", "score_consistency", "no_dominance",
        ],
    },
}

# ── Reference sequence for delta calculations ────────────────────────────────

_NATIVE_SST14 = "AGCKNFFWKTFTSC"


# ── Evaluate a single criterion ──────────────────────────────────────────────

def _evaluate_criterion(
    criterion_id: str,
    pharma: dict,
    thresholds: dict | None = None,
) -> dict[str, Any]:
    """Evaluate one criterion. Returns pass/fail with value and threshold."""
    reg = CRITERIA_REGISTRY.get(criterion_id)
    if not reg:
        return {"id": criterion_id, "passed": False, "error": "unknown criterion"}

    thresh = thresholds or reg["threshold"]
    result: dict[str, Any] = {
        "id": criterion_id,
        "label": reg["label"],
        "group": reg["group"],
        "description": reg["description"],
        "unit": reg["unit"],
        "threshold": thresh,
    }

    try:
        if criterion_id == "gravy":
            val = pharma["gravy"]
            lo = thresh.get("min", -999)
            hi = thresh.get("max", 999)
            result.update(value=val, passed=lo <= val <= hi)

        elif criterion_id == "boman_index":
            val = pharma["boman_index"]
            result.update(value=val, passed=val >= thresh.get("min", 2.48))

        elif criterion_id == "instability_index":
            val = pharma["instability_index"]
            result.update(value=val, passed=val <= thresh.get("max", 40.0))

        elif criterion_id == "aliphatic_index":
            val = pharma["aliphatic_index"]
            result.update(value=val, passed=val <= thresh.get("max", 150.0))

        elif criterion_id == "isoelectric_point":
            val = pharma["isoelectric_point"]
            lo = thresh.get("min", 4.0)
            hi = thresh.get("max", 10.0)
            result.update(value=val, passed=lo <= val <= hi)

        elif criterion_id == "extinction_coefficient":
            val = pharma["extinction_coefficient"]["epsilon_280_ss"]
            result.update(value=val, passed=val >= thresh.get("min", 1000))

        elif criterion_id == "n_end_rule":
            info = pharma["n_end_rule"]
            val = info["predicted_halflife_hours"]
            result.update(
                value=val,
                detail=f"N-term: {info['n_terminal_residue']} ({info['stability_category']})",
                passed=val >= thresh.get("min", 2.0),
            )

        elif criterion_id == "hydrophobic_moment":
            val = pharma["hydrophobic_moment"]["mu_h_max"]
            result.update(value=val, passed=val <= thresh.get("max", 0.6))

        elif criterion_id == "wimley_white":
            val = pharma["wimley_white"]["ww_total_kcal"]
            result.update(
                value=val,
                detail=pharma["wimley_white"]["interpretation"],
                passed=val >= thresh.get("min", -5.0),
            )

        elif criterion_id == "protease_sites":
            candidate_total = pharma["protease_sites"]["total_sites"]
            native_pharma = compute_pharmacology(_NATIVE_SST14)
            native_total = native_pharma["protease_sites"]["total_sites"]
            delta = candidate_total - native_total
            max_delta = thresh.get("max_delta_vs_native", 2)
            result.update(
                value=candidate_total,
                detail=f"native={native_total}, Δ={delta:+d}",
                passed=delta <= max_delta,
            )

        elif criterion_id == "charge_ph_profile":
            cp = pharma["charge_ph_profile"]
            val = abs(cp["charge_at_ph74"])
            result.update(
                value=round(cp["charge_at_ph74"], 2),
                detail=f"pH7.4={cp['charge_at_ph74']:+.2f}, pH6.5={cp['charge_at_ph65']:+.2f}, Δ={cp['delta_charge_tumor_vs_plasma']:+.2f}",
                passed=val <= thresh.get("max_abs_charge_ph74", 5.0),
            )

        elif criterion_id == "blosum62":
            bl = pharma["blosum62"]
            val = bl["avg_score"]
            result.update(
                value=val,
                detail=f"{bl['n_mutations']} mutations: {bl['n_conservative']} conserv, {bl['n_non_conservative']} non-conserv",
                passed=val >= thresh.get("min_avg_score", -2.0),
            )

        elif criterion_id == "metal_coordination":
            mc = pharma["metal_coordination"]
            val = mc["n_strong"]
            result.update(
                value=val,
                detail=f"total={mc['total_count']}, risk={mc['chelator_interference_risk']}",
                passed=val <= thresh.get("max_strong", 1),
            )

        elif criterion_id == "nephrotox":
            neph = compute_nephrotox_risk(pharma["sequence"])
            risk = neph["risk_level"]
            max_level = thresh.get("max_risk_level", "Moderate")
            level_order = {"Low": 0, "Moderate": 1, "High": 2}
            val = neph["renal_risk_score"]
            result.update(
                value=val,
                detail=f"{risk} (score {val}), {neph.get('warning', '')}",
                passed=level_order.get(risk, 2) <= level_order.get(max_level, 1),
            )

        # Statistical criteria — return placeholder (needs experiment records)
        elif criterion_id in ("rank_stability", "score_consistency", "no_dominance"):
            result.update(
                value=None,
                detail="Requires multi-run experiment data",
                passed=True,
                skipped=True,
            )

        else:
            result.update(value=None, passed=False, error="not implemented")

    except Exception as exc:
        result.update(value=None, passed=False, error=str(exc))

    return result


# ── Main validation entry point ──────────────────────────────────────────────

def validate_unified(
    sequences: list[str],
    criteria: list[str] | None = None,
    threshold_overrides: dict[str, dict] | None = None,
    reference: str = _NATIVE_SST14,
) -> dict[str, Any]:
    """Run unified validation on a list of candidate sequences.

    Parameters
    ----------
    sequences : list of sequence strings
    criteria : list of criterion IDs to evaluate (None = all default_enabled)
    threshold_overrides : per-criterion threshold overrides
    reference : reference sequence for BLOSUM62 / protease delta

    Returns
    -------
    dict with per-candidate results, each with per-criterion breakdown
    """
    if criteria is None:
        criteria = [k for k, v in CRITERIA_REGISTRY.items() if v["default_enabled"]]

    overrides = threshold_overrides or {}
    results = []

    for seq in sequences:
        seq_upper = seq.upper().strip()
        pharma = compute_pharmacology(seq_upper, reference)

        checks = []
        n_passed = 0
        n_failed = 0
        n_skipped = 0

        for crit_id in criteria:
            custom_thresh = overrides.get(crit_id)
            check = _evaluate_criterion(crit_id, pharma, custom_thresh)
            checks.append(check)
            if check.get("skipped"):
                n_skipped += 1
            elif check.get("passed"):
                n_passed += 1
            else:
                n_failed += 1

        n_evaluated = n_passed + n_failed
        pass_rate = (n_passed / n_evaluated * 100) if n_evaluated > 0 else 0

        if pass_rate >= 80:
            verdict = "PASS"
        elif pass_rate >= 60:
            verdict = "CAUTION"
        else:
            verdict = "FAIL"

        results.append({
            "sequence": seq_upper,
            "verdict": verdict,
            "pass_rate": round(pass_rate, 1),
            "n_passed": n_passed,
            "n_failed": n_failed,
            "n_skipped": n_skipped,
            "n_total": len(criteria),
            "checks": checks,
        })

    return {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "criteria_used": criteria,
        "n_candidates": len(results),
        "results": results,
    }


def get_criteria_registry() -> dict:
    """Return the full criteria registry for frontend rendering."""
    return {
        "criteria": CRITERIA_REGISTRY,
        "presets": PRESETS,
    }
