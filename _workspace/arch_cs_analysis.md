# SSTR2 Radiopharmaceutical Screening AI — Systems/Architecture Review

**Scope:** Read-only CS/systems architecture review of the SSOT system at
`AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/` (AG_src + pyrosetta_flow + backend + frontend)
plus its runtime compute dependency `pipeline_local/`.
**Date:** 2026-06-09 · **Reviewer:** principal-architect (read-only)
All paths below are relative to repo root `/home/dongjukim/Documents/workspace/tmp/SST14-M_scr/`.
Nested package root abbreviated `ai4sci-kaeri/` = `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/`.

---

## 1. Executive Summary

This is a **single-host, single-experiment research dashboard** wrapped around an
LLM-driven peptide-optimization loop. The architecture is coherent for a one-operator
demo but has several systemic limits that block multi-user / multi-experiment / cluster scaling.

Top findings (ranked):

1. **(High) Single-experiment global lock + in-process state.** The whole "experiment" concept
   is a single OS subprocess tracked by module-global variables (`backend/state.py:141-143`),
   protected by one `threading.Lock`. Exactly one run can exist process-wide; a backend restart
   loses the handle (PID orphaned), and there is **no resume/checkpoint** (grep for
   `resume|checkpoint` in `runner.py`/`run_pyrosetta_flow.py` returns nothing).
2. **(High) Compute/LLM resource asymmetry.** vLLM is pinned to a **single** H100
   (`_launch_vllm.sh:3` `CUDA_VISIBLE_DEVICES=2`, no `--tensor-parallel-size`), while the real
   bottleneck — FlexPepDock refinement at ~4 min/candidate — is **CPU-bound** and capped at
   `os.cpu_count()` threads on the same host (`runner.py:897`). The "4×H100" are effectively
   idle relative to the screening throughput limiter.
3. **(High) Status coordination is a single shared `/tmp` JSON file.** All run state flows
   through one flock-guarded file (`backend/status_emitter.py:117-133`, read in
   `backend/state.py:99-125`), polled by the UI every 2 s. This is the only source of truth for a
   live run, is not multi-run capable, and is lost on host reboot.
4. **(High) Two-layer split with name collisions.** `ai4sci-kaeri/pyrosetta_flow/` and
   top-level `pipeline_local/`-sibling `pyrosetta_flow/` both exist, as do two `scripts/`
   packages. `backend/state.py:61-66` documents that `sys.path` ordering must be exactly right
   (append, not insert) to avoid one shadowing the other — a latent, fragile import contract.
5. **(Med) No durable job/queue/DB layer; everything is files + in-memory dicts.** The manual
   FlexPepDock path uses a file-based single-worker queue (`pipeline_local/scripts/flexpepdock_worker.py:49-50`
   lock-file + per-job dirs); selectivity jobs live in a process-local `_JOBS` dict
   (`backend/routers/status.py:47`). Nothing survives a process restart.
6. **(Med) Polling-only transport, two overlapping poll loops, no SSE/WebSocket.**
   `usePipelineStatus` (2 s) and `useExperiment` (3 s) poll independently
   (`frontend/.../hooks/usePipelineStatus.ts:238-246`).
7. **(Med) Reproducibility is partial.** Seeds are deterministic and well-structured
   (`runner.py:816-834`), but there is no config→result lineage manifest, no version pinning of
   PyRosetta/vLLM model weights, and `pyproject.toml` still points pytest at the now-orphaned
   `pipelines/` dir.

The system is **fit for its current purpose** (one scientist, one host, one run, visualized live).
The recommendations target the next step: durable, multi-run, partially distributed operation.

---

## 2. Annotated End-to-End Data Flow

