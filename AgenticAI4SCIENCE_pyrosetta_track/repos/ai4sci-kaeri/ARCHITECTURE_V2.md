# ARCHITECTURE V2 — 3-ARM Unified Pipeline

**Date**: 2026-03-05
**Status**: Design (pre-implementation)
**Branch**: `feature/v2-3arm` (to be created)
**Depends on**: ARCHITECTURE.md (v1, current production)

---

## 1. Goals

1. **Silo A + Silo B parallel execution** with independent error isolation
2. **Unified UI** — tab-based navigation, cross-silo candidate comparison
3. **NIM endpoint flexibility** — auto-detect local Docker, fallback to cloud API
4. **Multi-trial validation** — configurable trial count for FlexPepDock variance reduction
5. **Cross-silo validation** — same motif found by two independent approaches = high confidence

---

## 2. System Architecture

```
                        ┌──────────────────────────────┐
                        │        Frontend (React)       │
                        │  Tab: [Silo B] [Silo A] [All]│
                        │  + Settings / NIM Config page │
                        └──────────────┬───────────────┘
                                       │ /api/*
                        ┌──────────────┴───────────────┐
                        │     FastAPI Backend            │
                        │     PipelineRegistry           │
                        │     ProcessManager             │
                        └──────┬────────────┬───────────┘
                               │            │
                  ┌────────────┴──┐   ┌─────┴──────────────┐
                  │   Silo B      │   │     Silo A          │
                  │  PyRosetta    │   │  8-Step NIM Pipeline │
                  │  (subprocess) │   │  (subprocess)        │
                  └───────────────┘   └──────────────────────┘
                         │                      │
                  ┌──────┴──────────────────────┴──────┐
                  │     Shared: StatusEmitter, Agents   │
                  │     CommonCandidate, JSONL log       │
                  └─────────────────────────────────────┘
```

---

## 3. Backend — New Components

### 3.1 PipelineRegistry

Single registry for all pipeline types. New pipelines register via decorator.

```python
# backend/pipeline_registry.py
class PipelineRegistry:
    _pipelines: Dict[str, PipelineMeta] = {}

    @classmethod
    def register(cls, name: str, runner_fn: Callable, config_cls: type):
        cls._pipelines[name] = PipelineMeta(name, runner_fn, config_cls)

    @classmethod
    def get(cls, name: str) -> PipelineMeta:
        return cls._pipelines[name]

    @classmethod
    def list_all(cls) -> List[str]:
        return list(cls._pipelines.keys())
```

Registration:
```python
PipelineRegistry.register(
    "silo_b",
    runner_fn=run_pyrosetta_agentic_mutdock_flow,
    config_cls=FlowConfig,
)
PipelineRegistry.register(
    "silo_a",
    runner_fn=run_3arm_pipeline,
    config_cls=SiloAConfig,
)
```

### 3.2 ProcessManager

Independent subprocess per silo. Error in one silo never affects the other.

```python
# backend/process_manager.py
class ProcessManager:
    _processes: Dict[str, ProcessHandle] = {}

    def start(self, pipeline_name: str, config: dict) -> str:
        """Launch pipeline in subprocess, return run_id."""
        meta = PipelineRegistry.get(pipeline_name)
        run_id = f"{pipeline_name}_{datetime.now():%Y%m%dT%H%M%S}"
        handle = ProcessHandle(
            process=subprocess.Popen(...),
            run_id=run_id,
            pipeline=pipeline_name,
        )
        self._processes[run_id] = handle
        return run_id

    def stop(self, run_id: str) -> bool: ...
    def status(self, run_id: str) -> dict: ...
    def list_running(self) -> List[str]: ...
```

### 3.3 NIMEndpointResolver

Auto-detect local Docker containers. User-selectable [Local] / [Cloud] toggle.

```python
# backend/nim_resolver.py
NIM_SERVICES = {
    "esmfold":      {"container": "nvcr.io/nim/esmfold",      "port": 8081},
    "rfdiffusion":  {"container": "nvcr.io/nim/rfdiffusion",  "port": 8082},
    "proteinmpnn":  {"container": "nvcr.io/nim/proteinmpnn",  "port": 8083},
    "diffdock":     {"container": "nvcr.io/nim/diffdock",      "port": 8084},
    "boltz2":       {"container": "nvcr.io/nim/boltz-2",       "port": 8085},
    "openfold3":    {"container": "nvcr.io/nim/openfold3",     "port": 8086},
    "esm2":         {"container": "nvcr.io/nim/esm2",          "port": 8087},
    "molmim":       {"container": "nvcr.io/nim/molmim",        "port": 8088},
}

class NIMEndpointResolver:
    def __init__(self, mode: str = "auto"):
        """mode: 'auto' | 'local' | 'cloud'"""
        self.mode = mode
        self._cache: Dict[str, str] = {}

    def resolve(self, service: str) -> str:
        """Return endpoint URL for a NIM service."""
        if self.mode == "cloud" or (self.mode == "auto" and not self._is_local(service)):
            return f"https://health.api.nvidia.com/v1/{service}"
        return f"http://localhost:{NIM_SERVICES[service]['port']}/v1"

    def _is_local(self, service: str) -> bool:
        """Check if Docker container is running locally."""
        # docker ps --filter + health check, cached per session
        ...

    def status_all(self) -> Dict[str, dict]:
        """Return status of all NIM services for UI display."""
        return {
            name: {
                "local_available": self._is_local(name),
                "endpoint": self.resolve(name),
                "mode": "local" if self._is_local(name) else "cloud",
            }
            for name in NIM_SERVICES
        }
```

