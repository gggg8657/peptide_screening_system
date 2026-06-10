#!/usr/bin/env python3
"""
Fig. 1 – Variant D (Horizontal S-curve / snake layout)

Iterative search workflow of the proposed system
(Planner–Candidate Generation–Simulation–QCRanker–DiversityManager–Critic–Reporter
 and the feedback loop)
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# ── colour palette ──────────────────────────────────────────────────
AGENT_FILL   = "#EEF2F7"
AGENT_BORDER = "#2C3E6B"
PROC_FILL    = "#FFF3E0"
PROC_BORDER  = "#C75B12"
ARROW_FWD    = "#37474F"
ARROW_FB     = "#1565C0"
BG_DASH      = "#E8EAF0"

# ── figure ──────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(17, 9), dpi=300)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")
ax.set_xlim(-2, 20)
ax.set_ylim(-1.5, 10.5)
ax.set_aspect("equal")
ax.axis("off")

# ── positions ───────────────────────────────────────────────────────
# Top row x centres (left to right): wider spacing for labels
TOP_X = [2.0, 6.5, 11.0, 15.5]
TOP_Y = 6.5
# Bottom row x centres (right to left)
BOT_X_DM, BOT_X_CR, BOT_X_RP = 13.0, 8.5, 4.0
BOT_Y = 2.0

# ── box dimensions ──────────────────────────────────────────────────
AGENT_W, AGENT_H = 2.8, 1.1
PROC_W,  PROC_H  = 3.0, 0.95

# ── subtle dashed background box ────────────────────────────────────
bg = FancyBboxPatch(
    (-0.5, 0.0), 19.0, 9.0,
    boxstyle="round,pad=0.3",
    facecolor="#F8F9FB", edgecolor=BG_DASH,
    linewidth=1.5, linestyle="--", zorder=0,
)
ax.add_patch(bg)

# ── helper: draw a rounded box with title + bullet lines ────────────
def draw_box(cx, cy, w, h, title, lines, fill, border, is_agent=True):
    x0 = cx - w / 2
    y0 = cy - h / 2
    box = FancyBboxPatch(
        (x0, y0), w, h,
        boxstyle="round,pad=0.12",
        facecolor=fill, edgecolor=border,
        linewidth=2.5, zorder=2,
    )
    ax.add_patch(box)
    # title
    if is_agent:
        ty = cy + h * 0.22
    else:
        ty = cy + h * 0.18
    ax.text(cx, ty, title,
            ha="center", va="center",
            fontsize=13, fontweight="bold", color=border, zorder=3)
    # bullet lines
    for i, line in enumerate(lines):
        ly = ty - 0.30 - i * 0.24
        ax.text(cx, ly, f"• {line}",
                ha="center", va="center",
                fontsize=9, color="#444444", zorder=3)


# ── top row  (left → right) ─────────────────────────────────────────
draw_box(TOP_X[0], TOP_Y, AGENT_W, AGENT_H,
         "Planner", ["Mutation strategy", "Prior-iteration feedback"],
         AGENT_FILL, AGENT_BORDER)

draw_box(TOP_X[1], TOP_Y, PROC_W, PROC_H,
         "Candidate Generation", ["SST14-based mutation proposals"],
         PROC_FILL, PROC_BORDER, is_agent=False)

draw_box(TOP_X[2], TOP_Y, PROC_W, PROC_H,
         "Simulation", ["PyRosetta FlexPepDock refinement"],
         PROC_FILL, PROC_BORDER, is_agent=False)

draw_box(TOP_X[3], TOP_Y, AGENT_W, AGENT_H,
         "QCRanker", ["ΔG / clash gate", "Rule-based ranking"],
         AGENT_FILL, AGENT_BORDER)

# ── bottom row  (right → left) ──────────────────────────────────────
draw_box(BOT_X_DM, BOT_Y, AGENT_W, AGENT_H,
         "DiversityManager", ["Duplicate suppression", "Mutation-bias control"],
         AGENT_FILL, AGENT_BORDER)

draw_box(BOT_X_CR, BOT_Y, AGENT_W, AGENT_H,
         "Critic", ["Failure-pattern analysis", "Improvement points"],
         AGENT_FILL, AGENT_BORDER)

draw_box(BOT_X_RP, BOT_Y, AGENT_W, AGENT_H,
         "Reporter", ["Structured logs", "Top candidates + rationale"],
         AGENT_FILL, AGENT_BORDER)

# ── helper: straight arrow between boxes (arrow at box midline) ──────
def straight_arrow(x1, y1, x2, y2, color=ARROW_FWD, style="-", lw=1.8):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>", color=color,
            lw=lw, linestyle=style,
            shrinkA=3, shrinkB=3,
            mutation_scale=16,
        ),
        zorder=4,
    )

def arrow_label(x, y, label, color="#37474F"):
    ax.text(x, y, label,
            ha="center", va="center",
            fontsize=9.5, fontstyle="italic", color=color, zorder=5)


# ── top-row forward arrows ──────────────────────────────────────────
# Arrows go at TOP_Y, labels placed well ABOVE the top edge of boxes
label_y_top = TOP_Y + AGENT_H / 2 + 0.35  # above boxes

# Planner → CandGen
x_start = TOP_X[0] + AGENT_W / 2
x_end   = TOP_X[1] - PROC_W / 2
straight_arrow(x_start, TOP_Y, x_end, TOP_Y)
arrow_label((x_start + x_end) / 2, label_y_top, "Mutation strategy")

# CandGen → Simulation
x_start = TOP_X[1] + PROC_W / 2
x_end   = TOP_X[2] - PROC_W / 2
straight_arrow(x_start, TOP_Y, x_end, TOP_Y)
arrow_label((x_start + x_end) / 2, label_y_top, "Mutant candidates")

# Simulation → QCRanker
x_start = TOP_X[2] + PROC_W / 2
x_end   = TOP_X[3] - AGENT_W / 2
straight_arrow(x_start, TOP_Y, x_end, TOP_Y)
arrow_label((x_start + x_end) / 2, label_y_top, "ΔG + clash scores")

# ── right-side curved connector: QCRanker → DiversityManager ────────
arrow_right = FancyArrowPatch(
    posA=(TOP_X[3] + AGENT_W * 0.15, TOP_Y - AGENT_H / 2),
    posB=(BOT_X_DM + AGENT_W * 0.15, BOT_Y + AGENT_H / 2),
    connectionstyle="arc3,rad=0.45",
    arrowstyle="-|>",
    color=ARROW_FWD, lw=1.8,
    mutation_scale=16,
    zorder=4,
)
ax.add_patch(arrow_right)
arrow_label(16.8, 4.25, "Ranked\ncandidates")

# ── bottom-row forward arrows ───────────────────────────────────────
# Labels placed well BELOW the bottom edge of boxes
label_y_bot = BOT_Y - AGENT_H / 2 - 0.35

# DivMgr → Critic  (right to left)
x_start = BOT_X_DM - AGENT_W / 2
x_end   = BOT_X_CR + AGENT_W / 2
straight_arrow(x_start, BOT_Y, x_end, BOT_Y)
arrow_label((x_start + x_end) / 2, label_y_bot, "Diversified set")

# Critic → Reporter  (right to left)
x_start = BOT_X_CR - AGENT_W / 2
x_end   = BOT_X_RP + AGENT_W / 2
straight_arrow(x_start, BOT_Y, x_end, BOT_Y)
arrow_label((x_start + x_end) / 2, label_y_bot, "Critique report")

# ── feedback arrow: Reporter → Planner  (dashed blue, left side) ────
arrow_fb = FancyArrowPatch(
    posA=(BOT_X_RP - AGENT_W * 0.15, BOT_Y + AGENT_H / 2),
    posB=(TOP_X[0] - AGENT_W * 0.15, TOP_Y - AGENT_H / 2),
    connectionstyle="arc3,rad=0.55",
    arrowstyle="-|>",
    color=ARROW_FB, lw=2.2, linestyle="--",
    mutation_scale=18,
    zorder=4,
)
ax.add_patch(arrow_fb)
arrow_label(0.8, 4.25, "Feedback +\niteration context", color=ARROW_FB)

# ── legend (top-left) ───────────────────────────────────────────────
legend_handles = [
    mpatches.Patch(facecolor=AGENT_FILL, edgecolor=AGENT_BORDER,
                   linewidth=1.5, label="Agent"),
    mpatches.Patch(facecolor=PROC_FILL, edgecolor=PROC_BORDER,
                   linewidth=1.5, label="Process step"),
    plt.Line2D([0], [0], color=ARROW_FWD, lw=1.8,
               marker=">", markersize=7, label="Forward flow"),
    plt.Line2D([0], [0], color=ARROW_FB, lw=2.0, linestyle="--",
               marker=">", markersize=7, label="Feedback loop"),
]
ax.legend(
    handles=legend_handles,
    loc="upper left",
    bbox_to_anchor=(0.0, 1.0),
    frameon=True, framealpha=0.9,
    edgecolor="#CCCCCC",
    fontsize=10,
    ncol=1,
    handlelength=2.2,
)

# ── save ─────────────────────────────────────────────────────────────
out = ("/home/helloworld/Documents/workspace/repos/PRST_N_FM/"
       "AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/docs/"
       "fig1_variant_d.png")
fig.savefig(out, bbox_inches="tight", facecolor="white", dpi=300)
plt.close(fig)
print(f"Saved → {out}")
