#!/usr/bin/env python3
"""Render the eleven-configuration and five-model Shortcut comparisons from aggregate scores only."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
matplotlib.rcParams["svg.hashsalt"] = "streetbench-newer-models-v1"

ROOT = Path(__file__).resolve().parents[1]
COLORS = {"Luna": "#e48622", "Sol": "#386fe8", "Astra": "#9a70b3",
          "Sol 6.1": "#6b9a1f", "Opus 5.5": "#b8456f"}
HARNESSES = ("Shortcut", "Codex", "Codex + GPT Researcher")
RELEASED_MODELS = ("Luna", "Sol", "Astra")
NEWER_MODELS = ("Sol 6.1", "Opus 5.5")
# Inches, matching scripts/render_results.py (11.4 x 6.8 figure with eleven bar slots).
WIDTH, SLOT, TOP, BOTTOM = 11.4, 0.371, 1.43, 1.29
SUBTITLE = "Same 200 companies and answer key · 200 usable forecasts per configuration"
FOOTER = "Exploratory retrospective comparison. Street consensus MAE: $0.1467/share."


def load():
    released = json.loads((ROOT / "results/scores.json").read_text())["rows"]
    newer = json.loads((ROOT / "results/newer-models.json").read_text())["rows"]
    by_key = {(row["harness"], row["model"]): row for row in released + newer}
    expected = ({(harness, model) for harness in HARNESSES for model in RELEASED_MODELS}
                | {("Shortcut", model) for model in NEWER_MODELS})
    if set(by_key) != expected or len(by_key) != len(released) + len(newer):
        raise ValueError("Expected the nine released configurations plus two newer Shortcut models")
    if any(row["cases"] != 200 or row["valid"] != 200 or abs(row["street_mae"] - 0.1467) > 1e-12
           for row in by_key.values()):
        raise ValueError("Every score must use 200 usable forecasts and the same Street baseline")
    return by_key


def render(by_key, groups, name, title):
    slots = sum(len(models) for _, models in groups) + len(groups) - 1
    height = TOP + BOTTOM + SLOT * slots
    fig, ax = plt.subplots(figsize=(WIDTH, height))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    fig.subplots_adjust(left=0.45, right=0.94, top=1 - TOP / height, bottom=BOTTOM / height)

    positions = []
    labels = []
    start = 0
    for harness, models in groups:
        for model_index, model in enumerate(models):
            y = start + model_index
            row = by_key[harness, model]
            reduction = 100 * row["improvement_over_street"] / row["street_mae"]
            ax.barh(y, reduction, height=0.66, color=COLORS[model], zorder=3)
            ax.text(reduction + 0.28, y, f"{reduction:.1f}%",
                    va="center", ha="left", fontsize=10, color="#15233a")
            positions.append(y)
            labels.append(model)
        ax.text(-0.76, start + (len(models) - 1) / 2, harness, transform=ax.get_yaxis_transform(),
                va="center", ha="left", fontsize=11, fontweight="bold",
                color="#15233a", clip_on=False)
        start += len(models) + 1

    ax.set_yticks(positions, labels)
    ax.set_ylim(-0.6, slots - 0.4)
    ax.tick_params(axis="y", length=0, pad=11, labelsize=10, colors="#25344c")
    ax.tick_params(axis="x", length=0, labelsize=9, colors="#5a687e")
    ax.set_xlim(0, 26)
    ax.set_xticks([0, 5, 10, 15, 20, 25])
    ax.xaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
    ax.invert_yaxis()
    ax.grid(axis="x", color="#dce2e9", linewidth=0.8, zorder=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlabel("Reduction in mean absolute EPS error vs Street · higher is better",
                  fontsize=10, color="#25344c", labelpad=11)

    fig.text(0.055, 1 - 0.41 / height, title,
             fontsize=17, fontweight="bold", color="#15233a")
    fig.text(0.055, 1 - 0.75 / height, SUBTITLE, fontsize=10, color="#5a687e")
    fig.text(0.055, 0.51 / height, FOOTER, fontsize=9, color="#5a687e")

    for extension in ("png", "svg"):
        path = ROOT / f"graphs/{name}.{extension}"
        fig.savefig(path,
                    dpi=170, facecolor="white",
                    metadata={"Creator": "Streetbench aggregate graph renderer",
                              "Date": "2026-10-01"})
        if extension == "svg":
            path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
    plt.close(fig)


def main():
    by_key = load()
    render(by_key, [("Shortcut", RELEASED_MODELS + NEWER_MODELS), ("Codex", RELEASED_MODELS),
                    ("Codex + GPT Researcher", RELEASED_MODELS)], "all-configurations",
           "EPS accuracy across eleven agent configurations")
    render(by_key, [("Shortcut", RELEASED_MODELS + NEWER_MODELS)], "shortcut-models",
           "EPS accuracy across five models in Shortcut")


if __name__ == "__main__":
    main()
