#!/usr/bin/env python3
"""Generate Fig. 1 — matching paper Section 2.1 description exactly.

Caption: "Iterative search workflow of the proposed system
(Planner–Candidate Generation–Simulation–QCRanker–DiversityManager–
Critic–Reporter and the feedback loop)"

No Input/Output boxes. Just the iterative loop.
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ── Style ────────────────────────────────────────────────────────────────
AGENT_FILL, AGENT_BORDER = "#EEF2F7", "#2C3E6B"
PROC_FILL,  PROC_BORDER  = "#FFF3E0", "#C75B12"

C_BG, C_LOOP_BG, C_LOOP_BD = "#FFFFFF", "#FAFBFD", "#B0BEC5"
C_TITLE, C_BODY = "#1A1A1A", "#333333"
C_ARROW, C_FEEDBACK, C_LABEL = "#37474F", "#1565C0", "#455A64"


def _box(ax, x, y, w, h, fill, border, lw=2.5, zorder=3):
    ax.add_patch(FancyBboxPatch(
        (x - w/2, y - h/2), w, h, boxstyle="round,pad=0.1",
        facecolor=fill, edgecolor=border, linewidth=lw, zorder=zorder))


def agent(ax, x, y, w, h, title, lines):
    _box(ax, x, y, w, h, AGENT_FILL, AGENT_BORDER)
    top = y + h/2 - 0.35
    ax.text(x, top, title, ha="center", va="center",
            fontsize=14, fontweight="bold", color=C_TITLE, zorder=4)
    for i, t in enumerate(lines):
        ax.text(x, top - 0.32 - i * 0.26, t, ha="center", va="center",
                fontsize=9.5, color=C_BODY, zorder=4)


def proc(ax, x, y, w, h, title, line):
    _box(ax, x, y, w, h, PROC_FILL, PROC_BORDER)
    ax.text(x, y + 0.18, title, ha="center", va="center",
            fontsize=13.5, fontweight="bold", color=C_TITLE, zorder=4)
    ax.text(x, y - 0.20, line, ha="center", va="center",
            fontsize=9.5, color=C_BODY, zorder=4)


def arr(ax, x1, y1, x2, y2, color=C_ARROW, lw=1.8,
        style="arc3,rad=0.0", ls="-", ms=15):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", connectionstyle=style,
        mutation_scale=ms, lw=lw, color=color, linestyle=ls, zorder=2))


def lbl(ax, x, y, text):
    ax.text(x, y, text, ha="center", va="center",
            fontsize=10, color=C_LABEL, fontstyle="italic", zorder=5)


def main():
    fig, ax = plt.subplots(1, 1, figsize=(17, 10))
    ax.set_xlim(-0.5, 17.0)
    ax.set_ylim(-0.5, 9.5)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(C_BG)

    # ── Legend ──
    lx, ly = 0.2, 9.0
    _box(ax, lx + 0.18, ly, 0.30, 0.22, AGENT_FILL, AGENT_BORDER, lw=1.8, zorder=5)
    ax.text(lx + 0.52, ly, "Agent", ha="left", va="center",
            fontsize=10, color=C_TITLE, zorder=5)
    _box(ax, lx + 2.4, ly, 0.30, 0.22, PROC_FILL, PROC_BORDER, lw=1.8, zorder=5)
    ax.text(lx + 2.74, ly, "Process step", ha="left", va="center",
            fontsize=10, color=C_TITLE, zorder=5)
    ax.add_patch(FancyArrowPatch(
        (lx + 5.2, ly), (lx + 5.6, ly), arrowstyle="-|>", mutation_scale=11,
        lw=1.8, color=C_FEEDBACK, linestyle="--", zorder=5))
    ax.text(lx + 5.78, ly, "Feedback loop", ha="left", va="center",
            fontsize=10, color=C_TITLE, zorder=5)

    # ── Loop background ──
    _box(ax, 8.25, 4.0, 16.0, 8.0, C_LOOP_BG, C_LOOP_BD, lw=1.0, zorder=0)
    ax.text(8.25, 7.7, "Mutate \u2013 Dock \u2013 QC \u2013 Critique \u2013 Report  Loop",
            ha="center", va="center", fontsize=11, color="#90A4AE",
            fontstyle="italic", zorder=1)

    # ══════════════════════════════════════════════════════════
    # BOX SIZES
    # ══════════════════════════════════════════════════════════
    aw, ah = 2.9, 1.2    # agent
    pw, ph = 3.2, 1.0    # process

    # ══════════════════════════════════════════════════════════
    # TOP ROW — Planner → Candidate Generation → Simulation
    # ══════════════════════════════════════════════════════════
    ty = 6.5

    px = 2.8
    agent(ax, px, ty, aw, ah, "Planner",
          ["Mutation strategy", "Prior-iteration feedback"])

    gx = 8.0
    proc(ax, gx, ty, pw, ph, "Candidate Generation",
         "SST14-based mutation proposals")

    sx = 14.0
    proc(ax, sx, ty, pw, ph, "Simulation",
         "PyRosetta FlexPepDock refinement")

    g = 0.1
    arr(ax, px + aw/2 + g, ty, gx - pw/2 - g, ty)
    lbl(ax, (px + aw/2 + gx - pw/2) / 2, ty + 0.78, "Mutation strategy")

    arr(ax, gx + pw/2 + g, ty, sx - pw/2 - g, ty)
    lbl(ax, (gx + pw/2 + sx - pw/2) / 2, ty + 0.68, "Mutant candidates")

    # ══════════════════════════════════════════════════════════
    # RIGHT: Simulation → QCRanker (down)
    # ══════════════════════════════════════════════════════════
    by_ = 2.0

    qx = 14.0
    agent(ax, qx, by_, aw, ah, "QCRanker",
          ["\u0394G / clash gate", "Rule-based ranking"])

    arr(ax, sx, ty - ph/2 - g, qx, by_ + ah/2 + g)
    lbl(ax, sx + 1.15, (ty - ph/2 + by_ + ah/2) / 2, "\u0394G + clash scores")

    # ══════════════════════════════════════════════════════════
    # BOTTOM ROW — QCRanker → DiversityMgr → Critic → Reporter
    # ══════════════════════════════════════════════════════════
    dmx = 10.0
    agent(ax, dmx, by_, aw + 0.5, ah, "DiversityManager",
          ["Duplicate suppression", "Mutation-bias control"])

    cx = 6.0
    agent(ax, cx, by_, aw, ah, "Critic",
          ["Failure-pattern analysis", "Improvement points"])

    rx = 2.4
    agent(ax, rx, by_, aw, ah, "Reporter",
          ["Structured logs", "Top candidates + rationale"])

    arr(ax, qx - aw/2 - g, by_, dmx + (aw+0.5)/2 + g, by_)
    lbl(ax, (qx - aw/2 + dmx + (aw+0.5)/2) / 2, by_ - 0.88, "Ranked candidates")

    arr(ax, dmx - (aw+0.5)/2 - g, by_, cx + aw/2 + g, by_)
    lbl(ax, (dmx - (aw+0.5)/2 + cx + aw/2) / 2, by_ - 0.88, "Diversified set")

    arr(ax, cx - aw/2 - g, by_, rx + aw/2 + g, by_)
    lbl(ax, (cx - aw/2 + rx + aw/2) / 2, by_ - 0.88, "Critique report")

    # ══════════════════════════════════════════════════════════
    # FEEDBACK — Reporter → Planner (dashed blue, up left side)
    # ══════════════════════════════════════════════════════════
    arr(ax, rx + 0.1, by_ + ah/2 + g,
        px - 0.1, ty - ah/2 - g,
        color=C_FEEDBACK, lw=2.2, ls="--")
    ax.text(rx - 1.15, (by_ + ah/2 + ty - ah/2) / 2,
            "Feedback +\niteration context",
            ha="center", va="center",
            fontsize=9, color=C_FEEDBACK, fontstyle="italic", zorder=5)

    # ── Save ──
    out_dir = ("/home/helloworld/Documents/workspace/repos/PRST_N_FM/"
               "AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/docs")
    os.makedirs(out_dir, exist_ok=True)
    for fmt in ("svg", "png"):
        path = os.path.join(out_dir, f"system_architecture.{fmt}")
        fig.savefig(path, format=fmt, bbox_inches="tight", facecolor=C_BG, dpi=300)
        print(f"{fmt.upper()}: {path}")
    plt.close(fig)


if __name__ == "__main__":
    main()
