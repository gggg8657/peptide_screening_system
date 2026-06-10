# Linear Issue Drafts (PyRosetta Separate Track)

## 1) Engineering / Code

Title:
`[ai4sci-kaeri] Add PyRosetta notebook flow adapter`

Description:

Background:
- PyRosetta notebook flow is currently experiment-oriented and not directly reusable in pipeline execution.

Implementation Plan:
- Add `pyrosetta_flow/adapter.py`, `pyrosetta_flow/runner.py`, `pyrosetta_flow/schema.py`
- Add executable script `scripts/run_pyrosetta_flow.py`
- Save comparable outputs as JSON artifact

Definition of Done:
- Notebook-equivalent flow runs via CLI entry
- Artifact JSON generated with approach A/B candidate summaries

Estimate:
- `4h`

Suggested branch:
- `feature/fit-pyrosetta-notebook-flow`

Commit message draft:
- `feat: add PyRosetta notebook flow adapter [#ISSUE_KEY]`

## 2) Engineering / Code

Title:
`[ai4sci-kaeri] Wire PyRosetta flow into pipeline entrypoint`

Description:

Background:
- New flow needs optional invocation from existing entrypoint without touching core silo/orchestrator logic.

Implementation Plan:
- Add `--enable-pyrosetta-flow` path in `run_pipeline_live.py`
- Add required flags for input/output/env

Definition of Done:
- `run_pipeline_live.py` can invoke the new flow via flag
- Default execution path remains unchanged when flag is absent

Estimate:
- `2h`

Suggested branch:
- `feature/fit-pyrosetta-notebook-flow`

Commit message draft:
- `feat: wire PyRosetta flow into live entrypoint [#ISSUE_KEY]`

## 3) Research / Experiment

Title:
`[Research] Validate fitted flow against notebook baseline`

Description:

Background:
- Functional fitting requires explicit result consistency check against notebook baseline behavior.

Goal:
- Compare fitted flow vs notebook results on the same template and candidate count

Definition of Done:
- Comparison summary created (best ddG, mean ddG, runtime notes)
- Any major mismatch has hypothesis and next action

Estimate:
- `2h`

Suggested branch:
- `feature/fit-pyrosetta-notebook-flow`

Commit message draft:
- `docs: add fitted-flow validation notes [#ISSUE_KEY]`
