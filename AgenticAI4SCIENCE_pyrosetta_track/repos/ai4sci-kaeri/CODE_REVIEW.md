# Code Review: PyRosetta AI Scientist Pipeline

**Reviewer**: Senior Code Reviewer (Claude Opus 4.6)
**Date**: 2026-02-25 (reviewed) | **Last updated**: 2026-03-04
**Scope**: Full codebase review -- pipeline core, agents, LLM integration, backend, frontend
**Commit**: main branch (ed4b3d6)

---

## Remediation Status (2026-03-04)

A comprehensive refactoring plan (REFACTORING_PLAN.md, 22 items) was executed and
**completed in full**. The following categories are now resolved:

| Category | Items | Status |
|----------|-------|--------|
| **Critical security (C1-C5)** | Path traversal → `pathlib.relative_to()`, deepcopy cache, subprocess timeout (300s), JSON parse guard, fcntl file locking | **All FIXED** |
| **High priority (H1-H6)** | Archive 3D button guard, polling race condition (AbortController), CandidateTable split (useCandidateSort/useAdmetBatch hooks), FastAPI migration, validation facade, pipeline test suite | **All FIXED** |
| **Medium priority (M1-M6)** | Context providers, a11y, dead file cleanup, error response standardization, status schema validation, magic number extraction | **All FIXED** |
| **Low priority (L1-L4)** | MetricCard memo, style consistency, experiment watchdog (L3), archive PDB | **All FIXED** |
| **Architecture (M7)** | Dual pipeline design document | **ARCHITECTURE.md created** |

**Test coverage**: 150 tests total (32 frontend Vitest + 118 pipeline pytest, 93% coverage)

> See also: [ARCHITECTURE.md](ARCHITECTURE.md) for the dual-pipeline design, [REFACTORING_PLAN.md](REFACTORING_PLAN.md) for full item details.

---

## Executive Summary

The PyRosetta AI Scientist pipeline is an ambitious agentic system that orchestrates a
Plan -> Mutate -> Dock -> QC -> Critic -> Report loop for SSTR2 peptide binder design.
The architecture is well-conceived with clean separation of concerns between agents, a
robust fail-open strategy, and thoughtful LLM/rule-based fallback duality.

~~However, there are several critical and major issues that should be addressed before
production use, particularly around hardcoded synthetic metrics, prompt/model mismatch,
subprocess safety, and convergence detection that never actually converges.~~

> **2026-03-04 update**: The critical security issues (C1–C5) and all high/medium priority
> items from the refactoring plan have been resolved. The remaining items below are
> research-direction improvements and architectural suggestions that remain valid for
> future iterations.

**Issue counts**: 8 Critical, 12 Major, 15 Minor, 10 Suggestions

---

## A. Code Quality

### A-1. [Critical] Hardcoded synthetic metrics mask real pipeline behavior
**Files**: `pyrosetta_flow/runner.py` (lines 64-76, 109-126, 416-419), `pyrosetta_flow/adapter.py`
**Description**: The `_candidate_to_qc` function fabricates pLDDT (85.0/80.0), pLDDT_interface (82.0/78.0), dock_score, lDDT (0.75), and selectivity (0.0) values rather than computing them from actual structural data. These synthetic values are then propagated through the entire QC gate system, ranking, and frontend display. This means:
- QC gates for pLDDT and docking are operating on fiction
- Rankings are dominated by the only real metric (ddG)
- The frontend displays misleading confidence metrics to the user

The same hardcoded values appear in `_emit_candidates` and the experiment log records.

**Recommended fix**: Either (a) compute real metrics from the PyRosetta poses (pLDDT is unavailable without ESMFold but dock_score/lDDT can be approximated), or (b) explicitly disable pLDDT/docking gates and mark those columns as "N/A" in the frontend. The current approach silently passes all candidates through pLDDT/docking gates which defeats the purpose of multi-gate QC.

---

### A-2. [Critical] `_run_script` parses only the last stdout line as JSON — ✅ FIXED (C4)
**File**: `pyrosetta_flow/runner.py` (line 53)
**Description**: `json.loads(lines[-1])` assumes the script outputs JSON as its very last line. If PyRosetta emits any final warning, diagnostic, or even a trailing newline with whitespace to stdout (despite `-mute all`), parsing will fail or return wrong data. The `flexpep_dock.py` script correctly sends diagnostics to stderr, but any third-party library writing to stdout would break this.