```
┌── React 19 / Vite SPA (frontend/src) ──────────────────────────────────────┐
│  usePipelineStatus  ──poll 2s──► GET /api/status                            │
│  useExperiment      ──poll 3s──► GET /api/experiment/status                 │
│  ExperimentControl  ──POST────► POST /api/experiment/run {config}           │
└───────────────────────────┬────────────────────────────────────────────────┘
        Vite dev proxy  /api → http://127.0.0.1:8787  (vite.config.ts:14-21)
                            ▼
┌── FastAPI backend (backend/main.py) — 21 routers under /api ───────────────┐
│  POST /api/experiment/run  (routers/experiment.py:208)                      │
│    • experiment_lock + _reap_if_dead()  (zombie guard)                      │
│    • builds argv → subprocess.Popen(setsid, stdout→log file)  :266-273      │
│    • spawns watchdog thread (max-runtime kill)  :280-285                    │
│    • writes "initializing" status JSON          :276                        │
│    • stores Popen in module global state.experiment_proc :266               │
└───────────────────────────┬────────────────────────────────────────────────┘
                            ▼ subprocess (bio-tools conda python)
┌── scripts/run_pyrosetta_flow.py → pyrosetta_flow/runner.py ────────────────┐
│  run_pyrosetta_agentic_mutdock_flow()  (runner.py:555)                      │
│  per iteration (serial, runner.py:710):                                     │
│    1. Planner.execute(...) ─HTTP─► vLLM Qwen3-32B :8000  (blocking)         │
│    2. generate mutants (seeded RNG)  :812-836                               │
│    3. ThreadPoolExecutor(max_workers≤cpu_count)  :967                       │
│         each _dock_one → subprocess → AG_src/scripts/flexpep_dock.py        │
│         (bio-tools conda, ~4 min/candidate, CPU-bound)  :932-945            │
│    4. QC ranker / bandit / convergence / Critic / Reporter                  │
│    5. StatusEmitter.flush() after every state mutation  (status_emitter.py) │
└───────────────────────────┬────────────────────────────────────────────────┘
                            ▼ fcntl.flock write
        /tmp/pipeline_local_status.json  (single shared file)
                            ▲ mtime-cached read
        backend read_status() (state.py:99) ◄── GET /api/status polling ──── UI
```

Separate, parallel surface (not the main loop): the **manual** FlexPepDock tool path
`POST /api/flexpepdock/*` (routers/flexpepdock.py) enqueues into a **file-based, single-worker**
queue at `runs_local/flexpepdock_jobs/` (`pipeline_local/scripts/flexpepdock_worker.py:49-50`,
lock-file enforced single concurrency). This is a *second*, independent execution mechanism for
the same docking primitive.

---

## 3. Findings by Area

### 3.1 Component & Data-Flow Architecture — **High**

- **Hidden coupling: `/tmp` JSON is a cross-process global variable.** The runner subprocess and
  the FastAPI process communicate solely through `/tmp/pipeline_local_status.json`
  (`status_emitter.py:30-34`, `state.py:40-45`). The contract is implicit (dict shape defined by
  `DEFAULT_STEPS`/`DEFAULT_AGENTS`, `status_emitter.py:42-64`) and re-parsed/re-typed in the
  frontend (`usePipelineStatus.ts:170-236`). Three independent definitions of the same schema
  (emitter Python dict, `PipelineStatusUpdate` pydantic model `routers/status.py:20-31` with
  `extra="allow"`, TS `PipelineStatus` interface) must be kept in sync by hand.
- **Two-layer split risk (High).** CONSOLIDATION.md keeps `pipeline_local/` as a sibling compute
  layer imported via `OUTER_REPO_ROOT` appended to `sys.path` (`state.py:31-34, 61-66`). The
  `parent.parent.parent` path math (`state.py:33`) is brittle: a directory move or running from a
  different CWD silently re-breaks `/api/flexpepdock/*`, `/api/binding_pocket/*`, `/api/stability/*`
  (this exact bug was the ×4 → ×3 fix on 2026-06-09, per the file comment :27-31).
- **Name-collision risk (High, confirmed).** Both `ai4sci-kaeri/pyrosetta_flow/` and a top-level
  `pyrosetta_flow/` exist (top-level has `bayesian_optimizer.py`, `gnina_rescoring.py`,
  `pareto_ranking.py` — overlapping names with the nested package), and two `scripts/` packages.
  Import correctness depends entirely on `sys.path` *ordering* documented in a comment
  (`state.py:61-64`). Any tool that does `sys.path.insert(0, outer)` would shadow the working
  nested modules. This is a correctness landmine, not just style.
