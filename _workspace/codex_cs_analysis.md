**Executive Summary**

From a CS/software-engineering perspective, the system’s biggest risks are operational correctness, not algorithms: a 1,720-line orchestration god-object, mixed file-based state writers, silent fallback paths that turn failed compute into plausible-looking scores, and weak production boundaries around API access/process control. The codebase has useful tests, but many high-risk paths are mocked, so the real `FastAPI -> subprocess/conda -> PyRosetta/vLLM -> JSON status` loop is under-verified.

No files were modified. No `-o` path was provided, so I’m returning the written report here.

**Findings Table**

| id | area | sev | file:line | problem | concrete fix | risk-to-fix |
|---|---|---:|---|---|---|---|
| F01 | Architecture | High | `pyrosetta_flow/runner.py:555`, `:1720` | `run_pyrosetta_agentic_mutdock_flow` spans most of a 1,720 LOC file and owns agents, mutation, docking, ranking, reporting, status, history, visualization, and validation. | Split into `RunController`, `CandidateGenerator`, `DockingExecutor`, `ScoringPipeline`, `ArtifactWriter`; preserve CLI facade. | Med |
| F02 | Modularity | Med | `runner.py:56-75` | Optional scoring imports use `pass`/feature flags, making capabilities implicit at import time. | Move dependency discovery into explicit startup diagnostics and typed capability objects. | Low |
| F03 | Error handling | High | `runner.py:235`, `:269`, `:301`, `:355`, `:390`, `:1331` | Many “non-fatal” catches continue after scoring/pharma/ranking failures; `:1331` has `except Exception: pass`. | Define fail-open vs fail-closed policy per stage; record structured degradation in status/artifacts. | Low-Med |
| F04 | State/concurrency | High | `status_emitter.py:127-131`, `backend/state.py:118-124`, `routers/status.py:180`, `routers/experiment.py:98` | Status writer uses lock+rename, but readers do not lock and multiple routes directly overwrite the same JSON without atomic replace. | Introduce one `StatusStore` with atomic write, lock discipline, schema validation, and read retry. | Low |
| F05 | State/process | High | `backend/state.py:141-143`, `routers/experiment.py:209`, `:266-271` | Experiment state is in-memory globals; multi-worker/restart loses truth and can orphan processes. | Store run state in SQLite/Postgres or a process supervisor table; make API stateless. | Med |
| F06 | Subprocess control | High | `flexpepdock_worker.py:638`, `:721-733`; `routers/experiment.py:271` | FlexPepDock uses blocking `subprocess.run`; cancellation/progress are synthetic until timeout. Unix-only `preexec_fn=os.setsid` appears in backend. | Use `Popen` with process group, streamed logs, cancellation polling, and platform-neutral `start_new_session=True`. | Med |
| F07 | Worker locking | Med | `flexpepdock_worker.py:165-191`, `:219-260` | Global lock is write-then-check, not `flock`; per-job lock is better. Possible startup race with multiple workers. | Use `os.open(..., O_CREAT|O_EXCL)` or `flock` for global lock too. | Low |
| F08 | Scientific compute robustness | High | `flexpepdock_worker.py:651`, `:682`, `:699-700`; `AG_src/pipeline/step06_rosetta.py:335-337`, `:647` | Failed PyRosetta/FlexPepDock can return random or stub scores, which can enter rankings as if computed. | Fail closed by default; require explicit `allow_stub=true` in dev; tag and exclude stub rows from ranking. | Low |
| F09 | Persistence | Med | `pyrosetta_flow/ranking.py:8-14`, `:18-28` | `experiment_log.jsonl` appends without lock and silently skips malformed records on read. | Locked JSONL append, checksum/version fields, quarantine malformed lines. | Low |
| F10 | Reproducibility | Med | `runner.py:816-829`, `pipeline_local/steps/step05b_selectivity.py:280`, `flexpepdock_worker.py:699` | Some paths seed `random.Random`, but Python `hash()` and unseeded stub randomness break reproducibility. | Use stable `sha256`-based seeds; log RNG seeds for every candidate/trial. | Low |
| F11 | Security | High | `backend/main.py:67`, `:113-133` | No API auth; all operational routers are exposed under `/api`. CORS is local-only but not an auth boundary. | Add API token/session auth, CSRF posture for browser use, and role checks for run-control/upload endpoints. | Med |
| F12 | Input robustness | Med | `routers/selectivity.py:72-85` | Upload reads entire file into memory and accepts arbitrary suffix beyond PDB/CIF allowlist. | Enforce suffix/content-type/size limits; stream to temp file; validate PDB/CIF parser before replace. | Low |
| F13 | Path handling | Med | `routers/status.py:217-224` | Archive path containment uses string `startswith`; static router uses stronger `relative_to` at `static.py:26`, `:48`. | Replace with `Path.relative_to()` and strict `run_id` regex everywhere. | Low |
| F14 | Env hygiene | Med | `backend/state.py:31-35`, `pipeline_local/backend/state.py:33-35`, `routers/flexpepdock.py:43-45` | Runtime `sys.path` mutation and parent-depth assumptions are fragile after consolidation. | Package `ai4sci-kaeri`/`pipeline_local` installably; remove path surgery from app code. | Med |
| F15 | Dependencies | Med | `requirements.txt` uses `biopython>=1.79`; `frontend/package.json` uses many `^`; `requirements_peptools.txt` notes env conflict. | Mixed exact/floating deps and multiple conda envs make reproducibility brittle. | Add lockfiles per env, CI matrix for `bio-tools`/`peptools`, and documented env contracts. | Med |
| F16 | Testing | High | `pipeline_local/tests/test_step05c_boltz_cross.py:12-13`, `pyrosetta_flow/tests/test_alternative_scoring_integration.py:148-170` | Critical subprocess/scoring paths are mostly mocked; real integration is not continuously verified. | Add marked slow smoke tests for vLLM health, conda import, one tiny FlexPepDock/worker job, and status polling. | Med |
| F17 | Performance | Med | `check_receptor_structure.py:66-73`; `schema.py:29`, `runner.py:1525` | O(n²) clash loop; high parallel defaults risk oversubscribing expensive PyRosetta subprocesses. | Use KD-tree/grid spatial index; central resource scheduler with CPU/GPU/env slots. | Low-Med |
| F18 | LLM abstraction | Med | `AG_src/llm/provider.py:287-291`, `:90-93` | Provider returns `None` for transport and JSON failures, conflating “no LLM” with “LLM failed.” | Return typed result/error, retries with backoff, and explicit degraded-mode status. | Low |

**Top-5 Recommended Actions**

1. Build a single `StatusStore` and make all status/history writes go through it.  
This directly addresses races across `StatusEmitter`, `/status`, experiment startup, and backend polling.

2. Disable production stubs by default.  
Random/stub compute results are the highest likelihood path to false confidence. Failed docking/scoring should fail the candidate or the run unless dev mode explicitly opts in.

3. Extract `runner.py` into staged services behind stable interfaces.  
Keep the CLI/API behavior, but split orchestration, candidate generation, docking execution, scoring, and artifact writing. This lowers risk for every future change.

4. Add real integration smoke tests.  
At minimum: vLLM model endpoint, `bio-tools` PyRosetta import, one subprocess timeout/cancel path, one worker queue job, and status polling during a write.

5. Harden the API boundary.  
Add auth for run-control/upload/status mutation endpoints, strict request models, file size/type validation, and `Path.relative_to()` containment checks consistently.