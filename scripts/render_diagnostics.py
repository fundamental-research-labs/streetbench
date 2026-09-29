#!/usr/bin/env python3
"""Render case-level Street comparisons from released aggregate counts only."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams["svg.hashsalt"] = "streetbench-paired-outcomes-v1"

ROOT = Path(__file__).resolve().parents[1]
HARNESSES = ("Shortcut", "Codex", "Codex + GPT Researcher")
MODELS = ("Luna", "Sol", "Astra")
COLORS = {"closer_than_street": "#278666", "same_absolute_error": "#c5cbd3",
          "farther_than_street": "#d8776a"}
LABELS = {"closer_than_street": "Closer", "same_absolute_error": "Same error",
          "farther_than_street": "Farther"}


def main():
    data = json.loads((ROOT / "results/diagnostics.json").read_text())
    rows = {(row["harness"], row["model"]): row for row in data["rows"]}
    if set(rows) != {(h, m) for h in HARNESSES for m in MODELS}:
        raise ValueError("Expected nine harness and model combinations")
    if any(sum(row[key] for key in COLORS) != 200 for row in rows.values()):
        raise ValueError("Every case-level comparison must total 200")

    fig, ax = plt.subplots(figsize=(11.3, 6.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    fig.subplots_adjust(left=0.43, right=0.95, top=0.76, bottom=0.18)
    positions, labels = [], []
    for group, harness in enumerate(HARNESSES):
        for model_index, model in enumerate(MODELS):
            y = group * 4 + model_index
            row = rows[(harness, model)]
            left = 0
            for key in COLORS:
                count = row[key]
                ax.barh(y, count, left=left, height=0.67, color=COLORS[key], zorder=3)
                if count:
                    ax.text(left + count / 2, y, str(count), ha="center", va="center",
                            color="#ffffff" if key != "same_absolute_error" else "#334155",
                            fontsize=7 if count < 10 else 9, fontweight="bold")
                left += count
            positions.append(y)
            labels.append(model)
        ax.text(-0.73, group * 4 + 1, harness, transform=ax.get_yaxis_transform(),
                va="center", ha="left", fontsize=11, fontweight="bold",
                color="#17293b", clip_on=False)

    ax.set_yticks(positions, labels)
    ax.tick_params(axis="y", length=0, pad=11, labelsize=10, colors="#26374b")
    ax.tick_params(axis="x", length=0, labelsize=9, colors="#56677a")
    ax.set_xlim(0, 200)
    ax.set_xticks([0, 50, 100, 150, 200])
    ax.invert_yaxis()
    ax.grid(axis="x", color="#e2e6eb", linewidth=0.8, zorder=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlabel("Companies out of 200", fontsize=10, color="#26374b", labelpad=10)
    fig.text(0.05, 0.94, "Where agents beat the Street", fontsize=17,
             fontweight="bold", color="#17293b")
    fig.text(0.05, 0.89, "Forecast absolute EPS error versus final Street consensus on the same case",
             fontsize=10, color="#56677a")
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLORS[key]) for key in COLORS]
    fig.legend(handles, [LABELS[key] for key in COLORS], loc="upper right",
               bbox_to_anchor=(0.96, 0.87), frameon=False, ncol=3, fontsize=9)
    fig.text(0.05, 0.06, "Exploratory retrospective comparison. Bars count wins, ties, and losses. MAE also depends on their size.",
             fontsize=9, color="#56677a")
    for extension in ("png", "svg"):
        path = ROOT / f"graphs/paired-outcomes.{extension}"
        fig.savefig(path, dpi=170, facecolor="white",
                    metadata={"Creator": "Streetbench aggregate diagnostics renderer",
                              "Date": "2026-09-29"})
        if extension == "svg":
            path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
    plt.close(fig)


if __name__ == "__main__":
    main()
