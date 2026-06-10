# Infrastructure Reference

## 1. Pipeline Modules

### 1.1 Silo A — 3-Arm SSTR2 Virtual Screening

**Path:** `pipelines/silo_a/`

Three parallel virtual screening arms targeting SSTR2, unified via cross-arm normalization.

```
Config (YAML) → NimClientBundle (DI)
  → Arm 1: MolMIM → DiffDock (small molecule)
  → Arm 2: FlexPepDock (peptide variants)
  → Arm 3: RFdiffusion → ProteinMPNN → ESMFold (de novo)
  → UnifiedScorer → Ranked Candidates + Manifest
```

| Module | File | Purpose |
|--------|------|---------|
| Config | `src/config.py` | Pydantic `SiloAConfig` — pocket, arm1/2/3, scoring, output |
| Models | `src/models.py` | `ArmName`, `RunStatus`, `CandidateRecord`, `ArmResult` |
| Clients | `src/clients.py` | `NimClientBundle` DI + 5 Protocol interfaces + factory |
| Arms | `src/arms.py` | `ArmRunner` ABC + `Arm1SmallMolRunner`, `Arm2FlexPepRunner`, `Arm3DeNovoRunner` |
| Scoring | `src/scoring.py` | `UnifiedScorer` — MinMax normalization, cross-arm ranking with diversity weight |
| Orchestrator | `src/orchestrator.py` | `SiloAOrchestrator` — 3-arm execution, scoring, manifest; `to_unified()` for cross-silo comparison |

### 1.2 Silo B — HIL SST-14 Mutant Generation

**Path:** `pipelines/silo_b/`

Constraint-driven mutant generation from SST-14 template (`AGCKNFFWKTFTSC`) with multi-objective scoring and 3-phase human-in-the-loop (HIL) gates.

```
Config → Constraint Compiler → Generator → Drugability Filter
  → Docking (FlexPepDock) → Stability Estimator → Multi-Objective Scoring
  → HIL Gate 1 (static) → Gate 2 (docking triage) → Gate 3 (human)
  → Top Candidates + Manifest
```

| Module | File | Purpose |
|--------|------|---------|
| Config | `src/config.py` | 30+ Pydantic models with strict `extra=forbid` validation |
| Constraint | `src/constraint_compiler.py` | Frozen positions, per-position AA allowlists, pairwise rules; sequence validation |
| Generator | `src/generator.py` | Auto-selects enumerate/sampling strategy by design space density; Hamming dedup |
| Filter | `src/filters.py` | `DrugabilityFilter` (NG/DG deamidation, Met oxidation, aggregation) + `DuplicateFilter` |
| Docking | `src/docking.py` | `DockingRunner` ABC + `PyRosettaDockingRunner` (~15s/candidate) + `MockDockingRunner` |
| Stability | `src/stability.py` | 5-factor heuristic (hydropathy, charge, proline/glycine penalty, conservation) |
| Relax | `src/relax.py` | `ComplexRelaxer` ABC + `PyRosettaComplexRelaxer` (FastRelax with coordinate constraints) |
| Scoring | `src/scoring.py` | 5-objective synthesis (dG, stability, druggability, diversity, HIL confidence) + violation penalties |
| Gates | `src/gates.py` | `HILGate` ABC + `DefaultHILGate` — 3-phase gate reports |
| Orchestrator | `src/orchestrator.py` | Full pipeline orchestration + `to_unified()` converter |

**Docs:** `docs/ARCHITECTURE.md` (6-layer design), `docs/METHODOLOGY.md` (10-step pipeline), `configs/schema.md` (YAML schema reference).

### 1.3 Orchestration Layer

**Path:** `pipelines/orchestration/`

Cross-silo state machine coordinating Silo A/B/C execution, failure recovery, and result aggregation.

| File | Purpose |
|------|---------|
| `state_machine.py` | `RunState` (8 states: CREATED→DISPATCHED→RUNNING→RECOVERING→JOIN_WAIT→JOIN_READY→AGGREGATING→COMPLETED/ABORTED), `SiloState`, `FailureKind` enums; mode-aware join-readiness checker |
| `policy.py` | Pydantic policy models: `JoinPolicy` (all_of join, required/optional silos), `ResourcePolicy` (max workers per silo), `FailureClassifierPolicy` (scientific vs system), `RecoveryPolicy` (exponential backoff), `RankingFusionPolicy` (weighted_sum/pareto/rank_product) |
| `aggregator.py` | `rank_fusion_weighted_sum()` — per-silo weight normalization, cross-silo fusion into `AggregatedResult` |
| `recovery.py` | `decide_retry()` — exponential backoff [10s, 30s, 60s], configurable max retries |

