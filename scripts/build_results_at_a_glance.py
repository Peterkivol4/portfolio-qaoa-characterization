#!/usr/bin/env python3
"""Build lightweight reviewer-facing summary artifacts from committed results."""

from __future__ import annotations

import csv
import textwrap
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
FIGURES_DIR = DOCS_DIR / "figures"
SUITE_AGGREGATED = ROOT / "results" / "multi_regime_suite" / "suite_aggregated.csv"
SUITE_DASHBOARD = ROOT / "results" / "multi_regime_suite" / "suite_dashboard.png"
MIXER_SUMMARY = ROOT / "results" / "mixer_dominance_pilot_v2" / "mixer_dominance_summary.csv"

DECISION_MAP_PNG = FIGURES_DIR / "decision_map.png"
RESULTS_AT_A_GLANCE_PDF = DOCS_DIR / "results_at_a_glance.pdf"
RESULTS_AT_A_GLANCE_PNG = DOCS_DIR / "results_at_a_glance.png"

METHOD_LABELS = {
    "classical_markowitz": "Classical",
    "bayesian_optimization": "BO",
    "random": "Random",
    "spsa": "SPSA",
    "tie": "Tie",
}
METHOD_COLORS = {
    "classical_markowitz": "#2E8B57",
    "bayesian_optimization": "#3A78C2",
    "random": "#D98C2B",
    "spsa": "#8A57B4",
    "tie": "#9A9A9A",
}


def load_suite_rows() -> list[dict[str, str]]:
    with SUITE_AGGREGATED.open(newline="") as handle:
        return list(csv.DictReader(handle))


def load_mixer_counts() -> Counter[str]:
    with MIXER_SUMMARY.open(newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["method"] != "classical_markowitz"]
    return Counter(row["better_mixer"] for row in rows)


def best_methods_by_study(
    rows: list[dict[str, str]],
    study_name: str,
    *,
    metric: str,
    higher_is_better: bool,
) -> dict[str, str]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["study_name"] == study_name:
            grouped[row["study_value"]].append(row)

    best: dict[str, str] = {}
    for value, subset in grouped.items():
        scores = [(row["method"], float(row[metric])) for row in subset]
        extreme = max(score for _, score in scores) if higher_is_better else min(score for _, score in scores)
        winners = sorted(method for method, score in scores if abs(score - extreme) <= 1e-12)
        best[value] = winners[0] if len(winners) == 1 else "tie"
    return best


def sorted_study_values(study_name: str, values: set[str]) -> list[str]:
    if study_name == "regime":
        preferred = [
            "baseline",
            "clustered_assets",
            "hard_budget",
            "high_correlation",
            "low_correlation",
            "sparse_covariance",
        ]
        return [value for value in preferred if value in values]
    return sorted(values, key=lambda value: float(value))


def humanize_value(study_name: str, value: str) -> str:
    if study_name == "regime":
        return value.replace("_", "\n")
    if study_name == "asset_scale":
        return f"n={value}"
    if study_name == "eval_budget":
        return f"evals={value}"
    return value


def build_decision_map(rows: list[dict[str, str]]) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    study_specs = [
        ("regime", "Best Mean Raw Objective by Regime"),
        ("asset_scale", "Best Mean Raw Objective by Asset Count"),
        ("eval_budget", "Best Mean Raw Objective by Evaluation Budget"),
    ]

    fig, axes = plt.subplots(len(study_specs), 1, figsize=(12.5, 7.6))
    cmap = ListedColormap([METHOD_COLORS[key] for key in ["classical_markowitz", "bayesian_optimization", "random", "spsa", "tie"]])
    color_index = {key: idx for idx, key in enumerate(["classical_markowitz", "bayesian_optimization", "random", "spsa", "tie"])}

    for ax, (study_name, title) in zip(axes, study_specs, strict=True):
        values = sorted_study_values(study_name, {row["study_value"] for row in rows if row["study_name"] == study_name})
        winners = best_methods_by_study(rows, study_name, metric="mean_best_raw_objective", higher_is_better=False)
        encoded = [[color_index[winners[value]] for value in values]]
        ax.imshow(encoded, aspect="auto", cmap=cmap, vmin=0, vmax=len(color_index) - 1)
        ax.set_title(title, fontsize=12, loc="left", pad=10)
        ax.set_yticks([])
        ax.set_xticks(range(len(values)))
        ax.set_xticklabels([humanize_value(study_name, value) for value in values], fontsize=9)
        for col, value in enumerate(values):
            winner = winners[value]
            ax.text(
                col,
                0,
                METHOD_LABELS[winner],
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
                color="white" if winner in {"classical_markowitz", "bayesian_optimization", "spsa"} else "black",
            )

    legend_handles = [
        Patch(facecolor=METHOD_COLORS[key], label=METHOD_LABELS[key])
        for key in ["classical_markowitz", "bayesian_optimization", "random", "spsa", "tie"]
    ]
    fig.legend(handles=legend_handles, loc="upper center", ncol=5, frameon=False, bbox_to_anchor=(0.5, 0.985))
    fig.suptitle(
        "PortfolioQAOA Decision Map\nBroad-suite raw-objective winners stay classical; feasibility in this retained artifact is a four-way tie at 100%.",
        fontsize=14,
        fontweight="bold",
        y=0.94,
    )
    fig.text(
        0.01,
        0.02,
        "Quantum-only rider: in the mixer pilot, xy wins 17/24 quantum-only paired summaries, with 6 ties and 1 product_x win.",
        fontsize=10,
    )
    fig.subplots_adjust(top=0.82, bottom=0.10, hspace=0.45)
    fig.savefig(DECISION_MAP_PNG, dpi=220, bbox_inches="tight")
    plt.close(fig)