- **Mixed responsibility in backend.** `backend/` contains both thin routers (`routers/`) and
  heavyweight scientific compute modules (`pharmacology.py` 583 lines, `unified_validation.py`,
  `pharma_properties.py` is in AG_src at 876 lines). The web tier and the science tier are not
  cleanly separated, so a UI request can trigger nontrivial CPU work synchronously
  (e.g. `/api/status` enriches every candidate on-the-fly, `routers/status.py:60-154`).

### 3.2 Scalability — **High**

- **Real bottleneck is CPU docking, not LLM.** Each candidate = one FlexPepDock subprocess
  ~4 min (`schema.py:33` comment, `script_timeout=600`). Per iteration N candidates run via
  `ThreadPoolExecutor(max_workers=min(n_jobs, max_parallel_workers=32, os.cpu_count()))`
  (`runner.py:897, 967`). So throughput ≈ `cpu_count` candidates per 4 min, single host only.
  For N iterations × K candidates the wall-clock is `~4min × ceil(N·K / cpu_count)` plus serial
  LLM/critic time between iterations (`runner.py:710` loop is sequential).
- **GPU under-utilization.** vLLM serves one model on one GPU (`_launch_vllm.sh:3`,
  `--max-model-len 16384`, no tensor/pipeline parallel). LLM calls are infrequent (planner/critic/
  reporter, a handful per iteration) and blocking. The 4×H100 fleet provides no benefit to the
  docking-bound critical path.
- **No distributed docking.** Two non-distributed mechanisms exist: in-process ThreadPool (main
  loop) and a single-worker file queue (`flexpepdock_worker.py` enforces one worker via
  `LOCK_FILE`, :50, `acquire_lock` :165). Neither spreads work across hosts.
- **Options:** (a) move docking to a real task queue (Celery/RQ/Dramatiq + Redis, or a Slurm/
  Ray cluster) with M worker nodes; (b) since each `_dock_one` is already an isolated subprocess
  (`runner.py:914-965`), it is a near-drop-in unit of work for a distributed executor; (c) cache
  ddG by sequence hash to skip re-docking duplicates (dedup logic exists at `runner.py:838` but
  only within a run / via `seen_sequences`).

### 3.3 State & Coordination — **High**

- **flock-JSON vs DB.** Live state = one file, atomic via tmp+rename under flock
  (`status_emitter.py:125-133`). Concurrency-safe for writers, but: single run only, no history
  query, no transactions, lost on reboot, and every mutation rewrites the *entire* document
  (`flush()` serializes full `_state` on each of ~dozens of calls per iteration — write
  amplification).
- **Experiment lifecycle is solid but in-memory only.** start/stop/status/watchdog/zombie-reap are
  implemented correctly (`routers/experiment.py:104-145` watchdog + `_reap_if_dead`; SIGTERM→SIGKILL
  process-group kill via `os.killpg`/`setsid` :271, 306-312). **But** all lifecycle state lives in
  module globals (`state.experiment_proc/run_id`, `state.py:142-143`); a backend restart abandons a
  running subprocess (orphan) and the API will report `running:false` while docking continues.
- **Single-experiment global limit (High).** `start_experiment` rejects a second run
  (`routers/experiment.py:215-216`). No queue, no per-user namespacing — multi-user is impossible
  without code change.
- **No resume/checkpoint.** Confirmed absent. A watchdog kill or crash at iteration 4/5 discards
  all in-flight work except whatever reached the status file / `experiment_log.jsonl`.
- **Selectivity jobs in a process-local dict** (`_JOBS`, referenced `routers/status.py:47`) — lost
  on restart and not shareable across workers (so the backend must run single-process; `--workers >1`
  uvicorn would break both `_JOBS` and the experiment globals).

### 3.4 API Design — **Med**

- **Router organization is clean and extensible.** 21 routers, consistent `/api` prefix, versioned
  extension point for future silos (`main.py:48-56, 133`). Standardized error envelope
  `{error, detail, status_code}` via three exception handlers (`main.py:73-108`) — good.