**Config:** `configs/orchestration_policy.yaml` — join policy (all_of, timeout 7200s), resource limits (A:3, B:2, C:1 workers), failure classification (scientific vs system), recovery (max 3 retries), ranking fusion weights (A:0.34, B:0.33, C:0.33).

### 1.4 Shared Models

**Path:** `pipelines/shared/models.py`

| Type | Purpose |
|------|---------|
| `Silo` (enum) | SILO_A, SILO_B, SILO_C |
| `Modality` (enum) | SMALL_MOL, PEPTIDE_VARIANT, DE_NOVO, SST14_MUTANT |
| `UnifiedCandidate` (frozen dataclass) | Cross-silo comparison schema — id, silo, modality, structure, raw_scores, bridge_metrics (dg_est, clash, stability, feasibility), confidence, provenance |
| `CrossSiloManifest` | Run audit trail — run_id, timestamp, config hashes, candidates |

**Design patterns:** ABC + mock implementations, frozen dataclasses, Pydantic strict validation, DI via protocol interfaces.

---

## 2. BioNeMo Integration

**Path:** `bionemo/`

NVIDIA BioNeMo NIM API client library. Cloud-hosted inference — no local GPU required. All clients inherit from `NVIDIABaseClient` (exponential backoff retry for 429/5xx, API key loading from env var / .env file / key file).

| Client | Model | Endpoint | Function |
|--------|-------|----------|----------|
| `molmim_client.py` | MolMIM (65.2M) | `health.api.nvidia.com/.../molmim` | Small molecule generation/optimization (CMA-ES, QED/plogP) |
| `diffdock_client.py` | DiffDock | `health.api.nvidia.com/.../diffdock` | Molecular docking (protein + ligand binding poses) |
| `rfdiffusion_client.py` | RFdiffusion | `health.api.nvidia.com/.../rfdiffusion` | De novo backbone design (contig DSL, hotspot targeting) |
| `proteinmpnn_client.py` | ProteinMPNN | `health.api.nvidia.com/.../proteinmpnn` | Inverse folding (backbone → sequence, temperature sampling) |
| `esmfold_client.py` | ESMFold (650M) | `health.api.nvidia.com/.../esmfold` | Structure prediction (sequence → PDB, pLDDT confidence) |

**Pipeline scenarios** (`01_`–`07_`): MolMIM embedding similarity, molecule generation, property optimization, SSTR2 pocket analysis, small molecule screening (Arm 1), FlexPepDock (Arm 2), de novo binder design (Arm 3).

---

## 3. Testing

**Framework:** pytest (+ unittest in some AG_src tests)

| Suite | Path | Tests | Scope |
|-------|------|-------|-------|
| Silo A | `pipelines/silo_a/tests/` | 9 | Config loading, scoring normalization, cross-arm ranking |
| Silo B | `pipelines/silo_b/tests/` | 24 | Config, constraints, filters, generator, docking, relax, scoring, orchestrator |
| Orchestration | `tests/orchestration/` | 7 | State machine, policy loading, failure classification, retry logic |
| Shared | `pipelines/shared/tests/` | 1 | UnifiedCandidate serialization |
| AG_src Agents | `AG_src/tests/` | 165 | Agents, config, schemas, design alignment, pharma properties (13 methods + 5 rules), selectivity, pipeline E2E |
| PyRosetta Flow | `pyrosetta_flow/tests/` | 118 | Adapter, bandit, convergence, ranking, runner helpers/integration, schema |

**Total: ~341 tests across 28 files.**

```bash
pytest pipelines/silo_a/tests/ -q    # Silo A
pytest pipelines/silo_b/tests/ -q    # Silo B
pytest tests/orchestration/ -q        # Orchestration
```

**Pytest config** (`pyproject.toml`):
```toml
[tool.pytest.ini_options]
testpaths = ["pipelines"]
pythonpath = ["."]
```

---

## 4. CI/CD