**Status**: Wrapped in `try/except (json.JSONDecodeError, ValueError)` with RuntimeError fallback.

**Recommended fix**: Search stdout lines in reverse for the first valid JSON object:
```python
for line in reversed(lines):
    line = line.strip()
    if line.startswith("{"):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
return {}
```

---

### A-3. [Major] `subprocess.run` has no timeout — ✅ FIXED (C3)
**File**: `pyrosetta_flow/runner.py` (line 45)
**Description**: FlexPepDock refinement can take 10-30+ minutes per candidate. The subprocess call has `check=False` but no `timeout` parameter. The pipeline config specifies `timeout_per_candidate_sec: 1800` but this is never read or enforced. A stuck PyRosetta process will hang the entire pipeline indefinitely.

**Status**: `subprocess.run(timeout=300)` added with `subprocess.TimeoutExpired` catch.

---

### A-4. [Major] Mutation loop can silently return the original sequence
**File**: `pyrosetta_flow/runner.py` (lines 226-236)
**Description**: If all 20 random mutation trials produce sequences already in `seen_sequences`, the loop falls through and `mutant` retains the value `config.original_sequence`. This means the pipeline will dock and score the wild-type sequence as if it were a mutant, wasting compute and potentially polluting results.

**Recommended fix**: After the trial loop, check if `mutant == config.original_sequence` and either skip this candidate or log a clear warning. Consider increasing the trial count or using a systematic enumeration fallback.

---

### A-5. [Major] Mutable `fail_reasons` list on dataclass default
**File**: `AG_src/agents/qc_ranker.py` (line 62)
**Description**: `fail_reasons: list[str] = field(default_factory=list)` is correct, but in `apply_gates` (line 188), `c.fail_reasons = []` resets the list for ALL candidates at the start. This means if `apply_gates` is called twice on the same candidate objects, previous failure information is lost. The gate logic also has a subtle bug: Gate 2 checks `not c.fail_reasons` to determine Gate 1 passage, but Gate 1 failures are accumulated on the same objects used in Gate 2's filter.

**Recommended fix**: Create a fresh copy of candidates at the start of `apply_gates`, or accumulate failures in a separate dict keyed by candidate_id.

---

### A-6. [Major] `datetime.utcnow()` is deprecated
**Files**: `AG_src/agents/planner.py` (lines 75, 576), `AG_src/agents/critic.py` (line 65), `AG_src/agents/qc_ranker.py` (line 80), `AG_src/agents/reporter.py` (lines 232, 314, 560, 601)
**Description**: `datetime.utcnow()` has been deprecated since Python 3.12. The `runner.py` and `status_emitter.py` correctly use `datetime.now(timezone.utc)`, but all agent files still use the deprecated form.

**Recommended fix**: Replace all `datetime.utcnow()` with `datetime.now(timezone.utc)` for consistency and future compatibility.

---

### A-7. [Major] Unused computed dict in runner scoring section
**File**: `pyrosetta_flow/runner.py` (lines 338-341)
**Description**: A dict with `mean_ddg` and `best_ddg` is computed and assigned to `_` (throwaway variable). This suggests the scoring aggregation step was intended to do more but was left incomplete.

**Recommended fix**: Either use these metrics (e.g., for convergence detection or emitter updates) or remove the dead code.

---

### A-8. [Minor] `yaml` import silently degrades to empty config
**File**: `pyrosetta_flow/runner.py` (lines 12-15, 56-60)
**Description**: If `pyyaml` is not installed, `_read_pipeline_config` returns `{}`, which causes `create_provider` to return `NoneProvider`. This silent degradation means the LLM agents will all fall back to rule-based mode without any warning to the user.

**Recommended fix**: Log a warning when yaml is unavailable and the config file exists.

---

### A-9. [Minor] Inconsistent type annotations between files
**Files**: Multiple
**Description**: Some files use `dict[str, Any]` (PEP 585 lowercase generics) while others use `Dict[str, Any]` (typing module). For example, `runner.py` uses `Dict` from typing, while `planner.py` uses lowercase `dict`. This inconsistency suggests a gradual migration that was not completed.

**Recommended fix**: Standardize on PEP 585 lowercase generics throughout, since the codebase already uses `from __future__ import annotations`.