**Key constraint**: Cloud API code (nim_client.py) is NOT modified. Only the endpoint URL changes.

### 3.4 Unified Ranking

Cross-silo candidate comparison with weighted scoring:

```
Final Score = ddG(0.35) + selectivity(0.20) + stability(0.15)
            + pharmacokinetics(0.15) + chelator_compatibility(0.15)
```

- Candidates from both silos appear in one table
- Color-coded by source silo
- Cross-silo matches (same motif from both) flagged as high-confidence

---

## 4. Frontend — Navigation & Pages

### 4.1 Tab Bar (not sidebar)

Tab bar at top — 0% content area reduction vs sidebar.

```
┌──────────────────────────────────────────────────────┐
│  [Silo B: PyRosetta]  [Silo A: 3-ARM]  [Combined]   │
│  [Settings]                                          │
└──────────────────────────────────────────────────────┘
```

### 4.2 Page Structure

| Page | Route | Content |
|------|-------|---------|
| Silo B | `/silo-b` | Current dashboard (as-is) |
| Silo A | `/silo-a` | NIM pipeline dashboard |
| Combined | `/combined` | Cross-silo ranking, convergence overlay |
| Settings | `/settings` | NIM config, trial presets, API keys |
| About | `/about` | System features, architecture, references |

### 4.3 Routing (react-router v6)

```tsx
// Phase 0: wrap existing App content
<BrowserRouter>
  <AppLayout>           {/* tabs + header */}
    <Routes>
      <Route path="/" element={<Navigate to="/silo-b" />} />
      <Route path="/silo-b" element={<PipelineDetailPage pipeline="silo_b" />} />
      <Route path="/silo-a" element={<PipelineDetailPage pipeline="silo_a" />} />
      <Route path="/combined" element={<CombinedPage />} />
      <Route path="/settings" element={<SettingsPage />} />
    </Routes>
  </AppLayout>
</BrowserRouter>
```

### 4.4 Validation Trial Presets (implemented)

ExperimentControl now has 4 preset buttons:

| Button | Trials | Use Case |
|--------|--------|----------|
| Off | 1 | Fast screening, no extra validation |
| 3 Quick | 3 | Quick variance check (~10 min) |
| 5 Std | 5 | Standard validation (~15 min) |
| 10 Paper | 10 | Publication-quality, top-3 mean (~30 min) |

Backend `FlowConfig.validation_n_trials` already supports this (added 2026-03-04).

### 4.5 NIM Config Page

```
┌─────────────────────────────────────────────────┐
│  NIM Service Configuration                       │
│                                                   │
│  Mode: [Auto] [Local Only] [Cloud Only]          │
│  NGC API Key: [••••••••••••] [Save]              │
│                                                   │
│  ┌──────────┬────────┬──────────┬────────────┐   │
│  │ Service  │ Status │ Mode     │ GPU Req    │   │
│  ├──────────┼────────┼──────────┼────────────┤   │
│  │ ESMFold  │  local │ Local    │ 8GB VRAM   │   │
│  │ ProtMPNN │  local │ Local    │ 8GB VRAM   │   │
│  │ RFdiff   │ cloud  │ Cloud    │ 24GB VRAM  │   │
│  │ DiffDock │ cloud  │ Cloud    │ 16GB VRAM  │   │
│  │ Boltz-2  │ cloud  │ Cloud    │ 24GB VRAM  │   │
│  │ OpenFold3│ cloud  │ Cloud    │ 16GB VRAM  │   │
│  │ ESM2     │  local │ Local    │ 4GB VRAM   │   │
│  │ MolMIM   │ cloud  │ Cloud    │ 8GB VRAM   │   │
│  └──────────┴────────┴──────────┴────────────┘   │
│                                                   │
│  Recommended: ESMFold + ProteinMPNN + ESM2 local │
│  (20GB VRAM total), rest cloud                   │
└─────────────────────────────────────────────────┘
```

