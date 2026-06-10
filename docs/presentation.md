---
marp: true
theme: default
paginate: true
backgroundColor: #ffffff
style: |
  section { font-family: 'Pretendard', sans-serif; }
  h1 { color: #1a365d; }
  h2 { color: #2d3748; }
  table { font-size: 0.8em; }
  code { font-size: 0.85em; }
  .columns { display: flex; gap: 1.5em; }
  .col { flex: 1; }
---

# Design and Operational Verification of an Agentic AI System for SSTR2-Binding Peptide Candidate Screening

**Dongju Kim**, Soyeon Kim, Yonggyun Yu, Min-Kyu Kim, Ki-Bum Ahn, Ho-Seong Seo*, Yujong Kim*

Korea Atomic Energy Research Institute (KAERI)

**KNS 2026 Spring Conference** | Jeju, 2026-05-07~08

---

## Background & Motivation

- **Neuroendocrine tumors (NETs)** overexpress SSTR2 (Somatostatin Receptor Type 2)
- Current radiopharmaceuticals (DOTATATE, DOTATOC) show clinical success but limited chemical diversity
- **Opportunity**: AI-driven peptide design can systematically explore sequence space beyond manual analog synthesis

### Why AI Co-Scientist?

| Challenge | Traditional Approach | AI Co-Scientist |
|-----------|---------------------|-----------------|
| Sequence space | Manual analog design | Automated combinatorial exploration |
| Evaluation | Sequential wet-lab | In silico docking + pharmacological validation |
| Optimization | Expert intuition | Bayesian bandit + statistical convergence |
| Throughput | ~10 candidates/study | ~240 candidates/hr (screening) |

---

## Research Objective

**Goal**: Design and verify an agentic AI system that autonomously screens SSTR2-selective peptide binder candidates starting from the SST-14 scaffold.

### Dual-Silo Strategy

```
Silo A: De novo backbone design via 8 NVIDIA NIM cloud APIs
        (RFdiffusion -> ProteinMPNN -> ESMFold -> DiffDock -> FlexPepDock)

Silo B: SST-14 guided mutation via local PyRosetta
        (mutate -> dock iterative loop with 5-agent orchestration)
```

### SST-14 Scaffold

```
Sequence:  A  G  C  K  N  F  F  W  K  T  F  T  S  C
Position:  1  2  3  4  5  6  7  8  9  10 11 12 13 14
                |                                  |
                +---- Cys3-Cys14 disulfide bond ---+
                          [FWKT] pharmacophore (pos 7-10)
```

---

## System Architecture Overview

```
+----------------------------------------------------------------------+
|                    SSTR2 AI Co-Scientist System                      |
+-------------------------------+--------------------------------------+
|  Silo A: NIM API Pipeline     |  Silo B: PyRosetta Flow             |
|                               |                                      |
|  De novo backbone design      |  SST-14 guided mutation              |
|  8 NVIDIA NIM APIs            |  Local PyRosetta only                |
|  8-step + selectivity         |  mutate -> dock iterative loop       |
+-------------------------------+--------------------------------------+
|                       Shared Components                              |
|  5 Agents: Planner | QC&Ranker | DiversityMgr | Critic | Reporter   |
|  LLM Provider (Ollama Qwen 2.5 7B)                                  |
|  StatusEmitter (pipeline -> dashboard bridge)                        |
|  FlexPepDock script (PyRosetta docking wrapper)                      |
+----------------------------------------------------------------------+
|  Backend: FastAPI (7 routers, 30+ endpoints)                         |
|  Frontend: React 19 + TypeScript (5 pages, 20+ components)          |
|  CI/CD: GitHub Actions (7 jobs)                                      |
+----------------------------------------------------------------------+
```

---

## Dual-Silo Strategy: Comparison

| Aspect | Silo A (NIM API Pipeline) | Silo B (PyRosetta Flow) |
|--------|--------------------------|-------------------------|
| **Approach** | De novo backbone design | Known peptide mutation |
| **API Dependency** | 8 NVIDIA NIM APIs | None (local only) |
| **Candidate Source** | ProteinMPNN inverse folding | SST-14 random/guided mutation |
| **QC Methods** | pLDDT + dock + Rosetta + selectivity | ddG + stability + pharmacology |
| **Convergence** | ddG delta + patience | Mann-Whitney U + CV |
| **Optimization** | Grid search | Thompson Sampling bandit |
| **Throughput** | API-limited | ~240 cands/hr (Stage 1) |
| **Status** | Design phase | **Fully operational** |

### Complementary Design

- Silo A explores **novel folds** (de novo backbone)
- Silo B explores **sequence variants** of a known binder (SST-14)
- Shared QC gates and pharmacological validation ensure consistency

---

## 5-Agent Agentic System

```
                    +------------------+
                    |     Planner      |  Hypothesis generation
                    | (focus positions,|  + mutation strategy
                    |  mutation type)  |
                    +--------+---------+
                             |
                             v
+------------------+   +-----------+   +------------------+
| DiversityManager |<--| QC&Ranker |-->|     Critic       |
| (structural      |   | (ddG gate,|   | (parameter       |
|  diversity check)|   |  ranking) |   |  adjustment,     |
+------------------+   +-----------+   |  learning)       |
                             |         +------------------+
                             v
                    +------------------+
                    |    Reporter      |  Iteration summary
                    | (lab notebook,   |  + artifact generation
                    |  artifacts)      |
                    +------------------+
```

Each agent is LLM-driven (Qwen 2.5 7B via Ollama), operating in an iterative loop with structured I/O schemas and tool access.

---

## Silo B Pipeline Detail

```
Config (YAML)
  |
  v
Baseline Refinement (best-of-N trials on WT SST-14)
  |
  v
+--[ Iteration Loop ]----------------------------------------+
|                                                             |
|  1. Planner Agent -> hypothesis + focus positions           |
|  2. Mutation Generation (guided via Thompson Sampling)      |
|  3. FlexPepDock (parallel ThreadPoolExecutor)               |
|  4. QC & Ranker -> ddG gate + multi-criteria ranking        |
|  5. Convergence Detector (Mann-Whitney U test)              |
|  6. Diversity Manager -> structural diversity check         |
|  7. Critic Agent -> parameter adjustments for next round    |
|  8. Reporter Agent -> iteration artifacts + lab notebook    |
|                                                             |
+--[ Repeat until convergence or max_iterations ]-----------+
  |
  v
Final Archive (top candidates + PDB structures + dashboard JSON)
```

---

## Silo A Pipeline Detail (8-Step)

```
Step 01: Receptor prep         (OpenFold3 / PDB fallback)
Step 02: Backbone generation   (RFdiffusion NIM)
Step 03: Sequence design       (ProteinMPNN NIM)
Step 03b: BLOSUM62 mutation    (local text-level)
Step 04: Fast QC               (ESMFold NIM -> pLDDT gate)
Step 05: Docking               (DiffDock + Boltz-2 NIM)
Step 05b: Selectivity          (off-target SSTR1/3/4/5)
Step 06: Rosetta refinement    (PyRosetta FlexPepDock)
Step 07: Analysis              (FoldMason lDDT + PyMOL renders)
Step 08: Stability prediction  (half-life estimation)
```

| NIM API Model | Purpose | Step |
|---------------|---------|------|
| RFdiffusion | De novo backbone design | 02 |
| ProteinMPNN | Inverse folding | 03 |
| ESMFold | Structure prediction + pLDDT | 04 |
| DiffDock | Molecular docking | 05 |
| Boltz-2 | Complex structure + affinity | 05 |
| MolMIM | Small molecule generation | Arm1 |
| OpenFold3 | Receptor structure prediction | 01 |

---

## Thompson Sampling Bandit

### Position Optimization via Bayesian Learning

```
For each mutable position i in {1..14} \ {7,8,9,10}:

  Prior:    Beta(alpha_i, beta_i)       # initially Beta(1,1) = uniform
  Sample:   theta_i ~ Beta(alpha_i, beta_i)
  Select:   top-K positions by theta_i
  Mutate:   generate candidates at selected positions
  Observe:  ddG improvement? (yes/no)
  Update:   alpha_i += reward,  beta_i += (1 - reward)
```

### Key Properties

- **Exploration-exploitation balance**: naturally concentrates on productive positions
- **FWKT protection**: positions 7-10 excluded from mutation (pharmacophore conservation)
- **History-aware**: learns across iterations within and across runs
- Focus positions automatically converge to **pos 5, 6, 11** (highest signal)

---

## Convergence Detection

### Mann-Whitney U Test (scipy-free implementation)

- Compare ddG distributions of recent vs. previous iterations
- **Null hypothesis**: no significant improvement in binding energy
- Convergence declared when p-value > threshold (no significant difference)

### Two-Stage Funnel Protocol

| Stage | Trials/candidate | Throughput | Purpose |
|-------|-----------------|------------|---------|
| **Stage 1** (Screening) | 1 trial | ~240 cands/hr | Rapid filtering |
| **Stage 2** (Validation) | up to 10 trials | ~25 cands/hr | Statistical rigor |

### Early Stopping

- CV (coefficient of variation) threshold: **< 0.15**
- Average convergence at **5-6 trials** (out of max 10)
- Final metric: **top-3 mean of N trials** (robust to outliers)
- FlexPepDock: ~70 seconds per trial

---

## Pharmacological Validation

### 13 Properties + 5 Structural Rules

| # | Property | Method | Reference |
|---|----------|--------|-----------|
| 1 | Molecular Weight | Sum of residue MW | Standard |
| 2 | Isoelectric Point | Henderson-Hasselbalch | Lehninger |
| 3 | Net Charge (pH 7.4) | pKa-based | Stryer |
| 4 | GRAVY | Kyte-Doolittle mean | Kyte & Doolittle 1982 |
| 5 | Boman Index | Solubility predictor | Boman 2003 |
| 6 | Instability Index | Dipeptide weights | Guruprasad 1990 |
| 7 | Aliphatic Index | Aliphatic side chain vol | Ikai 1980 |
| 8 | Hydrophobic Moment | Eisenberg helix | Eisenberg 1982 |
| 9 | Wimley-White Score | Interface partitioning | Wimley & White 1996 |
| 10 | Amphipathicity | Hydrophobic face ratio | Computed |
| 11 | Half-life (mammalian) | N-end rule | Bachmair 1986 |
| 12 | Extinction Coefficient | Trp/Tyr/Cys count | Gill & von Hippel 1989 |
| 13 | Aromaticity | Phe+Trp+Tyr fraction | Lobry & Gautier 1994 |

---

## Structural Rules (5 Binary Gates)

| Rule | Criterion | Rationale |
|------|-----------|-----------|
| **FWKT Conservation** | Positions 7-10 = FWKT | Core pharmacophore for SSTR2 binding |
| **K9-D122 Salt Bridge** | Lys at pos 9 required | Electrostatic anchor to SSTR2 D122 |
| **Cys3-Cys14 Disulfide** | Cys at pos 3 and 14 | Cyclic constraint for conformational rigidity |
| **Phe6-Phe11 Stacking** | Aromatic at pos 6 and 11 | Hydrophobic packing stabilization |
| **N-term Chelator** | Compatible N-terminus | Required for radiometal (68Ga/177Lu/225Ac) chelation |

### QC Gate Logic

```
Final PASS = Rule_1 AND Rule_2 AND Rule_3 AND Rule_4 AND Rule_5
```

All five rules must be satisfied. No weighting or subjective scoring -- purely physicochemical criteria derived from literature.

---

## Paper Validation Results

### 7-Candidate Benchmark (top-3 mean of 10 trials)

| Rank | ID | Sequence | ddG (REU) | Notes |
|------|-----|----------|-----------|-------|
| 1 | NOV-01 | YSCKNFFWKTFTSN | **-43.92** | Novel, WT-equivalent |
| 2 | LIT-01 (WT) | AGCKNFFWKTFTSC | -43.78 | SST-14 native baseline |
| 3 | LIT-02 | FCCKNFFWKTCTSC | -42.11 | Literature analog |
| 4 | NOV-02 | AGCKNDFWKTFGSE | -41.47 | Novel candidate |
| 5 | SAN-02 (K9A) | AGCKNFFWATFTSC | -39.53 | Sanity: K9A mutation |
| 6 | SAN-01 (W8A) | AGCKNFFAKTFTSC | -38.22 | Sanity: W8A mutation |
| 7 | LIT-03 | APCKNFFWKTFSSC | -37.30 | Literature analog |

**Key finding**: NOV-01 achieves WT-equivalent binding (-43.92 vs -43.78) with a non-native sequence, demonstrating the system can discover competitive binders.

---

## Sanity Check: Negative Controls

### Pharmacophore Disruption Confirms Directional Consistency

| Mutation | Sequence | ddG (REU) | Delta vs WT | Interpretation |
|----------|----------|-----------|-------------|----------------|
| **W8A** | AGCKNFF**A**KTFTSC | -38.22 | **+5.56** | Trp8 critical for binding |
| **K9A** | AGCKNFFW**A**TFTSC | -39.53 | **+4.25** | Lys9 salt bridge essential |

- Both FWKT pharmacophore disruptions show **destabilization** (less negative ddG)
- Confirms the docking protocol correctly captures binding-relevant interactions
- **FWKT conservation rate**: 100% across all passing candidates

---

## Position Optimization Results

### Combinatorial Exploration of Positions 5, 6, 11

- **Search space**: 7 x 7 x 7 = **343 variants** (selected amino acids per position)
- **Docked**: 20 candidates (after FWKT + structural rule pre-filter)
- **Best result**: ddG = **-27.191 REU** (4.4x native SST-14 in single-trial screening)

### Mutation Tolerance Pattern

| Position | Tolerated | Rejected | Notes |
|----------|-----------|----------|-------|
| Pos 1-2 | A, Y, F, S | - | N-term flexibility |
| Pos 3 | **Cys only** | All others | Disulfide bond required |
| Pos 5 | N, D, Q, E | P, G | Hydrophilic preferred |
| Pos 6 | F, Y, W | A, G, V | Aromatic required (stacking) |
| Pos 7-10 | **FWKT only** | All others | Pharmacophore locked |
| Pos 11 | F, Y, W, T | A, G | Aromatic/polar preferred |
| Pos 14 | **Cys only** | All others | Disulfide bond required |

---

## Mutation Pattern Analysis

### Thompson Sampling Learned Position Priorities

```
Position importance (learned from docking feedback):

Pos 5  (Asn): ████████████████████  High signal
Pos 6  (Phe): ████████████████████  High signal
Pos 11 (Phe): ████████████████████  High signal
Pos 1  (Ala): ████████████         Moderate
Pos 2  (Gly): ████████████         Moderate
Pos 12 (Thr): ████████             Low
Pos 13 (Ser): ████████             Low
Pos 4  (Lys): ████                 Minimal
```

### Key Insights

- Positions 5, 6, 11 dominate binding energy variation
- Hydrophobic/aromatic residues at pos 6, 11 stabilize via pi-stacking with receptor
- Pos 5 substitutions modulate solvent-exposed electrostatics
- FWKT core (pos 7-10) and disulfide (pos 3, 14) are invariant

---

## Dashboard & Monitoring

### React 19 Real-time Dashboard (5 Pages)

| Page | Key Components |
|------|---------------|
| **Silo B** (main) | Live iteration tracking, candidate table, convergence graph |
| **Silo A** | NIM API pipeline step progress |
| **Combined** | Cross-silo candidate comparison, unified ranking |
| **Settings** | Pipeline parameters, LLM model selection, gate thresholds |
| **About** | System info, 17 validation criteria reference table |

### Visualization Components (20+)

```
ConvergenceGraph     DdGDistribution     MutationAnalysis
SARHeatmap           SequenceLogo        PositionEnrichment
QCGateChart          RiskMatrix          PharmacologyPanel
ValidationPanel      RunComparisonPanel  CandidateTable
MetricCard           StatusBadge         VisualizationPanel
```

- **Real-time updates** via StatusEmitter (backend -> frontend bridge)
- **3D structure viewer** integration for top candidates

---

## Testing & CI/CD

### Test Coverage

| Layer | Framework | Tests | Coverage |
|-------|-----------|-------|----------|
| Backend (pyrosetta_flow) | pytest | **118** | **93%** |
| Frontend (React) | Vitest + RTL | **36** | Key components |
| Silo A pipeline | pytest | 9 | Pipeline steps |
| Silo B pipeline | pytest | 24 | HIL mutant gen |
| **Total** | | **187** | |

### CI/CD Pipeline (7 Jobs)

```
Job 1: Python lint (ruff)
Job 2: Python syntax check
Job 3: Silo A unit tests
Job 4: Silo B unit tests
Job 5: Backend tests (pyrosetta_flow)
Job 6: Frontend lint + tests (ESLint + Vitest)
Job 7: Vendored code check (flake8)
```

All 7 jobs passing on GitHub Actions.

---

## Discussion

### System Verification Results

- **Directional consistency**: Sanity checks (W8A, K9A) confirm destabilization as expected
- **Novel candidate discovery**: NOV-01 achieves WT-equivalent binding with non-native sequence
- **Statistical rigor**: top-3 mean of 10 trials provides robust ranking
- **Automation**: Full pipeline from hypothesis to ranked candidates without manual intervention

### Limitations

- In silico only (no wet-lab validation yet)
- FlexPepDock scoring function approximations
- Silo A integration pending (NIM API dependency)

---

## Future Work

### Near-term

- **Silo A integration**: Complete NIM API pipeline and cross-silo candidate merging
- **Expanded search**: Full 20-position combinatorial with bandit-guided pruning
- **Enhanced LLM agents**: Fine-tuned domain-specific models for hypothesis generation

### Wet-lab Validation Plan

| Phase | Activity | Radiometal |
|-------|----------|------------|
| 1 | Solid-phase peptide synthesis (top 5 candidates) | - |
| 2 | SSTR2 binding assay (IC50 determination) | - |
| 3 | Radiolabeling + stability | ^68Ga |
| 4 | In vivo biodistribution (NET xenograft) | ^177Lu |
| 5 | Therapeutic efficacy study | ^225Ac |

### Long-term Vision

- Generalizable agentic AI platform for **any GPCR-peptide** system
- Integration with AlphaFold3 for structure-guided design

---

## Conclusion

1. **Designed and verified** a 5-agent agentic AI system for SSTR2-binding peptide candidate screening

2. **Dual-silo architecture** enables complementary exploration: de novo design (Silo A) + guided mutation (Silo B)

3. **Operational verification** through paper validation:
   - 7 candidates benchmarked with top-3 mean of 10 trials
   - NOV-01 achieves WT-equivalent binding (ddG = -43.92 REU)
   - Sanity checks confirm directional consistency

4. **Thompson Sampling bandit** automatically identifies productive mutation positions (5, 6, 11)

5. **Two-stage funnel** achieves ~240 candidates/hr (screening) with statistical validation

6. **Production-grade engineering**: 187 tests, 93% backend coverage, 7 CI/CD jobs, real-time dashboard

---

## Thank You

### Contact

**Dongju Kim**
dongjukim.dev@gmail.com

Korea Atomic Energy Research Institute (KAERI)

---

### Acknowledgments

This work was supported by KAERI internal R&D programs.

**Software**: PyRosetta (RosettaCommons), NVIDIA NIM APIs, Ollama, React, FastAPI

---

<!--
Build instructions:
  npx @marp-team/marp-cli docs/presentation.md --html --pdf
  npx @marp-team/marp-cli docs/presentation.md --html
-->
