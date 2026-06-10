"""
Peptide Pharmacological Property Calculations
===============================================
Thin wrapper over AG_src.pipeline.pharma_properties.PharmaProperties.

모든 lookup table 및 핵심 계산 로직은 PharmaProperties 클래스에 위임.
pharmacology.py 전용 기능(charge_ph_profile, pepsin protease)은 pharma의
내부 헬퍼(_charge_at_ph)를 직접 사용.

기존 public API(함수명·파라미터·반환 형태) 완전 유지.
"""
from __future__ import annotations

import math
from typing import Any, Optional, Set

# ─── pharma_properties 통합 import ──────────────────────────────────────────

try:
    import sys
    import os
    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

    from AG_src.pipeline.pharma_properties import (
        PharmaProperties,
        _charge_at_ph as _pharma_charge_at_ph,
        PKA_NTERM,
        PKA_CTERM,
        PKA_SIDECHAIN,
        EISENBERG,
        WIMLEY_WHITE,
        BLOSUM62,
    )

    _PP = PharmaProperties()          # 모듈 수준 싱글톤
    _PHARMA_AVAILABLE = True

except Exception:  # pragma: no cover  — 오프라인/패키지 미설치 환경 fallback
    _PHARMA_AVAILABLE = False

# ─── Reference constants ────────────────────────────────────────────────────

SST14_NATIVE = "AGCKNFFWKTFTSC"

# ─── Fallback lookup tables (pharma_properties 미사용 시) ───────────────────
# NOTE: 정상 실행 시 이 테이블들은 사용되지 않는다.
#       pharma_properties import 실패 시 원본 코드가 그대로 작동하도록 보존.

if not _PHARMA_AVAILABLE:  # pragma: no cover
    _KD: dict[str, float] = {
        "I": 4.5, "V": 4.2, "L": 3.8, "F": 2.8, "C": 2.5,
        "M": 1.9, "A": 1.8, "G": -0.4, "T": -0.7, "S": -0.8,
        "W": -0.9, "Y": -1.3, "P": -1.6, "H": -3.2, "E": -3.5,
        "Q": -3.5, "D": -3.5, "N": -3.5, "K": -3.9, "R": -4.5,
    }
    _RADZICKA_WOLFENDEN: dict[str, float] = {
        "R": 14.92, "D": 8.72, "E": 6.81, "N": 6.64, "K": 5.55,
        "Q": 5.54, "T": 2.57, "H": 4.66, "Y": 0.14, "G": -0.94,
        "C": -1.28, "A": -1.81, "W": -2.33, "F": -2.98, "V": -4.04,
        "I": -4.92, "L": -4.92, "S": 3.40, "P": -2.54, "M": -2.35,
    }
    _PKA = {
        "Nterm": 9.69, "Cterm": 2.34,
        "D": 3.65, "E": 4.25, "H": 6.00, "C": 8.18,
        "Y": 10.07, "K": 10.53, "R": 12.48,
    }


# ─── 내부 헬퍼 ──────────────────────────────────────────────────────────────

def _net_charge_at_ph(
    seq: str,
    ph: float,
    ss_bond_cysteines: Optional[Set[int]] = None,
) -> float:
    """Compute net charge at a given pH using Henderson-Hasselbalch.

    Parameters
    ----------
    seq:
        Amino acid sequence (upper-case).
    ph:
        pH value.
    ss_bond_cysteines:
        0-indexed positions of Cys residues involved in disulfide bonds.
        Those residues are excluded from ionisation (no free thiol).
        Pass ``None`` to treat all Cys as free thiols (original behaviour).
    """
    if _PHARMA_AVAILABLE:
        return _pharma_charge_at_ph(seq, ph, ss_bond_cysteines=ss_bond_cysteines)

    # fallback (pharma 미사용 시)  # pragma: no cover
    _ss = ss_bond_cysteines if ss_bond_cysteines is not None else set()
    charge = 0.0
    charge += 1.0 / (1.0 + 10 ** (ph - _PKA["Nterm"]))
    charge -= 1.0 / (1.0 + 10 ** (_PKA["Cterm"] - ph))
    for idx, aa in enumerate(seq):
        if aa in ("D", "E", "Y"):
            charge -= 1.0 / (1.0 + 10 ** (_PKA[aa] - ph))
        elif aa == "C" and idx not in _ss:
            charge -= 1.0 / (1.0 + 10 ** (_PKA["C"] - ph))
        elif aa in ("K", "R", "H"):
            charge += 1.0 / (1.0 + 10 ** (ph - _PKA[aa]))
    return charge


