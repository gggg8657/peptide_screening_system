# PlifePred2 Hour Conversion Review — 2026-05-20

## Finding

No defensible general conversion from PlifePred2 ranking/probability score to half-life hours was found.

- PyPI/package metadata describes the output CSV `Halflife` column as `Predicted probability`.
- Installed `plifepred2==1.0` source loads a scikit-learn model and writes `model.predict_proba(X)[:, 1]` to the `Halflife` column when available.
- The Mathur et al. 2018 PlifePred paper reports half-life modeling in blood, but the installed PlifePred2 package does not expose a documented score-to-hour regression formula.

Therefore arbitrary PlifePred2 scores are treated as rank-only. The wrapper returns:

- `rank_score`: raw PlifePred2 score
- `predicted_hours`: `None` for ordinary inputs
- `conversion_method`: `unavailable`
- `absolute_confidence`: `P4`

## Implemented Calibration Table

Only exact benchmark lookup values are allowed. This is not a fitted conversion and must not be applied to novel sequences.

| Benchmark | Input key | Known t1/2 | Wrapper hours | Method |
|---|---:|---:|---:|---|
| SST-14 | `AGCKNFFWKTFTSC` | 3 min project benchmark; NCBI/StatPearls reports 1-3 min | 0.05 h | `calibration_table` |

## Four-Benchmark Check

| Benchmark | Known/reference t1/2 | PlifePred2 applicability | Wrapper result |
|---|---:|---|---|
| SST-14 | 3 min project benchmark | L-AA sequence can be scored; endogenous peptide is cyclic/disulfide, so Layer 1 router still treats it as non-linear | `rank_score=3.3801775046779348`, `predicted_hours=0.05` |
| Octreotide | ~100 min subcutaneous elimination half-life | Modified cyclic octapeptide with D-residue/C-terminal alcohol; PlifePred2 natural model input is not an exact representation | `predicted_hours=None` unless an exact supported benchmark key is added |
| Lanreotide | ~2 h immediate-release systemic half-life; depot/autogel values are formulation-driven days | Modified cyclic octapeptide with non-natural residues | `predicted_hours=None` |
| RC-160 / Vapreotide | ~30 min | Modified cyclic octapeptide | `predicted_hours=None` |

## Decision

Layer 1 now consumes PlifePred through `predict_halflife_plifepred()`.

- If `predicted_hours` is a finite number, PlifePred contributes to the weighted hour ensemble.
- If `predicted_hours` is `None`, PlifePred is reported unavailable with reason `PlifePred2 rank only, hours unavailable`.
- No score scaling, regression coefficient, or monotonic mapping was invented.

## Sources Checked

- PlifePred2 PyPI/package metadata: output format labels `Halflife` as `Predicted probability`.
- Installed source: `/home/dongjukim/miniforge3/envs/peptools/lib/python3.11/site-packages/plifepred2/plifepred2.py`.
- Mathur D. et al. 2018, PLOS ONE 13(6): e0196829.
- NCBI Bookshelf/StatPearls somatostatin overview: SST-14 half-life reported as 1-3 min.
- Drug reference summaries for octreotide (~100 min), lanreotide immediate-release (~2 h), and vapreotide/RC-160 (~30 min).