- **Polling vs push (Med).** No SSE/WebSocket; two independent poll loops
  (`usePipelineStatus.ts:238-245` even documents the overlap). For a live, fast-moving timeline this
  is wasteful and adds up-to-2 s latency. The codebase already acknowledges a unified endpoint would
  help (same comment block).
- **`/api/status` does synchronous compute per poll (Med).** Every 2 s the endpoint recomputes 6
  enrichment fields per candidate (instability, GRAVY, net charge, pharmacophore heuristics) by
  importing pharmacology/admet modules and iterating selectivity `_JOBS`
  (`routers/status.py:60-154`). This couples read latency to candidate count and re-does work that
  could be memoized or written once by the emitter.
- **Error contract leaks/inconsistencies (Low).** Global handler returns a generic 500 hiding
  details (`main.py:73-82`) — good for prod, bad for the failed-run debuggability this research tool
  needs. Some endpoints return `{"error": ...}` with HTTP 200 (`experiment.py:216`,
  `experiment/models` :192) instead of a 4xx/5xx, so the FE must inspect the body.

### 3.5 Reproducibility / MLOps — **Med**

- **Seeds: good.** RNG is fully derived from `seed_base + iteration*1000 + idx*100 + ... + trial`
  (`runner.py:816-834`), so mutant proposals are deterministic given config — strong.
- **Config→result lineage: weak.** `FlowArtifacts` stores `asdict(config)` (`schema.py:82, 102`)
  and `experiment_log.jsonl` records a one-line summary per archived run
  (`routers/experiment.py:56-64`). But there is **no capture of code/git SHA, PyRosetta version,
  vLLM model revision, or environment hash** alongside results. The LLM model name is logged as a
  string only (`status_emitter.py:97`).
- **Version pinning gaps.** `_launch_vllm.sh` pulls `Qwen/Qwen3-32B` (a moving HF tag, not a pinned
  revision). Frontend has a `package-lock.json` (good). No backend `requirements.txt`/lockfile was
  found at the package root (`AG_src/*.txt` absent); conda env is referenced by name `bio-tools`
  (`schema.py:19`) with `environment-bio-tools.yml` at repo root but PyRosetta builds are not hash-pinned.
- **Stale config.** `pyproject.toml` `testpaths = ["pipelines"]` points at the directory that
  CONSOLIDATION.md moved to `_backup/orphaned_20260609/` — pytest discovery is now misconfigured.

### 3.6 Observability — **Med**

- **Logging.** Python `logging` is used in routers/provider; subprocess stdout/stderr is redirected
  to per-run files `experiment_{run_id}.log` (`routers/experiment.py:264-265`) — good for post-mortem.
- **JSONL run log** (`experiment_log.jsonl`) gives coarse run history (`/api/experiment/history`
  :323-339).
- **Gaps:** no metrics (Prometheus), no tracing, no structured event log of per-candidate timings
  beyond the in-status `timeline` array (`status_emitter.py:348-365`). Failed candidates are captured
  as `CandidateResult(ddg=999, fail_reason=...)` (`runner.py:955-965`) and surfaced in the timeline,
  which is reasonable, but there is no aggregate failure-rate metric or alerting. The generic 500
  handler (3.4) reduces debuggability of HTTP failures.

### 3.7 Frontend Architecture — **Med**

- **State management.** Local hooks + `PipelineContext` (`contexts/PipelineContext.tsx`); no Redux/
  Zustand store for server state (a `stores/theme.ts` exists for theme only). Server state is held in
  `useState` inside `usePipelineStatus` with manual fetch/normalize. Workable but reinvents
  caching/retry/dedup that React Query would provide.
- **Polling hooks.** Clean AbortController usage and archive-vs-live switching
  (`usePipelineStatus.ts:262-326`); two separate intervals (2 s / 3 s) by design.
- **Mock-mode fallback.** Mock data exists (`frontend/src/data/mockData.ts`) but is **only**
  imported by `pages/SiloBPage.tsx:27` — it is not a global offline fallback for the main dashboard;
  the live dashboard shows a disconnected state when no status file exists
  (`usePipelineStatus.ts:273-283`). So "mock mode" is page-local, not a system-wide degradation mode.