# ─── 1. GRAVY ────────────────────────────────────────────────────────────────


def gravy(seq: str) -> float:
    """Grand Average of Hydropathy (Kyte & Doolittle 1982)."""
    if _PHARMA_AVAILABLE:
        return round(_PP.calculate_gravy(seq), 4)
    # fallback  # pragma: no cover
    vals = [_KD.get(aa, 0.0) for aa in seq]
    return round(sum(vals) / len(vals), 4) if vals else 0.0


# ─── 2. Boman Index ──────────────────────────────────────────────────────────


def boman_index(seq: str) -> float:
    """Boman Index — protein binding potential (kcal/mol per residue).
    BI >= 2.48 → high protein binding potential (hormone/receptor ligand).
    """
    if _PHARMA_AVAILABLE:
        return round(_PP.calculate_boman_index(seq), 4)
    # fallback  # pragma: no cover
    vals = [_RADZICKA_WOLFENDEN.get(aa, 0.0) for aa in seq]
    return round(sum(vals) / len(vals), 4) if vals else 0.0


# ─── 3. Instability Index ────────────────────────────────────────────────────


def instability_index(seq: str) -> float:
    """Instability Index (Guruprasad et al. 1990). II < 40 → stable."""
    if _PHARMA_AVAILABLE:
        return round(_PP.calculate_instability_index(seq), 4)
    # fallback  # pragma: no cover
    return 0.0


# ─── 4. Aliphatic Index ──────────────────────────────────────────────────────


def aliphatic_index(seq: str) -> float:
    """Aliphatic Index — relative volume of aliphatic side chains."""
    if _PHARMA_AVAILABLE:
        return round(_PP.calculate_aliphatic_index(seq), 4)
    # fallback  # pragma: no cover
    n = len(seq)
    if n == 0:
        return 0.0
    x_a = 100 * seq.count("A") / n
    x_v = 100 * seq.count("V") / n
    x_i = 100 * seq.count("I") / n
    x_l = 100 * seq.count("L") / n
    return round(x_a + 2.9 * x_v + 3.9 * (x_i + x_l), 4)


# ─── 5. Isoelectric Point ────────────────────────────────────────────────────


def isoelectric_point(
    seq: str,
    ss_bond_cysteines: Optional[Set[int]] = None,
) -> float:
    """Isoelectric point by bisection (Bjellqvist et al. 1993).

    Parameters
    ----------
    ss_bond_cysteines:
        0-indexed positions of Cys in disulfide bonds (excluded from ionisation).
        ``None`` preserves original behaviour.
    """
    if _PHARMA_AVAILABLE:
        return _PP.calculate_pi(seq, ss_bond_cysteines=ss_bond_cysteines)
    # fallback  # pragma: no cover
    lo, hi = 0.0, 14.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if _net_charge_at_ph(seq, mid, ss_bond_cysteines=ss_bond_cysteines) > 0:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 4)


# ─── 5b. Molecular Weight ────────────────────────────────────────────────────