**File:** `.github/workflows/ci.yml` — 7 jobs, triggered on push (main, feature/**) and PR (main).

| Job | Description |
|-----|-------------|
| 1. Python Lint & Syntax | `py_compile` syntax check + Flake8 critical errors (E9/F63/F7/F82, blocking) + style warnings (non-blocking, max-complexity=15, max-line-length=120). Excludes vendored/venv dirs. |
| 2. Client Import Test | Validates BioNeMo module imports (all 5 clients) + utility script imports. |
| 3. Structure File Validation | PDB/CIF parsing via BioPython. CIF→PDB round-trip test on AF3 output files. |
| 4. Documentation Link Check | Internal file link validation in all `.md` files. Skips http/https/mailto/anchors. Non-blocking. |
| 5. NIM API Smoke Test | Health check to NIM API endpoint. Push-to-main only, requires `NVIDIA_API_KEY` secret. |
| 6. Frontend Lint, Test & Build | Node.js 20: ESLint + Vitest/RTL tests + TypeScript build (`ai4sci-kaeri/frontend/`). |
| 7. ai4sci-kaeri Python Lint | Separate lint for `ai4sci-kaeri/` working dir. Excludes `AG_src/scripts` (vendored). |

All jobs run on `ubuntu-latest` with Python 3.11 (except Job 6: Node 20). Permissions: `contents: read`.

---

## 5. Environment Setup

**Conda environment:** `bio-tools` (defined in `environment-bio-tools.yml`)

```bash
conda env create -f environment-bio-tools.yml
conda activate bio-tools
python scripts/verify_bio_tools_env.py   # smoke test
```

**Channels:** RosettaCommons, conda-forge, bioconda, defaults

| Category | Packages |
|----------|----------|
| Python | >=3.10, <3.13 |
| Scientific | numpy, scipy |
| Structural Biology | biopython, rdkit, gemmi |
| Modeling | pyrosetta (academic license), pymol-open-source, foldmason |
| Utilities | tqdm, ipywidgets, psutil |
| Pip | meeko, py3Dmol, pynvml |

**API key setup:** Set `NGC_CLI_API_KEY=nvapi-...` env var, or place in `molmim.key`/`ngc.key`, or use `bionemo/.env`.

**Notes:**
- PyRosetta requires academic license from RosettaCommons
- All AI inference uses NVIDIA NIM cloud API — no local GPU required
- See `ENVIRONMENT.md` for detailed setup and verification steps

---

## 6. Scripts & Utilities

**Path:** `scripts/` — 22 shell scripts + 8 Python scripts

### Pipeline Execution

| Script | Purpose |
|--------|---------|
| `run_sstr2_pipeline.sh` | Runs all 3 Arms sequentially (calls bionemo/05,06,07) |
| `run_scenarios.sh` | Runs MolMIM scenarios 01–03 |
| `run_arm1.sh` / `run_arm2.sh` / `run_arm3.sh` | Individual arm execution |
| `run_pocket_analysis.sh` | SSTR2 pocket extraction (preprocessing) |
| `run_arm3_esmfold.sh` / `run_arm3_step2.sh` / `run_arm3_step2_v2.sh` | Arm 3 phase variants |

### Testing & Verification

| Script | Purpose |
|--------|---------|
| `test_molmim.sh` / `test_molmim_curl.sh` | MolMIM API connectivity tests |
| `test_esmfold.sh` / `test_diffdock.sh` | ESMFold / DiffDock API tests |
| `setup_ubuntu2204.sh` | Full environment setup (Miniconda, conda env, tool verification) |
| `verify_bio_tools_env.py` | Import smoke test (Biopython, Meeko, PyRosetta) |

### Build & Infrastructure

| Script | Purpose |
|--------|---------|
| `build_autodock_gpu.sh` | AutoDock-GPU compilation |
| `compile_mermaid.sh` | Mermaid diagram generation |
| `git_status.sh` / `push_bionemo.sh` / `push_pipeline.sh` / `sync_and_push.sh` | Git operations |

### Python Utilities

| Script | Purpose |
|--------|---------|
| `cif_to_pdb.py` | mmCIF → PDB conversion (BioPython) |
| `peptide_design_utils.py` | Cysteine detection, design position generation |
| `generate_architecture_diagram.py` | Matplotlib system architecture figure |
| `fig1_variant_{a,b,c,d}.py` | Publication figure variants |
