# Mock / Fake / Hardcoded Data Audit Report

**Auditor**: QA Integrity Audit
**Date**: 2026-02-25 (audited) | **Last updated**: 2026-03-04
**Scope**: All pipeline, agent, frontend, and demo files in `ai4sci-kaeri/`
**Severity Scale**:
- **CRITICAL** -- Value presented as real computation but is fabricated; corrupts scientific conclusions
- **MAJOR** -- Misleading to a reader who does not check source code carefully
- **MINOR** -- Acceptable fallback, clearly labeled, or test-only code

## Remediation Status (2026-03-04)

The refactoring plan (22 items completed) addressed several security and code quality
issues, but **the mock/hardcoded data findings remain largely unchanged** as they are
by-design for the current PyRosetta-only (Silo B) mode:

| Finding | Status | Notes |
|---------|--------|-------|
| #1 (runner.py hardcoded metrics) | **Open — by design** | Silo B only computes ddG via PyRosetta; pLDDT/lDDT/dock_score require NIM APIs (Silo A) |
| #2 (run_pipeline_live.py simulations) | **Open — by design** | Live pipeline uses simulation fallbacks when NIM/PyRosetta unavailable |
| #3 (run_pipeline_demo.py) | **Accepted** | Clearly labeled demo file |
| #4 (frontend mock fallback) | **Improved** | Mock label more visible; live/mock state clearly distinguished |
| #5-8 (stub results) | **Open** | Stub/fallback values remain for tool-unavailable scenarios |
| #9-12 (minor fallbacks) | **Accepted** | Defensive fallbacks with clear labeling |

> **Key insight**: Most CRITICAL findings are inherent to the dual-pipeline architecture.
> Silo B (pyrosetta_flow) only produces real ddG values. Full metric computation requires
> Silo A (AG_src/pipeline) with NIM API integration. See [ARCHITECTURE.md](ARCHITECTURE.md)
> and [TODO_NIM_FULL_PIPELINE.md](TODO_NIM_FULL_PIPELINE.md) for the integration roadmap.

---

## 1. CRITICAL: Hardcoded pLDDT / lDDT / dock_score / selectivity in runner.py (PyRosetta Flow)

### 1a. `_candidate_to_qc()` -- lines 63-76

**File**: `pyrosetta_flow/runner.py`

```python
plddt_mean=85.0 if objective_mode == "ddg_only" else 80.0,
plddt_interface=82.0 if objective_mode == "ddg_only" else 78.0,
dock_score=-8.0 - min(0.0, candidate.ddg) * 0.1,
lddt=0.75,
```

| Field | Value | Source | Verdict |
|-------|-------|--------|---------|
| `plddt_mean` | 85.0 or 80.0 | **Hardcoded constant** | CRITICAL -- No ESMFold/OpenFold prediction runs; value is fabricated |
| `plddt_interface` | 82.0 or 78.0 | **Hardcoded constant** | CRITICAL -- Same as above |
| `dock_score` | `-8.0 - min(0, ddg)*0.1` | **Fabricated formula** | CRITICAL -- Not from DiffDock or any docking engine; it is a synthetic linear function of ddG |
| `lddt` | 0.75 | **Hardcoded constant** | CRITICAL -- No FoldMason or structural alignment runs |

**Impact**: These values flow into the QCRankerAgent, are used for gate decisions, written to `rank_table.csv`, and displayed in reports. A reader of the rank table would assume pLDDT=85.0 means ESMFold computed high confidence. It does not.

**Recommended fix**: Either (a) run ESMFold/FoldMason to get real values, or (b) set all fields to `NaN`/`None` and clearly label them as "not computed" in all outputs.

---

### 1b. `_emit_candidates()` -- lines 109-126

**File**: `pyrosetta_flow/runner.py`

```python
"pLDDT": 85.0 if c.objective_mode == "ddg_only" else 80.0,
"dockScore": round(-8.0 - min(0.0, c.ddg) * 0.1, 3),
"ddG": round(c.ddg, 3),          # <-- ddG IS real (from PyRosetta)
"lDDT": 0.75,
"selectivity": 0.0,
"finalScore": round(-c.ddg, 3),
```

Same hardcoded values are emitted to the **frontend dashboard** via `StatusEmitter.set_candidates()`. A user watching the live dashboard sees `pLDDT=85.0` and `lDDT=0.75` as if they were measured.

| Field | Severity |
|-------|----------|
| `pLDDT` 85.0/80.0 | CRITICAL |
| `dockScore` formula | CRITICAL |
| `lDDT` 0.75 | CRITICAL |
| `selectivity` 0.0 | MAJOR -- always zero, never computed in this flow |
| `finalScore` = `-ddG` | MAJOR -- ignores pLDDT/lDDT/dock entirely despite weighted formula in QCRanker |

