#!/usr/bin/env python3
"""
Fig. 1 Variant B -- Circular / ring layout
Iterative search workflow of the proposed system.

Components arranged on an ellipse, flowing clockwise with curved arrows.
"""

import math
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(16, 10), dpi=300)
ax.set_xlim(-1.5, 17.5)
ax.set_ylim(-0.5, 9.5)
ax.set_aspect("equal")
ax.axis("off")
fig.patch.set_facecolor("white")

# ---------------------------------------------------------------------------
# Ellipse parameters  (centre, radii)
# ---------------------------------------------------------------------------
cx, cy = 8.0, 4.5
rx, ry = 5.5, 3.5

# ---------------------------------------------------------------------------
# Component definitions -- angle in degrees measured clockwise from 12-o'clock
# We convert to standard math radians (counter-clockwise from 3-o'clock).
# clock_deg  0 => top,  90 => right,  180 => bottom,  270 => left
# ---------------------------------------------------------------------------
components = [
    # (label, clock_deg, type, title, bullets)
    ("Planner",              0,   "agent",
     "Planner",
     ["Mutation strategy", "Prior-iteration feedback"]),
    ("Candidate\nGeneration", 52,  "process",
     "Candidate Generation",
     ["SST14-based mutation proposals"]),
    ("Simulation",           105, "process",
     "Simulation\n(PyRosetta FlexPepDock)",
     ["PyRosetta FlexPepDock refinement"]),
    ("QCRanker",             155, "agent",
     "QCRanker",
     ["\u0394G / clash gate", "Rule-based ranking"]),
    ("DiversityManager",     205, "agent",
     "DiversityManager",
     ["Duplicate suppression", "Mutation-bias control"]),
    ("Critic",               258, "agent",
     "Critic",
     ["Failure-pattern analysis", "Improvement points"]),
    ("Reporter",             310, "agent",
     "Reporter",
     ["Structured logs", "Top candidates + rationale"]),
]

# Arrow labels (from -> to)
arrow_labels = [
    "Mutation strategy",
    "Mutant candidates",
    "\u0394G + clash scores",
    "Ranked candidates",
    "Diversified set",
    "Critique report",
    "Feedback + iteration context",
]

# ---------------------------------------------------------------------------
# Style palette
# ---------------------------------------------------------------------------
AGENT_FILL   = "#EEF2F7"
AGENT_BORDER = "#2C3E6B"
PROC_FILL    = "#FFF3E0"
PROC_BORDER  = "#C75B12"
FEEDBACK_CLR = "#1565C0"
LW           = 2.5

# ---------------------------------------------------------------------------
# Helper -- clock degrees to (x, y) on the ellipse
# ---------------------------------------------------------------------------
def clock_to_xy(clock_deg):
    """Convert clock-position degrees to (x, y) on the ellipse.
    0 deg = 12-o'clock (top), clockwise positive."""
    # Convert: math_angle = 90 - clock_deg  (in degrees)
    rad = math.radians(90 - clock_deg)
    x = cx + rx * math.cos(rad)
    y = cy + ry * math.sin(rad)
    return x, y


# ---------------------------------------------------------------------------
# Draw boxes
# ---------------------------------------------------------------------------
BOX_W = 3.0
BOX_H = 1.55

box_centres = []  # store (x, y) for arrow routing

for comp in components:
    label, clock_deg, ctype, title, bullets = comp
    bx, by = clock_to_xy(clock_deg)
    box_centres.append((bx, by))

    fill  = AGENT_FILL  if ctype == "agent" else PROC_FILL
    edge  = AGENT_BORDER if ctype == "agent" else PROC_BORDER

    # FancyBboxPatch anchor is lower-left
    rect = FancyBboxPatch(
        (bx - BOX_W / 2, by - BOX_H / 2),
        BOX_W, BOX_H,
        boxstyle="round,pad=0.12",
        facecolor=fill, edgecolor=edge, linewidth=LW,
        zorder=3,
    )
    ax.add_patch(rect)

    # Title -- nudge up more for multi-line titles
    n_title_lines = title.count("\n") + 1
    title_y_off = 0.32 if n_title_lines == 1 else 0.38
    ax.text(bx, by + title_y_off, title,
            ha="center", va="center", fontsize=14, fontweight="bold",
            color="#1a1a1a", zorder=4, linespacing=0.95)

    # Bullets
    bullet_text = "\n".join(f"\u2022 {b}" for b in bullets)
    ax.text(bx, by - 0.35, bullet_text,
            ha="center", va="center", fontsize=9,
            color="#444444", zorder=4, linespacing=1.25)

# ---------------------------------------------------------------------------
# Draw curved arrows between successive components
# ---------------------------------------------------------------------------
def edge_point(centre, target, half_w, half_h):
    """Find the intersection of the line (centre -> target) with the
    bounding box of the node, so the arrow starts/ends at the box edge."""
    dx = target[0] - centre[0]
    dy = target[1] - centre[1]
    if dx == 0 and dy == 0:
        return centre
    # Scale factors to reach box edge
    scales = []
    if dx != 0:
        scales.append(half_w / abs(dx))
    if dy != 0:
        scales.append(half_h / abs(dy))
    s = min(scales) if scales else 1.0
    return (centre[0] + dx * s, centre[1] + dy * s)


