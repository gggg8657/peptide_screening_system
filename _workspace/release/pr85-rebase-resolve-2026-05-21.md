# PR #85 rebase / conflict resolution report — 2026-05-21

## Scope

- Branch: `feat/layer1-ensemble-framework-20260520`
- Base after fetch: `origin/main` = `94b49f571c40124dc1ec408272f1612eae5b18ae`
- Rebased original commits: 5
- Worktree used: `.worktrees/pr85-rebase` to avoid touching dirty files in the primary checkout.

## Rebased commits

1. `chore(backup): 2026-05-20 로컬 WIP 스냅샷 (롤백용 원격 브랜치)`
2. `docs(action-items): 5월 회의 D-8 준비 + audit 사후 갱신`
3. `feat(scoring): Layer 1 ensemble framework (PlifePred + HLE + pepADMET HBM)`
4. `feat(scoring): PlifePred hour wrapper — SST-14 calibration + 정직한 unavailable`
5. `feat(scoring): Layer 2 (pepMSND-local) + Layer 3 (ADMET-AI) ensemble — 정직한 P4/외삽`

## Conflicts

### `runs_local/final_candidates/synthesis_orders/PRST-001.md`

- Conflict source: first replayed backup commit.
- Resolution: kept `origin/main` side because it already contained the 2026-05-20 ADMET revalidation and Gate-2 option B decision text. The replayed side lacked that later decision section and would have rolled it back.
- Intent conflict: none beyond older backup content versus newer main content.

### `runs_local/final_candidates/synthesis_orders/PRST-002.md`

- Conflict source: first replayed backup commit.
- Resolution: kept `origin/main` side because it already contained the 2026-05-20 ADMET revalidation and Gate-2 option B decision text. The replayed side lacked that later decision section and would have rolled it back.
- Intent conflict: none beyond older backup content versus newer main content.

## Additional CI fix

- File: `pipeline_local/tests/test_layer1_ensemble.py`
- Reason: after Layer 2 became a real local pepMSND route, `route_halflife_prediction()` correctly returns `layer2_daa_cyclic_pepmsnd` instead of the old `layer2_daa_cyclic_pepmsnd_stub`.
- Resolution: updated the two stale test expectations while preserving the Layer 1 rejection checks for D-AA/cyclic inputs.

## Verification

Command:

```bash
conda run -n bio-tools pytest pipeline_local/tests/ -q
```

Result:

```text
692 passed, 7 skipped, 2 xfailed, 15 warnings in 63.58s
```

Focused checks also passed:

```text
conda run -n bio-tools pytest pipeline_local/tests/test_layer1_ensemble.py pipeline_local/tests/test_layer3_admet_ai.py pipeline_local/tests/test_pharmacology_guards.py -q
84 passed in 0.26s
```

## Residual issues

- No unresolved merge conflicts.
- No pytest failures after the test expectation fix.
- Warnings are pre-existing runtime/deprecation/stability predictor warnings observed during the full test run; they did not fail the suite.