---

### 1c. `run_records` experiment log -- lines 406-428

**File**: `pyrosetta_flow/runner.py`

```python
"plddt": 85.0 if c.objective_mode == "ddg_only" else 80.0,
"dock_score": round(-8.0 - min(0.0, c.ddg) * 0.1, 3),
"lddt": 0.75,
"selectivity": 0.0,
"final_score": round(-c.ddg, 3),
```

These hardcoded values are **persisted to `experiment_log.jsonl`** and used for historical ranking across runs. The contamination propagates to all future runs that read historical data.

**Severity**: CRITICAL

---

### 1d. `set_best_candidate()` -- lines 582-589

**File**: `pyrosetta_flow/runner.py`

```python
emitter.set_best_candidate({
    "id": best.candidate_id,
    "sequence": best.sequence,
    "plddt": 85.0 if best.objective_mode == "ddg_only" else 80.0,
    "dockScore": round(-8.0 - min(0.0, best.ddg) * 0.1, 3),
})
```

The "best candidate" shown in the dashboard header also has fabricated pLDDT and dock score.

**Severity**: CRITICAL

---

## 2. CRITICAL: Simulated Docking Scores in run_pipeline_live.py

### 2a. Step 05 -- DiffDock is entirely simulated (lines 558-572)

**File**: `run_pipeline_live.py`

```python
# STEP 5: Docking scores (simulated with pLDDT-correlated mock)
base_score = -(r["plddt_mean"] / 10.0) + random.gauss(0, 1.0)
dock_results.append({
    "seq_id": r["seq_id"],
    "dock_score": round(base_score, 2),
    "confidence": round(random.uniform(0.6, 0.95), 2),
})
```

DiffDock is **never called**. The dock score is fabricated from `pLDDT / -10 + noise`. The confidence is `random.uniform(0.6, 0.95)` -- pure random.

**Severity**: CRITICAL -- Comment says "simulated" but the dashboard shows these as real docking scores.

---

### 2b. Step 06 -- Rosetta simulation fallback (lines 692-705)

**File**: `run_pipeline_live.py`

```python
# Simulation fallback (original logic)
ddg = dr["dock_score"] * 0.8 + random.gauss(0, 1.5)
rosetta_results.append({
    "ddg": round(ddg, 1),
    "clash": random.choice([0, 0, 0, 1]),
    ...
})
```

When PyRosetta is not available (or fails), ddG is fabricated from `dock_score * 0.8 + noise` and clash is randomized. The config default `fallback_to_simulation: true` means this is the **most likely execution path** on machines without PyRosetta.

**Severity**: CRITICAL

---

### 2c. Step 05b -- Selectivity estimation fallback (lines 802-823)

**File**: `run_pipeline_live.py`

```python
ot = {
    "SSTR1": sstr2_ddg + random.gauss(15.0, 3.0),
    "SSTR3": sstr2_ddg + random.gauss(18.0, 4.0),
    "SSTR4": sstr2_ddg + random.gauss(20.0, 3.5),
    "SSTR5": sstr2_ddg + random.gauss(12.0, 3.0),
}
```

Off-target docking scores are **invented by adding Gaussian noise** to SSTR2 ddG. The offsets (15.0, 18.0, 20.0, 12.0) are arbitrary. Even the "live" PyRosetta path uses this same random fallback when individual off-target docking fails (lines 776-778).

**Severity**: CRITICAL

---

### 2d. Step 07 -- lDDT fallback with random.uniform (line 920)

**File**: `run_pipeline_live.py`

```python
"lDDT": step07_lddt_scores.get(sid, round(random.uniform(0.55, 0.9), 3)),
```

When FoldMason lDDT is not available for a candidate, lDDT is filled with `random.uniform(0.55, 0.9)` -- pure random noise masquerading as a structural quality metric.

**Severity**: CRITICAL

---

### 2e. Interface pLDDT approximation (line 992)

**File**: `run_pipeline_live.py`

```python
plddt_interface=r.get("plddt_mean", 0.0) * 0.85,  # approximate interface pLDDT
```

Interface pLDDT is fabricated as `mean_pLDDT * 0.85`. There is no per-residue analysis of interface residues.

**Severity**: MAJOR -- At least the formula is documented with a comment, but the 0.85 factor is arbitrary.

---

## 3. CRITICAL: run_pipeline_demo.py -- All Data is Mock

**File**: `run_pipeline_demo.py`

The entire file is a demo with all external tools replaced by `MagicMock`:

| Function | What it fakes | Lines |
|----------|---------------|-------|
| `make_step01()` | Receptor prep (hardcoded pocket residues) | 94-100 |
| `make_step02()` | RFdiffusion (hardcoded 10 backbone names) | 102-107 |
| `make_step03()` | ProteinMPNN (truncated DOTATATE sequence) | 109-119 |
| `make_step04()` | ESMFold QC (`random.gauss(78, 12)` for pLDDT) | 121-136 |
| `make_step05()` | DiffDock (`random.gauss(-6.5, 2.0)` for dock score) | 138-151 |
| `make_step05b()` | Selectivity (`random.gauss` offsets) | 153-178 |
| `make_step06()` | PyRosetta (`random.gauss(-6.0, 2.5)` for ddG) | 180-193 |
| `make_step07()` | FoldMason/PyMOL (hardcoded paths) | 195-201 |

**Severity**: MINOR for the demo file itself (it is clearly labeled as "dry-run mode" in docstring). However:
- **MAJOR** concern: The demo produces output files in `runs/` that are indistinguishable from real pipeline output.
- A user could accidentally run `run_pipeline_demo.py`, then switch to `run_pipeline_live.py` and inherit contaminated historical data from `experiment_log.jsonl`.

---

## 4. MAJOR: Frontend Mock Data Displayed When Backend Offline

### 4a. `frontend/src/data/mockData.ts`

**File**: `frontend/src/data/mockData.ts`

This file generates 50 fake candidates with `randomInRange()` for pLDDT, dockScore, ddG, lDDT, selectivity, and finalScore. It also contains hardcoded QC gate statistics and convergence data showing improvement from ddG=-5.2 to ddG=-8.6 over 5 iterations.

### 4b. `frontend/src/App.tsx` -- lines 51-63

```typescript
const steps = isLive ? live.steps : PIPELINE_STEPS
const agents = isLive ? live.agents : AGENTS
const candidates = isLive ? live.candidates : CANDIDATES   // <-- mock fallback
const qcGates = isLive ? live.qcGates : QC_GATES
const convergence = isLive ? live.convergence : CONVERGENCE_DATA
```

When the backend is not connected, the dashboard silently falls back to mock data. The only indicator is a small "Mock" label in the header (line 216). The convergence graph showing beautiful improvement from -5.2 to -8.6 is entirely fabricated.

**Severity**: MAJOR -- A screenshot of this dashboard could be mistaken for real results. The "Mock" label is subtle (11px gray text).

### 4c. `frontend/src/mockData.ts` (legacy file)

A second mock data file exists at `frontend/src/mockData.ts` with 50 randomly generated candidates. This appears to be an older version but is still present.

**Severity**: MINOR (not currently imported by App.tsx, which uses `data/mockData.ts` instead).

---

## 5. MAJOR: step06_rosetta.py Stub Results

**File**: `AG_src/pipeline/step06_rosetta.py`

```python
def _stub_rosetta_result(complex_pdb: str) -> RosettaResult:
    """PyRosetta not installed; returning STUB result. ddg=0.0 is NOT a real calculation."""
    return RosettaResult(seq_id="", ddg=0.0, total_score=0.0, clash_score=0, ...)
```

When PyRosetta subprocess fails, a stub result with `ddg=0.0` is returned. The warning is logged but the `ddg=0.0` value propagates downstream. Similarly, `compute_binding_ddg()` returns `0.0` on failure (line 259).

**Severity**: MAJOR -- `ddg=0.0` is misleading; it suggests neutral binding when in reality no computation was performed.

**Recommended fix**: Return `ddg=float('nan')` or `ddg=999.0` (sentinel) and propagate a `fail_reason` flag.

---

## 6. MAJOR: step07_analysis.py Placeholder lDDT

**File**: `AG_src/pipeline/step07_analysis.py`

```python
# FoldMason failed fallback (line 248):
lddt_scores = {Path(p).stem: 0.0 for p in pdb_paths}

# FoldMason parse failure fallback (line 237):
lddt_scores = {Path(p).stem: 1.0 for p in pdb_paths}
```

Two different fallbacks:
- On FoldMason **crash**: all lDDT = 0.0
- On FoldMason **parse failure**: all lDDT = 1.0 (perfect score!)

The `lDDT=1.0` fallback is particularly dangerous -- it would cause all candidates to pass the lDDT gate with perfect scores.

**Severity**: MAJOR for `lDDT=1.0`; MINOR for `lDDT=0.0` (conservative).

---

## 7. MAJOR: Interface Analysis Stubs in step07_analysis.py

**File**: `AG_src/pipeline/step07_analysis.py` (lines 310-325)

