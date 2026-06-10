[GOAL — READ-ONLY CS CODE ANALYSIS. DO NOT MODIFY ANY FILE. Output a written report only.]

You are a senior Computer Science / software engineering reviewer. Analyze the SSTR2 radiopharmaceutical screening AI system in this repository from a **pure CS/software-engineering** perspective (NOT the biology). Your job is ANALYSIS ONLY — propose problems and concrete remediation. Do NOT edit code.

## System layout (already consolidated, see CONSOLIDATION.md)
- SSOT (working system): `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/`
  - `AG_src/` — LLM agents (planner/critic/reporter), 8-step pipeline (pipeline/step*.py), llm/provider.py (Ollama/vLLM)
  - `pyrosetta_flow/` — agentic mutate→dock→ddG loop (runner.py ~1600 LOC, multiobjective.py, bandit.py, convergence.py, pareto_ranking.py, bayesian_optimizer.py)
  - `backend/` — FastAPI (routers/, state.py, status_emitter.py)
  - `frontend/` — React 19 + Vite + TypeScript
- Compute layer (runtime dep of backend): `pipeline_local/` (scripts/flexpepdock_worker.py etc.)
- LLM served via vLLM Qwen3-32B on :8000; PyRosetta docking via `bio-tools` conda env subprocess.

## Analyze and report on (with file:line evidence where possible):
1. **Architecture & modularity**: coupling/cohesion, SOLID violations, god-objects (runner.py is ~1600 LOC — assess), separation of concerns between agents/compute/IO, abstraction quality of LLM provider + scoring.
2. **Concurrency & parallelism correctness**: ThreadPoolExecutor usage for FlexPepDock subprocesses, the fcntl.flock-based JSON status file (status_emitter.py) — race conditions, atomicity, the backend reading while runner writes. subprocess timeout handling.
3. **Error handling**: bare `except: pass`, silent failures, non-fatal swallowing that hides real errors, retry logic, partial-failure recovery in the N-iteration loop.
4. **State management**: file-based status (/tmp JSON + flock) vs a proper store; experiment_log.jsonl as accumulating store; in-memory backend state.py globals (experiment_proc); reproducibility (seeds).
5. **Testing**: coverage gaps, what is mocked vs real, the pharmacology_guards regression approach, missing integration/e2e tests, test isolation.
6. **Performance**: CPU-bound PyRosetta serialization (each dock ~4min), LLM call latency, the O(n²) brute-force CA distance loops you may find, caching opportunities (.rosetta_cache), redundant recomputation.
7. **Security & robustness**: `--dangerously-bypass-approvals-and-sandbox` in agent-wrapper, subprocess shell injection surface, unvalidated inputs in FastAPI routers, path traversal in static file serving, API auth (none?).
8. **Dependency & env hygiene**: dual codebases, sys.path manipulation (backend/state.py appends OUTER root — assess fragility), conda-env coupling, pinned vs floating deps.
9. **Code quality**: dead code, duplication between AG_src.pipeline.step* and pipeline_local.steps.step*, naming, type hints, docstring/comment accuracy, magic numbers.
10. **Technical debt & risk register**: rank the top issues by (severity × likelihood), each with a concrete, minimal remediation and an estimate of risk-to-fix.

## Output format (write to the -o output file):
A prioritized markdown report: Executive summary → Findings table (id, area, severity High/Med/Low, file:line, problem, concrete fix, risk-to-fix) → Top-5 recommended actions with rationale. Be specific and cite real paths/symbols you actually read. No code edits.
