# HLE Regression Callable Wrapper — 2026-05-21

## Summary

- Added callable wrapper: `pipeline_local.scripts.predict_halflife_pepmsnd.predict_halflife_hle_regression`.
- Integrated Layer 1 adapter: `pipeline_local.scoring.layer1_ensemble._predict_hle_regression`.
- Updated `ENDPOINT_CONFIDENCE["halflife_hle_regression_albumin"]` with callable path and `d_amino_acid_support=False`.
- No model coefficients, weights, executable, or repo-local HLE artifact were found under `pipeline_local/`; the wrapper therefore returns `unavailable` instead of inventing half-life hours.

## Model Source / Artifact Status

- Repo search: `rg -n 'hle|HLE|halflife_hle|albumin|ENDPOINT_CONFIDENCE' pipeline_local ...` and `find pipeline_local -iname '*hle*' -o -iname '*albumin*' -o -iname '*ezan*'`.
- Found metadata and release-note references only; no callable model artifact before this change.
- Public source checked: ScienceDirect article "Development of a predictive algorithm for the efficacy of half-life extension strategies", Int J Pharm 660:124382, DOI `10.1016/j.ijpharm.2024.124382`.
- Public abstract confirms HLE regression family and reported model performance: half-life R2 `0.879`, clearance R2 `0.820`, Vd R2 `0.937`.
- Public abstract does not expose enough regression coefficients to compute peptide half-life hours. Current wrapper is intentionally unavailable until a verified coefficient table/model file is added.

## Wrapper Design

Return schema:

```python
{
    "predicted_hours": float | None,
    "method": "hle_regression_albumin" | "unavailable",
    "absolute_confidence": "P3" | "P4",
    "warnings": list[str],
}
```

Current behavior:

- Standard L-AA sequence: callable returns `predicted_hours=None`, `method="unavailable"`, `recommended=True`, `absolute_confidence="P4"`.
- D-AA/non-standard notation: callable rejects input with `recommended=False`, `unavailable=True`.
- Layer 1 includes HLE in weighted average only when `predicted_hours` is numeric and hour-valued.

## Test Results

```text
conda run -n bio-tools pytest pipeline_local/tests/test_layer1_ensemble.py pipeline_local/tests/test_pharmacology_guards.py -q
84 passed in 0.33s

conda run -n bio-tools pytest pipeline_local/tests/ -q
713 passed, 5 skipped, 2 xfailed, 15 warnings in 65.31s
```

## Layer 1 L-AA Smoke

Command:

```bash
conda run -n bio-tools python -c '... compute_layer1_halflife("AGAKNFFWKTFTSA") ...'
```

Observed:

```json
{
  "sequence": "AGAKNFFWKTFTSA",
  "ensemble_halflife_hours": null,
  "tools_used": [],
  "tools_unavailable": ["plifepred", "hle_regression", "pepadmet_hbm"],
  "absolute_confidence": "UNAVAILABLE",
  "recommended": true,
  "unavailable": true,
  "hle_reason": "HLE regression coefficients/model artifact are not present in this checkout."
}
```

Interpretation: Layer 1 now calls HLE through a real wrapper path, but correctly refuses to fabricate hours without verified regression parameters.