```python
buried_sasa=float(len(contact_rec) * 25),   # ~25 A^2 per contact residue stub
n_hbonds=max(0, len(contact_rec) // 3),
n_salt_bridges=max(0, len(contact_rec) // 10),
```

When BioPython is available, buried SASA, H-bonds, and salt bridges are approximated from contact count using rough heuristics (25 A^2/contact, 1 hbond per 3 contacts, 1 salt bridge per 10 contacts). When BioPython is unavailable, all values are 0.

**Severity**: MAJOR -- These structural descriptors are presented in reports without caveat.

---

## 8. MAJOR: MCP PyRosetta Server Placeholders

**File**: `AG_src/tools/mcp/pyrosetta_server.py`

```python
"reweighted_score": score,  # placeholder: use reweighted scorefxn (line 498)
"dSASA_hphobic": 0.0,       # placeholder (line 600)
"dSASA_polar": 0.0,          # placeholder (line 601)
```

Interface analysis fields `dSASA_hphobic` and `dSASA_polar` are hardcoded to 0.0. The `reweighted_score` just echoes the unweighted score.

**Severity**: MAJOR -- If these values are displayed in reports, they misrepresent the interface character.

---

## 9. MINOR: run_pipeline_live.py -- Steps 02/03 Explicitly Mocked

**File**: `run_pipeline_live.py`

```python
# Line 436: step_h("STEP 02", "RFdiffusion - backbone generation (dry-run mock)")
# Line 444: backbones.append({... "pdb": f"MOCK-BB-{i}"})
# Line 450: step_h("STEP 03", "ProteinMPNN - sequence design (dry-run mock)")
```

Steps 02 (RFdiffusion) and 03 (ProteinMPNN) are explicitly labeled as "dry-run mock" in the live pipeline. The backbone PDB paths contain "MOCK-BB-" prefix.

**Severity**: MINOR -- Clearly labeled. However, these mock backbones are used as inputs to ESMFold (Step 04), which does make real API calls, creating a confusing mix of real and fake data.

---

## 10. MINOR: pipeline_config.yaml `fallback_to_simulation: true`

**File**: `AG_src/config/pipeline_config.yaml` (line 207)

```yaml
fallback_to_simulation: true
```

This is the **default configuration**. It means any new user running the pipeline will silently get simulated PyRosetta results when PyRosetta is not installed, with no prominent warning in the output files.

**Severity**: MAJOR -- The default should be `false` to force users to acknowledge they are getting simulated data.

---

## 11. MINOR: Docking Engine Fallback Scores

**File**: `AG_src/pipeline/step05_docking.py` (line 222)

```python
or [-float(i) for i in range(len(poses))]  # fallback dummy scores
```

When the docking engine returns no scores, dummy scores `-0.0, -1.0, -2.0, ...` are generated based on pose index.

**Severity**: MINOR -- Defensive fallback, but scores are meaningless.

---

## 12. MINOR: Selectivity Placeholder Confidence

**File**: `AG_src/pipeline/step05b_selectivity.py` (line 184)

```python
confidence=0.0,  # placeholder
```

Off-target docking confidence is always 0.0.

**Severity**: MINOR -- Only affects logging/display, not gate decisions.

---

## Summary Table

