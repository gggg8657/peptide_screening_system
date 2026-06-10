# PR #84 rebase resolve — 2026-05-21

## Rebase result

- Worktree: `.worktrees/pr84-rebase`
- Branch: `docs/meeting-prep-and-post-audit-20260520`
- Base: `origin/main` at PR #85 merge commit `5b57481`
- Initial rebase stopped on `8c0b7cc chore(backup): 2026-05-20 로컬 WIP 스냅샷 (롤백용 원격 브랜치)`.
- Conflict files from that backup commit:
  - `docs/meet_log/2026-04-06_action_items/A-10_SSTR3_docking_fix.md`
  - `docs/meet_log/2026-04-06_action_items/README.md`
  - `docs/meet_log/2026-04-06_action_items/STATUS_2026-05-20.md`
  - `pipeline_local/scripts/pharmacology_guards.py`
  - `runs_local/final_candidates/synthesis_orders/PRST-001.md`
  - `runs_local/final_candidates/synthesis_orders/PRST-002.md`
- Resolution: skipped the backup snapshot commit because it touched 92 files and was not the PR #84 7-file docs patch. The following PR #84 docs commit was then dropped by Git as already upstream.

## MEETING_PREP Q&A update

Updated `docs/meet_log/2026-04-06_action_items/MEETING_PREP_2026-05-28.md` for D-7 status:

- PR #85 merged: Layer 1/2/3 framework is now on `main`.
- PR #90 merged: PDB/CIF binding pocket center mismatch fixed by unified `auth_*` parsing; A-01 docking follow-up recalculation recommended.
- PR #92~#100 merged: LLM UX, Mol* mapping, FlexPepDock timeout/worker/sub-progress, orphan cleanup, FE badge, and EOD docs summarized as operational stabilization.

### New Q6~Q8

- Q6 explains negative Layer 2 R² honestly: R²=-0.028, Spearman ρ=-0.119, MAE=33.12h; framework exists but the model is not decision-grade.
- Q7 explains ADMET=1.00 for PRST candidates as an OOD warning requiring wet-lab ADMET/hemolysis/cytotoxicity assays, not a standalone synthesis go/no-go.
- Q8 defines the 6월 meeting roadmap: DGL/pepADMET/PEPlife2 environment cleanup, HBM/wet-lab calibration data, Layer 2 retraining, and PR #90-aligned A-01 docking recalculation.

## CI result

- PR #84 latest-head status after push: `mergeable=MERGEABLE`, `mergeStateStatus=CLEAN`.
- Bio Pipeline CI: all required checks passed on the pushed head.
  - Python Lint & Syntax: SUCCESS
  - Client Import Test: SUCCESS
  - PDB/CIF Structure Validation: SUCCESS
  - Documentation Link Check: SUCCESS
  - Frontend Lint, Test & Build: SUCCESS
  - ai4sci-kaeri Python Lint: SUCCESS
  - NIM API Smoke Test: SKIPPED
- Local verification: `ls -la docs/meet_log/2026-04-06_action_items/` completed; docs-only change after rebase.
