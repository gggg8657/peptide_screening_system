"""
SAR PSSM Heatmap Analysis
==========================
Computes a Position-Specific Scoring Matrix (PSSM) from experiment_log.jsonl
records, enabling Structure-Activity Relationship (SAR) heatmap visualization.

Reference sequence: AGCKNFFWKTFTSC (14-mer, SST-14)
Fixed positions (0-indexed): 2(C), 6(F), 7(W), 8(K), 9(T), 13(C)
Mutable positions (0-indexed): 0, 1, 3, 4, 5, 10, 11, 12
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from typing import Any, Dict, List, Optional

REFERENCE_SEQUENCE = "AGCKNFFWKTFTSC"
MUTABLE_POSITIONS = [0, 1, 3, 4, 5, 10, 11, 12]  # 0-indexed
FIXED_POSITIONS = [2, 6, 7, 8, 9, 13]  # 0-indexed

DDG_PLAUSIBLE_MIN = -60.0
DDG_PLAUSIBLE_MAX = 200.0


def _filter_candidates(records: list[dict]) -> list[dict]:
    """Filter to successful candidates with plausible ddG values."""
    out = []
    for r in records:
        if r.get("record_type") != "candidate":
            continue
        if r.get("status") != "success":
            continue
        ddg = float(r.get("ddg", 999))
        if ddg >= 900:
            continue
        if not (DDG_PLAUSIBLE_MIN <= ddg <= DDG_PLAUSIBLE_MAX):
            continue
        out.append(r)
    return out


def _identify_mutations(sequence: str) -> dict[int, str]:
    """Return {0-indexed position: amino acid} for positions differing from WT."""
    mutations = {}
    for i, (ref_aa, seq_aa) in enumerate(zip(REFERENCE_SEQUENCE, sequence)):
        if seq_aa != ref_aa and i in MUTABLE_POSITIONS:
            mutations[i] = seq_aa
    return mutations


def compute_sar_pssm(records: list[dict]) -> dict:
    """Compute SAR PSSM from experiment records.

    Returns:
        {
            "pssm": {position_idx: {amino_acid: {count, mean_ddg, std_ddg, best_ddg, delta_vs_wt}}},
            "position_summary": {position_idx: {best_aa, best_ddg, worst_aa, worst_ddg, wt_aa, wt_mean_ddg, n_substitutions}},
            "meta": {n_records_used, n_total_records, reference_sequence, mutable_positions}
        }
    """
    candidates = _filter_candidates(records)

    # Collect per-position per-AA ddG observations
    # pos_aa_ddgs[position][amino_acid] = [ddg values]
    pos_aa_ddgs: dict[int, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for r in candidates:
        seq = r.get("sequence", "")
        if len(seq) != len(REFERENCE_SEQUENCE):
            continue
        ddg = float(r["ddg"])

        # Record WT amino acids at mutable positions if sequence matches WT there
        for pos in MUTABLE_POSITIONS:
            aa = seq[pos]
            pos_aa_ddgs[pos][aa].append(ddg)

    # Build PSSM
    pssm: dict[int, dict[str, dict]] = {}
    position_summary: dict[int, dict] = {}

    for pos in MUTABLE_POSITIONS:
        wt_aa = REFERENCE_SEQUENCE[pos]
        wt_ddgs = pos_aa_ddgs[pos].get(wt_aa, [])
        wt_mean = statistics.mean(wt_ddgs) if wt_ddgs else 0.0

        pssm[pos] = {}
        best_entry: Optional[tuple[str, float]] = None
        worst_entry: Optional[tuple[str, float]] = None

        for aa, ddg_list in sorted(pos_aa_ddgs[pos].items()):
            mean_ddg = statistics.mean(ddg_list)
            std_ddg = statistics.stdev(ddg_list) if len(ddg_list) > 1 else 0.0
            best_ddg = min(ddg_list)
            delta = round(mean_ddg - wt_mean, 4)

            pssm[pos][aa] = {
                "count": len(ddg_list),
                "mean_ddg": round(mean_ddg, 4),
                "std_ddg": round(std_ddg, 4),
                "best_ddg": round(best_ddg, 4),
                "delta_vs_wt": delta,
            }

            if best_entry is None or mean_ddg < best_entry[1]:
                best_entry = (aa, mean_ddg)
            if worst_entry is None or mean_ddg > worst_entry[1]:
                worst_entry = (aa, mean_ddg)

        position_summary[pos] = {
            "wt_aa": wt_aa,
            "wt_mean_ddg": round(wt_mean, 4) if wt_ddgs else None,
            "wt_count": len(wt_ddgs),
            "best_aa": best_entry[0] if best_entry else wt_aa,
            "best_mean_ddg": round(best_entry[1], 4) if best_entry else None,
            "worst_aa": worst_entry[0] if worst_entry else wt_aa,
            "worst_mean_ddg": round(worst_entry[1], 4) if worst_entry else None,
            "n_substitutions": len(pos_aa_ddgs[pos]),
        }

    return {
        "pssm": {str(k): v for k, v in pssm.items()},
        "position_summary": {str(k): v for k, v in position_summary.items()},
        "meta": {
            "n_records_used": len(candidates),
            "n_total_records": len(records),
            "reference_sequence": REFERENCE_SEQUENCE,
            "mutable_positions": MUTABLE_POSITIONS,
            "fixed_positions": FIXED_POSITIONS,
            "plausibility_bounds": {
                "min": DDG_PLAUSIBLE_MIN,
                "max": DDG_PLAUSIBLE_MAX,
            },
        },
    }


def compute_epistasis_pairs(records: list[dict], min_count: int = 3) -> list[dict]:
    """Find pairs of positions that show synergy or antagonism when mutated together.

    Compares the observed ddG of double-mutants against the expected additive
    effect from single-mutant data to detect epistatic interactions.

    Returns a list of dicts sorted by |epistasis_score| descending:
        [{pos_a, pos_b, aa_a, aa_b, observed_mean_ddg, expected_additive_ddg,
          epistasis_score, count, interpretation}]
    """
    candidates = _filter_candidates(records)

    # Collect single-mutation effects: position -> aa -> [ddg]
    single_mut_ddgs: dict[int, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    # Collect double-mutation observations: (pos_a, aa_a, pos_b, aa_b) -> [ddg]
    double_mut_ddgs: dict[tuple, list[float]] = defaultdict(list)
    # WT baseline
    wt_ddgs: list[float] = []

    for r in candidates:
        seq = r.get("sequence", "")
        if len(seq) != len(REFERENCE_SEQUENCE):
            continue
        ddg = float(r["ddg"])
        mutations = _identify_mutations(seq)

        if len(mutations) == 0:
            wt_ddgs.append(ddg)
        elif len(mutations) == 1:
            pos, aa = next(iter(mutations.items()))
            single_mut_ddgs[pos][aa].append(ddg)
        elif len(mutations) == 2:
            items = sorted(mutations.items())
            (pos_a, aa_a), (pos_b, aa_b) = items
            double_mut_ddgs[(pos_a, aa_a, pos_b, aa_b)].append(ddg)

    wt_mean = statistics.mean(wt_ddgs) if wt_ddgs else 0.0

    results: list[dict] = []
    for (pos_a, aa_a, pos_b, aa_b), ddg_list in double_mut_ddgs.items():
        if len(ddg_list) < min_count:
            continue
        single_a = single_mut_ddgs[pos_a].get(aa_a, [])
        single_b = single_mut_ddgs[pos_b].get(aa_b, [])
        if not single_a or not single_b:
            continue

        mean_a = statistics.mean(single_a)
        mean_b = statistics.mean(single_b)
        # Expected additive: dG_A + dG_B - dG_WT (so the WT baseline isn't double-counted)
        expected = mean_a + mean_b - wt_mean
        observed = statistics.mean(ddg_list)
        epistasis = round(observed - expected, 4)

        if abs(epistasis) < 0.5:
            interpretation = "additive"
        elif epistasis < 0:
            interpretation = "synergistic"
        else:
            interpretation = "antagonistic"

        results.append({
            "pos_a": pos_a,
            "aa_a": aa_a,
            "pos_b": pos_b,
            "aa_b": aa_b,
            "observed_mean_ddg": round(observed, 4),
            "expected_additive_ddg": round(expected, 4),
            "epistasis_score": epistasis,
            "count": len(ddg_list),
            "single_a_count": len(single_a),
            "single_b_count": len(single_b),
            "interpretation": interpretation,
        })

    results.sort(key=lambda x: abs(x["epistasis_score"]), reverse=True)
    return results
