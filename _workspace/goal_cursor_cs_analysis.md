[GOAL — READ-ONLY CS SYSTEM/ARCHITECTURE ANALYSIS. DO NOT MODIFY ANY FILE. Analysis report only — you are in plan mode.]

You are a principal software architect. Analyze the SSTR2 screening AI system in this repository from a **systems/architecture CS** perspective. ANALYSIS ONLY — do not edit code. Focus on the macro picture (complement, do not duplicate, a separate code-level review).

## System (see CONSOLIDATION.md)
- Working system (SSOT): `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/` = AG_src (LLM agents + 8-step pipeline) + pyrosetta_flow (mutate→dock→ddG agentic loop) + backend (FastAPI) + frontend (React/Vite).
- Compute layer: `pipeline_local/` (PyRosetta workers). LLM: vLLM Qwen3-32B :8000. Docking: PyRosetta via bio-tools conda subprocess. Status bridge: StatusEmitter → /tmp JSON (flock) → FastAPI → React polling.

## Analyze and report on:
1. **Component/data-flow architecture**: draw the end-to-end flow (UI → backend /experiment/run → subprocess runner → vLLM + PyRosetta → StatusEmitter file → backend polling → UI). Identify architectural smells, hidden couplings, the "two-layer" (ai4sci-kaeri + pipeline_local) split risk.
2. **Scalability**: PyRosetta docking is CPU-bound and serial-ish (4min/candidate); 4×H100 used only for vLLM. Where is the bottleneck for N-iteration × K-candidate screening? How would this scale to 100s of candidates? Queue/worker model? Distributed docking?
3. **State & coordination**: file-based status (flock JSON) vs message queue/DB; experiment lifecycle (start/stop/watchdog, zombie reaping); single-experiment-at-a-time global limitation; resume/checkpoint.
4. **API design**: FastAPI router organization (12+ routers), REST consistency, polling vs websockets/SSE for live updates, error contract.
5. **Reproducibility & MLOps**: seed control, experiment provenance (config→result lineage), artifact management (runs/, archives), model/version pinning (vLLM model, PyRosetta version), env reproducibility.
6. **Observability**: logging strategy, the JSONL experiment log, lack of metrics/tracing, debuggability of failed runs.
7. **Frontend architecture**: React state management (Zustand/Context), polling hooks, mock-mode fallback, type-safety contract with backend.
8. **Deployment & ops**: how services are launched (manual uvicorn/vite/vllm), no process manager/orchestration, port conflicts, single-host assumption, restart/recovery.
9. **Extensibility**: how hard to add a new objective (e.g., new ADMET model), a new docking engine, a new off-target receptor? Plugin/strategy boundaries.
10. **Architecture risk register**: top systemic risks ranked, each with a target architecture / migration path and effort estimate.

## Output (write your full analysis to a file `_workspace/cursor_cs_analysis.md` using your file tools if available, otherwise print the full report):
Markdown: Executive summary → annotated data-flow → findings by area (with severity) → target-architecture recommendations → prioritized roadmap (quick wins vs strategic). Cite real paths. NO code edits.