- **Backend type contract (Med).** TS interface `PipelineStatus` (`usePipelineStatus.ts:45-73`) is a
  hand-maintained mirror of the Python emitter dict with extensive defensive `as`-casting and `??`
  defaults (`:142-236`). No generated client (no OpenAPI codegen), so schema drift is silent until a
  field renders blank.

### 3.8 Deploy / Ops — **High**

- **All-manual, single-host.** vLLM (`_launch_vllm.sh`), uvicorn (`main.py:142-144`, `--reload`),
  and Vite dev server are launched by hand; the Vite proxy hardcodes `127.0.0.1:8787`
  (`vite.config.ts:17`) and CORS hardcodes `localhost:5173/8787` (`main.py:67`). No process manager
  (systemd/supervisor/pm2), no container, no health-gated startup ordering.
- **Single-process assumption.** Because experiment state and `_JOBS` are module globals, uvicorn
  must run with a single worker; horizontal scaling of the API is not possible as-is.
- **Recovery.** None automated: a backend restart orphans a running docking subprocess (3.3); a host
  reboot loses `/tmp` status. `--reload` in `__main__` (`main.py:144`) is a dev convenience that would
  be dangerous in any shared deployment (restarts mid-run).

### 3.9 Extensibility — **Med**

- **Add a new objective:** moderate. Objectives flow through `objective_mode` (`schema.py:24`),
  `choose_objective_mode`, `multiobjective.py` scalarization (`_mo_scalar`, `runner.py:79`), and QC.
  Adding one touches the runner's scoring path, the QC ranker, and the emitter/TS field list — no
  single plugin seam.
- **Add a docking engine:** the unit of work `_dock_one` shells out to a fixed script
  `AG_src/scripts/flexpep_dock.py` (`runner.py:560, 932`). Swapping engines means editing the runner
  (no strategy interface for "docker"); however the subprocess+JSON-on-stdout contract
  (`_run_script` :419-456) is a reasonable boundary to generalize into a plugin.
- **Add an off-target receptor:** selectivity already iterates SSTR1/3/4/5 (`runner.py:1586-1598`,
  `enable_selectivity`, `selectivity_top_k`, `schema.py:43-46`); adding a receptor is largely data +
  config, the cheapest extension axis.
- **Bandit/BO/convergence are cleanly modular** (`bandit.py`, `bayesian_optimizer.py`,
  `convergence.py`, `pareto_ranking.py`) and dependency-light (convergence implements Mann-Whitney
  without scipy, `convergence.py:30-64`) — good separation; these are the most reusable parts.

---

## 4. Target-Architecture Recommendations

1. **Introduce a durable run store (replace `/tmp` JSON as SoT).** SQLite (single-host, zero-ops) or
   Postgres for runs, iterations, candidates, and job status. Keep the status file as a *derived
   cache* for the live view if desired. Enables history queries, multi-run, restart survival, and
   removes the full-document rewrite amplification in `flush()`.
2. **Promote docking to a real job queue + worker pool.** Each `_dock_one` becomes a task; run K
   workers per host and scale to multiple hosts (Redis+RQ for simplicity, or Ray/Slurm for a
   cluster). Add a **sequence→ddG cache** keyed by (sequence, template, protocol) to eliminate
   repeat docking. This directly attacks the throughput limiter (3.2).
3. **Decouple experiment lifecycle from process memory.** Persist `run_id`, PID, pgid, and state to
   the DB; on backend startup, reconcile (adopt or reap) orphaned subprocesses. Add `--resume` that
   reloads completed iterations from the store and continues.
4. **Switch live transport to SSE (or WebSocket).** A single `/api/events` stream replaces the two
   poll loops; the emitter publishes deltas instead of full-document rewrites. Falls back to polling
   if the stream drops.
5. **Generate the frontend client from OpenAPI.** FastAPI already exposes the schema; codegen the TS
   types/client to kill the hand-maintained `PipelineStatus` mirror and silent drift (3.7).
6. **Fold `pipeline_local` import contract into an explicit package boundary.** Either (a) install
   `pipeline_local` as an editable package (`pip install -e`) so imports don't depend on `sys.path`
   order, or (b) rename the colliding top-level `pyrosetta_flow`/`scripts` packages. Removes the
   landmine at `state.py:61-66`.