def add_bullets(
    ax: plt.Axes,
    x: float,
    y: float,
    lines: list[str],
    *,
    fontsize: float = 11.5,
    line_step: float = 0.045,
    wrap_width: int = 78,
) -> float:
    for line in lines:
        wrapped = textwrap.fill(line, width=wrap_width, initial_indent="- ", subsequent_indent="  ")
        ax.text(x, y, wrapped, fontsize=fontsize, va="top", ha="left")
        y -= line_step * (wrapped.count("\n") + 1)
    return y


def build_results_at_a_glance(rows: list[dict[str, str]]) -> None:
    mixer_counts = load_mixer_counts()
    study_values: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        study_values[row["study_name"]].add(row["study_value"])
    raw_winners = Counter(
        best_methods_by_study(rows, study_name, metric="mean_best_raw_objective", higher_is_better=False)[study_value]
        for study_name, study_value in {(row["study_name"], row["study_value"]) for row in rows}
    )
    total_slices = len({(row["study_name"], row["study_value"]) for row in rows})

    fig = plt.figure(figsize=(11.0, 8.5))
    title_ax = fig.add_axes([0.06, 0.86, 0.88, 0.12])
    title_ax.axis("off")
    title_ax.text(0.0, 1.0, "PortfolioQAOA: Results at a Glance", fontsize=22, fontweight="bold", va="top")
    title_ax.text(
        0.0,
        0.56,
        "Question: when is a more sophisticated classical optimizer worth its runtime, shot, queue, and mitigation cost for constrained QAOA portfolio optimization?",
        fontsize=12.5,
        va="top",
    )
    title_ax.text(
        0.0,
        0.12,
        "Built from the committed broad suite and mixer pilot artifacts under results/.",
        fontsize=11,
        va="top",
        color="#444444",
    )

    left_ax = fig.add_axes([0.06, 0.12, 0.46, 0.70])
    left_ax.axis("off")
    right_text_ax = fig.add_axes([0.56, 0.50, 0.38, 0.32])
    right_text_ax.axis("off")
    right_image_ax = fig.add_axes([0.56, 0.12, 0.38, 0.30])
    right_image_ax.axis("off")

    y = 1.0
    left_ax.text(0.0, y, "Experimental grid", fontsize=14, fontweight="bold", va="top")
    y -= 0.07
    y = add_bullets(
        left_ax,
        0.0,
        y,
        [
            f"Broad suite reported {total_slices} study slices across {len(study_values['regime'])} regimes, {len(study_values['asset_scale'])} asset scales, {len(study_values['depth'])} depth settings, {len(study_values['eval_budget'])} evaluation budgets, {len(study_values['shot_budget'])} shot budgets, {len(study_values['cvar_alpha'])} CVaR settings, and {len(study_values['invalid_penalty'])} invalid-penalty settings.",
            "Methods compared in the broad suite: Classical Markowitz, Random Search, SPSA, and Bayesian Optimization.",
            "Separate mixer pilot: 24 quantum-only paired summaries across mixer type, regime hardness, asset count, and 2q depolarizing noise.",
        ],
        wrap_width=62,
        line_step=0.055,
    )
    y -= 0.03
    left_ax.text(0.0, y, "Top findings", fontsize=14, fontweight="bold", va="top")
    y -= 0.07
    add_bullets(
        left_ax,
        0.0,
        y,
        [
            f"Classical Markowitz is the raw-objective winner in all {raw_winners['classical_markowitz']} reported broad-suite study slices.",
            "In the retained broad-suite artifact, feasibility is already saturated: every method reaches a 100% mean feasible-hit rate, so BO does not win by feasibility alone there.",
            f"In the mixer pilot, xy wins {mixer_counts['xy']}/24 quantum-only paired summaries, with {mixer_counts['tie']} ties and {mixer_counts['product_x']} product_x wins.",
        ],
        wrap_width=62,
        line_step=0.060,
    )

    y = 1.0
    right_text_ax.text(0.0, y, "Caveats", fontsize=14, fontweight="bold", va="top")
    y -= 0.09
    add_bullets(
        right_text_ax,
        0.0,
        y,
        [
            "This repo does not claim quantum advantage; the committed broad suite is explicitly negative in that sense.",
            "The broad suite is a characterization artifact, not a general live-hardware performance proof; live IBM results exist, but they are narrower than the suite.",
            "Exact-reference gaps are only available where exact enumeration is enabled; larger instances rely on best-valid tracking rather than hidden ground truth.",
        ],
        wrap_width=48,
        line_step=0.070,
    )

    if DECISION_MAP_PNG.exists():
        right_image_ax.imshow(plt.imread(DECISION_MAP_PNG))
        right_image_ax.set_title("Decision-map artifact", fontsize=12, loc="left", pad=8)

    fig.text(
        0.06,
        0.04,
        "Read next: docs/decision_map.md | docs/when_bo_was_not_worth_it.md | results/multi_regime_suite/suite_report.md",
        fontsize=10.5,
    )

    fig.savefig(RESULTS_AT_A_GLANCE_PDF, bbox_inches="tight")
    fig.savefig(RESULTS_AT_A_GLANCE_PNG, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    rows = load_suite_rows()
    build_decision_map(rows)
    build_results_at_a_glance(rows)
    print(f"Wrote {DECISION_MAP_PNG}")
    print(f"Wrote {RESULTS_AT_A_GLANCE_PDF}")
    print(f"Wrote {RESULTS_AT_A_GLANCE_PNG}")


if __name__ == "__main__":
    main()