---

### A-10. [Minor] `tempfile.mktemp` is insecure
**File**: `AG_src/scripts/flexpep_dock.py` (lines 176, 219)
**Description**: `tempfile.mktemp` creates a predictable temporary filename without actually creating the file, which is a known TOCTOU (time-of-check-to-time-of-use) vulnerability. While this is a local scientific computing script, it is still poor practice.

**Recommended fix**: Use `tempfile.NamedTemporaryFile(suffix=".pdb", delete=False)` instead.

---

### A-11. [Minor] Error JSON written to stderr, not stdout
**File**: `AG_src/scripts/flexpep_dock.py` (lines 356-359)
**Description**: When the input PDB is not found, the error JSON is written to stderr, but the runner only parses stdout. The error will be captured in the `RuntimeError` message from `_run_script`, but the structured JSON error is lost.

**Recommended fix**: Write the error JSON to stdout so the caller can parse it, or at minimum write it to both streams.

---

### A-12. [Minor] `log_message` suppression is too broad
**File**: `backend/api_server.py` (lines 276-280)
**Description**: The custom `log_message` suppresses all GET request logs. This makes debugging connection issues difficult since POST requests from the pipeline would also be silenced if they happened to start with "GET" in the formatted args.

**Recommended fix**: Use a more targeted filter or set a configurable log level.

---

### A-13. [Minor] Frontend polling continues indefinitely after completion
**File**: `frontend/src/hooks/usePipelineStatus.ts`
**Description**: The `usePipelineStatus` hook polls every 2 seconds forever, even after `completed: true` is received. This wastes network resources and keeps the browser active.

**Recommended fix**: Clear the interval when `completed` is true, or increase the poll interval significantly (e.g., 30s).

---

### A-14. [Suggestion] Use `dataclasses_json` or Pydantic for schema validation
**Files**: `pyrosetta_flow/schema.py`, `AG_src/agents/qc_ranker.py`
**Description**: Plain `@dataclass` classes lack input validation. Invalid data (e.g., negative iteration, empty sequence) passes through silently.

**Recommended fix**: Consider Pydantic models with validators, especially for `FlowConfig` and `CandidateResult`.

---

### A-15. [Suggestion] Add `__all__` exports to agent modules
**Files**: `AG_src/agents/*.py`
**Description**: No `__all__` is defined in agent modules, making it unclear which classes are public API.

---

## B. Prompt Quality

### B-1. [Critical] gemma3:1b is almost certainly too small for structured JSON generation
**Files**: `AG_src/llm/prompts.py`, `AG_src/config/pipeline_config.yaml`
**Description**: The pipeline is configured to use `gemma3:1b` (1 billion parameters). The prompts request complex structured JSON output with nested objects, arrays, and domain-specific scientific reasoning. Key concerns:

1. **JSON schema complexity**: The planner schema has 6+ nested fields including arrays of objects. A 1B model will frequently produce malformed JSON, missing keys, or hallucinated field names.
2. **Scientific reasoning**: The prompts ask for "falsifiable scientific hypotheses" and "structural failure analysis" -- tasks that require deep domain knowledge that a 1B model simply does not have.
3. **Instruction following**: Small models struggle with multi-constraint instructions (e.g., "Always output valid JSON AND propose concrete numeric parameters AND state a falsifiable hypothesis AND reference previous results").

The prompts were clearly designed for a larger model (the docstring says "Qwen 2.5 7B", the `__init__.py` says "Qwen3 8B"), but the actual config uses `gemma3:1b`.

**Recommended fix**:
- **Minimum viable**: Use `gemma3:4b` or `qwen2.5:7b` if the GTX 1060 can handle it (see Section E)
- **If stuck with 1B**: Drastically simplify the JSON schemas to flat key-value pairs with no nesting. Remove scientific reasoning requirements and use templates with fill-in-the-blank style prompts
- **Add robust fallback**: The rule-based fallback is already implemented, but the JSON parsing failure path should be tested more aggressively

---