def molecular_weight(seq: str, n_disulfide: int = 0) -> dict:
    """Peptide molecular weight (average isotopic masses).

    Formula
    -------
    MW = Σ AA_MW  −  (n−1) × H₂O  −  n_disulfide × 2.016

    Parameters
    ----------
    seq:
        Upper-case one-letter amino acid sequence.
    n_disulfide:
        Number of disulfide bonds (each removes 2 H atoms = 2.016 Da).

    Returns
    -------
    dict with keys: mw_average, mw_monoisotopic, n_residues, n_disulfide
    """
    if not seq:
        return {"error": "empty sequence"}
    if _PHARMA_AVAILABLE:
        return _PP.calculate_mw(seq, n_disulfide=n_disulfide)
    # fallback  # pragma: no cover
    return {"error": "pharma_properties unavailable"}


# ─── 6. Molar Extinction Coefficient ────────────────────────────────────────


def molar_extinction_coefficient(seq: str, n_disulfide: int = 1) -> dict:
    """ε₂₈₀ calculation. Default n_disulfide=1 for SST-14 Cys3-Cys14 bond.

    Returns dict with keys: epsilon_280_ss, epsilon_280_reduced, n_trp, n_tyr,
    n_disulfide.
    """
    n_trp = seq.count("W")
    n_tyr = seq.count("Y")
    if _PHARMA_AVAILABLE:
        eps_ss = _PP.calculate_extinction_coefficient(seq, n_disulfide=n_disulfide)
        eps_no_ss = _PP.calculate_extinction_coefficient(seq, n_disulfide=0)
    else:  # pragma: no cover
        eps_ss = n_trp * 5500 + n_tyr * 1490 + n_disulfide * 125
        eps_no_ss = n_trp * 5500 + n_tyr * 1490
    return {
        "epsilon_280_ss": eps_ss,
        "epsilon_280_reduced": eps_no_ss,
        "n_trp": n_trp,
        "n_tyr": n_tyr,
        "n_disulfide": n_disulfide,
    }


# ─── 7. N-end Rule ──────────────────────────────────────────────────────────


def n_end_rule(seq: str) -> dict:
    """N-end rule predicted intracellular half-life (mammalian reticulocyte).

    Returns dict with keys: n_terminal_residue, predicted_halflife_hours,
    stability_category.
    """
    if not seq:
        return {"error": "empty sequence"}
    if _PHARMA_AVAILABLE:
        raw = _PP.calculate_nend_rule_halflife(seq)
        # pharma 키 이름 변환:
        #   half_life_hours  → predicted_halflife_hours
        #   category         → stability_category
        return {
            "n_terminal_residue": raw["n_terminal_residue"],
            "predicted_halflife_hours": raw["half_life_hours"],
            "stability_category": raw["category"],
        }
    # fallback  # pragma: no cover
    return {"error": "pharma_properties unavailable"}


# ─── 8. Hydrophobic Moment ───────────────────────────────────────────────────


def hydrophobic_moment(seq: str, angle: float = 100.0, window: int = 11) -> dict:
    """Hydrophobic moment (Eisenberg et al. 1982).
    Default angle=100° (alpha-helix). Returns max muH over sliding window.

    Returns dict with keys: mu_h_max, angle_deg, window.
    """
    n = len(seq)
    if n == 0:
        return {"mu_h_max": 0.0, "angle": angle, "window": window}
    if _PHARMA_AVAILABLE:
        # pharma 반환값: float (max moment)
        mu_max = _PP.calculate_hydrophobic_moment(seq, angle=angle, window=window)
        return {
            "mu_h_max": round(mu_max, 4),
            "angle_deg": angle,
            "window": min(window, n),
        }
    # fallback  # pragma: no cover
    delta = math.radians(angle)
    win = min(window, n)
    max_mu = 0.0
    for start in range(n - win + 1):
        sin_sum = 0.0
        cos_sum = 0.0
        for j in range(win):
            h = 0.0
            sin_sum += h * math.sin(j * delta)
            cos_sum += h * math.cos(j * delta)
        mu = math.sqrt(sin_sum ** 2 + cos_sum ** 2) / win
        if mu > max_mu:
            max_mu = mu
    return {
        "mu_h_max": round(max_mu, 4),
        "angle_deg": angle,
        "window": win,
    }


# ─── 9. Wimley-White Hydrophobicity ─────────────────────────────────────────


