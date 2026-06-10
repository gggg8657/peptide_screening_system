"""
ADMET & Nephrotoxicity Risk Computation
=========================================
Sequence-only ADMET property estimation and PRRT-specific renal retention
risk scoring for peptide radiopharmaceutical candidates.

No external dependencies -- pure Python computation from amino acid sequence.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Amino acid residue molecular weights (monoisotopic, Da)
# Weight of residue = AA - H2O (peptide bond formation removes water)
# ---------------------------------------------------------------------------
_AA_RESIDUE_WEIGHTS: dict[str, float] = {
    "A": 71.03711,  "R": 156.10111, "N": 114.04293, "D": 115.02694,
    "C": 103.00919, "E": 129.04259, "Q": 128.05858, "G": 57.02146,
    "H": 137.05891, "I": 113.08406, "L": 113.08406, "K": 128.09496,
    "M": 131.04049, "F": 147.06841, "P": 97.05276,  "S": 87.03203,
    "T": 101.04768, "W": 186.07931, "Y": 163.06333, "V": 99.06841,
}

_WATER_MW = 18.01056  # H2O added once for free termini

# ---------------------------------------------------------------------------
# Kyte-Doolittle hydropathy scale
# ---------------------------------------------------------------------------
_KD_HYDROPATHY: dict[str, float] = {
    "A":  1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C":  2.5,
    "E": -3.5, "Q": -3.5, "G": -0.4, "H": -3.2, "I":  4.5,
    "L":  3.8, "K": -3.9, "M":  1.9, "F":  2.8, "P": -1.6,
    "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V":  4.2,
}

# ---------------------------------------------------------------------------
# H-bond donor / acceptor sidechain counts
# Donors: sidechain NH/OH groups.  K(NH3+), R(3NH), H(NH), N(NH2),
#         Q(NH2), S(OH), T(OH), W(NH), Y(OH)
# Acceptors: sidechain C=O / OH / COO-.  D(COO-), E(COO-), N(C=O),
#            Q(C=O), S(OH), T(OH), Y(OH)
# ---------------------------------------------------------------------------
_SIDECHAIN_HBD: dict[str, int] = {
    "K": 1, "R": 3, "H": 1, "N": 2, "Q": 2,
    "S": 1, "T": 1, "W": 1, "Y": 1,
}
_SIDECHAIN_HBA: dict[str, int] = {
    "D": 2, "E": 2, "N": 1, "Q": 1, "S": 1, "T": 1, "Y": 1,
}


def compute_admet(sequence: str) -> dict:
    """Compute ADMET-like properties from amino acid sequence.

    Parameters
    ----------
    sequence : str
        One-letter amino acid sequence (e.g. ``"FDTDATRGDEFA"``).

    Returns
    -------
    dict with keys:
        mw, net_charge_ph74, n_hbd, n_hba, hydrophobicity,
        amphipathicity_index, druglikeness_score, druglikeness_breakdown
    """
    seq = sequence.upper().strip()
    length = len(seq)
    if length == 0:
        return {"error": "empty sequence"}

    # --- Molecular weight ---
    mw = sum(_AA_RESIDUE_WEIGHTS.get(aa, 0.0) for aa in seq) + _WATER_MW

    # --- Net charge at pH 7.4 ---
    charge = 0.0
    for aa in seq:
        if aa in ("K", "R"):
            charge += 1.0
        elif aa in ("D", "E"):
            charge -= 1.0
        elif aa == "H":
            charge += 0.1
    # N-terminus (+1) and C-terminus (-1) cancel out at physiological pH
    # but we add them explicitly per spec
    charge += 1.0   # N-term NH3+
    charge -= 1.0   # C-term COO-
    net_charge = round(charge, 2)

    # --- H-bond donors (sidechain + backbone NH) ---
    n_hbd = sum(_SIDECHAIN_HBD.get(aa, 0) for aa in seq)
    n_hbd += length  # Each residue has one backbone NH (except Pro, but simplified)

    # --- H-bond acceptors (sidechain + backbone CO) ---
    n_hba = sum(_SIDECHAIN_HBA.get(aa, 0) for aa in seq)
    n_hba += length  # Each residue has one backbone C=O

    # --- Hydrophobicity (mean Kyte-Doolittle) ---
    kd_vals = [_KD_HYDROPATHY.get(aa, 0.0) for aa in seq]
    hydrophobicity = round(sum(kd_vals) / length, 4)

    # --- Amphipathicity index (variance of hydropathy) ---
    mean_kd = hydrophobicity
    amphipathicity_index = round(
        sum((v - mean_kd) ** 2 for v in kd_vals) / length, 4
    )

    # --- Druglikeness score (0-100, peptide-specific) ---
    breakdown: dict[str, dict] = {}
    score = 0

    # Rule 1: MW 1200-2000 for 14-mer
    mw_ok = 1200.0 <= mw <= 2000.0
    if mw_ok:
        score += 25
    breakdown["mw_range"] = {"passed": mw_ok, "value": round(mw, 2), "range": "1200-2000 Da", "points": 25 if mw_ok else 0}

    # Rule 2: |net_charge| <= 3
    charge_ok = abs(net_charge) <= 3.0
    if charge_ok:
        score += 25
    breakdown["charge"] = {"passed": charge_ok, "value": net_charge, "range": "|charge| <= 3", "points": 25 if charge_ok else 0}

    # Rule 3: hydrophobicity between -2 and +1
    hydro_ok = -2.0 <= hydrophobicity <= 1.0
    if hydro_ok:
        score += 25
    breakdown["hydrophobicity"] = {"passed": hydro_ok, "value": hydrophobicity, "range": "[-2, +1]", "points": 25 if hydro_ok else 0}

    # Rule 4: No 3+ consecutive identical residues
    has_repeat = bool(re.search(r"(.)\1{2,}", seq))
    repeat_ok = not has_repeat
    if repeat_ok:
        score += 25
    breakdown["no_repeats"] = {"passed": repeat_ok, "value": not repeat_ok, "range": "no 3+ consecutive identical AA", "points": 25 if repeat_ok else 0}

    return {
        "mw": round(mw, 2),
        "net_charge_ph74": net_charge,
        "n_hbd": n_hbd,
        "n_hba": n_hba,
        "hydrophobicity": hydrophobicity,
        "amphipathicity_index": amphipathicity_index,
        "druglikeness_score": score,
        "druglikeness_breakdown": breakdown,
    }


def compute_nephrotox_risk(sequence: str) -> dict:
    """Compute PRRT-specific renal retention risk from amino acid sequence.

    Based on the observation that cationic residues (Lys, Arg, His) drive
    renal tubular reabsorption of radiolabelled peptides.  Reference:
    DOTATATE has 1 Lys, charge ~+1, renal_risk_score ~25 (Low).

    Parameters
    ----------
    sequence : str
        One-letter amino acid sequence.

    Returns
    -------
    dict with keys:
        n_lys, n_arg, n_his, cationic_residues, net_charge,
        renal_risk_score, risk_level, warning
    """
    seq = sequence.upper().strip()
    if not seq:
        return {"error": "empty sequence"}

    n_lys = seq.count("K")
    n_arg = seq.count("R")
    n_his = seq.count("H")
    cationic = n_lys + n_arg + n_his

    # Net charge (same calc as ADMET, but we duplicate to keep this self-contained)
    charge = 0.0
    for aa in seq:
        if aa in ("K", "R"):
            charge += 1.0
        elif aa in ("D", "E"):
            charge -= 1.0
        elif aa == "H":
            charge += 0.1
    net_charge = round(charge, 2)

    # Renal risk score: min(100, (n_lys + n_arg) * 20 + max(0, net_charge) * 15)
    renal_risk_score = min(
        100,
        round((n_lys + n_arg) * 20 + max(0.0, net_charge) * 15, 1),
    )

    # Risk level
    if renal_risk_score < 30:
        risk_level = "Low"
    elif renal_risk_score <= 60:
        risk_level = "Moderate"
    else:
        risk_level = "High"

    # Warning message
    warning = ""
    if risk_level == "Moderate":
        warning = (
            f"Moderate renal retention risk (score {renal_risk_score}). "
            f"Sequence contains {n_lys} Lys + {n_arg} Arg = {n_lys + n_arg} cationic residues. "
            "Consider kidney-protective co-infusion (e.g. amino acid infusion) during PRRT."
        )
    elif risk_level == "High":
        warning = (
            f"High renal retention risk (score {renal_risk_score}). "
            f"Sequence contains {n_lys} Lys + {n_arg} Arg = {n_lys + n_arg} cationic residues "
            f"with net charge {net_charge:+.1f}. "
            "Strong likelihood of nephrotoxicity under PRRT. "
            "Recommend reducing cationic content or adding Gelofusine co-administration."
        )

    return {
        "n_lys": n_lys,
        "n_arg": n_arg,
        "n_his": n_his,
        "cationic_residues": cationic,
        "net_charge": net_charge,
        "renal_risk_score": renal_risk_score,
        "risk_level": risk_level,
        "warning": warning,
    }


def compute_admet_full(sequence: str) -> dict:
    """Combined ADMET + nephrotoxicity result for a single sequence."""
    admet = compute_admet(sequence)
    nephrotox = compute_nephrotox_risk(sequence)
    return {
        "sequence": sequence.upper().strip(),
        "admet": admet,
        "nephrotox": nephrotox,
    }


def merge_pepadmet_into_admet_results(sequences: list[str], results: list[dict]) -> list[dict]:
    """각 ADMET 결과에 pepADMET 독성(ML) 예측을 병합한다.

    - `SKIP_PEPADMET=1` 이면 호출 생략(테스트/빠른 응답).
    - repo/conda 미구성 시 `pepadmet` 키만 추가하고 available=False.
    """
    import os

    if os.environ.get("SKIP_PEPADMET") == "1":
        return results

    if len(sequences) != len(results):
        return results

    try:
        from pyrosetta_flow.pepadmet_runner import predict_toxicity_batch
    except ImportError:
        for r in results:
            r["pepadmet"] = {"available": False, "error": "pyrosetta_flow import failed"}
        return results

    try:
        preds = predict_toxicity_batch(sequences)
    except Exception as exc:  # noqa: BLE001 — subprocess/conda 전파
        err = str(exc)[:300]
        for r in results:
            r["pepadmet"] = {"available": False, "error": err}
        return results

    for i, r in enumerate(results):
        if i < len(preds):
            r["pepadmet"] = preds[i]
        else:
            r["pepadmet"] = {"available": False, "error": "pepadmet batch length mismatch"}
    return results