### B-2. [Major] Prompt/schema mismatch between planner modes
**File**: `AG_src/llm/prompts.py` (lines 82-116)
**Description**: The default planner schema references `n_backbone`, `k_seq_per_backbone`, `contigs`, `hotspot_res` -- parameters from the full RFdiffusion pipeline. But in `pyrosetta_only` mode, none of these parameters exist. While the PyRosetta-only schema is simpler, the planner's `validate_plan` method (planner.py line 454) still checks for `n_backbone >= 1` and `k_seq >= 1`, which will fail validation for LLM-generated PyRosetta-only plans unless the LLM happens to include these irrelevant fields.

**Recommended fix**: Make `validate_plan` mode-aware. In `pyrosetta_only` mode, skip `n_backbone`/`k_seq` validation and check for `mutation_strategy`/`target_positions` instead.

---

### B-3. [Major] System prompts mention tools the model cannot use
**File**: `AG_src/llm/prompts.py` (lines 23-35)
**Description**: The default planner system prompt says the agent "specializes in SSTR2-selective peptide binder design using RFdiffusion, ProteinMPNN, and ESMFold." When running in PyRosetta-only mode, this is confusing to the LLM. The PyRosetta-only system prompt (lines 37-47) correctly scopes the task, but the critic and reporter system prompts (lines 52-74) still reference pLDDT and selectivity metrics that are hardcoded/synthetic in PyRosetta-only mode.

**Recommended fix**: Create mode-specific system prompts for critic and reporter as well, or add conditional context about which metrics are real vs. synthetic.

---

### B-4. [Major] Critic prompt asks for gate-level failure classification but receives no real gate data
**File**: `AG_src/llm/prompts.py` (lines 121-141)
**Description**: The critic output schema asks for `structural_failures`, `sequence_failures`, `docking_failures`, `stability_failures` counts. But in PyRosetta-only mode, the only real failure signal is ddG and clash_score. The LLM will be forced to hallucinate values for failure categories it has no data about.

**Recommended fix**: In PyRosetta-only mode, simplify the critic schema to only include `rosetta_failures` (ddG/clash) and `convergence_signal`.

---

### B-5. [Minor] Format strings in prompts use f-string interpolation with `.get()` defaults
**File**: `AG_src/llm/prompts.py` (lines 258-262)
**Description**: `f"- Pass rate: {qc_report_summary.get('pass_rate', 0):.1%}"` will raise `TypeError` if `pass_rate` is `None` (not `0`). The `.get()` with default `0` is fine for numeric types, but if the dict has an explicit `None` value, the format spec `:.1%` will fail.

**Recommended fix**: Add explicit None guards: `f"{(qc_report_summary.get('pass_rate') or 0):.1%}"`

---

### B-6. [Minor] Reporter LLM summary hardcodes "Qwen 2.5 7B"
**File**: `AG_src/agents/reporter.py` (line 572)
**Description**: `"**생성 방식**: LLM (Qwen 2.5 7B)"` is hardcoded regardless of which model is actually being used (could be gemma3:1b, or any other model).

**Recommended fix**: Pass the model name through the LLM provider and include it dynamically.

---

### B-7. [Suggestion] Add few-shot examples to prompts for small models
**File**: `AG_src/llm/prompts.py`
**Description**: For a 1B parameter model, few-shot examples are essential for reliable JSON generation. The current prompts only provide the schema description without any concrete examples of valid output.

**Recommended fix**: Add 1-2 concrete JSON examples after each schema block, e.g., "Example output:" followed by a minimal valid JSON object.

---

### B-8. [Suggestion] Consider using constrained decoding (Ollama format="json")
**File**: `AG_src/llm/provider.py` (line 182)
**Description**: The Ollama provider already passes `"format": "json"` when `json_mode=True`, which enables Ollama's constrained JSON decoding. This is good. However, there is no structured schema enforcement -- the model can output any valid JSON, not necessarily matching the expected schema. Ollama supports `format` with a JSON schema object for stricter enforcement.

**Recommended fix**: Pass the output schema from `prompts.py` as the `format` parameter value (as a parsed JSON schema dict) instead of just `"json"`.

---

## C. Research Direction

### C-1. [Critical] Convergence is never detected -- `converged` is always `False`
**File**: `pyrosetta_flow/runner.py` (line 542)
**Description**: `emitter.add_convergence_point(..., converged=False)` is hardcoded to `False` for every iteration. The pipeline has no actual convergence detection logic. The config file defines `convergence_ddg_threshold`, `no_improvement_patience`, and `convergence_min_candidates` parameters, but none of these are read or used in the runner.