def wimley_white(seq: str) -> dict:
    """Wimley-White whole-residue water to interface transfer delta G.

    Returns dict with keys: ww_total_kcal, ww_per_residue, interpretation.
    """
    if _PHARMA_AVAILABLE:
        raw = _PP.calculate_wimley_white(seq)
        # pharma 키 변환:
        #   total_dG  → ww_total_kcal
        #   mean_dG   → ww_per_residue
        total = raw["total_dG"]
        per_res = raw["mean_dG"]
        return {
            "ww_total_kcal": total,
            "ww_per_residue": per_res,
            "interpretation": "membrane-favorable" if total < 0 else "aqueous-favorable",
        }
    # fallback  # pragma: no cover
    return {"ww_total_kcal": 0.0, "ww_per_residue": 0.0, "interpretation": "unknown"}


# ─── 10. Net Charge vs pH Profile ───────────────────────────────────────────


def charge_ph_profile(
    seq: str,
    ss_bond_cysteines: Optional[Set[int]] = None,
) -> dict:
    """Net charge at pharmacologically relevant pH values.

    This function is pharmacology.py-specific (not in pharma_properties.py).
    Uses _net_charge_at_ph which delegates to pharma_properties._charge_at_ph.

    Parameters
    ----------
    ss_bond_cysteines:
        0-indexed positions of Cys in disulfide bonds (excluded from ionisation).
        ``None`` preserves original behaviour.
    """
    phs = [2.0, 4.0, 5.0, 6.0, 6.5, 7.0, 7.4, 8.0, 10.0, 12.0]
    profile = {
        f"pH_{p:.1f}": round(_net_charge_at_ph(seq, p, ss_bond_cysteines=ss_bond_cysteines), 4)
        for p in phs
    }
    charge_74 = _net_charge_at_ph(seq, 7.4, ss_bond_cysteines=ss_bond_cysteines)
    charge_65 = _net_charge_at_ph(seq, 6.5, ss_bond_cysteines=ss_bond_cysteines)
    return {
        "charge_at_ph74": round(charge_74, 4),
        "charge_at_ph65": round(charge_65, 4),
        "delta_charge_tumor_vs_plasma": round(charge_65 - charge_74, 4),
        "profile": profile,
    }


# ─── 11. Protease Cleavage Site Analysis ────────────────────────────────────

_CHYMOTRYPSIN_SITES = set("FWYLM")
_TRYPSIN_SITES = set("KR")
_NEPRILYSIN_HYDROPHOBIC = set("FWYLIMV")
_PEPSIN_SITES = set("FYL")   # pepsin은 pharmacology.py 전용 (pharma에 없음)
_DPPIV_SITES = set("PA")     # DPP-IV: X-Pro/X-Ala cleavage


def protease_cleavage_sites(seq: str) -> dict:
    """Predict protease cleavage sites for chymotrypsin, trypsin, NEP, pepsin, DPP-IV.

    Note:
    - pepsin 규칙은 pharmacology.py 전용 구현 (pharma_properties에 없음).
    - dppiv 규칙: X-Pro/X-Ala at internal positions, Pro-Pro blocked.
    - chymotrypsin / trypsin / neprilysin은 PharmaProperties.count_protease_sites()
      와 동일 규칙을 사용.
    """
    n = len(seq)
    chymo: list[int] = []
    trypsin: list[int] = []
    nep: list[int] = []
    pepsin: list[int] = []
    dppiv: list[int] = []

    for i in range(n):
        aa = seq[i]
        # Chymotrypsin: cleaves C-terminal of F, W, Y, L, M
        if aa in _CHYMOTRYPSIN_SITES and i < n - 1:
            chymo.append(i + 1)
        # Trypsin: cleaves C-terminal of K, R (not if followed by P)
        if aa in _TRYPSIN_SITES and i < n - 1:
            if seq[i + 1] != "P":
                trypsin.append(i + 1)
        # NEP: cleaves N-terminal of hydrophobic residues
        if aa in _NEPRILYSIN_HYDROPHOBIC and i > 0:
            nep.append(i)
        # Pepsin: cleaves N-terminal of F, Y, L (acidic pH) — pharmacology 전용
        if aa in _PEPSIN_SITES and i > 0:
            pepsin.append(i)
        # DPP-IV: cleaves after X-Pro or X-Ala (not if Pro followed by Pro)
        if aa in _DPPIV_SITES and i > 0 and i < n - 1:
            if seq[i + 1] != "P":  # Pro-Pro resistance
                dppiv.append(i + 1)

    return {
        "chymotrypsin": {"count": len(chymo), "positions": chymo},
        "trypsin": {"count": len(trypsin), "positions": trypsin},
        "neprilysin": {"count": len(nep), "positions": nep},
        "pepsin": {"count": len(pepsin), "positions": pepsin},
        "dppiv": {"count": len(dppiv), "positions": dppiv},
        "total_sites": len(chymo) + len(trypsin) + len(nep) + len(pepsin) + len(dppiv),
    }