---

## 5. NIM Docker Local Deployment

### 5.1 Service Analysis

| Service | Image | GPU VRAM | Local Feasible | Priority |
|---------|-------|----------|----------------|----------|
| ESMFold | nvcr.io/nim/esmfold | ~8GB | Yes | High (QC) |
| ProteinMPNN | nvcr.io/nim/proteinmpnn | ~8GB | Yes | High (seq design) |
| ESM2 | nvcr.io/nim/esm2 | ~4GB | Yes | Medium |
| MolMIM | nvcr.io/nim/molmim | ~8GB | Yes | Low |
| DiffDock | nvcr.io/nim/diffdock | ~16GB | Possible | Medium |
| RFdiffusion | nvcr.io/nim/rfdiffusion | ~24GB | Needs A100 | Low |
| Boltz-2 | nvcr.io/nim/boltz-2 | ~24GB | Needs A100 | Low |
| OpenFold3 | nvcr.io/nim/openfold3 | ~16GB | Possible | Low |

### 5.2 Hybrid Strategy (recommended)

- **Local** (RTX 3090/4090 24GB): ESMFold + ProteinMPNN + ESM2 (~20GB total)
- **Cloud**: RFdiffusion, Boltz-2, DiffDock, OpenFold3 (high VRAM or infrequent)
- **Code change**: ~50 lines in nim_client.py endpoint routing via NIMEndpointResolver

---

## 6. Implementation Phases

### Phase 0: Zero-Risk Migration (current code, no breakage)

| Task | Files | Risk |
|------|-------|------|
| Add react-router v6 | frontend/package.json, App.tsx | **Done** |
| Split App.tsx → AppLayout + PipelineDetailPage | frontend/src/ | **Done** |
| Validation trial preset UI | ExperimentControl.tsx | **Done** |
| `validation_n_trials` in ExperimentConfig | useExperiment.ts | **Done** |

### Phase 1: Backend Infra

| Task | Files | Dependencies |
|------|-------|-------------|
| PipelineRegistry | backend/pipeline_registry.py | None |
| ProcessManager | backend/process_manager.py | PipelineRegistry |
| NIMEndpointResolver | backend/nim_resolver.py | None |
| `/api/pipelines` router | backend/routers/pipelines.py | Registry + Manager |

### Phase 2: Silo A Integration

| Task | Files | Dependencies |
|------|-------|-------------|
| SiloAConfig dataclass | AG_src/pipeline/ | CommonFlowConfig |
| StatusEmitter for Silo A | AG_src/pipeline/orchestrator.py | StatusEmitter |
| Silo A tab in frontend | frontend/src/ | Phase 1 routing |

### Phase 3: Combined Dashboard

| Task | Files | Dependencies |
|------|-------|-------------|
| CommonCandidate schema | backend/ or shared/ | Phase 2 |
| Cross-silo ranking table | frontend CombinedPage | CommonCandidate |
| Convergence overlay graph | ConvergenceGraph.tsx | Both silos emitting |
| Settings page (NIM config) | frontend SettingsPage | NIMEndpointResolver |

### Phase 4: Advanced

| Task | Description |
|------|-------------|
| Cross-silo candidate exchange | Silo A top → Silo B refinement |
| Unified QC gate | Combined metrics from both silos |
| Wet-lab proposal generation | WS5, based on combined results |

---

## 7. Legacy Cleanup

| Item | Action | Reason |
|------|--------|--------|
| `backend/api_server.py` | Delete | 100% redundant with FastAPI routers |
| `AG_src/pipeline/orchestrator.py` CLI entry | Keep | Standalone execution still useful |
| Silo B direct execution CLI | Keep | `python -m pyrosetta_flow.runner` |

---

## 8. Design Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| V2-D1 | Tab bar (not sidebar) | 0% content area loss, matches current layout |
| V2-D2 | react-router v6 | Industry standard, lazy loading support |
| V2-D3 | ProcessManager subprocess isolation | One silo crash never affects the other |
| V2-D4 | NIMEndpointResolver auto-detect | Cloud code untouched, transparent URL routing |
| V2-D5 | Both silos run in parallel | Independent processes, shared StatusEmitter |
| V2-D6 | CommonCandidate unified schema | Cross-silo ranking requires shared format |
| V2-D7 | Phase 0 first | Zero-risk migration, validate routing before adding features |
| V2-D8 | Hybrid NIM deployment | ESMFold+ProtMPNN+ESM2 local (20GB), rest cloud |
| V2-D9 | Trial count presets in UI | User-selectable validation thoroughness |
| V2-D10 | JSONL common log format | Already proven in Silo B, append-only, streaming-friendly |