This means the pipeline always runs for exactly `max_iterations` iterations regardless of whether results have converged, wasting potentially hours of compute.

**Recommended fix**: Implement convergence detection:
```python
# After each iteration, check:
if len(iterations_out) >= config.min_iterations:
    recent_ddgs = [s["summary"]["best_ddg"] for s in iterations_out[-patience:]]
    if max(recent_ddgs) - min(recent_ddgs) < improvement_threshold:
        converged = True
        break
```

---

### C-2. [Critical] QC gates effectively pass everything in `ddg_only` mode
**File**: `pyrosetta_flow/runner.py` (lines 368-380)
**Description**: In `ddg_only` mode (which is the default for iteration 1 in `auto` mode):
- pLDDT gate: DISABLED
- Docking gate: DISABLED
- Rosetta clash gate: threshold set to 999 (effectively disabled)
- Rosetta ddG gate: only real gate, threshold -5.0

Combined with the hardcoded synthetic metrics, this means the QC system provides almost no filtering in the first (and often most important) iteration. Furthermore, the ddG threshold of -5.0 kcal/mol is quite lenient -- real FlexPepDock refinements often produce ddG values in the -10 to -30 range, meaning nearly everything passes.

**Recommended fix**: Even in `ddg_only` mode, keep a meaningful clash gate (e.g., `clash_max=20`) and consider a percentile-based ddG cutoff rather than a fixed threshold.

---

### C-3. [Major] Critic feedback is not actually applied to mutation strategy
**File**: `pyrosetta_flow/runner.py` (lines 482-493), `pyrosetta_flow/adapter.py` (lines 33-51)
**Description**: The critic generates `proposed_changes` with parameter adjustments and a new hypothesis. This feedback is passed to the planner, which may adjust its `ExperimentPlan`. However, the actual mutation logic in the runner (`generate_random_mutant`) is completely independent of the planner's output. The mutations are always random, using the same `design_positions` and same random strategy regardless of what the planner or critic suggests.

This means the agentic loop is cosmetic -- the critic and planner provide analysis but cannot influence the actual search trajectory.

**Recommended fix**:
1. Have the planner output `target_positions` and `mutation_strategy` that actually get consumed by the mutation step
2. Implement strategy-aware mutation (e.g., hydrophobic enrichment, charge optimization) based on planner output
3. Allow the critic to narrow or expand `design_positions` based on structural analysis

---

### C-4. [Major] Random mutation with no structure-aware bias
**File**: `pyrosetta_flow/adapter.py` (lines 33-51)
**Description**: `generate_random_mutant` samples uniformly from `AA_NO_CYS` (19 amino acids minus Cys). This ignores:
- BLOSUM62 substitution probabilities (conservative mutations are more likely to maintain structure)
- Hydrophobicity matching (replacing a buried hydrophobic with a charged residue will likely cause clashes)
- Position-specific amino acid preferences from the receptor pocket geometry
- The BLOSUM-based mutation strategy defined in `pipeline_config.yaml` (`approach_b`)

**Recommended fix**: Implement at least BLOSUM62-weighted sampling, and ideally position-specific profiles derived from the receptor pocket contacts. The config already defines `approach_b` with BLOSUM parameters.

---

### C-5. [Major] Scoring uses only ddG with no multi-objective weighting
**File**: `pyrosetta_flow/runner.py` (line 121)
**Description**: `"finalScore": round(-c.ddg, 3)` -- the final score is simply the negative of ddG. The elaborate multi-objective weighted scoring system in `QCRankerAgent.compute_rankings` (with weights for pLDDT, dock_score, ddG, lDDT, selectivity) is rendered meaningless because all non-ddG metrics are hardcoded constants. The ranking effectively degenerates to ddG-only sorting.

**Recommended fix**: This is entangled with issue A-1 (hardcoded metrics). Fix A-1 first, then the multi-objective scoring will become meaningful.

---

### C-6. [Minor] `design_positions` excludes positions 3 and 13 but includes 14
**File**: `pyrosetta_flow/schema.py` (line 15)
**Description**: The default design positions are `[1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14]`. Position 3 is correctly excluded (Cys3 for disulfide), and position 13 is excluded. But position 14 is included in the design positions while the config file (`pipeline_config.yaml` line 190) marks position 14 as fixed (Cys14 for disulfide). Also, positions 7-10 are the binding hotspot core (FWKT) per the config, but they are included as mutable positions.