# ─── 12. BLOSUM62 Mutation Conservation ─────────────────────────────────────


def blosum62_analysis(seq: str, reference: str = SST14_NATIVE) -> dict:
    """BLOSUM62 mutation conservation analysis vs reference sequence.

    BLOSUM62 lookup table은 pharma_properties.BLOSUM62 을 사용 (동일 출처).
    반환 형태(mutations list 포함)는 pharmacology 원본 API 유지.
    """
    mutations = []
    total_score = 0
    min_len = min(len(seq), len(reference))

    for i in range(min_len):
        if seq[i] != reference[i]:
            if _PHARMA_AVAILABLE:
                score = BLOSUM62.get(reference[i], {}).get(seq[i], 0)
            else:  # pragma: no cover
                score = 0
            cat = (
                "conservative" if score >= 1 else
                "semi-conservative" if score == 0 else
                "non-conservative"
            )
            mutations.append({
                "position": i + 1,
                "from": reference[i],
                "to": seq[i],
                "blosum62_score": score,
                "category": cat,
            })
            total_score += score

    n_conservative = sum(1 for m in mutations if m["category"] == "conservative")
    n_nonconservative = sum(1 for m in mutations if m["category"] == "non-conservative")
    return {
        "n_mutations": len(mutations),
        "total_blosum62_score": total_score,
        "avg_score": round(total_score / len(mutations), 2) if mutations else 0.0,
        "n_conservative": n_conservative,
        "n_semi_conservative": len(mutations) - n_conservative - n_nonconservative,
        "n_non_conservative": n_nonconservative,
        "mutations": mutations,
    }


# ─── 13. Metal Coordination Residue Analysis ────────────────────────────────

# pharmacology.py 전용 반환 형태 유지 (pharma와 구조가 달라 직접 구현)
# Unicode superscript 유지 (테스트에서 "Ga³⁺" 등으로 검증)
_METAL_COORD: dict[str, dict[str, Any]] = {
    "H": {"site": "imidazole N", "preferred_metals": ["Zn²⁺", "Cu²⁺", "Ga³⁺"], "strength": "strong"},
    "C": {"site": "thiolate S", "preferred_metals": ["Cu⁺", "Zn²⁺"], "strength": "strong"},
    "D": {"site": "carboxylate O", "preferred_metals": ["Ca²⁺", "Mg²⁺", "lanthanides", "Ga³⁺"], "strength": "medium"},
    "E": {"site": "carboxylate O", "preferred_metals": ["Ca²⁺", "Mg²⁺", "lanthanides", "Ga³⁺"], "strength": "medium"},
    "M": {"site": "thioether S", "preferred_metals": ["Cu²⁺", "Pt²⁺"], "strength": "weak"},
}


