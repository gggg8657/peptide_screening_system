# Layer 1 Ensemble Implementation Notes — 2026-05-20

## Scope

- Added `pipeline_local/scoring/layer1_ensemble.py`.
- Added `pipeline_local/scoring/ensemble_router.py`.
- Added focused tests in `pipeline_local/tests/test_layer1_ensemble.py`.
- Patched `pipeline_local/scripts/pharmacology_guards.py` with Layer 1 ensemble metadata.

## Wrapper status observed

- `predict_halflife_pepmsnd.py` exposes PlifePred2, but the existing wrapper and H-06 guard state that its output is a probability/ranking score, not hours.
- No callable HLE regression wrapper is present in this checkout. PR #74 / commit `f2460e5` only adds confidence metadata for `halflife_hle_regression_albumin`.
- pepADMET HBM remains web-only. The local wrapper checks `https://pepadmet.ddai.tech/` and marks blocked/unreachable responses explicitly.

## Implementation decision

`compute_layer1_halflife()` includes only predictions that provide an explicit numeric half-life value in hours. Missing tools, HTTP 403, unimplemented parsers, and probability/ranking scores are returned under `individual_predictions[tool]["unavailable"] = True`.

This avoids converting PlifePred2 scores or web availability checks into serum half-life hours.