7. **Add a lineage manifest per run.** Capture git SHA, conda env hash, PyRosetta version, vLLM model
   revision (pin `Qwen/Qwen3-32B` to a commit), config, and seeds into the run record. Fix
   `pyproject.toml testpaths`.
8. **Containerize + process-manage.** systemd units (or compose) for vLLM, backend, frontend with
   health-gated ordering; externalize CORS/proxy hosts to env (`main.py:67`, `vite.config.ts:17`).

---

## 5. Prioritized Roadmap

### Quick Wins (days, low risk)
- **Fix `pyproject.toml testpaths`** to the real test dirs (currently points at orphaned
  `pipelines/`). *(trivial)*
- **Pin the vLLM model revision** in `_launch_vllm.sh` and record it in the run log. *(hours)*
- **Return proper HTTP status codes** for `experiment/run`/`models` error bodies instead of 200
  (`routers/experiment.py:192, 216`). *(hours)*
- **Add a sequence→ddG cache** within and across runs (extend `seen_sequences`, `runner.py:838`) to
  skip duplicate docking. *(1–2 days, high ROI on throughput)*
- **Startup reconciliation of orphaned experiment PID** written to a small state file, so a backend
  restart can re-adopt or reap a running run. *(1–2 days)*
- **Install `pipeline_local` as editable package** to remove the `sys.path`-order landmine
  (`state.py:61-66`). *(1 day)*

### Strategic (weeks, structural)
- **Durable run store (SQLite→Postgres)** replacing `/tmp` JSON as source of truth. *(1–2 wks)*
- **Distributed docking via job queue + worker pool**, reusing `_dock_one` as the task unit.
  Unlocks N-host scaling and lets the H100s and CPUs be provisioned independently. *(2–4 wks)*
- **Resume/checkpoint** for the iteration loop, backed by the run store. *(1–2 wks, depends on store)*
- **SSE event stream + OpenAPI-generated FE client**, retiring the dual poll loops and hand-mirrored
  types. *(1–2 wks)*
- **Plugin seams for objective and docking-engine** (strategy interface around `_run_script`/
  `_mo_scalar`), so new scoring functions/engines don't require editing the 1,700-line runner.
  *(2–3 wks)*
- **Containerization + process supervision + externalized hosts/CORS.** *(1–2 wks)*

---

### Severity Risk Register (severity × likelihood)

| # | Risk | Sev | Like | Evidence | Target |
|---|------|-----|------|----------|--------|
| R1 | Backend restart orphans running docking; live state in `/tmp` lost on reboot | High | High | `state.py:142-143`, `routers/experiment.py:266`; `status_emitter.py:30` | Durable store + startup reconciliation (rec 1,3) |
| R2 | CPU docking is throughput ceiling; H100s idle | High | High | `runner.py:897,967`; `_launch_vllm.sh:3` | Job queue + worker pool + dedup cache (rec 2) |
| R3 | `sys.path`-order import collision (`pyrosetta_flow`/`scripts` × 2) | High | Med | `state.py:61-66`; dual packages confirmed | Editable install / rename (rec 6) |
| R4 | Single-experiment, single-process global limit blocks multi-user / uvicorn `--workers>1` | High | Med | `routers/experiment.py:215`; `_JOBS` in `routers/status.py:47` | Run store + queue (rec 1,2) |
| R5 | Schema drift across 3 hand-maintained definitions | Med | High | `status_emitter.py:42-64`, `routers/status.py:20-31`, `usePipelineStatus.ts:45-236` | OpenAPI codegen (rec 5) |
| R6 | No lineage/version pinning → non-reproducible results | Med | Med | `_launch_vllm.sh`; `schema.py:82` | Lineage manifest (rec 7) |
| R7 | Poll latency + `/api/status` synchronous enrichment cost scales with candidates | Med | Med | `usePipelineStatus.ts:238`; `routers/status.py:60-154` | SSE + write-once enrichment (rec 4) |
| R8 | Manual, single-host deploy; no recovery/supervision | Med | Med | `main.py:144`; `vite.config.ts:17`; `main.py:67` | Containerize + supervise (rec 8) |