| # | File | What is Faked | Severity | Lines |
|---|------|---------------|----------|-------|
| 1a | `pyrosetta_flow/runner.py` | pLDDT=85/80, pLDDT_iface=82/78, dock_score formula, lDDT=0.75 in QC conversion | CRITICAL | 63-76 |
| 1b | `pyrosetta_flow/runner.py` | Same values emitted to dashboard | CRITICAL | 109-126 |
| 1c | `pyrosetta_flow/runner.py` | Same values persisted to experiment_log.jsonl | CRITICAL | 406-428 |
| 1d | `pyrosetta_flow/runner.py` | Best candidate display | CRITICAL | 582-589 |
| 2a | `run_pipeline_live.py` | DiffDock scores = `-pLDDT/10 + noise` | CRITICAL | 558-572 |
| 2b | `run_pipeline_live.py` | Rosetta ddG simulation fallback | CRITICAL | 692-705 |
| 2c | `run_pipeline_live.py` | Off-target selectivity = `ddG + gauss(15-20)` | CRITICAL | 802-823 |
| 2d | `run_pipeline_live.py` | lDDT = `random.uniform(0.55, 0.9)` fallback | CRITICAL | 920 |
| 2e | `run_pipeline_live.py` | Interface pLDDT = `mean * 0.85` | MAJOR | 992 |
| 3 | `run_pipeline_demo.py` | All 8 pipeline steps fully mocked | MINOR | 94-201 |
| 4a | `frontend/src/data/mockData.ts` | 50 random candidates, fake convergence curve | MAJOR | 83-145 |
| 4b | `frontend/src/App.tsx` | Silent fallback to mock data when backend offline | MAJOR | 51-63 |
| 5 | `AG_src/pipeline/step06_rosetta.py` | Stub ddG=0.0 when PyRosetta unavailable | MAJOR | 533-538 |
| 6 | `AG_src/pipeline/step07_analysis.py` | Placeholder lDDT=0.0 or 1.0 on FoldMason failure | MAJOR | 237-248 |
| 7 | `AG_src/pipeline/step07_analysis.py` | Interface SASA/hbond/salt bridge heuristics | MAJOR | 310-316 |
| 8 | `AG_src/tools/mcp/pyrosetta_server.py` | dSASA_hphobic=0.0, dSASA_polar=0.0 placeholders | MAJOR | 598-601 |
| 9 | `run_pipeline_live.py` | Steps 02/03 mock backbones/sequences | MINOR | 436-450 |
| 10 | `pipeline_config.yaml` | `fallback_to_simulation: true` default | MAJOR | 207 |
| 11 | `AG_src/pipeline/step05_docking.py` | Fallback dummy dock scores | MINOR | 222 |
| 12 | `AG_src/pipeline/step05b_selectivity.py` | Confidence=0.0 placeholder | MINOR | 184 |

---

## Recommendations

### Immediate (before any paper submission or presentation)

1. **runner.py**: Replace all hardcoded pLDDT/lDDT/dock_score/selectivity with `None` or `NaN`. Add a `"data_source": "not_computed"` flag to all emitted records. Only the `ddg` field (from actual PyRosetta FlexPepDock) is real.

2. **run_pipeline_live.py**: Remove the simulated docking fallback or clearly tag every record with `"simulated": true` that propagates to the dashboard and CSV outputs.

3. **pipeline_config.yaml**: Change `fallback_to_simulation: false` as default. Require users to explicitly opt in.

4. **Frontend**: Add a prominent full-width banner (not just a small badge) when showing mock data. Consider disabling the dashboard entirely when no live data exists.

### Medium-term

5. **experiment_log.jsonl**: Add a `data_source` field to every record (`"pyrosetta_real"`, `"simulated"`, `"not_computed"`) so contaminated historical data can be identified and filtered.

6. **step06_rosetta.py**: Change stub `ddg=0.0` to `ddg=float('inf')` or `ddg=999.0` with `fail_reason="pyrosetta_unavailable"`.

7. **step07_analysis.py**: Change FoldMason parse-failure fallback from `lDDT=1.0` to `lDDT=0.0` or `NaN`.

### Long-term

8. Implement a data provenance system that tracks which values are computed vs. estimated vs. fabricated, and displays this information in all reports and the dashboard.

---

## What IS Real

For clarity, these values **are** computed by actual tools when the tools are available:

| Value | Source | Condition |
|-------|--------|-----------|
| `ddg` (runner.py flow) | PyRosetta InterfaceAnalyzerMover via `flexpep_dock.py` | Always real in PyRosetta flow |
| `total_score` | PyRosetta `get_fa_scorefxn()` | Always real in PyRosetta flow |
| `clash_score` | PyRosetta per-residue `fa_rep > 10.0` count | Always real in PyRosetta flow |
| `pLDDT` (run_pipeline_live.py) | ESMFold NIM API | Only when NIM API key is set and API returns 200 |
| `ddg` (run_pipeline_live.py) | PyRosetta FlexPepDock | Only when PyRosetta conda env is available |
| Selectivity (run_pipeline_live.py) | PyRosetta off-target docking | Only when PyRosetta + AlphaFold structures available |

The mutation generation (`generate_random_mutant` in adapter.py) is legitimate -- it uses seeded RNG to produce sequence variants, which is standard practice.

---

## Security Fixes Applied (2026-03-04)

While mock data findings remain open by design, the following security issues from
the related CODE_REVIEW.md have been resolved:

- **C1 Path traversal**: `pathlib.relative_to()` replaces `.startswith()` in all file-serving endpoints
- **C2 Cache mutation**: `copy.deepcopy()` on all `_read_status()` returns
- **C3 Subprocess timeout**: 300s timeout on FlexPepDock subprocess calls
- **C4 JSON parse guard**: `try/except (JSONDecodeError, ValueError)` around stdout parsing
- **C5 File locking**: `fcntl.flock()` in `StatusEmitter.flush()` prevents concurrent write corruption

---

*End of audit report.*
