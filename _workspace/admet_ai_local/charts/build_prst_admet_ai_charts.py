#!/usr/bin/env python3
"""PRST-001~004 + Octreotide Layer3 ADMET-AI 시각화 (matplotlib).

데이터 원본만 사용: `_workspace/admet_ai_local/layer3_prst001_004_octreotide_raw.json`.
H-06 외삽 경고 문구를 모든 차트에 포함한다.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT.parent / "layer3_prst001_004_octreotide_raw.json"

# Figure text is EN-only (DejaVuSans); captions live in KO docs (*.md).
H06_CAPTION = (
    "H-06 WARN: ADMET-AI is LOW-confidence extrapolation outside small-molecule training; "
    "do not treat raw scores as measurements."
)

ORDER = ["PRST-001", "PRST-002", "PRST-003", "PRST-004", "Octreotide"]


def category_for_key(k: str) -> str:
    base = k.replace("_drugbank_approved_percentile", "")
    absorption = (
        "molecular_weight",
        "logP",
        "hydrogen_bond_acceptors",
        "hydrogen_bond_donors",
        "Lipinski",
        "QED",
        "stereo_centers",
        "tpsa",
        "Bioavailability_Ma",
        "HIA_Hou",
        "Caco2_Wang",
        "PAMPA_NCATS",
        "Solubility_AqSolDB",
        "Lipophilicity_AstraZeneca",
    )
    distribution = (
        "VDss_Lombardo",
        "PPBR_AZ",
        "BBB_Martins",
        "HydrationFreeEnergy_FreeSolv",
    )
    metabolism = (
        "CYP1A2_Veith",
        "CYP2C19_Veith",
        "CYP2C9_Substrate_CarbonMangels",
        "CYP2C9_Veith",
        "CYP2D6_Substrate_CarbonMangels",
        "CYP2D6_Veith",
        "CYP3A4_Substrate_CarbonMangels",
        "CYP3A4_Veith",
    )
    excretion = (
        "Half_Life_Obach",
        "Clearance_Hepatocyte_AZ",
        "Clearance_Microsome_AZ",
        "LD50_Zhu",
    )
    toxicity = (
        "PAINS_alert",
        "BRENK_alert",
        "NIH_alert",
        "AMES",
        "Carcinogens_Lagunin",
        "ClinTox",
        "DILI",
        "hERG",
        "Skin_Reaction",
        "NR-AR-LBD",
        "NR-AR",
        "NR-AhR",
        "NR-Aromatase",
        "NR-ER-LBD",
        "NR-ER",
        "NR-PPAR-gamma",
        "Pgp_Broccatelli",
        "SR-ARE",
        "SR-ATAD5",
        "SR-HSE",
        "SR-MMP",
        "SR-p53",
    )
    if base in absorption:
        return "Absorption"
    if base in distribution:
        return "Distribution"
    if base in metabolism:
        return "Metabolism"
    if base in excretion:
        return "Excretion"
    if base in toxicity:
        return "Toxicity"
    return "Other"


def finite_vals(rows: list[dict[str, float]], key: str) -> np.ndarray:
    out = []
    for r in rows:
        v = float(r[key])
        if math.isnan(v):
            continue
        out.append(v)
    return np.array(out, dtype=float)


def mean_toxicity_prob(by_name: dict[str, dict[str, float]], name: str) -> float:
    """알림·카운터(PAINS/BRENK/NIH) 제외 평균 — 0~1 근처 확률형 endpoint 만."""
    keys = [
        "AMES",
        "Carcinogens_Lagunin",
        "ClinTox",
        "DILI",
        "hERG",
        "Skin_Reaction",
        "NR-AR-LBD",
        "NR-AR",
        "NR-AhR",
        "NR-Aromatase",
        "NR-ER-LBD",
        "NR-ER",
        "NR-PPAR-gamma",
        "Pgp_Broccatelli",
        "SR-ARE",
        "SR-ATAD5",
        "SR-HSE",
        "SR-MMP",
        "SR-p53",
    ]
    vals = [by_name[name][k] for k in keys]
    return float(np.mean(vals))


def absorption_proxy(by_name: dict[str, dict[str, float]], name: str) -> float:
    """흡수 proxy: Bioavailability_Ma + HIA_Hou 평균 (원본 JSON 출력)."""
    return float(np.mean([by_name[name]["Bioavailability_Ma"], by_name[name]["HIA_Hou"]]))


def main() -> None:
    payload = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    by_name: dict[str, dict[str, float]] = {}
    for item in payload["results"]:
        by_name[item["name"]] = {k: float(v) for k, v in item["predictions"].items()}

    names = ORDER
    all_keys = list(by_name[names[0]].keys())

    cat_order = ["Absorption", "Distribution", "Metabolism", "Excretion", "Toxicity", "Other"]
    keyed = [(k, category_for_key(k)) for k in all_keys]
    keyed.sort(key=lambda x: (cat_order.index(x[1]), x[0]))
    sorted_keys = [k for k, _ in keyed]

    nz: list[list[float]] = []
    for k in sorted_keys:
        col: list[float] = []
        vals = finite_vals([by_name[n] for n in names], k)
        lo, hi = float(vals.min()), float(vals.max())
        for n in names:
            v = float(by_name[n][k])
            if hi > lo:
                col.append((v - lo) / (hi - lo))
            else:
                col.append(0.5)
        nz.append(col)
    zm = np.array(nz, dtype=float)

    fig_h, ax_h = plt.subplots(figsize=(7.5, 22))
    im = ax_h.imshow(zm, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=1)
    ax_h.set_xticks(range(len(names)))
    ax_h.set_xticklabels(names, rotation=35, ha="right")
    ax_h.set_yticks(range(len(sorted_keys)))
    ax_h.set_yticklabels(sorted_keys, fontsize=4)

    prev_c = None
    for i in range(len(keyed) - 1):
        _, c0 = keyed[i]
        _, c1 = keyed[i + 1]
        if c0 != c1:
            ax_h.axhline(i + 0.5, color="white", linewidth=0.5)

    plt.colorbar(im, ax=ax_h, fraction=0.025, pad=0.03, label="min-max normalized per endpoint (n=5)")

    fig_h.text(
        0.5,
        0.99,
        f"Layer 3 ADMET-AI · 104 keys · sorted by Abs/Dist/Met/Exc/Tox\n{H06_CAPTION}",
        ha="center",
        va="top",
        fontsize=9,
        transform=fig_h.transFigure,
    )
    fig_h.subplots_adjust(top=0.94, bottom=0.06, left=0.36, right=0.95)
    fig_h.savefig(ROOT / "admet_ai_heatmap_104x5.png", dpi=220)
    plt.close(fig_h)

    ref = by_name["Octreotide"]
    pr1 = by_name["PRST-001"]
    diffs = [(k, pr1[k] - ref[k]) for k in sorted_keys]
    vals = sorted(diffs, key=lambda x: abs(x[1]), reverse=True)[:32]

    fig_b, ax_b = plt.subplots(figsize=(10, 8))
    ypos = np.arange(len(vals))
    ax_b.barh(ypos, [v for _, v in vals], color="steelblue")
    ax_b.set_yticks(ypos)
    ax_b.set_yticklabels([k for k, _ in vals], fontsize=8)
    ax_b.invert_yaxis()
    ax_b.set_xlabel("Delta = PRST-001 − Octreotide (raw Layer 3 predictions)")
    ax_b.set_title(f"Top-|Delta| endpoints (32)\n{H06_CAPTION}", fontsize=9)
    fig_b.tight_layout()
    fig_b.savefig(ROOT / "admet_ai_diff_prst001_vs_octreotide_top.png", dpi=200)
    plt.close(fig_b)

    tiers = {
        "PRST-001": "S",
        "PRST-002": "B",
        "PRST-003": "B",
        "PRST-004": "B",
        "Octreotide": "REF",
    }
    colors_map = {"S": "#e6c200", "B": "#4682b4", "REF": "#888888"}

    fig_sc, ax_sc = plt.subplots(figsize=(7.8, 5.4))
    for n in names:
        x = absorption_proxy(by_name, n)
        y = mean_toxicity_prob(by_name, n)
        c = colors_map[tiers[n]]
        ax_sc.scatter(x, y, s=(320 if tiers[n] == "REF" else 260), alpha=0.9, edgecolors="k", linewidths=0.45, color=c)
        xytext = (-12, 10) if n != "Octreotide" else (10, -16)
        ax_sc.annotate(f"{n}\n[{tiers[n]}]", (x, y), textcoords="offset points", xytext=xytext, fontsize=9)

    ax_sc.set_xlabel("Absorption proxy: mean(Bioavailability_Ma, HIA_Hou) · raw predictions")
    ax_sc.set_ylabel(
        "Toxicity proxy: meanprob endpoints excluding PAINS/BRENK/NIH counters · mixed scales"
    )
    ax_sc.set_title(
        f"Tier labels from tier_* CSV vs Layer 3 toxicity proxy\n{H06_CAPTION}", fontsize=9
    )

    plt.tight_layout()
    plt.savefig(
        ROOT / "admet_ai_tier_scatter_toxicity_vs_absorption_proxy.png",
        dpi=200,
        bbox_inches="tight",
    )
    plt.close(fig_sc)

    # 메타 저장 (표/보고 재현용 — 수치 근거)
    meta = {
        "source_json": "_workspace/admet_ai_local/layer3_prst001_004_octreotide_raw.json",
        "h06_disclaimer": H06_CAPTION,
        "scatter_absorption_proxy_endpoints": ["Bioavailability_Ma", "HIA_Hou"],
        "scatter_toxicity_mean_excludes_counters": True,
        "rows": [],
    }

    def pick(name: str) -> dict:
        p = by_name[name]
        return {
            "molecular_weight": p["molecular_weight"],
            "QED": p["QED"],
            "Bioavailability_Ma": p["Bioavailability_Ma"],
            "HIA_Hou": p["HIA_Hou"],
            "hERG": p["hERG"],
            "ClinTox": p["ClinTox"],
        }

    for n in names:
        meta["rows"].append({"name": n, **pick(n)})
    (ROOT / "chart_metadata_minimal.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
