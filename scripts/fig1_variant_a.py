#!/usr/bin/env python3
"""
Fig. 1  --  Variant A (wide rectangular loop)

Iterative search workflow of the proposed system
(Planner - Candidate Generation - Simulation - QCRanker -
 DiversityManager - Critic - Reporter  and the feedback loop)

Output: docs/fig1_variant_a.png
"""

import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ── Output path ──────────────────────────────────────────────────────────
OUT = pathlib.Path(
    "/home/helloworld/Documents/workspace/repos/PRST_N_FM/"
    "AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/docs/"
    "fig1_variant_a.png"
)
OUT.parent.mkdir(parents=True, exist_ok=True)

# ── Palette ──────────────────────────────────────────────────────────────
AGENT_FILL = "#EEF2F7"
AGENT_EDGE = "#2C3E6B"
PROC_FILL  = "#FFF3E0"
PROC_EDGE  = "#C75B12"
ARROW_FWD  = "#37474F"
ARROW_FB   = "#1565C0"
BG_LOOP    = "#F7F8FA"
WHITE      = "#FFFFFF"

BOX_LW     = 2.5
TITLE_SZ   = 13
DESC_SZ    = 9.0
LABEL_SZ   = 9.5

# ── Canvas (wider to fit everything) ─────────────────────────────────────
fig, ax = plt.subplots(figsize=(17, 10), dpi=300)
fig.patch.set_facecolor(WHITE)
ax.set_facecolor(WHITE)
ax.set_xlim(0, 18.5)
ax.set_ylim(0, 10.5)
ax.set_aspect("equal")
ax.axis("off")

# Dashed background
bg = FancyBboxPatch(
    (0.3, 0.4), 17.9, 9.2,
    boxstyle="round,pad=0.3",
    facecolor=BG_LOOP, edgecolor="#B0BEC5",
    linestyle="--", linewidth=1.2, zorder=0,
)
ax.add_patch(bg)

# ── draw_box ─────────────────────────────────────────────────────────────
def draw_box(cx, cy, w, h, title, lines, kind="agent"):
    fill = AGENT_FILL if kind == "agent" else PROC_FILL
    edge = AGENT_EDGE if kind == "agent" else PROC_EDGE
    x0, y0 = cx - w / 2, cy - h / 2
    ax.add_patch(FancyBboxPatch(
        (x0, y0), w, h,
        boxstyle="round,pad=0.18",
        facecolor=fill, edgecolor=edge,
        linewidth=BOX_LW, zorder=2,
    ))
    ty = cy + h * 0.24
    ax.text(cx, ty, title,
            ha="center", va="center",
            fontsize=TITLE_SZ, fontweight="bold", color=edge, zorder=3)
    for i, ln in enumerate(lines):
        ax.text(cx, ty - 0.40 - i * 0.32, f"\u2022 {ln}",
                ha="center", va="center",
                fontsize=DESC_SZ, color="#444444", zorder=3)
    return dict(cx=cx, cy=cy, w=w, h=h,
                top=(cx, cy + h / 2), bot=(cx, cy - h / 2),
                left=(cx - w / 2, cy), right=(cx + w / 2, cy))

# ── Geometry ─────────────────────────────────────────────────────────────
BW   = 2.6
BH_A = 1.60
BH_P = 1.35

Y_T  = 7.5
Y_B  = 2.8

# X centres -- generous spacing, Planner far left
X_PL = 2.0
X_CG = 6.5
X_SM = 10.8
X_QC = 15.3
X_DM = 11.5
X_CR = 7.6
X_RP = 3.7

# ── Draw boxes ───────────────────────────────────────────────────────────
pl = draw_box(X_PL, Y_T, BW, BH_A, "Planner",
              ["Mutation strategy", "Prior-iteration feedback"])
cg = draw_box(X_CG, Y_T, BW, BH_P, "Candidate Generation",
              ["SST14-based mutation proposals"], kind="process")
sm = draw_box(X_SM, Y_T, BW, BH_P, "Simulation",
              ["PyRosetta FlexPepDock refinement"], kind="process")
qc = draw_box(X_QC, Y_B, BW, BH_A, "QCRanker",
              ["\u0394G / clash gate", "Rule-based ranking"])
dm = draw_box(X_DM, Y_B, BW, BH_A, "DiversityManager",
              ["Duplicate suppression", "Mutation-bias control"])
cr = draw_box(X_CR, Y_B, BW, BH_A, "Critic",
              ["Failure-pattern analysis", "Improvement points"])