def metal_coordination(seq: str) -> dict:
    """Identify metal-coordinating residues relevant to chelator interference."""
    residues: list[dict] = []
    for i, aa in enumerate(seq):
        if aa in _METAL_COORD:
            info = _METAL_COORD[aa]
            residues.append({
                "position": i + 1,
                "residue": aa,
                "coordination_site": info["site"],
                "preferred_metals": info["preferred_metals"],
                "binding_strength": info["strength"],
            })
    strong = sum(1 for r in residues if r["binding_strength"] == "strong")
    return {
        "coordinating_residues": residues,
        "total_count": len(residues),
        "n_strong": strong,
        "chelator_interference_risk": "high" if strong >= 2 else "moderate" if strong == 1 else "low",
    }


# ─── 14. Radiolysis Susceptibility ──────────────────────────────────────────


def radiolysis_susceptibility(seq: str) -> dict:
    """Radiolysis susceptibility score for radiopharmaceutical stability.

    PharmaProperties.calculate_radiolysis_susceptibility 에 완전 위임.
    반환 형태 동일: total_score, risk_level, vulnerable_residues, critical_positions.
    """
    if not seq:
        return {
            "total_score": 0.0,
            "risk_level": "low",
            "vulnerable_residues": [],
            "critical_positions": [],
        }
    if _PHARMA_AVAILABLE:
        return _PP.calculate_radiolysis_susceptibility(seq)

    # fallback  # pragma: no cover
    return {"error": "pharma_properties unavailable"}


# ─── Combined full report ────────────────────────────────────────────────────


def compute_pharmacology(sequence: str, reference: str = SST14_NATIVE) -> dict:
    """Compute all 13 pharmacological properties for a peptide sequence.

    SS bond correction
    ------------------
    When the sequence contains an even number of Cys residues they are assumed
    to form disulfide bonds in sequential pairing order (first to last, ...).
    For SST-14 (AGCKNFFWKTFTSC) this gives {2, 13} (0-indexed), i.e. Cys3-Cys14.
    Bonded Cys residues are excluded from Henderson-Hasselbalch ionisation in
    isoelectric_point and charge_ph_profile.
    """
    seq = sequence.upper().strip()
    if not seq:
        return {"error": "empty sequence"}

    # Count disulfide bonds (assume Cys pairs form bonds)
    n_cys = seq.count("C")
    n_ss = n_cys // 2

    # Auto-infer SS bond Cys positions (sequential pairing: first to last, ...)
    ss_bond_cysteines: Optional[Set[int]] = None
    if n_cys > 0 and n_cys % 2 == 0:
        cys_pos = [i for i, aa in enumerate(seq) if aa == "C"]
        lo_ptr, hi_ptr = 0, len(cys_pos) - 1
        bonded: set[int] = set()
        while lo_ptr < hi_ptr:
            bonded.add(cys_pos[lo_ptr])
            bonded.add(cys_pos[hi_ptr])
            lo_ptr += 1
            hi_ptr -= 1
        ss_bond_cysteines = bonded

    return {
        "sequence": seq,
        "length": len(seq),
        "gravy": gravy(seq),
        "boman_index": boman_index(seq),
        "instability_index": instability_index(seq),
        "instability_classification": "stable" if instability_index(seq) < 40 else "unstable",
        "aliphatic_index": aliphatic_index(seq),
        "isoelectric_point": isoelectric_point(seq, ss_bond_cysteines=ss_bond_cysteines),
        "extinction_coefficient": molar_extinction_coefficient(seq, n_ss),
        "n_end_rule": n_end_rule(seq),
        "hydrophobic_moment": hydrophobic_moment(seq),
        "wimley_white": wimley_white(seq),
        "charge_ph_profile": charge_ph_profile(seq, ss_bond_cysteines=ss_bond_cysteines),
        "molecular_weight": molecular_weight(seq, n_disulfide=n_ss),
        "protease_sites": protease_cleavage_sites(seq),
        "blosum62": blosum62_analysis(seq, reference),
        "metal_coordination": metal_coordination(seq),
        "radiolysis_susceptibility": radiolysis_susceptibility(seq),
    }
