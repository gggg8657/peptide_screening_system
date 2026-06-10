---
marp: true
theme: default
paginate: true
backgroundColor: #ffffff
style: |
  section { font-family: 'Pretendard', sans-serif; }
  h1 { color: #1a365d; }
  h2 { color: #2d3748; }
  h3 { color: #4a5568; }
  table { font-size: 0.75em; }
  code { font-size: 0.8em; }
  .small { font-size: 0.7em; }
  .highlight { background: #fefce8; padding: 0.5em; border-left: 4px solid #eab308; }
---

# AI-Powered SSTR2-Binding Peptide Screening Platform for Radiopharmaceutical Development

**Dongju Kim**
Korea Atomic Energy Research Institute (KAERI)

---

## SSTR2 & Neuroendocrine Tumors (NETs)

### Clinical Significance

- **SSTR2** (Somatostatin Receptor Type 2, UniProt P30874) — 369-aa GPCR
- Overexpressed in **>80%** of well-differentiated NETs (pancreatic, GI, lung)
- Theranostic target: same receptor for **diagnosis** (PET) and **therapy** (PRRT)

### Current Clinical Use

| Application | Radiopharmaceutical | Isotope | Approval |
|-------------|-------------------|---------|----------|
| PET Imaging | ^68Ga-DOTATATE (NETSPOT) | ^68Ga | FDA 2016 |
| PET Imaging | ^68Ga-DOTATOC | ^68Ga | EU |
| PRRT Therapy | ^177Lu-DOTATATE (LUTATHERA) | ^177Lu | FDA 2018 |
| Alpha Therapy | ^225Ac-DOTATATE | ^225Ac | Investigational |

All current agents are based on **octreotide analogs** — cyclic octapeptides derived from SST-14.

---

## Current Radiopharmaceuticals — Comparison

| Property | DOTATATE | DOTATOC | DOTATNOC | Octreotide |
|----------|----------|---------|----------|------------|
| Chelator | DOTA | DOTA | DOTA | - |
| Core Motif | D-Phe-Cys-Tyr-D-Trp-Lys-Thr-Cys-Thr | Similar | Similar | Cyclic octapeptide |
| SSTR2 IC50 | **1.5 nM** (^177Lu) | 14 nM (^68Ga) | 1.6 nM (^68Ga) | 2.0 nM |
| SSTR Selectivity | SSTR2 >> SSTR5 | SSTR2 ~ SSTR5 | Pan-SSTR2/3/5 | SSTR2/5 |
| Clinical Status | Gold standard | Widely used | EU approved | Diagnostic only |

### Key Limitation

All derive from the **same octreotide scaffold** — limited chemical diversity for optimization.

---

## Limitations of Current Approach

### Why We Need AI-Driven Peptide Design

| Challenge | Current Approach | This Platform |
|-----------|-----------------|---------------|
| Sequence space | Manual analog synthesis (~10 variants) | Automated: **~240 candidates/hr** |
| Evaluation | Sequential wet-lab IC50 | In silico ddG + 13 pharmacological properties |
| Optimization | Expert intuition | **Thompson Sampling** Bayesian bandit |
| Scaffold | Octreotide (8-aa) only | SST-14 (14-aa) — larger exploration space |
| Throughput | Months per analog series | Hours per screening campaign |

<div class="highlight">

**Opportunity**: SST-14 (`AGCKNFFWKTFTSC`) retains the native SSTR2 pharmacophore (FWKT) while providing 14 positions for optimization — a significantly larger design space than octreotide's 8 residues.

</div>

---

## SST-14 Scaffold — The Starting Point

### Native Somatostatin-14

```
Sequence:  A  G  C  K  N  F  F  W  K  T  F  T  S  C
Position:  1  2  3  4  5  6  7  8  9  10 11 12 13 14
               |                                  |
               +---- Cys3-Cys14 disulfide bond ---+
                         [FWKT] pharmacophore (pos 7-10)
```

### Critical Structural Features

| Feature | Positions | Function | Radiopharmaceutical Relevance |
|---------|-----------|----------|-------------------------------|
| **FWKT motif** | 7-10 | Core SSTR2 pharmacophore | Must be preserved for receptor binding |
| **Cys3-Cys14** | 3, 14 | Disulfide bond (cyclic constraint) | Conformational rigidity → metabolic stability |
| **Lys9** | 9 | Salt bridge with SSTR2 D122 | Electrostatic anchor — critical for IC50 |
| **Phe6-Phe11** | 6, 11 | Aromatic stacking | Hydrophobic packing in binding pocket |
| **N-terminus** | 1 | Chelator conjugation site | DOTA/NOTA attachment point |

---

## Platform Overview — Dual-Silo Architecture

```
+----------------------------------------------------------------------+
|                    SSTR2 AI Co-Scientist System                      |
+-------------------------------+--------------------------------------+
|  Silo A: NIM API Pipeline     |  Silo B: PyRosetta Flow             |
|  (De novo backbone design)    |  (SST-14 guided mutation)           |
|  8 NVIDIA NIM cloud APIs      |  Local PyRosetta only               |
|  Novel fold exploration       |  Sequence variant optimization      |
+-------------------------------+--------------------------------------+
|                       Shared Components                              |
|  5-Agent AI System: Planner → QC&Ranker → DiversityMgr → Critic     |
|  → Reporter                                                         |
|  Real-time Dashboard (React 19, 20 visualization components)        |
|  FastAPI Backend (7 routers, 30+ endpoints)                          |
+----------------------------------------------------------------------+
```

### For Radiopharmaceutical Researchers

- **Silo A** explores completely **novel peptide folds** — potential new scaffolds
- **Silo B** systematically optimizes the **known SST-14 binder** — immediate clinical translation
- Both feed into the same **validation and visualization dashboard**

---

## AI Agent = Virtual Research Team

### 5 Agents as Specialized Research Roles

| Agent | Role Analogy | What It Does |
|-------|-------------|--------------|
| **Planner** | Principal Investigator | Generates hypotheses: which positions to mutate, what amino acids to try |
| **QC & Ranker** | Quality Control Lead | Applies ddG gate (≤ **-5.0** kcal/mol), clash gate (≤ **10**), ranks candidates |
| **Diversity Manager** | Structural Biologist | Ensures candidates are structurally diverse, not redundant |
| **Critic** | Peer Reviewer | Analyzes failures, proposes parameter adjustments (max 2/iteration) |
| **Reporter** | Lab Notebook Manager | Generates PyMOL 4-panel renders, Markdown reports, JSONL logs |

Each agent is **LLM-driven** (Qwen 2.5 7B) and operates in an iterative loop with structured I/O.

---

## Dashboard — 5-Page Real-Time Monitoring

| Page | Description | Key Components |
|------|-------------|----------------|
| **Silo B** (default) | Live mutation-dock loop monitoring | All 20 visualization components |
| **Silo A** | NIM API 8-step pipeline progress | Pipeline steps, API service status |
| **Combined** | Cross-silo unified candidate ranking | Weighted scoring (ddG 35%, selectivity 20%, stability 15%, PK 15%, chelator 15%) |
| **Settings** | Experiment configuration | Iterations, candidates/iter, LLM model, validation trials, feature toggles |
| **About** | System documentation | Architecture diagrams, 17 validation criteria reference table |

### Technology Stack

- **Frontend**: React 19 + TypeScript + Vite 7 + Recharts
- **Backend**: FastAPI 2.0 + uvicorn (port 8787)
- **Pipeline**: PyRosetta + FlexPepDock + Thompson Sampling bandit
- **CI/CD**: GitHub Actions — **7 jobs**, all passing

---

## CandidateTable — Primary Screening View

### What It Shows

| Column | Description | Radiopharmaceutical Meaning |
|--------|-------------|----------------------------|
| **Rank** | Composite ranking (top-3 highlighted gold/silver/bronze) | Priority order for synthesis |
| **ddG** (kcal/mol) | Interface binding free energy (FlexPepDock) | **IC50 proxy** — more negative = stronger SSTR2 binding |
| **Total Score** (REU) | Rosetta total energy after refinement | Overall structural favorability |
| **Clash** (REU) | Steric conflict score (fa_rep) | Amber >5, Red >10 — steric clash risks chelator interference |
| **Final Score** | Derived ranking metric | Combined assessment |
| **Result** | PASS / FAIL / REF badges | Gate-filtered suitability |

### Additional Columns

- **Repro.** — ddG reproducibility across multiple trials (median, range color-coded)
- **Validation** — Unified PASS/CAUTION/FAIL from 23-criteria assessment
- **Drug-like** — Peptide druglikeness score (0-100): MW, charge, hydrophobicity
- **Nephrotox** — PRRT renal retention risk (Low/Moderate/High) — **critical for ^177Lu/^225Ac therapy**

### Why It Matters for Radiopharmaceutical Development

The ddG score serves as an **in silico proxy for binding affinity**. For PRRT, tumor retention is directly proportional to SSTR2 binding — candidates with more negative ddG are expected to show higher tumor-to-background ratios in PET imaging and greater therapeutic efficacy. The nephrotoxicity column flags candidates that may cause excessive renal dose — the **dose-limiting toxicity** in peptide-based PRRT.

---

## CandidateTable — Interactive Features

### Sorting, Filtering, and Selection

- **5 sortable columns** with ascending/descending toggle (click column headers)
- **Filter by result**: All | PASS | FAIL | REF — isolate candidates that pass all structural rules
- **Paginated**: 12 candidates per page with navigation
- **Checkbox selection** → batch validation and 3D structure viewing

### 3D Viewer Integration

Each candidate row has a **3D button** that opens the Mol* structure viewer modal, loading the corresponding PDB file from `GET /api/structures/{path}`. This allows immediate visual inspection of:

- Binding pose relative to SSTR2
- DOTA/NOTA conjugation site accessibility at N-terminus
- Key interactions (K9-D122 salt bridge, FWKT pocket insertion)

### Batch Validation

Select multiple candidates → click **Validate** → triggers `POST /api/validate/selected` which checks:
- ddG ≤ **-5.0** | Clash ≤ **10** | Total Score ≤ **-300**

---

## PharmacologyPanel — 13 Property Assessment

### Row 1: Physical Properties

| Property | Method | Threshold | Radiopharmaceutical Significance |
|----------|--------|-----------|----------------------------------|
| **GRAVY** | Kyte-Doolittle 1982 mean | [-2, 1] normal | Hydrophobicity → membrane permeation, blood clearance rate, **non-specific organ uptake** |
| **Boman Index** | Radzicka-Wolfenden 1988 | ≥ 2.48 for GPCR | Protein binding potential → **SSTR2 interaction strength**, non-specific plasma protein binding |
| **Instability Index** | Guruprasad 1990 dipeptide weights | < 40 = stable | Metabolic stability → **in vivo half-life**, resistance to serum peptidases |
| **Aliphatic Index** | Ikai 1980 aliphatic volume | Higher = thermostable | Thermal stability → **radiolabeling durability** at elevated temperatures |

### Why It Matters for Radiopharmaceutical Development

GRAVY directly predicts whether a peptide radiotracer will have acceptable blood clearance kinetics. Hydrophilic peptides (negative GRAVY) are preferred for PET tracers requiring rapid background clearance. The Boman index ≥ 2.48 threshold indicates sufficient protein-binding character for GPCR-targeted ligands — essential for SSTR2 radioligands.

---

## PharmacologyPanel — Electrochemistry & Metabolism

### Row 2: Charge & Metabolism

| Property | Method | Radiopharmaceutical Significance |
|----------|--------|----------------------------------|
| **pI** (Isoelectric Point) | Henderson-Hasselbalch | Charge at physiological pH → **renal filtration** behavior (cationic peptides retained in kidneys) |
| **Extinction Coeff** (280nm) | Gill & von Hippel 1989 (Trp/Tyr/Cys count) | UV detection capability → **purification QC** during GMP manufacturing |
| **N-end Rule Half-life** | Bachmair 1986 | N-terminal residue determines metabolic half-life → **in vivo stability** window |
| **Hydrophobic Moment** | Eisenberg 1982 helix model | Amphipathicity → **membrane insertion** propensity, cell uptake mechanism |

### Row 3: Membrane & Stability

| Property | Method | Radiopharmaceutical Significance |
|----------|--------|----------------------------------|
| **Wimley-White Score** | Wimley & White 1996 interface | Water/membrane partitioning → **cellular uptake** vs. aqueous distribution |
| **Charge pH Profile** | pH 7.4 (plasma) vs 6.5 (tumor) | **Tumor selectivity** — charge difference exploits acidic tumor microenvironment |
| **Protease Sites** | Chymotrypsin/trypsin/neprilysin/pepsin | Cleavage vulnerability → **serum stability**, need for D-amino acid substitution |
| **Metal Coordination** | Coordinating residues (His, Cys, Asp, Glu) | **Chelator interference risk** — competing metal-binding sites reduce labeling efficiency |

---

## PharmacologyPanel — Data Source & BLOSUM62

### API Endpoint

```
POST /api/pharmacology/batch
Body: { "sequences": ["AGCKNFFWKTFTSC", "YSCKNFFWKTFTSN", ...] }
Response: { "results": [{ sequence, gravy, boman_index, instability_index, ... }] }
```

- Accepts up to **50 sequences** per batch
- All 13 properties computed from sequence alone (no structure required)
- **pharmacology.py** backend: ~400 lines of pure Python, literature-referenced

### BLOSUM62 Mutation Analysis

The panel includes a **mutation table** comparing each candidate to SST-14 native:

| Column | Description |
|--------|-------------|
| Position | 1-indexed residue position |
| From → To | Native → mutated amino acid |
| BLOSUM62 Score | Conservation score (positive = conservative) |
| Category | Conservative / Semi-conservative / Non-conservative |

### Why It Matters for Radiopharmaceutical Development

Conservative mutations (high BLOSUM62 score) are more likely to **preserve SSTR2 binding** while potentially improving other pharmacological properties. Non-conservative mutations at positions 5, 6, 11 may dramatically alter binding — these are the positions our Thompson Sampling bandit identifies as highest-signal.

---

## ValidationPanel — 5 Structural Rules + Unified Assessment

### Binary Structural Rules (All Must PASS)

| # | Rule | Criterion | Why It's Non-negotiable |
|---|------|-----------|------------------------|
| 1 | **FWKT Conservation** | Positions 7-10 = FWKT | Core pharmacophore — loss = no SSTR2 binding |
| 2 | **K9-D122 Salt Bridge** | Lys at position 9 | Electrostatic anchor to SSTR2 Asp122 (min **2.58A** distance) |
| 3 | **Cys3-Cys14 Disulfide** | Cys at positions 3 and 14 | Cyclic constraint — breaking causes **>+25 REU** penalty/residue |
| 4 | **Phe6-Phe11 Stacking** | Aromatic at positions 6 and 11 | Hydrophobic packing stabilization in binding pocket |
| 5 | **N-term Chelator** | Compatible N-terminus | Required for DOTA/NOTA conjugation — **mandatory for radiolabeling** |

### Unified Validation (23 Criteria)

```
POST /api/validate/unified
Criteria groups: pharmacological (13) + radiopharmaceutical (2) + statistical (3)
Presets: "PRRT Radiopharmaceutical" (default) | "General Peptide" | "Custom"
```

Verdict: **PASS** (≥80%) | **CAUTION** (50-80%) | **FAIL** (<50%)

### Why It Matters for Radiopharmaceutical Development

Rule 5 (N-term chelator) is unique to radiopharmaceutical development — it ensures the peptide's N-terminus is sterically accessible for DOTA/NOTA conjugation without disrupting the SSTR2-binding pharmacophore.

---

## ConvergenceGraph — Optimization Tracking

### What It Shows

- **Recharts ComposedChart**: Line (best ddG per iteration) + Bar (top candidates count)
- **Y-axis left**: ddG (kcal/mol) — lower is better
- **Y-axis right**: Number of top candidates per iteration
- **Convergence threshold**: Δ < **0.5** kcal/mol between consecutive iterations

### Key Metrics (3 stat cards)

| Metric | Description |
|--------|-------------|
| Best ddG | Lowest ddG achieved across all iterations |
| Last ΔddG | Change from previous iteration (green < 0.5, orange ≥ 0.5) |
| Top Candidates | Count of candidates passing QC gates in current iteration |

### Convergence Detection: Mann-Whitney U Test

- Compares ddG distributions of recent vs. previous iterations
- **Null hypothesis**: no significant improvement
- Convergence declared when p-value > threshold (no further improvement)
- Implemented **without scipy dependency** (custom rank-sum calculation)

### Why It Matters for Radiopharmaceutical Development

Researchers can monitor in real-time whether the AI system has exhausted the productive sequence space. When convergence is reached, the current top candidates represent the **best achievable binders** within the explored space — ready for wet-lab synthesis prioritization.

---

## DdGDistribution — Binding Energy Landscape

### What It Shows

- **Recharts BarChart histogram**: ddG values binned at **2.5 kcal/mol** intervals
- Range: **-50 to 0** kcal/mol
- **QC threshold reference line** at **-5.0 kcal/mol** (red dashed)
- Bins left of threshold = passing candidates (stronger binders)

### Summary Statistics (4 cards)

| Stat | Description |
|------|-------------|
| Mean | Average ddG across all candidates |
| Median | Middle value (robust to outliers) |
| Std Dev | Spread of binding energies |
| Pass Gate | Percentage of candidates with ddG ≤ -5.0 |

### Why It Matters for Radiopharmaceutical Development

The distribution shape reveals the **binding energy landscape** of the explored sequence space. A left-shifted distribution (more negative values) indicates the Thompson Sampling bandit is successfully guiding mutations toward higher-affinity sequences. The **-5.0 threshold** corresponds roughly to the minimum binding energy needed for detectable tumor uptake in PET imaging. Candidates well below this threshold (e.g., ddG < -20) are strong candidates for synthesis.

---

## MutationAnalysis — BLOSUM62 Conservation vs ddG

### What It Shows

1. **Position mutation frequency bars** — per-position breakdown of conservative (blue) vs non-conservative (amber) mutations across all candidates
2. **FWKT pharmacophore highlighting** — positions 7-10 shown in yellow (should have 0% mutation frequency)
3. **Scatter plot**: mutation count vs ddG — reveals whether more mutations help or hurt

### Summary Statistics

| Stat | Description |
|------|-------------|
| FWKT Conservation | Percentage of candidates preserving FWKT (target: **100%**) |
| Conservative count | Mutations within BLOSUM62 substitution groups |
| Non-conservative count | Mutations across substitution groups |
| Total candidates | Number of valid sequences analyzed |

### BLOSUM62 Groups Used

```
STA, NEQK, NHQK, NDEQ, QHRK, MILV, MILF, HY, FYW, AG, DE, KR, ST, NQ
```

### Why It Matters for Radiopharmaceutical Development

Conservative mutations are more likely to maintain SSTR2 binding while improving pharmacokinetic properties. The scatter plot helps identify the **optimal mutation count** — too few mutations limit improvement, too many risk destroying binding. For radiopharmaceutical candidates, we want **1-3 mutations** at positions 5, 6, 11 with preserved FWKT.

---

## SARHeatmap — Structure-Activity Relationship

### What It Shows

- **20 x 14 SVG grid**: 20 amino acids (y-axis) × 14 SST-14 positions (x-axis)
- Color scale: slate (0 frequency) → cyan (mid) → **yellow (high frequency)**
- FWKT positions (7-10) have **yellow background highlight**
- Native residues marked as "ref" with dashed border

### Data Source

Computed client-side from all candidates in current pipeline run:
- For each candidate sequence, count amino acid substitutions at each position vs SST-14 native
- Matrix cells show raw count of that AA at that position

### Key Patterns to Look For

| Pattern | Interpretation |
|---------|---------------|
| Hot columns (5, 6, 11) | Positions with highest mutation frequency → optimization targets |
| Cold columns (3, 7-10, 14) | Conserved positions → structural constraints (disulfide, pharmacophore) |
| Hot rows (D, Y, V at pos 5-6) | Preferred amino acid substitutions → synthesis priorities |

### Why It Matters for Radiopharmaceutical Development

The heatmap is a **visual SAR summary** showing which positions tolerate mutation and which amino acids are enriched. For medicinal chemists designing the synthesis campaign, this directly maps to the combinatorial library design — synthesize variants at hot positions with enriched amino acids.

---

## SequenceLogo — Position Conservation

### What It Shows

- **SVG sequence logo**: Shannon information content (bits) per position
- Max theoretical information: log2(20) ≈ **4.32 bits** (single AA perfectly conserved)
- Letter height = information × frequency
- **Color coding**: Hydrophobic (gray) | Polar (green) | Positive (blue) | Negative (red)
- FWKT region (positions 7-10) has amber background highlight

### Information Content Calculation

```
For each position:
  H(pos) = -Σ p(aa) × log2(p(aa))     # Shannon entropy
  I(pos) = log2(20) - H(pos)           # Information content (bits)
  Height(aa) = I(pos) × freq(aa)       # Per-letter height
```

### Interpretation Guide

| Conservation Level | Bits | Meaning |
|-------------------|------|---------|
| Perfectly conserved | ~4.3 | Only 1 AA observed (e.g., C3, C14, F7, W8, K9, T10) |
| Moderately conserved | 2-3 | 2-3 dominant AAs |
| Variable | 0-1 | Many AAs tolerated — optimization opportunity |

### Why It Matters for Radiopharmaceutical Development

High-information positions are **structural constraints** that must be preserved in any radiopharmaceutical candidate. Low-information positions (1, 2, 5, 12, 13) are **optimization handles** where mutations can improve pharmacokinetics without sacrificing SSTR2 binding.

---

## PositionEnrichment — Top Amino Acids per Position

### What It Shows

- **14-row table**: one row per SST-14 position
- For each position: **Top-1, Top-2, Top-3** amino acids with frequency (%) and average ddG
- Color coding: green (favorable ddG) → amber → red (unfavorable)
- FWKT positions highlighted with amber background

### Columns

| Column | Description |
|--------|-------------|
| Pos | Position number (1-14) |
| Ref | Native SST-14 residue |
| Top-1/2/3 | Most frequent AA + frequency% + avg ddG |
| Avg ddG | Mean ddG across all candidates at that position |

### Key Findings from Our Data

| Position | Best Substitution | ddG Impact | Rationale |
|----------|------------------|------------|-----------|
| Pos 5 (Asn) | **Val** (-27.19 best) | -21 vs native | Hydrophobic contact improvement |
| Pos 6 (Phe) | **Asp** (-14.86 best) | Acidic residue stabilizes pocket | Charge complementarity |
| Pos 11 (Phe) | **Ser/Thr** | Reduces per-residue energy from +10.8 to <+1.0 | Steric relief |

### Why It Matters for Radiopharmaceutical Development

This table directly informs **peptide synthesis priorities**. The top-enriched amino acids at each position represent the most promising substitutions for wet-lab validation. Combined with the BLOSUM62 conservation data, this guides the **minimal mutation set** that maximizes binding improvement.

---

## MoleculeViewer — 3D Structure Inspection

### What It Shows

**Mol* v5.6.1** molecular viewer embedded in a full-screen modal with 4 representation modes:

| Mode | Representation | Use Case |
|------|---------------|----------|
| **Complex** | Cartoon (polymer) + Sticks (ligands) | Overall binding pose assessment |
| **Cartoon** | Clean backbone ribbon only | Secondary structure visualization |
| **Ball & Stick** | All atoms as spheres + bonds | Key residue interaction analysis |
| **Surface** | Molecular surface | Binding interface and DOTA attachment site |

### API Integration

```
View 3D button → GET /api/structures/{candidate_id}.pdb
                 → Mol* loads PDB → applyPreset(trajectory, 'default')
```

### Interactive Controls

- **Drag** to rotate | **Scroll** to zoom | **Shift+Drag** to translate
- Camera reset button | Fullscreen toggle | Escape to close

### Why It Matters for Radiopharmaceutical Development

3D visualization is critical for assessing:
1. **DOTA/NOTA conjugation geometry** — is the N-terminus spatially accessible?
2. **Binding pose quality** — does FWKT insert properly into the SSTR2 pocket?
3. **K9-D122 salt bridge distance** — is the electrostatic anchor intact?
4. **Steric clashes** near the chelator attachment site that could reduce labeling efficiency

---

## VisualizationPanel — PyMOL 4-Panel Renders

### What It Shows

**2×2 image grid** generated by PyMOL (headless subprocess) via the Reporter agent:

| Panel | Content | Radiopharmaceutical Insight |
|-------|---------|----------------------------|
| **Overview** | Full SSTR2-peptide complex | Global binding orientation |
| **Close-up** | Binding pocket zoom | FWKT insertion depth, contact distances |
| **Interface** | Contact residues highlighted | Interface size → binding strength correlation |
| **Electrostatics** | Charge surface map | Charge complementarity → no interference with metal coordination |

### Features

- **Lightbox** — click any panel for full-resolution view with focus trap (accessibility)
- **Iteration tag** — shows which pipeline iteration generated the render
- **Lazy loading** — images loaded on scroll for performance
- Images served via `GET /api/images/{path}`

### Why It Matters for Radiopharmaceutical Development

The electrostatics panel is particularly important — it reveals whether the peptide's charge distribution is compatible with DOTA-metal coordination. Positive charge near the N-terminus could interfere with ^68Ga^3+ or ^177Lu^3+ chelation, while the interface panel confirms sufficient contact area for high-affinity binding required for tumor retention.

---

## QCGateChart — Quality Funnel Visualization

### What It Shows

- **Recharts stacked BarChart**: green (Passed) + red (Failed) per gate
- **4 interactive gate summary badges** with pass rate %, mini progress bars
- Click any badge to filter the chart to that gate only

### Gate Definitions (Silo B — PyRosetta mode)

| Gate | Criterion | Pass Threshold |
|------|-----------|---------------|
| **ddG Gate** | Interface binding energy | ddG ≤ **-5.0** kcal/mol |
| **Clash Gate** | Steric conflict score | Clash ≤ **10** REU |
| **Total Score Gate** | Rosetta total energy | Total ≤ **-300** REU |
| **Structural Rules** | 5 binary rules (FWKT, K9, SS, Phe, chelator) | All 5 PASS |

### Gate Logic

```
Final PASS = ddG_Gate AND Clash_Gate AND TotalScore_Gate AND StructuralRules
```

**Sequential AND** — a candidate must pass all gates. No weighting or subjective scoring.

### Why It Matters for Radiopharmaceutical Development

The funnel visualization shows the **attrition rate** at each quality gate. If most candidates fail at the ddG gate, the mutation strategy needs adjustment. If they fail at structural rules, the FWKT conservation is likely being violated. This helps researchers understand **where in the pipeline candidates are being lost** and adjust the search strategy accordingly.

---

## RiskMatrix — Project Risk Assessment

### What It Shows

- **3×3 probability-impact grid**: Low/Medium/High × Critical/Severe/Minor
- **Priority badges**: P0 (critical red) | P1 (high orange) | P2 (medium yellow) | P3 (low green)
- Click any risk badge → detail modal with description, probability, and impact

### Risk Categories Relevant to Radiopharmaceutical Development

| Priority | Risk Example | Impact |
|----------|-------------|--------|
| **P0** | FlexPepDock scoring artifact (ddG outliers) | False positive candidates waste synthesis resources |
| **P1** | In silico ≠ in vitro binding (force field limitations) | Synthesized candidates may not bind SSTR2 |
| **P1** | Chelator conjugation disrupts binding | Labeled compound loses affinity |
| **P2** | Limited sequence diversity in explored space | Missing optimal candidates |
| **P2** | Renal toxicity underestimated | PRRT dose-limiting toxicity |

### Why It Matters for Radiopharmaceutical Development

Transparent risk communication helps researchers make **informed go/no-go decisions** on which candidates to advance to expensive radiosynthesis. The P0 risks (scoring artifacts) are flagged by outlier detection in the CandidateTable (ddG > |80| → amber warning, > |100| → red warning).

---

## RunComparisonPanel — Multi-Experiment History

### What It Shows

- **Archived run table** with sortable columns:
  - Run ID | Started | Status (DONE/RUNNING) | Iterations | Candidates | Best ddG | Trend | LLM Model
- **Mini sparkline** per run showing ddG convergence trend
- **Current run highlighted** with cyan border and "current" badge

### Data Source

```
GET /api/runs          → list of archived runs
GET /api/runs/{run_id} → full run data (candidates, convergence, agents)
```

### Why It Matters for Radiopharmaceutical Development

Multiple experiment runs with different parameters (LLM model, iteration count, mutation strategy) can be compared side-by-side. Researchers can identify which configuration produces the **best candidates** and whether results are reproducible across runs. The LLM model column tracks whether different AI models (Qwen 2.5 7B, Llama 3.1, etc.) lead to different mutation strategies.

---

## ExperimentControl — Pipeline Configuration

### Configurable Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| **Iterations** | 1-999 | 2 | Mutate-dock-score feedback loops |
| **Candidates** | 2-32 | 8 | Mutant variants generated per iteration |
| **Top-K** | 1-20 | 5 | Best candidates passed to next iteration |
| **LLM Model** | Ollama models | qwen2.5:7b | Agent reasoning engine |
| **Objective** | Auto / ddG Only / ddG+Constraints | Auto | Scoring mode selection |
| **Validation Trials** | Off/3/5/10 | 1 | Multi-trial FlexPepDock validation |

### Feature Toggles (6 Add-ons)

| Feature | Tag | Description |
|---------|-----|-------------|
| Cross-Run Dedup | Efficiency | Skip sequences tested in prior runs |
| **Bandit Guidance** | Optimization | Thompson Sampling position selection |
| **Convergence Detection** | Statistics | Mann-Whitney U plateau detection |
| Disulfide Constraint | Structural | Enforce Cys3-Cys14 during FlexPepDock |
| **ADMET Gate** | Pharma | Druglikeness + nephrotoxicity scoring |
| SAR Analysis | Analysis | Position-specific mutation impact heatmap |

### Why It Matters for Radiopharmaceutical Development

The validation trials setting is critical — at **10 trials** (paper standard), each candidate gets 10 independent FlexPepDock runs with **top-3 mean** aggregation, providing statistically robust ddG estimates (~70 sec/trial, early stopping at CV < 0.15). This is essential for confident go/no-go decisions on expensive radiosynthesis.

---

## AgentMonitor — Real-Time Agent Status

### What It Shows

- **5 agent cards** with real-time status: Idle (gray) | Active (green pulse) | Error (red)
- Each card shows:
  - Agent type badge: **LLM** (blue) or **Code** (gray)
  - Task count and per-iteration rate
  - Last active timestamp
  - Latest message (mono-spaced)
  - Expandable **report panel** (hypothesis, proposed changes, summary)

### Agent Report Types

| Agent | Report Content |
|-------|---------------|
| **Planner** | Hypothesis text + mutation strategy |
| **Critic** | Hypothesis + proposed parameter changes (old → new with rationale) |
| **Reporter** | Iteration summary (Markdown) |

### Why It Matters for Radiopharmaceutical Development

The agent monitor provides **transparency into AI reasoning**. Researchers can read the Planner's hypothesis ("Focus mutations on position 6 — acidic residues may form new salt bridge with receptor K305") and the Critic's feedback ("Reduce mutation rate — last iteration produced too many FWKT violations"). This makes the AI's decision-making **auditable and interpretable** — essential for regulatory documentation.

---

## AgentFlowDiagram — Execution Pipeline Visualization

### What It Shows

- **SVG flow diagram** with 6 nodes arranged in a cycle:
  - **Top row** (Generation): Planner → Candidate Gen → Simulation
  - **Bottom row** (Evaluation): QC Ranker → Reporter → Critic
  - **Feedback loop**: Critic → Planner (amber dashed arrow)

### Visual Indicators

| Indicator | Meaning |
|-----------|---------|
| Green dot + glow | Agent currently active |
| Cyan dot | Step completed |
| Red dot + glow | Error state |
| Gray dot | Idle / waiting |
| Animated dashed edges | Data flowing between agents |
| Iteration badge | Current iteration / total |

### Interactive

Click any node → **detail panel** slides in showing agent's last message, hypothesis, and proposed changes.

### Why It Matters for Radiopharmaceutical Development

The flow diagram provides a **high-level overview** of where the pipeline is in its current iteration. During long multi-hour runs (10 iterations × 8 candidates × ~70 sec FlexPepDock), researchers can quickly check if the pipeline is progressing normally or if an agent has encountered an error that needs attention.

---

## Paper Validation — 7-Candidate Benchmark

### Top-3 Mean of 10 Independent Trials

| Rank | ID | Sequence | ddG (REU) | Delta vs WT | Notes |
|------|-----|----------|-----------|-------------|-------|
| 1 | NOV-01 | YSCKNFFWKTFTSN | **-43.92** | -0.15 | **Novel, WT-equivalent** |
| 2 | LIT-01 (WT) | AGCKNFFWKTFTSC | **-43.78** | -- | SST-14 native baseline |
| 3 | LIT-02 | FCCKNFFWKTCTSC | -42.11 | +1.67 | Octreotide-mapped analog |
| 4 | NOV-02 | AGCKNDFWKTFGSE | -41.47 | +2.31 | Novel candidate |
| 5 | SAN-02 (K9A) | AGCKNFFWATFTSC | -39.53 | +4.25 | **Neg. control** |
| 6 | SAN-01 (W8A) | AGCKNFFAKTFTSC | -38.22 | +5.56 | **Neg. control** |
| 7 | LIT-03 | APCKNFFWKTFSSC | -37.30 | +6.47 | CST-14 analog |

<div class="highlight">

**Key Finding**: NOV-01 achieves WT-equivalent binding (**-43.92** vs -43.78 REU) with a non-native sequence (Y1S→Y, S13→N), demonstrating the system can discover competitive binders through systematic exploration.

</div>

---

## Sanity Check — Negative Controls

### Pharmacophore Disruption Validates Directional Consistency

| Mutation | Target | Sequence | ddG (REU) | Delta vs WT | Interpretation |
|----------|--------|----------|-----------|-------------|----------------|
| **W8A** | Trp8 → Ala | AGCKNFF**A**KTFTSC | -38.22 | **+5.56** | Trp8 critical — deepest pocket insertion (13 contacts, min **2.91A**) |
| **K9A** | Lys9 → Ala | AGCKNFFW**A**TFTSC | -39.53 | **+4.25** | Lys9 essential — salt bridge to D122/D136 (min **2.58A**) |

### Validation Metrics

- Both FWKT disruptions show **destabilization** (less negative ddG) ✓
- Directional consistency confirms FlexPepDock captures binding-relevant interactions ✓
- **FWKT conservation rate**: 100% across all passing candidates ✓

### Why It Matters for Radiopharmaceutical Development

These controls prove that the computational scoring function correctly identifies the pharmacophore elements critical for SSTR2 binding. W8 and K9 are the same residues responsible for binding in DOTATATE/DOTATOC — our system independently validates their importance, building confidence in the in silico predictions.

---

## Position 5,6,11 Optimization — Combinatorial Search

### Search Strategy

- **Search space**: 7 × 7 × 7 = **343 combinatorial variants** (selected AAs per position)
- Pre-filtered by FWKT + structural rules → **308 candidates**
- Docked: **20 candidates** (top-ranked by BLOSUM62 + structural compatibility)
- Baseline: analog2 (`AGCKFDFWKTITSC`, ddG = -14.855)

### Top Results

| Rank | Sequence | Pos5 | Pos6 | Pos11 | ddG (REU) | vs Native |
|------|----------|------|------|-------|-----------|-----------|
| 1 | AGCKVDFWKTSTSC | **V** | **D** | **S** | **-27.191** | -21.018 |
| 2 | AGCKVDFWKTTTSC | V | D | T | -23.415 | -17.242 |
| 3 | AGCKYNFWKTSTSC | Y | N | S | -19.224 | -13.051 |

- **15 of 20** docked candidates beat native SST-14
- Best result: **4.4×** lower ddG than native SST-14

### Why It Matters for Radiopharmaceutical Development

Positions 5, 6, 11 are the **optimization handles** — they tolerate mutations that dramatically improve binding without disrupting the FWKT pharmacophore or Cys3-Cys14 disulfide. For radiopharmaceutical candidates, Val5 + Asp6 + Ser11 represents the **most promising substitution pattern** for wet-lab validation.

---

## Mutation Pattern — Thompson Sampling Learned Priorities

### Position Importance (Learned from Docking Feedback)

```
Pos 5  (Asn): ████████████████████  High signal — hydrophilic preferred
Pos 6  (Phe): ████████████████████  High signal — aromatic required
Pos 11 (Phe): ████████████████████  High signal — aromatic/polar preferred
Pos 1  (Ala): ████████████         Moderate — N-term flexibility
Pos 2  (Gly): ████████████         Moderate
Pos 12 (Thr): ████████             Low
Pos 13 (Ser): ████████             Low
Pos 4  (Lys): ████                 Minimal
```

### Mutation Tolerance Summary

| Position | Tolerated AAs | Rejected AAs | Constraint |
|----------|---------------|-------------|------------|
| 1-2 | A, Y, F, S | - | N-term flexibility (chelator access) |
| **3** | **Cys only** | All others | Disulfide bond required |
| 5 | N, D, Q, E, V | P, G | Hydrophilic/hydrophobic tolerated |
| 6 | F, Y, W, D | A, G, V | Aromatic required (pi-stacking) |
| **7-10** | **FWKT only** | All others | **Pharmacophore locked** |
| 11 | F, Y, W, T, S | A, G | Aromatic/polar preferred |
| **14** | **Cys only** | All others | Disulfide bond required |

---

## Best Candidates — Cross-Pipeline Summary

### All Pipelines Combined

| Pipeline | Best Sequence | Metric | Value |
|----------|---------------|--------|-------|
| FastDesign (Silo A) | TPCQTWFYMDAISC | dG | **-62.9** REU |
| De Novo (Silo A, Arm 3) | AALARTIAARFRKELEA | pLDDT | **81.4** |
| Analog Sim (Silo B) | AGCKFDFWKTITSC | ddG | **-14.855** REU |
| Pos 5,6,11 Opt (Silo B) | AGCKVDFWKTSTSC | ddG | **-27.191** REU |
| Paper Validation (Silo B) | YSCKNFFWKTFTSN | top-3 mean | **-43.92** REU |

### Recommended Candidates for Radiosynthesis

| Priority | Candidate | Key Advantages |
|----------|-----------|----------------|
| **#1** | NOV-01 (YSCKNFFWKTFTSN) | WT-equivalent binding, all rules PASS, novel sequence |
| **#2** | Pos-opt best (AGCKVDFWKTSTSC) | 4.4× better than native, V5+D6+S11 pattern |
| **#3** | Analog2 (AGCKFDFWKTITSC) | Best analog sim, Asp6 stabilizes pocket |

---

## Chelator Selection — DOTA vs NOTA vs DTPA

### Chelator Comparison for SSTR2-Binding Peptides

| Property | DOTA | NOTA | DTPA |
|----------|------|------|------|
| **Structure** | Macrocyclic (12-membered) | Macrocyclic (9-membered) | Linear acyclic |
| **^68Ga Stability** | Kd ~ 10^-21 | Kd ~ **10^-26** (preferred) | Not suitable |
| **^177Lu Stability** | Kd ~ **10^-23** (standard) | Not ideal | Kd ~ 10^-22 |
| **^225Ac Stability** | **Standard choice** | Not validated | Not suitable |
| **Labeling Temp** | 95°C (^177Lu), RT (^68Ga) | RT (^68Ga) | RT |
| **Labeling Time** | 15-30 min | 5-10 min | 5 min |
| **Clinical Precedent** | DOTATATE, DOTATOC | ^68Ga-NOTA-compounds | Historical |

### Selection Guide by Clinical Purpose

| Purpose | Recommended Chelator | Isotope | Rationale |
|---------|---------------------|---------|-----------|
| **PET Diagnosis** | **NOTA** | ^68Ga | Higher kinetic stability, faster labeling |
| **Beta Therapy (PRRT)** | **DOTA** | ^177Lu | Gold standard, LUTATHERA precedent |
| **Alpha Therapy** | **DOTA** | ^225Ac | Daughter recoil consideration, best validated |
| **Theranostic Pair** | **DOTA** | ^68Ga + ^177Lu | Same construct for Dx + Tx |

---

## Isotope Guide — ^68Ga / ^177Lu / ^225Ac

### Radionuclide Properties

| Property | ^68Ga | ^177Lu | ^225Ac |
|----------|-------|--------|--------|
| **Decay** | β+ (positron) | β- (beta) | α (alpha) |
| **Half-life** | 68 min | 6.7 days | 10 days |
| **Energy** | 1.9 MeV (β+) | 497 keV (β-) | 5.8 MeV (α) |
| **Tissue Range** | ~2.4 mm (positron) | 1-2 mm | **50-80 μm** |
| **Application** | PET imaging | PRRT therapy | Targeted alpha therapy |
| **Production** | ^68Ge/^68Ga generator | Reactor | ^229Th decay chain |
| **Clinical Example** | NETSPOT | LUTATHERA | Investigational |

### Peptide Requirements by Isotope

| Requirement | ^68Ga (PET) | ^177Lu (Therapy) | ^225Ac (Alpha) |
|-------------|-------------|------------------|----------------|
| SSTR2 Affinity | IC50 < 10 nM | IC50 < **5 nM** | IC50 < **1 nM** |
| Metabolic Stability | Short OK | **High** required | **Very high** required |
| Renal Clearance | Rapid preferred | Moderate (co-infusion) | Critical (recoil daughters) |
| Hydrophobicity | Hydrophilic (neg GRAVY) | Moderate | Moderate |
| Key Pharma Properties | Low pI, rapid clearance | Low instability index, high stability | Ultra-high affinity, minimal off-target |

---

## Candidate-to-Drug — Translation Pathway

### From In Silico to Clinical Application

```
Phase 1: IN SILICO (This Platform)
  AI Co-Scientist → Candidate Generation → ddG Screening
  → Pharmacological Validation (13 props) → Structural Rules (5 gates)
  → Dashboard Review → TOP CANDIDATES SELECTED

Phase 2: SYNTHESIS
  Solid-Phase Peptide Synthesis (SPPS) → Purification (HPLC)
  → Chelator Conjugation (DOTA/NOTA) → Quality Control (MS, HPLC)

Phase 3: RADIOLABELING
  ^68Ga: Generator elution → Labeling (RT, 10 min) → QC (radio-TLC)
  ^177Lu: Reactor-produced → Labeling (95°C, 30 min) → QC
  ^225Ac: ^229Th generator → Labeling (RT, 60 min) → QC

Phase 4: PRECLINICAL
  In vitro: SSTR2 binding assay (IC50) → Internalization → Stability
  In vivo: Biodistribution (xenograft) → PET imaging → Dosimetry

Phase 5: CLINICAL
  Phase I: Safety, dosimetry (^68Ga-PET) → Phase II: Efficacy (^177Lu-PRRT)
```

---

## vs DOTATATE — Comparative Analysis

### SST-14 AI Candidates vs DOTATATE

| Aspect | DOTATATE | Our Best Candidates |
|--------|----------|-------------------|
| **Scaffold** | Octreotide (8-aa cyclic) | SST-14 (14-aa cyclic) |
| **Design Method** | Manual medicinal chemistry | AI-driven systematic search |
| **Sequence Space** | ~10 analogs tested historically | **22,000+** candidates screened |
| **SSTR2 Binding** | IC50 = 1.5 nM (^177Lu-DOTA) | ddG = **-43.92** REU (NOV-01, in silico) |
| **SSTR Selectivity** | SSTR2 >> SSTR5 | SSTR2-focused (selectivity gate in Silo A) |
| **Pharmacophore** | D-Phe-Cys-Tyr-D-Trp-Lys-Thr | **FWKT** (native SST-14 motif) |
| **Chelator** | DOTA (N-term) | DOTA/NOTA (N-term compatible, Rule 5) |
| **Clinical Data** | FDA-approved (LUTATHERA) | In silico validated, **wet-lab pending** |

### Potential Advantages

| Advantage | Rationale |
|-----------|-----------|
| Larger scaffold (14 vs 8 aa) | More positions for optimization |
| Native pharmacophore (FWKT) | Preserved original SSTR2 binding motif |
| AI-optimized positions 5,6,11 | Systematic exploration beyond human intuition |
| BLOSUM62-guided mutations | Conservation-aware substitutions |
| Statistical validation (top-3 mean, 10 trials) | Reproducible ddG measurements |

### Limitations

- **No wet-lab validation yet** — all data is computational
- FlexPepDock scoring approximations may not capture all binding determinants
- D-amino acid substitutions (used in DOTATATE for stability) not yet explored

---

## Wet-Lab Validation Plan — 5-Phase Roadmap

### Phase 1: Peptide Synthesis

| Step | Details | Timeline |
|------|---------|----------|
| SPPS | Top 5 candidates + WT reference | 2-3 weeks |
| Purification | Reverse-phase HPLC | 1 week |
| Characterization | MS (MW confirm), analytical HPLC (purity > 95%) | 1 week |
| Cyclization | Oxidative folding for Cys3-Cys14 disulfide | Included |

### Phase 2: In Vitro Binding

| Assay | Details |
|-------|---------|
| SSTR2 binding | Competitive displacement (^125I-SST-14), IC50 determination |
| Selectivity | SSTR1/3/4/5 counter-screening |
| Internalization | ^68Ga-labeled, CHO-SSTR2 cells, 37°C, 2h |
| Serum stability | Human serum, 37°C, time points 0/1/2/4/8/24h |

### Phase 3-5: Radiolabeling → Preclinical → Clinical

| Phase | Isotope | Key Endpoint |
|-------|---------|-------------|
| **3. Radiolabeling** | ^68Ga | Labeling yield > 95%, specific activity |
| **4. Biodistribution** | ^177Lu | Tumor-to-kidney ratio, blood clearance |
| **5. Therapy** | ^225Ac | Tumor growth inhibition, survival |

---

## Key Advantages of This Platform

### For Radiopharmaceutical Research

| Advantage | Detail |
|-----------|--------|
| **Systematic Exploration** | ~240 candidates/hr screening throughput |
| **Literature-Based Validation** | 13 pharmacological properties from peer-reviewed methods |
| **No Subjective Scoring** | Pure physicochemical criteria — reproducible and auditable |
| **Radiopharmaceutical-Aware** | Chelator compatibility (Rule 5), nephrotoxicity scoring, isotope-specific criteria |
| **Statistical Rigor** | Top-3 mean of N trials, Mann-Whitney U convergence, BLOSUM62 conservation |
| **Real-Time Dashboard** | 20 visualization components for immediate candidate assessment |
| **Transparent AI** | Auditable agent reasoning (Planner hypothesis, Critic feedback) |
| **Production-Grade** | 187 tests, 93% backend coverage, 7 CI/CD jobs |

### Technical Metrics

| Metric | Value |
|--------|-------|
| Backend Tests | **118** (93% coverage) |
| Frontend Tests | **36** (Vitest + RTL) |
| CI/CD Jobs | **7** (all passing) |
| API Endpoints | **30+** across 7 routers |
| UI Components | **20** visualization components |
| Dashboard Pages | **5** (Silo B, Silo A, Combined, Settings, About) |

---

## Conclusion

1. **Designed and verified** a 5-agent AI system for SSTR2-binding peptide screening with **radiopharmaceutical-specific validation criteria**

2. **Dual-silo architecture** enables complementary exploration: de novo design (Silo A) + SST-14 guided mutation (Silo B)

3. **NOV-01** achieves WT-equivalent binding (ddG = **-43.92** REU) — first AI-discovered candidate competitive with native SST-14

4. **Thompson Sampling** automatically identifies productive positions (5, 6, 11) — **V5 + D6 + S11** pattern yields **4.4×** improvement over native

5. **13 pharmacological properties + 5 structural rules** provide comprehensive evaluation from a radiopharmaceutical perspective — including chelator compatibility and nephrotoxicity assessment

6. **Real-time dashboard** with 20 visualization components enables immediate, interactive candidate assessment by radiopharmaceutical researchers

7. **Ready for wet-lab translation**: top candidates identified, DOTA/NOTA chelator strategies defined, 5-phase validation plan prepared

---

## Thank You

### Contact

**Dongju Kim**
dongjukim.dev@gmail.com

Korea Atomic Energy Research Institute (KAERI)

### Resources

- Dashboard: `http://localhost:5173` (frontend) / `http://localhost:8787` (API)
- Documentation: `docs/ai4sci-dashboard.md`, `docs/experiments-and-results.md`
- Diagrams: `docs/diagrams/radiopharma_workflow.mmd`, `candidate_evaluation.mmd`, `isotope_selection.mmd`

---

## Q&A

### Frequently Asked Questions

**Q: How does ddG relate to IC50?**
ddG from FlexPepDock is a **relative** binding energy metric. While not directly convertible to IC50, lower (more negative) ddG consistently correlates with stronger binding. Our sanity checks (W8A: +5.56, K9A: +4.25 destabilization) validate directional consistency.

**Q: Why SST-14 instead of octreotide?**
SST-14's 14-residue scaffold provides **more optimization positions** (5, 6, 11, 12, 13) while retaining the native SSTR2 pharmacophore (FWKT). The larger scaffold also accommodates the Cys3-Cys14 disulfide for conformational rigidity.

**Q: Can this platform be adapted for other GPCR targets?**
Yes — the architecture is generalizable. Replace the reference peptide, adjust structural rules, and retrain the Thompson Sampling bandit. The 13 pharmacological properties and dashboard are target-agnostic.

**Q: What about D-amino acid substitutions?**
Not yet explored in Silo B (PyRosetta FlexPepDock uses L-amino acids). D-amino acid scanning for metabolic stability is planned for the wet-lab validation phase.

---

<!--
Build instructions:
  npx @marp-team/marp-cli docs/presentation_radiopharma.md --html --pdf
  npx @marp-team/marp-cli docs/presentation_radiopharma.md --html
-->