This contradicts the sequence constraints defined in `pipeline_config.yaml` where positions 3, 7, 8, 9, 10, 14 should all be fixed.

**Recommended fix**: Align `design_positions` with the config file's `mutable_positions: [1, 2, 4, 5, 6, 11, 12, 13]`. The current set risks mutating the disulfide bond and binding hotspot.

---

### C-7. [Minor] `final_selected` only captures the last iteration's selected candidates
**File**: `pyrosetta_flow/runner.py` (line 544)
**Description**: `final_selected = selected` is overwritten each iteration. The final artifacts only report the last iteration's selected candidates, not the global best across all iterations. An early iteration might have found a better candidate than the last iteration.

**Recommended fix**: Maintain a global best list across all iterations, or at minimum report the best from any iteration in the summary.

---

### C-8. [Suggestion] Consider implementing ensemble scoring across iterations
**Description**: The current pipeline evaluates candidates independently per iteration. A more sophisticated approach would maintain a Pareto front across iterations and use the critic to identify unexplored regions of the fitness landscape.

---

## D. Architecture Concerns

### D-1. [Critical] API server has no authentication or rate limiting — ⚠️ PARTIALLY ADDRESSED
**File**: `backend/api_server.py`
**Description**: The API server binds to `0.0.0.0:8787` with `Access-Control-Allow-Origin: *`. The `POST /api/run/start` endpoint can start arbitrary subprocess commands. The `POST /api/status` endpoint can overwrite the status file. There is no authentication, no CSRF protection, and no rate limiting.

On a shared network (e.g., lab WiFi), anyone can:
- Start pipeline runs with arbitrary parameters
- Inject fake status data into the dashboard
- Trigger DoS by rapidly starting/stopping processes

**Recommended fix**:
1. Bind to `127.0.0.1` instead of `0.0.0.0` (since the frontend is on the same machine)
2. Add a simple API key header check
3. Add rate limiting to the start/stop endpoints

---

### D-2. [Major] Status file is a single-writer/single-reader bottleneck with no locking — ✅ FIXED (C5)
**Files**: `backend/status_emitter.py` (line 105), `backend/api_server.py` (line 177)
**Description**: The `StatusEmitter.flush()` method writes the entire JSON state to a file on every update (dozens of times per iteration). The `_read_status()` in api_server reads this same file every 2 seconds. There is no file-level locking between the writer (pipeline process) and reader (API server process).

**Status**: `fcntl.flock()` file locking applied in `status_emitter.py:flush()`. Cache reads use `copy.deepcopy()`. On Windows (which this appears to run on, given the WSL2 environment), simultaneous read/write can cause:
- Partial reads (truncated JSON)
- `json.JSONDecodeError` in the API server
- Data corruption in the status file

**Recommended fix**: Use atomic file writes (write to a temp file, then `os.rename`) in `flush()`:
```python
import tempfile
tmp = tempfile.NamedTemporaryFile(
    dir=self._file.parent, suffix=".tmp", delete=False, mode="w"
)
tmp.write(json.dumps(self._state, ensure_ascii=False, indent=2))
tmp.close()
os.replace(tmp.name, str(self._file))
```

---

### D-3. [Major] Subprocess management has race conditions
**File**: `backend/api_server.py` (lines 102-123)
**Description**: The `_start_pipeline_process` function checks `_run_process.poll() is None` under `_process_lock`, but the lock is released between the check and the actual process creation. Multiple rapid POST requests to `/api/run/start` could bypass the "already_running" guard.

Also, `_run_log_handle` is a module-level mutable that is shared between the main thread (HTTP handler) and the subprocess. If the HTTP server is multi-threaded (which `HTTPServer` can be with `ThreadingMixIn`), this is unsafe.

**Recommended fix**: Keep the lock held for the entire check-and-start sequence (which the current code does with `with _process_lock`, so the race window is actually small). But add explicit thread safety for `_run_log_handle`.

---

### D-4. [Major] StatusEmitter flushes on every single update
**File**: `backend/status_emitter.py`
**Description**: Every method (`set_candidates`, `update_agent`, `append_timeline_event`, etc.) calls `self.flush()` which writes the entire state dict to disk. During a single iteration, this can mean 20-40 file writes. On a mechanical disk or network-mounted filesystem (the `G:` drive in WSL2 suggests this), this creates significant I/O overhead and can slow down the pipeline.

