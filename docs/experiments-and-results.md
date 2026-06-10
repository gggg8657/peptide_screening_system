# Experiments and Results

> Comprehensive log of all experiments, notebooks, and pipeline results in the PRST_N_FM project.
> Target: SSTR2 (Somatostatin Receptor Type 2) | Reference peptide: SST-14 (`AGCKNFFWKTFTSC`)

---

## 1. Experiment Log

Six experiment documents in `experiments/` trace the progression from data preparation to virtual screening.

| # | File | Purpose | Key Result |
|---|------|---------|------------|
| 00 | `00_FULL_REPORT.md` | Master report covering the full pipeline (Arm 1-3 + FastDesign + Unified) | 3-Arm screening completed; best dG = -62.9 REU (FastDesign), best pLDDT = 81.4 (de novo) |
| 01 | `01_cif_to_pdb.md` | Convert AlphaFold3 mmCIF outputs to PDB format | 13/13 files converted (5 models + 8 templates) |
| 02 | `02_foldmason_msa.md` | Structure-based MSA of 3 AF3 models via FoldMason | Average MSA lDDT = 0.664 (moderate consistency) |
| 03 | `03_pymol_visualization.md` | Validate PDB loading and rendering in PyMOL OSS 3.1.0 | Cartoon, surface, B-factor coloring, multi-model alignment all functional |
| 04 | `04_pyrosetta_setup.md` | Install and verify PyRosetta 2026.06 in conda `bio-tools` | `pyrosetta.init()` successful; scoring, relax, docking ready |
| 05 | `05_sstr2_virtual_screening.md` | 3-Arm virtual screening pipeline (Small molecule / Peptide variant / De novo) | Arm 1: 40 candidates (QED 0.94); Arm 2: 13 variants designed; Arm 3: 16 de novo peptides (8 with pLDDT > 70) |

---

## 2. Demo Notebooks

Six Jupyter notebooks in `notebooks/` plus one Colab notebook provide interactive demonstrations.

| Notebook | Purpose | Key Content |
|----------|---------|-------------|
| `SSTR2_SST14_demo.ipynb` | FastDesign peptide optimization (main pipeline) | CIF-to-PDB, chain standardization, peptide relax, FastDesign x20, FlexPepDock refinement, 3D visualization |
| `demo_sstr2_virtual_screening.ipynb` | 3-Arm parallel screening demo | AF3 confidence analysis, binding pocket (35 residues), MolMIM/DiffDock, Ala-scanning, RFdiffusion+ProteinMPNN+ESMFold |
| `unified_sstr2_binder_discovery.ipynb` | Unified binder discovery (physics + AI) | 5-phase pipeline: QC, FastDesign, De Novo, integrated ranking, radiopharmaceutical assessment |
| `comparison_fastdesign_vs_dock.ipynb` | Head-to-head strategy comparison | Dock-then-Design (dG -54.5) vs Mutate-then-Dock (dG -33.6); 9.4x speed difference; resource profiling |
| `presentation_sstr2_pipeline.ipynb` | Presentation-quality dashboard | AF3 model comparison, FoldMason conservation, pocket analysis, 3-Arm summary with publication-ready figures |
| `colab_sstr2_demo/SSTR2_SST14_Pipeline.ipynb` | Google Colab self-contained demo | Installs PyRosetta via pyrosetta-installer; runs full pipeline from CIF-to-PDB through FlexPepDock |

**Comparison report**: `notebooks/comparison_results.md` documents the Dock-then-Design vs Mutate-then-Dock analysis with per-candidate data, resource timeseries, and diversity analysis. Conclusion: **two-stage funnel** (B for broad screening, A for refinement) is optimal.

---

## 3. Pipeline Results

### 3.1 Silo A Results (`results/`)

**FoldMason** (`results/foldmason/`): AA alignment, 3Di alignment, Newick guide tree, interactive HTML report.

**3-Arm Screening** (`results/sstr2_docking/`):

| Path | Contents |
|------|----------|
| `binding_pocket.json` | 35 pocket residues (5A cutoff from SST-14) |
| `sstr2_receptor.pdb` | Isolated SSTR2 receptor structure |
| `arm1_smallmol/` | 2 DiffDock result JSONs from MolMIM-generated candidates |
| `arm2_flexpep/` | Variant analysis JSON + wildtype PDB |
| `arm3_denovo/` | 4 RFdiffusion backbones, 16 ESMFold PDBs, 2 final result JSONs |

### 3.2 Silo B Results (`runs/`)

#### Paper Validation (`paper_validation/VALIDATION_REPORT.md`)

FlexPepDock ddG with 10 independent trials per candidate, top-3 mean metric:

| ID | Category | Sequence | Top-3 Mean ddG | Delta vs WT |
|----|----------|----------|-----------------|-------------|
| LIT-01 | WT reference | `AGCKNFFWKTFTSC` | **-43.78** | -- |
| NOV-01 | Novel (iter-1) | `YSCKNFFWKTFTSN` | **-43.92** | -0.15 (WT-equivalent) |
| LIT-02 | Octreotide-mapped | `FCCKNFFWKTCTSC` | -42.11 | +1.67 |
| NOV-02 | Novel (iter-2) | `AGCKNDFWKTFGSE` | -41.47 | +2.31 |
| SAN-02 | K9A (neg. ctrl) | `AGCKNFFWATFTSC` | -39.53 | +4.25 |
| SAN-01 | W8A (neg. ctrl) | `AGCKNFFAKTFTSC` | -38.22 | +5.56 |
| LIT-03 | CST-14 | `APCKNFFWKTFSSC` | -37.30 | +6.47 |

Sanity checks passed: W8A and K9A correctly show weakened binding.

#### SST-14 Analog Simulation (`sst14_analogs_sim/summary_report.md`)

6 analogs with 13 pharmacological properties + 5 structural rules:

| Rank | Analog | Sequence | ddG (REU) | Verdict |
|------|--------|----------|-----------|---------|
| 1 | analog2 | `AGCKFDFWKTITSC` | **-14.855** | Recommended (Asp6 stabilizes pocket) |
| 2 | analog1 | `AGCKYEFWKTVTSC` | -13.682 | Recommended |
| 3 | native | `AGCKNFFWKTFTSC` | -6.173 | Reference baseline |
| 4 | analog4 | `AGCKHFFWHTFTSC` | -4.955 | Conditional (His9 metal coordination risk) |
| 5 | analog5 | `YGCKNFFWKTFTST` | -2.589 | Rejected (SS bond destroyed) |
| 6 | analog3 | `AGCFIFFWKTFTSC` | +17.040 | Rejected (repulsive, Phe11 steric clash) |

#### Position 5,6,11 Optimization (`pos5_6_11_optimization/optimization_report.md`)

343 combinatorial variants -> 308 filtered -> 20 docked. Baseline: analog2.

| Rank | Sequence | Pos5 | Pos6 | Pos11 | ddG | vs Native |
|------|----------|------|------|-------|-----|-----------|
| 1 | `AGCKVDFWKTSTSC` | V | D | S | **-27.191** | -21.018 |
| 2 | `AGCKVDFWKTTTSC` | V | D | T | -23.415 | -17.242 |
| 3 | `AGCKYNFWKTSTSC` | Y | N | S | -19.224 | -13.051 |

15 of 20 docked candidates beat native SST-14. Best is 4.4x lower ddG than native.

#### Archives

`pyrosetta_flow/archives/` contains **24 archived run artifacts** from iterative pipeline executions.

---

## 4. Key Findings

### Binding Determinants
- **Trp8**: Deepest pocket insertion (13 SSTR2 contacts, min 2.91A). W8A causes +5.56 kcal/mol destabilization.
- **Lys9**: Salt bridges with D122/D136 (min 2.58A). K9A causes +4.25 kcal/mol destabilization.
- **FWKT motif** (pos 7-10) conservation is the primary constraint for SSTR2 binder design.

### Best Candidates Across Pipelines

| Pipeline | Best Sequence | Metric | Value |
|----------|---------------|--------|-------|
| FastDesign (Silo A) | `TPCQTWFYMDAISC` | dG | -62.9 REU |
| De Novo (Silo A, Arm 3) | `AALARTIAARFRKELEA` | pLDDT | 81.4 |
| Analog sim (Silo B) | `AGCKFDFWKTITSC` | ddG | -14.855 REU |
| Pos 5,6,11 opt (Silo B) | `AGCKVDFWKTSTSC` | ddG | -27.191 REU |
| Paper validation (Silo B) | `YSCKNFFWKTFTSN` | top-3 mean | -43.92 (WT-equivalent) |

### Mutation Patterns
- **Pos 5 (Asn)**: Val, Tyr, Phe tolerated; Trp causes steric clash (+32 REU)
- **Pos 6 (Phe)**: Asp/Glu substitution improves binding (acidic residue stabilizes pocket)
- **Pos 11 (Phe)**: Ser, Thr, Ile tolerated; reduces per-residue energy from +10.8 to <+1.0 REU
- **Cys3-Cys14 disulfide**: Must be preserved; breaking it causes >+25 REU penalty per residue

### Design Strategy
Two-stage funnel validated as optimal:
1. **Stage 1** (Mutate-then-Dock): ~240 candidates/hour, broad sequence space, 15s per candidate
2. **Stage 2** (Dock-then-Design): ~25 candidates/hour, 21 REU better dG on average, 142s per candidate