for i in range(len(components)):
    j = (i + 1) % len(components)
    src = box_centres[i]
    dst = box_centres[j]

    is_feedback = (i == len(components) - 1)  # Reporter -> Planner

    # Compute edge points
    sp = edge_point(src, dst, BOX_W / 2 + 0.05, BOX_H / 2 + 0.05)
    dp = edge_point(dst, src, BOX_W / 2 + 0.05, BOX_H / 2 + 0.05)

    # Connection style -- curve outward from the ellipse centre
    # Determine curvature direction: we want arrows to bow outward.
    mid_x = (sp[0] + dp[0]) / 2
    mid_y = (sp[1] + dp[1]) / 2
    # Vector from centre to midpoint
    vx = mid_x - cx
    vy = mid_y - cy

    # Use the cross product of (src->dst) with (centre->mid) to pick sign
    arrow_dx = dp[0] - sp[0]
    arrow_dy = dp[1] - sp[1]
    cross = arrow_dx * vy - arrow_dy * vx
    rad_sign = 0.3 if cross > 0 else -0.3

    style = f"arc3,rad={rad_sign}"

    color = FEEDBACK_CLR if is_feedback else "#555555"
    ls    = (0, (6, 4)) if is_feedback else "-"

    arrow = FancyArrowPatch(
        sp, dp,
        connectionstyle=style,
        arrowstyle="->,head_width=0.25,head_length=0.18",
        color=color,
        linewidth=2.0,
        linestyle=ls,
        zorder=2,
    )
    ax.add_patch(arrow)

    # --- Arrow label placement (outside the ring) -------------------------
    # Place label at the midpoint of the arc, pushed outward from centre.
    label_mid_x = (sp[0] + dp[0]) / 2
    label_mid_y = (sp[1] + dp[1]) / 2

    # Push outward from ellipse centre
    off_vx = label_mid_x - cx
    off_vy = label_mid_y - cy
    norm = math.hypot(off_vx, off_vy) or 1.0
    push = 0.55  # how far outside
    lx = label_mid_x + off_vx / norm * push
    ly = label_mid_y + off_vy / norm * push

    # Compute rotation angle so text follows the arc direction
    angle_deg = math.degrees(math.atan2(arrow_dy, arrow_dx))
    # Keep text upright (flip if upside-down)
    if angle_deg > 90:
        angle_deg -= 180
    elif angle_deg < -90:
        angle_deg += 180

    ax.text(lx, ly, arrow_labels[i],
            ha="center", va="center",
            fontsize=9.5, fontstyle="italic", color="#333333",
            rotation=angle_deg, rotation_mode="anchor",
            zorder=5,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))

# ---------------------------------------------------------------------------
# Centre text
# ---------------------------------------------------------------------------
ax.text(cx, cy, "Mutate \u2013 Dock \u2013 QC \u2013 Critique \u2013 Report Loop",
        ha="center", va="center",
        fontsize=12, fontstyle="italic", color="#bbbbbb", zorder=1)

# ---------------------------------------------------------------------------
# Legend (top-left)
# ---------------------------------------------------------------------------
legend_x, legend_y = 0.3, 9.0
legend_items = [
    (AGENT_FILL, AGENT_BORDER, "Agent"),
    (PROC_FILL,  PROC_BORDER,  "Process step"),
]
for idx, (fc, ec, lbl) in enumerate(legend_items):
    y_off = legend_y - idx * 0.55
    rect = FancyBboxPatch(
        (legend_x, y_off - 0.18), 0.55, 0.36,
        boxstyle="round,pad=0.06",
        facecolor=fc, edgecolor=ec, linewidth=LW, zorder=5)
    ax.add_patch(rect)
    ax.text(legend_x + 0.75, y_off, lbl,
            va="center", fontsize=10, color="#1a1a1a", zorder=5)

# Feedback arrow in legend
ly_fb = legend_y - 2 * 0.55
ax.annotate("",
            xy=(legend_x + 0.55, ly_fb),
            xytext=(legend_x, ly_fb),
            arrowprops=dict(arrowstyle="->", color=FEEDBACK_CLR,
                            lw=2.0, linestyle=(0, (6, 4))),
            zorder=5)
ax.text(legend_x + 0.75, ly_fb, "Feedback loop",
        va="center", fontsize=10, color="#1a1a1a", zorder=5)

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
out = ("/home/helloworld/Documents/workspace/repos/PRST_N_FM/"
       "AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/docs/"
       "fig1_variant_b.png")
fig.savefig(out, bbox_inches="tight", facecolor="white", pad_inches=0.3)
plt.close(fig)
print(f"Saved -> {out}")