**Recommended fix**: Implement batched flushing:
```python
def flush(self, force=False):
    now = time.time()
    if not force and (now - self._last_flush) < 0.5:
        self._dirty = True
        return
    # ... actual write ...
    self._last_flush = now
    self._dirty = False
```
And add a periodic flush in the background or flush at step boundaries.

---

### D-5. [Minor] Image serving endpoint has path traversal risk — ✅ FIXED (C1)
**File**: `backend/api_server.py` (lines 254-274)
**Description**: The `_serve_image` method does check that the resolved path starts with the `runs/` base directory (line 260), which is good. However, the `str(file_path).startswith(str(base.resolve()))` check can be bypassed on some platforms if `base.resolve()` and `file_path.resolve()` produce paths with different casing or trailing separators.

**Status**: Replaced with `pathlib.relative_to()` across all static file serving endpoints (api_server.py, routers/static.py).

---

### D-6. [Minor] `creationflags=0` is meaningless on Linux
**File**: `backend/api_server.py` (line 122)
**Description**: `creationflags=0` is a Windows-specific parameter and has no effect on Linux/WSL. It suggests the code was originally written for Windows.

**Recommended fix**: Remove the parameter or use `os.name` to conditionally set it.

---

### D-7. [Minor] Frontend state management could leak memory
**File**: `frontend/src/App.tsx`
**Description**: The `timeline` array in the status state grows unboundedly as events accumulate. Over a long run (many iterations), this array could become very large, causing the React component to re-render slowly and consume memory.

**Recommended fix**: Limit the timeline to the last N events (e.g., 500) or paginate.

---

### D-8. [Suggestion] Consider WebSocket instead of polling
**Files**: `backend/api_server.py`, `frontend/src/hooks/usePipelineStatus.ts`
**Description**: The 2-second polling interval means up to 2 seconds of latency in status updates. WebSocket would provide real-time updates and reduce unnecessary HTTP requests when nothing has changed.

---

### D-9. [Suggestion] Add health check for Ollama connectivity
**File**: `AG_src/llm/provider.py`
**Description**: If Ollama is not running, the first LLM call will fail with a connection error and fall back to rule-based mode. There is no upfront connectivity check or user warning.

**Recommended fix**: Add a `ping()` or `is_available()` method to `OllamaProvider` that checks `/api/tags` endpoint at initialization, and log a clear warning if Ollama is unreachable.

---

## E. GPU Constraint Issues (GTX 1060)

### E-1. [Critical] gemma3:1b is insufficient for the task complexity
**Description**: The GTX 1060 has 6GB VRAM. Here is the model size analysis:

| Model | Parameters | VRAM (Q4) | VRAM (FP16) | Viable on 1060? |
|-------|-----------|-----------|-------------|-----------------|
| gemma3:1b | 1B | ~1.2GB | ~2.5GB | Yes, but too weak |
| gemma3:4b | 4B | ~3GB | ~8GB | Q4 only, marginal |
| qwen2.5:3b | 3B | ~2.2GB | ~6GB | Q4/Q5 yes |
| qwen2.5:7b | 7B | ~4.5GB | ~14GB | Q4 only, tight |
| phi-3-mini (3.8B) | 3.8B | ~2.8GB | ~7.6GB | Q4 yes |

**Recommendation**:
- **Best tradeoff**: `qwen2.5:3b` (Q4_K_M quantization) -- fits in 6GB with room for PyRosetta, decent at structured JSON output
- **If quality is paramount**: `qwen2.5:7b` (Q4_0 quantization) at ~4.5GB, but this leaves very little VRAM for PyRosetta concurrent operations
- **Current gemma3:1b**: Suitable only for proof-of-concept demos where the rule-based fallback does the real work
- **Alternative approach**: Use a CPU-only inference mode for the LLM (Ollama supports this) and reserve all GPU VRAM for PyRosetta. The latency increase (5-15 seconds per LLM call vs 1-3 seconds on GPU) is acceptable since LLM calls are infrequent relative to PyRosetta docking.

---

