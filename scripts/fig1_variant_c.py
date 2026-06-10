#!/usr/bin/env python3
"""
Fig. 1 – Variant C (two-column vertical flow)

Caption: "Iterative search workflow of the proposed system
(Planner–Candidate Generation–Simulation–QCRanker–DiversityManager–
Critic–Reporter and the feedback loop)"
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.path import Path
import numpy as np
import os

# ── colour palette ──────────────────────────────────────────────────
AGENT_FILL   = "#EEF2F7"
AGENT_BORDER = "#2C3E6B"
PROC_FILL    = "#FFF3E0"
PROC_BORDER  = "#C75B12"
ARROW_GREY   = "#37474F"
FEEDBACK_BLUE = "#1565C0"
BG_WHITE     = "#FFFFFF"

# ── figure / axes ───────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 10), dpi=300)
fig.patch.set_facecolor(BG_WHITE)
ax.set_facecolor(BG_WHITE)
ax.set_xlim(0, 16)
ax.set_ylim(-0.5, 10)
ax.set_aspect("equal")
ax.axis("off")

# ── helper: draw a box ─────────────────────────────────────────────
BOX_W, BOX_H = 4.2, 1.5          # width / height of every box

def draw_box(cx, cy, title, bullets, kind="agent"):
    """Draw a rounded box centred at (cx, cy)."""
    fill  = AGENT_FILL  if kind == "agent" else PROC_FILL
    edge  = AGENT_BORDER if kind == "agent" else PROC_BORDER
    lw    = 2.5

    x0 = cx - BOX_W / 2
    y0 = cy - BOX_H / 2

    box = FancyBboxPatch(
        (x0, y0), BOX_W, BOX_H,
        boxstyle="round,pad=0.15",
        facecolor=fill, edgecolor=edge, linewidth=lw,
        zorder=3,
    )
    ax.add_patch(box)

    # title
    ax.text(cx, cy + 0.32, title,
            ha="center", va="center",
            fontsize=14, fontweight="bold", color="#1A1A2E",
            zorder=4)

    # bullet text (1 or 2 lines)
    bullet_text = "\n".join(f"• {b}" for b in bullets)
    ax.text(cx, cy - 0.30, bullet_text,
            ha="center", va="center",
            fontsize=9.5, color="#444444",
            linespacing=1.35, zorder=4)

    return (cx, cy)   # centre coords for arrow anchoring


# ── helper: vertical arrow with label ──────────────────────────────
def varrow(x_from, y_from, x_to, y_to, label,
           color=ARROW_GREY, style="-|>", ls="-", lw=2.0,
           label_side="right", connectionstyle=None):
    """Straight (or curved) arrow between two box centres,
    shortened so it starts/ends at box edges."""
    # shorten to box edge
    if y_from > y_to:          # going down
        y_start = y_from - BOX_H / 2 - 0.05
        y_end   = y_to   + BOX_H / 2 + 0.05
    else:                       # going up
        y_start = y_from + BOX_H / 2 + 0.05
        y_end   = y_to   - BOX_H / 2 - 0.05

    kw = dict(
        arrowstyle=style, color=color,
        linewidth=lw, linestyle=ls,
        shrinkA=0, shrinkB=0,
        zorder=2,
    )
    if connectionstyle:
        kw["connectionstyle"] = connectionstyle

    arrow = FancyArrowPatch(
        (x_from, y_start), (x_to, y_end), **kw
    )
    ax.add_patch(arrow)

    # label
    mid_x = (x_from + x_to) / 2
    mid_y = (y_start + y_end) / 2
    offset = 0.18
    ha = "left"
    if label_side == "left":
        offset = -0.18
        ha = "right"
    ax.text(mid_x + offset, mid_y, label,
            ha=ha, va="center",
            fontsize=10, fontstyle="italic", color="#555555",
            zorder=4)


# ── helper: horizontal / curved arrow ──────────────────────────────
def harrow(x_from, y_from, x_to, y_to, label,
           color=ARROW_GREY, style="-|>", ls="-", lw=2.0,
           connectionstyle=None, label_offset=(0, 0.25)):
    """Arrow that goes mostly horizontally (bridge or feedback)."""
    # shorten to box edges horizontally
    if x_from < x_to:
        x_start = x_from + BOX_W / 2 + 0.05
        x_end   = x_to   - BOX_W / 2 - 0.05
    else:
        x_start = x_from - BOX_W / 2 - 0.05
        x_end   = x_to   + BOX_W / 2 + 0.05

    kw = dict(
        arrowstyle=style, color=color,
        linewidth=lw, linestyle=ls,
        shrinkA=0, shrinkB=0,
        zorder=2,
    )
    if connectionstyle:
        kw["connectionstyle"] = connectionstyle

    arrow = FancyArrowPatch(
        (x_start, y_from), (x_end, y_to), **kw
    )
    ax.add_patch(arrow)

    mid_x = (x_start + x_end) / 2 + label_offset[0]
    mid_y = (y_from  + y_to)  / 2 + label_offset[1]
    ax.text(mid_x, mid_y, label,
            ha="center", va="center",
            fontsize=10, fontstyle="italic", color="#555555",
            zorder=4)


# ════════════════════════════════════════════════════════════════════
#  DRAW BOXES
# ════════════════════════════════════════════════════════════════════

LX, RX = 3.5, 12.5              # column centres

# — Left column (Generation Pipeline) ——
planner  = draw_box(LX, 7, "Planner",
                    ["Mutation strategy", "Prior-iteration feedback"],
                    kind="agent")
candgen  = draw_box(LX, 5, "Candidate Generation",
                    ["SST14-based mutation proposals"],
                    kind="process")
simul    = draw_box(LX, 3, "Simulation",
                    ["PyRosetta FlexPepDock refinement"],
                    kind="process")

# — Right column (Evaluation Pipeline) ——
qcranker = draw_box(RX, 7, "QCRanker",
                    ["ΔG / clash gate", "Rule-based ranking"],
                    kind="agent")
divmgr   = draw_box(RX, 5, "DiversityManager",
                    ["Duplicate suppression", "Mutation-bias control"],
                    kind="agent")
critic   = draw_box(RX, 3, "Critic",
                    ["Failure-pattern analysis", "Improvement points"],
                    kind="agent")
reporter = draw_box(RX, 1, "Reporter",
                    ["Structured logs", "Top candidates + rationale"],
                    kind="agent")


# ════════════════════════════════════════════════════════════════════
#  DRAW ARROWS
# ════════════════════════════════════════════════════════════════════

# Left column (top → bottom)
varrow(LX, 7, LX, 5, "Mutation strategy",    label_side="left")
varrow(LX, 5, LX, 3, "Mutant candidates",    label_side="left")

# Bridge: Simulation → QCRanker
# Custom path: exit Simulation right edge at y=3, travel horizontally,
# then curve up to enter QCRanker left edge at y=7
bridge_x0 = LX + BOX_W / 2 + 0.05
bridge_x1 = RX - BOX_W / 2 - 0.05
bridge_verts = [
    (bridge_x0, 3.0),           # start: right edge of Simulation
    (bridge_x0 + 1.5, 3.0),     # horizontal run out
    (bridge_x1 - 1.5, 7.0),     # curve control toward QCRanker
    (bridge_x1, 7.0),           # end: left edge of QCRanker
]
bridge_codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
bridge_path = Path(bridge_verts, bridge_codes)
bridge_arrow = FancyArrowPatch(
    path=bridge_path,
    arrowstyle="-|>",
    color=ARROW_GREY,
    linewidth=2.0,
    zorder=2,
)
ax.add_patch(bridge_arrow)
ax.text((bridge_x0 + bridge_x1) / 2, 5.65,
        "\u0394G + clash scores",
        ha="center", va="center",
        fontsize=10, fontstyle="italic", color="#555555",
        zorder=4)

# Right column (top → bottom)
varrow(RX, 7, RX, 5, "Ranked candidates",    label_side="right")
varrow(RX, 5, RX, 3, "Diversified set",      label_side="right")
varrow(RX, 3, RX, 1, "Critique report",      label_side="right")

# Feedback: Reporter → Planner (dashed blue, curving underneath)
# We draw from bottom of Reporter around the bottom-left to top of Planner
fb_start_x = RX - BOX_W / 2 - 0.05
fb_start_y = 1
fb_end_x   = LX - BOX_W / 2 - 0.05
fb_end_y   = 7

# Use a custom path via annotations for a nicer curve
verts = [
    (RX,              1 - BOX_H / 2 - 0.05),   # start below Reporter
    (RX,              0.0),                       # drop down
    (8.0,            -0.15),                      # bottom centre
    (LX,              0.0),                       # left bottom
    (LX,              7 - BOX_H / 2 - 0.40),    # rise toward Planner
]
# Smooth cubic-Bezier-like path
codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO]
path = Path(verts, codes)

feedback_patch = FancyArrowPatch(
    path=path,
    arrowstyle="-|>",
    color=FEEDBACK_BLUE,
    linewidth=2.2,
    linestyle="dashed",
    zorder=2,
)
ax.add_patch(feedback_patch)

# Finish the feedback arrow: small straight segment into Planner bottom
fb_finish = FancyArrowPatch(
    (LX, 7 - BOX_H / 2 - 0.40),
    (LX, 7 - BOX_H / 2 - 0.05),
    arrowstyle="-|>",
    color=FEEDBACK_BLUE,
    linewidth=2.2,
    linestyle="dashed",
    shrinkA=0, shrinkB=0,
    zorder=2,
)
ax.add_patch(fb_finish)

# feedback label
ax.text(8.0, -0.38, "Feedback + iteration context",
        ha="center", va="top",
        fontsize=10, fontstyle="italic", color=FEEDBACK_BLUE,
        zorder=4)


# ════════════════════════════════════════════════════════════════════
#  COLUMN HEADINGS
# ════════════════════════════════════════════════════════════════════
ax.text(LX, 8.25, "Generation Pipeline",
        ha="center", va="center",
        fontsize=13, fontstyle="italic", color="#888888", zorder=4)
ax.text(RX, 8.25, "Evaluation Pipeline",
        ha="center", va="center",
        fontsize=13, fontstyle="italic", color="#888888", zorder=4)


# ════════════════════════════════════════════════════════════════════
#  DASHED BACKGROUND BOX ("Iterative Loop")
# ════════════════════════════════════════════════════════════════════
loop_box = FancyBboxPatch(
    (0.6, -0.7), 14.8, 9.7,
    boxstyle="round,pad=0.3",
    facecolor="none",
    edgecolor="#AAAAAA",
    linewidth=1.5,
    linestyle="dashed",
    zorder=1,
)
ax.add_patch(loop_box)
ax.text(8.0, 9.25, "Iterative Loop",
        ha="center", va="center",
        fontsize=12, fontstyle="italic", color="#999999",
        zorder=4)


# ════════════════════════════════════════════════════════════════════
#  LEGEND  (top-left)
# ════════════════════════════════════════════════════════════════════
legend_handles = [
    mpatches.Patch(facecolor=AGENT_FILL, edgecolor=AGENT_BORDER,
                   linewidth=1.8, label="Agent"),
    mpatches.Patch(facecolor=PROC_FILL,  edgecolor=PROC_BORDER,
                   linewidth=1.8, label="Process step"),
    mpatches.Patch(facecolor="none", edgecolor=FEEDBACK_BLUE,
                   linewidth=1.8, linestyle="dashed",
                   label="Feedback loop"),
]
leg = ax.legend(handles=legend_handles,
                loc="upper left",
                frameon=True,
                framealpha=0.95,
                edgecolor="#CCCCCC",
                fontsize=11,
                handlelength=2.0,
                borderpad=0.8,
                labelspacing=0.6)
leg.set_zorder(5)


# ════════════════════════════════════════════════════════════════════
#  SAVE
# ════════════════════════════════════════════════════════════════════
out_dir = (
    "/home/helloworld/Documents/workspace/repos/PRST_N_FM/"
    "AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/docs"
)
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "fig1_variant_c.png")

fig.savefig(out_path, dpi=300, bbox_inches="tight",
            facecolor=BG_WHITE, pad_inches=0.25)
plt.close(fig)
print(f"Saved → {out_path}")
