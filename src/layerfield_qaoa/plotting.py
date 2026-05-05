from __future__ import annotations

from pathlib import Path
from typing import cast

import matplotlib.pyplot as plt
import numpy as np

from .reporting import compute_regret
from .results import SearchTrace


_METHOD_LABELS = {
    "classical_markowitz": "Classical",
    "random": "Random",
    "spsa": "SPSA",
    "bayesian_optimization": "BO",
}


def _artifact_path(prefix: Path, suffix: str) -> Path:
    return Path(f"{prefix}{suffix}")


def _study_value_sort_key(value: object) -> tuple[int, float | str]:
    if isinstance(value, (int, float, np.integer, np.floating)):
        return (0, float(value))
    return (1, str(value))


def plot_results(traces: dict[str, SearchTrace], prefix: Path) -> None:
    reference = min(min(trace.raw_objective_history) for trace in traces.values())
    simple = {}
    cumulative = {}
    for method, trace in traces.items():
        simple[method], cumulative[method] = compute_regret(trace.raw_objective_history, reference)

    fig, axes = plt.subplots(3, 2, figsize=(13, 12))
    for method, trace in traces.items():
        label = _METHOD_LABELS.get(method, method)
        axes[0, 0].plot(trace.raw_objective_history, label=label)
        axes[0, 1].plot(simple[method], label=label)
        axes[1, 0].plot(cumulative[method], label=label)
        axes[1, 1].plot(trace.best_valid_history, label=label)
        axes[2, 0].plot(trace.valid_ratio_history, label=label)
        axes[2, 1].plot(trace.variance_history, label=label)

    axes[0, 0].set_title("Best-so-far CVaR objective")
    axes[0, 1].set_title("Simple regret")
    axes[1, 0].set_title("Cumulative regret")
    axes[1, 1].set_title("Best valid energy")
    axes[2, 0].set_title("Valid ratio over time")
    axes[2, 1].set_title("Objective variance over time")

    for ax in axes.ravel():
        ax.set_xlabel("Evaluation")
        ax.grid(alpha=0.3)
        ax.legend()
    axes[0, 0].set_ylabel("Objective")
    axes[0, 1].set_ylabel("Regret")
    axes[1, 0].set_ylabel("Cumulative regret")
    axes[1, 1].set_ylabel("Feasible energy")
    axes[2, 0].set_ylabel("Valid ratio")
    axes[2, 1].set_ylabel("Variance")

    plt.tight_layout()
    plt.savefig(_artifact_path(prefix, ".png"), dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_suite_dashboard(aggregated_rows: list[dict[str, object]], output_path: Path) -> None:
    studies = sorted({str(row["study_name"]) for row in aggregated_rows})
    if not studies:
        return
    fig, axes = plt.subplots(len(studies), 2, figsize=(16, 4.8 * len(studies)), squeeze=False, gridspec_kw={"width_ratios": [1.8, 1.0]})
    for row_idx, study in enumerate(studies):
        subset = [row for row in aggregated_rows if str(row["study_name"]) == study]
        values = sorted({row["study_value"] for row in subset}, key=_study_value_sort_key)
        methods = [method for method in _METHOD_LABELS if any(str(row["method"]) == method for row in subset)]
        extra_methods = sorted({str(row["method"]) for row in subset if str(row["method"]) not in _METHOD_LABELS})
        methods.extend(extra_methods)
        line_ax = axes[row_idx, 0]
        heat_ax = axes[row_idx, 1]
        heatmap = np.full((len(methods), len(values)), np.nan, dtype=float)
        for method in methods:
            ys = []
            method_idx = methods.index(method)
            for value_idx, value in enumerate(values):
                row = next((item for item in subset if item["study_value"] == value and str(item["method"]) == method), None)
                if row is None:
                    ys.append(np.nan)
                    continue
                y = float(cast(float, row["mean_best_raw_objective"]))
                heatmap[method_idx, value_idx] = float(row.get("win_rate", float("nan")))
                ys.append(np.nan if not np.isfinite(y) else y)
            line_ax.plot([str(value) for value in values], ys, marker="o", label=_METHOD_LABELS.get(method, method))
        line_ax.set_title(f"Mean raw objective by {study}")
        line_ax.set_xlabel(study)
        line_ax.set_ylabel("Mean raw objective")
        line_ax.grid(alpha=0.3)
        line_ax.legend()

        im = heat_ax.imshow(heatmap, aspect="auto", cmap="YlGnBu", vmin=0.0, vmax=1.0)
        heat_ax.set_title(f"Win-rate matrix by {study}")
        heat_ax.set_xlabel(study)
        heat_ax.set_ylabel("Method")
        heat_ax.set_xticks(range(len(values)))
        heat_ax.set_xticklabels([str(value) for value in values], rotation=45, ha="right")
        heat_ax.set_yticks(range(len(methods)))
        heat_ax.set_yticklabels([_METHOD_LABELS.get(method, method) for method in methods])
        if heatmap.size <= 48:
            for method_idx in range(len(methods)):
                for value_idx in range(len(values)):
                    value = heatmap[method_idx, value_idx]
                    if np.isfinite(value):
                        heat_ax.text(value_idx, method_idx, f"{100.0 * value:.0f}%", ha="center", va="center", fontsize=8, color="black")
        fig.colorbar(im, ax=heat_ax, fraction=0.046, pad=0.04, label="Win rate")
    plt.tight_layout()
    plt.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_mixer_crossover(crossover_rows: list[dict[str, object]], output_path: Path) -> None:
    if not crossover_rows:
        return
    hardness_values = sorted({float(row["constraint_hardness"]) for row in crossover_rows})
    noise_values = sorted({float(row["depolarizing_strength_2q"]) for row in crossover_rows})
    if not hardness_values or not noise_values:
        return
    matrix = np.full((len(noise_values), len(hardness_values)), np.nan, dtype=float)
    labels = np.full((len(noise_values), len(hardness_values)), "", dtype=object)
    for row in crossover_rows:
        x_idx = hardness_values.index(float(row["constraint_hardness"]))
        y_idx = noise_values.index(float(row["depolarizing_strength_2q"]))
        matrix[y_idx, x_idx] = float(row.get("mean_mixer_delta", float("nan")))
        labels[y_idx, x_idx] = str(row.get("winner_mixer", ""))

    fig, ax = plt.subplots(figsize=(10, 4.8))
    im = ax.imshow(matrix, aspect="auto", cmap="RdYlBu", interpolation="nearest")
    ax.set_title("Mixer crossover by constraint hardness and 2q noise")
    ax.set_xlabel("Constraint hardness H(n, B)")
    ax.set_ylabel("2q depolarizing strength")
    ax.set_xticks(range(len(hardness_values)))
    ax.set_xticklabels([f"{value:.3f}" for value in hardness_values], rotation=45, ha="right")
    ax.set_yticks(range(len(noise_values)))
    ax.set_yticklabels([f"{value:.3f}" for value in noise_values])
    for y_idx in range(len(noise_values)):
        for x_idx in range(len(hardness_values)):
            if np.isfinite(matrix[y_idx, x_idx]):
                ax.text(
                    x_idx,
                    y_idx,
                    f"{labels[y_idx, x_idx]}\n{matrix[y_idx, x_idx]:.3f}",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="black",
                )
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="product_x - xy best-raw delta")
    plt.tight_layout()
    plt.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


__all__ = ['plot_results', 'plot_suite_dashboard', 'plot_mixer_crossover']
