#!/usr/bin/env python3
"""Render the nine-configuration EPS comparison from aggregate scores only."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
matplotlib.rcParams["svg.hashsalt"] = "streetbench-nine-configurations-v1"

ROOT = Path(__file__).resolve().parents[1]
COLORS = {"Luna": "#e48622", "Sol": "#386fe8", "Astra": "#9a70b3"}
HARNESSES = ("Shortcut", "Codex", "Codex + GPT Researcher")
MODELS = ("Luna", "Sol", "Astra")


def main():
    rows = json.loads((ROOT / "results/scores.json").read_text())["rows"]
    by_key = {(row["harness"], row["model"]): row for row in rows}
    expected = {(harness, model) for harness in HARNESSES for model in MODELS}
    if set(by_key) != expected:
        raise ValueError("Expected one score for each of the nine configurations")

    fig, ax = plt.subplots(figsize=(11.4, 6.8))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    fig.subplots_adjust(left=0.45, right=0.94, top=0.79, bottom=0.19)

    positions = []
    labels = []
    for group, harness in enumerate(HARNESSES):
        for model_index, model in enumerate(MODELS):
            y = group * 4 + model_index
            row = by_key[harness, model]
            reduction = 100 * row["improvement_over_street"] / row["street_mae"]
            ax.barh(y, reduction, height=0.66, color=COLORS[model], zorder=3)
            ax.text(reduction + 0.28, y, f"{reduction:.1f}%",
                    va="center", ha="left", fontsize=10, color="#15233a")
            positions.append(y)
            labels.append(model)
        ax.text(-0.76, group * 4 + 1, harness, transform=ax.get_yaxis_transform(),
                va="center", ha="left", fontsize=11, fontweight="bold",
                color="#15233a", clip_on=False)

    ax.set_yticks(positions, labels)
    ax.tick_params(axis="y", length=0, pad=11, labelsize=10, colors="#25344c")
    ax.tick_params(axis="x", length=0, labelsize=9, colors="#5a687e")
    ax.set_xlim(0, 21)
    ax.set_xticks([0, 5, 10, 15, 20])
    ax.xaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
    ax.invert_yaxis()
    ax.grid(axis="x", color="#dce2e9", linewidth=0.8, zorder=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlabel("Reduction in mean absolute EPS error vs Street · higher is better",
                  fontsize=10, color="#25344c", labelpad=11)

    fig.text(0.055, 0.94, "EPS accuracy across nine agent configurations",
             fontsize=17, fontweight="bold", color="#15233a")
    fig.text(0.055, 0.89,
             "Same 200 companies and answer key · 200 audited usable forecasts per configuration",
             fontsize=10, color="#5a687e")
    fig.text(0.055, 0.075,
             "Exploratory retrospective comparison. Street consensus MAE: $0.1467/share.",
             fontsize=9, color="#5a687e")

    for extension in ("png", "svg"):
        path = ROOT / f"graphs/completed-comparison.{extension}"
        fig.savefig(path,
                    dpi=170, facecolor="white",
                    metadata={"Creator": "Streetbench aggregate graph renderer",
                              "Date": "2026-09-28"})
        if extension == "svg":
            path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
    plt.close(fig)


if __name__ == "__main__":
    main()
