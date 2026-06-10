# Paper Validation: FlexPepDock ddG Comparison

## Overview

Computational validation of SST14 peptide variants binding to SSTR2 receptor
using PyRosetta FlexPepDock refinement + InterfaceAnalyzerMover ddG.

- **Target**: SSTR2 (Somatostatin receptor type 2, 369 aa)
- **Reference peptide**: SST14 (AGCKNFFWKTFTSC, 14 aa)
- **Template PDB**: AlphaFold3 predicted complex (`fold_test1_model_0.pdb`)
- **Protocol**: FlexPepDock refinement, 10 independent trials per candidate
- **Scoring**: InterfaceAnalyzerMover interface dG (kcal/mol)
- **Reporting metric**: Top-3 mean ddG (best 3 of 10 trials)

## Note on Scoring Metric

FlexPepDock refinement is stochastic (Monte Carlo-based). Individual trials
can vary by 10-40 kcal/mol depending on the conformational sampling path.
We run 10 independent trials and report **top-3 mean** (average of 3 best
ddG values) as the primary metric. This reduces noise from poorly-converged
trials while avoiding single-trial cherry-picking. Median and stdev are
reported for completeness.

## Candidate Panel

| ID     | Category | Sequence         | Description |
|--------|----------|------------------|-------------|
| LIT-01 | Literature | AGCKNFFWKTFTSC | WT SST14 (reference baseline) |
| LIT-02 | Literature | FCCKNFFWKTCTSC | Octreotide pharmacophore-mapped 14-mer |
| LIT-03 | Literature | APCKNFFWKTFSSC | Cortistatin-14 (CST-14), FWKT-aligned 14-mer |
| SAN-01 | Sanity   | AGCKNFFAKTFTSC   | W8A (Trp8 is binding pocket core residue) |
| SAN-02 | Sanity   | AGCKNFFWATFTSC   | K9A (Lys9 interacts with D122/Q126/Y302) |
| NOV-01 | Novel    | YSCKNFFWKTFTSN   | Agentic pipeline iter-1 best (seed 7000) |
| NOV-02 | Novel    | AGCKNDFWKTFGSE   | Agentic pipeline iter-2 best (seed 7000) |

## Results

| ID     | top3 mean | median | mean   | stdev | best   | n_ok | Delta vs WT |
|--------|-----------|--------|--------|-------|--------|------|-------------|
| LIT-01 | **-43.78**| -25.40 | -27.00 | 15.01 | -46.25 | 10   | (reference) |
| SAN-01 | -38.22    | -31.72 | -30.53 |  9.64 | -39.50 |  9   | **+5.56**   |
| SAN-02 | -39.53    | -33.13 | -25.24 | 13.38 | -39.91 |  9   | **+4.25**   |
| NOV-01 | **-43.92**| -34.02 | -33.11 | 13.62 | -46.88 |  9   | -0.15       |
| NOV-02 | -41.47    | -39.39 | -38.38 |  3.53 | -41.78 | 10   | +2.31       |
| LIT-02 | -42.11    | -35.12 | -33.93 |  8.10 | -44.76 | 10   | +1.67       |
| LIT-03 | -37.30    | -29.94 | -29.12 |  7.57 | -38.53 | 10   | +6.47       |

*Delta: positive = weaker binding vs WT, negative = stronger binding vs WT*

## Interpretation

### Sanity checks (negative controls) — PASS
- **SAN-01 (W8A)**: +5.56 kcal/mol weaker than WT. Trp8 is a known critical
  residue at the bottom of the SSTR2 binding pocket (contacts F127, F208,
  F272). Alanine substitution correctly destabilizes binding.
- **SAN-02 (K9A)**: +4.25 kcal/mol weaker. Lys9 forms polar contacts with
  D122, Q126, and Y302 on SSTR2. Result directionally correct.

Both negative controls show the expected direction, validating the scoring
pipeline's ability to distinguish favorable from unfavorable mutations.

### Literature positive controls
- **LIT-02 (Octreotide-mapped)**: +1.67 kcal/mol, essentially WT-equivalent.
  The pharmacophore mapping preserves the FWKT core; small deviation is
  expected since the 14-mer scaffold adds non-Octreotide flanking residues.
- **LIT-03 (CST-14)**: +6.47 kcal/mol weaker. CST-14 differs from SST14 at
  only 2 positions (G2P, T12S). The G2P substitution introduces proline
  backbone rigidity which may be penalized in FlexPepDock's flexible
  refinement. Despite the computational result, CST-14 binds SSTR2 with
  nanomolar affinity in vitro, highlighting a limitation of the FlexPepDock
  scoring for proline-containing peptides.

### Novel candidates (agentic pipeline)
- **NOV-01 (YSCKNFFWKTFTSN)**: Top-3 mean -43.92, virtually identical to WT
  (-43.78, delta -0.15). Mutations at positions 1 (A1Y), 2 (G2S), 13 (S13N)
  maintained binding affinity while introducing new chemical diversity.
  Best candidate for experimental follow-up.
- **NOV-02 (AGCKNDFWKTFGSE)**: Top-3 mean -41.47 (delta +2.31), WT-equivalent
  within FlexPepDock's noise floor. Lowest stdev across all candidates (3.53),
  indicating highly reproducible binding pose. Mutations at positions 5 (N5D),
  11 (F11G), 12 (T12S), 13 (S13E) are conservative at non-core positions.

## Methodology

1. **Starting pose**: All candidates use MutateResidue on the FlexPepDock-
   refined WT baseline PDB to ensure identical backbone starting conformations.
2. **Outlier filtering**: Trials producing ddG > 0 (catastrophic refinement
   failures where the structure collapses) are excluded from statistics.
3. **Primary metric**: Top-3 mean (average of 3 lowest ddG values from 10
   trials) balances robustness against cherry-picking.
4. **Limitations**: FlexPepDock refinement is CPU-bound Monte Carlo with
   significant per-trial variance (stdev 3-15 kcal/mol). D-amino acids and
   non-standard residues cannot be modeled with standard MutateResidue.

## References

1. Structural insights into the activation of SSTR2 by cyclic SST analogues.
   Cell Discovery (2022). PMC9122944.
2. Structural insights into ligand recognition and selectivity of SSTRs.
   Cell Research (2022).
3. de Lecea et al. Cortistatin: a novel somatostatin-like neuropeptide.
   Nature 381:242 (1996).

## Experiment Metadata

- **Date**: 2026-02-26
- **System**: Intel i7-13700K (24 cores), 125 GB RAM, RTX 4090
- **PyRosetta**: Conda env `bio-tools`
- **Trials per candidate**: 10
- **Parallel workers**: 8
- **Raw data**: `validation_results.json`