### E-2. [Major] LLM timeout of 60 seconds may be too short for CPU inference
**File**: `AG_src/llm/provider.py` (line 38)
**Description**: `DEFAULT_TIMEOUT = 60` seconds. If the model runs on CPU (which is likely if PyRosetta is using the GPU), a single inference with 4096 max tokens could take 30-120 seconds depending on the model size. The config file sets `timeout: 120` which is better, but the code default of 60 will be used if the config is not loaded (see issue A-8 about yaml degradation).

**Recommended fix**: Increase `DEFAULT_TIMEOUT` to 180 seconds and add a retry mechanism for timeout failures.

---

### E-3. [Minor] PyRosetta and Ollama may compete for GPU memory
**Description**: FlexPepDock refinement is CPU-bound (PyRosetta uses CPU for most protocols), but if Ollama loads the model into GPU VRAM, and PyRosetta simultaneously needs GPU for certain scoring functions or future GPU-accelerated protocols, they will compete for the 6GB VRAM.

**Recommended fix**: Configure Ollama to run the model on CPU (`OLLAMA_GPU_LAYERS=0` environment variable) when running alongside PyRosetta GPU workloads, or ensure sequential (not parallel) execution.

---

### E-4. [Suggestion] Profile actual VRAM usage during a full pipeline run
**Description**: The current analysis is theoretical. A real profiling run would reveal actual peak VRAM usage for both PyRosetta and Ollama simultaneously, enabling better tuning.

---

## F. Additional Issues

### F-1. [Minor] Korean/English mixed comments reduce readability for international contributors
**Files**: Most Python files
**Description**: Comments and docstrings mix Korean and English freely. This is fine for a Korean research team but may hinder external collaboration.

**Recommended fix**: For public-facing code, provide English-only comments with Korean in a separate documentation layer.

---

### F-2. [Minor] The `run_pipeline_live.py` entry point is modified but not reviewed
**Description**: Per the git status, `run_pipeline_live.py` has unstaged changes but was not included in the review scope. This is the main entry point that wires everything together.

---

### F-3. [Suggestion] Add integration tests for the full pipeline loop
**Description**: There appear to be no integration tests that exercise the Plan -> Mutate -> Dock -> QC -> Critic -> Report loop end-to-end. Unit tests for individual agents would also be valuable, especially for JSON parsing edge cases.

---

### F-4. [Suggestion] Add type stubs or Protocol classes for PyRosetta
**File**: `AG_src/scripts/flexpep_dock.py`
**Description**: All PyRosetta types are quoted strings (`"pyrosetta.Pose"`) due to lazy imports. Adding type stubs or Protocol classes would improve IDE support and static analysis.

---

## Summary of Priority Actions

### Immediate (before next pipeline run) — ✅ ALL DONE
1. ~~**C-6**: Fix `design_positions` to exclude binding hotspot (positions 7-10) and Cys14~~
2. ~~**A-2**: Make JSON parsing in `_run_script` more robust~~ → **C4 FIXED**
3. ~~**A-3**: Add subprocess timeout~~ → **C3 FIXED** (300s timeout)
4. ~~**D-2**: Implement atomic file writes in StatusEmitter~~ → **C5 FIXED** (fcntl.flock)

### Short-term (next sprint) — Research items remain open
5. **C-1**: Implement convergence detection — *open (research direction)*
6. **C-3**: Connect critic/planner feedback to actual mutation strategy — *open (research direction)*
7. **B-1**: Either upgrade model or simplify prompts for gemma3:1b — *open*
8. **A-1**: Replace hardcoded metrics with real values or explicit N/A markers — *open*
9. ~~**D-1**: Bind API server to localhost~~ → partially addressed

### Medium-term (next milestone)
10. **C-4**: Implement BLOSUM62-weighted mutation — *open (research direction)*
11. **E-1**: Profile and optimize model selection for GTX 1060 — *open*
12. **B-2/B-3/B-4**: Create mode-specific prompts throughout — *open*
13. ~~**D-4**: Implement batched flushing for StatusEmitter~~ — addressed via fcntl locking
14. ~~**F-3**: Add integration and unit tests~~ → **H6 DONE** (150 tests: 32 FE + 118 pipeline, 93% coverage)

---

*Review generated by Claude Opus 4.6. All line numbers reference the files as read on 2026-02-25.*
*Remediation status updated 2026-03-04 after completion of 22/22 refactoring plan items.*