rp = draw_box(X_RP, Y_B, BW, BH_A, "Reporter",
              ["Structured logs", "Top candidates + rationale"])

# ── arrow helpers ────────────────────────────────────────────────────────
def arr(p1, p2, color=ARROW_FWD, ls="-"):
    ax.add_patch(FancyArrowPatch(
        p1, p2, arrowstyle="-|>", color=color,
        linewidth=2.0, linestyle=ls, mutation_scale=18,
        shrinkA=4, shrinkB=4, zorder=4))

def lbl(x, y, txt, color=ARROW_FWD, va="bottom", ha="center", rot=0):
    ax.text(x, y, txt, ha=ha, va=va,
            fontsize=LABEL_SZ, fontstyle="italic",
            color=color, zorder=5, rotation=rot)

# ── TOP ROW arrows (labels ABOVE) ───────────────────────────────────────
arr(pl["right"], cg["left"])
lbl((pl["right"][0] + cg["left"][0]) / 2, Y_T + 0.52, "Mutation strategy")

arr(cg["right"], sm["left"])
lbl((cg["right"][0] + sm["left"][0]) / 2, Y_T + 0.52, "Mutant candidates")

# ── RIGHT SIDE: Simulation -> QCRanker (L-shaped along right margin) ────
RX = 17.2
arr(sm["right"], (RX, Y_T))
arr((RX, Y_T), (RX, Y_B))
arr((RX, Y_B), qc["right"])
lbl(RX + 0.22, (Y_T + Y_B) / 2, "\u0394G + clash scores",
    ha="left", va="center", rot=90)

# ── BOTTOM ROW arrows (flow left, labels BELOW) ─────────────────────────
arr(qc["left"], dm["right"])
lbl((qc["left"][0] + dm["right"][0]) / 2, Y_B - BH_A / 2 - 0.18,
    "Ranked candidates", va="top")

arr(dm["left"], cr["right"])
lbl((dm["left"][0] + cr["right"][0]) / 2, Y_B - BH_A / 2 - 0.18,
    "Diversified set", va="top")

arr(cr["left"], rp["right"])
lbl((cr["left"][0] + rp["right"][0]) / 2, Y_B - BH_A / 2 - 0.18,
    "Critique report", va="top")

# ── LEFT SIDE feedback: Reporter -> Planner (dashed blue L-route) ───────
LX = 0.7
arr(rp["left"], (LX, Y_B), color=ARROW_FB, ls="--")
arr((LX, Y_B), (LX, Y_T), color=ARROW_FB, ls="--")
arr((LX, Y_T), pl["left"], color=ARROW_FB, ls="--")
lbl(LX - 0.15, (Y_T + Y_B) / 2, "Feedback + iteration context",
    color=ARROW_FB, ha="right", va="center", rot=90)

# ── Legend (top-left) ────────────────────────────────────────────────────
LGX, LGY = 1.0, 9.95

# Agent swatch
ax.add_patch(FancyBboxPatch(
    (LGX, LGY - 0.17), 0.40, 0.34,
    boxstyle="round,pad=0.05",
    facecolor=AGENT_FILL, edgecolor=AGENT_EDGE,
    linewidth=1.8, zorder=6))
ax.text(LGX + 0.55, LGY, "Agent",
        va="center", fontsize=11, color="#333333", zorder=6)

# Process swatch
ax.add_patch(FancyBboxPatch(
    (LGX + 2.1, LGY - 0.17), 0.40, 0.34,
    boxstyle="round,pad=0.05",
    facecolor=PROC_FILL, edgecolor=PROC_EDGE,
    linewidth=1.8, zorder=6))
ax.text(LGX + 2.65, LGY, "Process step",
        va="center", fontsize=11, color="#333333", zorder=6)

# Feedback arrow swatch
ax.annotate("", xy=(LGX + 5.8, LGY), xytext=(LGX + 4.8, LGY),
            arrowprops=dict(arrowstyle="-|>", color=ARROW_FB,
                            lw=2.0, linestyle="--", mutation_scale=16),
            zorder=6)
ax.text(LGX + 5.95, LGY, "Feedback loop",
        va="center", fontsize=11, color="#333333", zorder=6)

# ── Save ─────────────────────────────────────────────────────────────────
fig.savefig(str(OUT), bbox_inches="tight", facecolor=WHITE, pad_inches=0.3)
plt.close(fig)
print(f"Saved -> {OUT}")
