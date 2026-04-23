from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import numpy as np
from scipy.stats import mannwhitneyu

from .config import RunSpec
from .constants import BOOTSTRAP_SEEDS, PAYLOAD_SCHEMA_VERSION, RESEARCH_QUESTION
from .landscape import QUBOSpectralProfile
from .qubo import PortfolioInstance
from .results import SearchTrace
from .native import bootstrap_mean_ci_native


METHOD_COMPARISON_ORDER = [
    "classical_markowitz",
    "random",
    "spsa",
    "bayesian_optimization",
]

MIXER_COMPARISON_ORDER = ["xy", "product_x"]


def _artifact_path(prefix: Path, suffix: str) -> Path:
    return Path(f"{prefix}{suffix}")


def compute_regret(history: list[float], reference: float) -> tuple[list[float], list[float]]:
    simple = [value - reference for value in history]
    cumulative = []
    running = 0.0
    for value in simple:
        running += value
        cumulative.append(running)
    return simple, cumulative


def _method_label(method: str) -> str:
    return {
        "classical_markowitz": "Classical Markowitz",
        "random": "Random Search",
        "spsa": "SPSA",
        "bayesian_optimization": "Bayesian Optimization",
    }.get(method, method)


def _finite_values(values: list[float]) -> list[float]:
    out = []
    for val in values:
        f = float(val)
        if np.isfinite(f):
            out.append(f)
    return out


def _mean_preserving_inf(values: list[float]) -> float:
    if not values:
        return float("nan")
    arr = [float(v) for v in values]
    if all(np.isposinf(arr)):
        return float("inf")
    finite = _finite_values(arr)
    if not finite:
        return float("nan")
    return mean(finite)


def _bootstrap_ci(values: list[float], resamples: int, seed: int) -> tuple[float, float]:
    finite = _finite_values(values)
    if not finite:
        return float("nan"), float("nan")
    if len(finite) == 1:
        return float(finite[0]), float(finite[0])
    arr = np.asarray(finite, dtype=float)
    native = bootstrap_mean_ci_native(arr, resamples, seed)
    if native is not None:
        return native
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(arr), size=(resamples, len(arr)))
    means = arr[idx].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def _mann_whitney_pvalue(values_a: list[float], values_b: list[float]) -> float:
    finite_a = _finite_values(values_a)
    finite_b = _finite_values(values_b)
    if len(finite_a) < 2 or len(finite_b) < 2:
        return float("nan")
    try:
        result = mannwhitneyu(finite_a, finite_b, alternative="two-sided")
    except ValueError:
        return float("nan")
    return float(result.pvalue)


def _fmt_metric(value: Any, digits: int = 4) -> str:
    try:
        f = float(value)
    except Exception:
        return str(value)
    if np.isnan(f):
        return "NA"
    if np.isposinf(f):
        return "inf"
    if np.isneginf(f):
        return "-inf"
    return f"{f:.{digits}f}"


def _row_float(row: dict[str, Any], key: str, default: float = float("nan")) -> float:
    value = row.get(key, default)
    try:
        return float(value)
    except Exception:
        return float(default)


def _mean_or_nan(values: list[float]) -> float:
    finite = _finite_values(values)
    if not finite:
        return float("nan")
    return float(mean(finite))


def _parse_violation_counts(value: Any) -> dict[int, int]:
    if isinstance(value, dict):
        return {int(key): int(val) for key, val in value.items()}
    if isinstance(value, str) and value:
        try:
            payload = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(payload, dict):
            return {int(key): int(val) for key, val in payload.items()}
    return {}


def _merge_violation_count_rows(rows: list[dict[str, Any]]) -> dict[int, int]:
    merged: dict[int, int] = {}
    for row in rows:
        for key, value in _parse_violation_counts(row.get("violation_counts", {})).items():
            merged[key] = merged.get(key, 0) + value
    return dict(sorted(merged.items()))


def _pairwise_mann_whitney(samples_by_method: dict[str, list[float]]) -> dict[tuple[str, str], tuple[float, float]]:
    raw: dict[tuple[str, str], float] = {}
    finite_tests = 0
    methods = [method for method in METHOD_COMPARISON_ORDER if method in samples_by_method]
    for idx, method_a in enumerate(methods):
        for method_b in methods[idx + 1:]:
            p_value = _mann_whitney_pvalue(samples_by_method[method_a], samples_by_method[method_b])
            raw[(method_a, method_b)] = p_value
            if np.isfinite(p_value):
                finite_tests += 1
    corrected: dict[tuple[str, str], tuple[float, float]] = {}
    for method in methods:
        corrected[(method, method)] = (1.0, 1.0)
    bonferroni_factor = max(finite_tests, 1)
    for (method_a, method_b), p_value in raw.items():
        adjusted = float(min(1.0, p_value * bonferroni_factor)) if np.isfinite(p_value) else float("nan")
        corrected[(method_a, method_b)] = (p_value, adjusted)
        corrected[(method_b, method_a)] = (p_value, adjusted)
    return corrected


def _method_cost_efficiency(summary: dict[str, Any]) -> float:
    score = float(summary["best_raw_objective"])
    billed = float(summary.get("total_estimated_billed_seconds", 0.0))
    cost = float(summary.get("total_estimated_qpu_cost_usd", 0.0))
    return score + 0.01 * billed + cost


def generate_single_run_insights(cfg: RunSpec, instance: PortfolioInstance, traces: dict[str, SearchTrace]) -> list[str]:
    method_summaries = {name: trace.as_summary() for name, trace in traces.items()}
    if not method_summaries:
        return []

    winner = min(method_summaries.items(), key=lambda kv: kv[1]["best_raw_objective"])
    feasible = max(method_summaries.items(), key=lambda kv: kv[1]["feasible_hit_rate"])
    cheapest = min(method_summaries.items(), key=lambda kv: _method_cost_efficiency(kv[1]))

    insights = [
        f"On regime={cfg.regime}, {_method_label(winner[0])} achieved the best raw objective {_fmt_metric(winner[1]['best_raw_objective'])}.",
        (
            f"Feasibility was strongest for {_method_label(feasible[0])} with feasible-hit rate "
            f"{feasible[1]['feasible_hit_rate']:.2%} and best valid energy {_fmt_metric(feasible[1]['best_valid_energy'])}."
        ),
    ]
    if instance.exact_feasible_energy is None:
        insights.append(
            "The exact feasible reference was not computed for this run, so approximation-gap metrics are intentionally reported as NA instead of silently falling back."
        )
    else:
        insights[0] = (
            f"On regime={cfg.regime}, {_method_label(winner[0])} achieved the best raw objective "
            f"({_fmt_metric(winner[1]['best_raw_objective'])}) relative to the exact feasible reference "
            f"({_fmt_metric(instance.exact_feasible_energy)})."
        )

    if cheapest[0] != winner[0]:
        insights.append(
            f"{_method_label(cheapest[0])} was the cheapest quality-adjusted method once billed time and estimated QPU cost were included, highlighting the difference between best score and best practical tradeoff."
        )

    if cfg.bo_target == "feasibility_aware":
        insights.append(
            "The BO path was configured with a feasibility-aware target, so the benchmark explicitly tests whether sophisticated search is learning portfolio quality or just surfing penalty walls."
        )

    if cfg.execution_mode != "fast_simulator":
        insights.append(
            f"This run used execution_mode={cfg.execution_mode} with topology={cfg.transpile_topology}, so the result includes backend-aware transpilation and cost accounting rather than an idealized sweep only."
        )

    return insights


def generate_project_positioning(cfg: RunSpec) -> dict[str, Any]:
    return {
        "research_question": RESEARCH_QUESTION,
        "what_this_project_is": (
            "A hardware-aware benchmark platform for constrained QAOA portfolio optimization rather than a one-off demo or toy VQE script."
        ),
        "technical_contributions": [
            "Multi-regime synthetic portfolio generator with exact feasible references on small instances.",
            "Constraint-aware QAOA benchmark with CVaR-style objectives, feasibility tracking, and valid-ratio histories.",
            "Strict runtime accounting across objective calls, effective shots, transpilation time, execution time, queue latency, and estimated billed QPU cost.",
            "Fair optimizer comparison across a classical Markowitz baseline, Random Search, SPSA, and Bayesian Optimization with periodic-safe surrogate handling for QAOA angles.",
            "Per-instance QUBO structure diagnostics including constraint hardness and simple spectral-profile summaries.",
        ],
        "why_it_is_interesting": (
            "It lets the user study when sophisticated classical search is actually worth its real hybrid-loop overhead, instead of assuming better optimization always means better practical performance."
        ),
        "current_run_context": {
            "regime": cfg.regime,
            "execution_mode": cfg.execution_mode,
            "noise_model": cfg.noise_model,
            "mixer_type": cfg.mixer_type,
            "p_layers": cfg.p_layers,
        },
    }


def build_run_payload(
    cfg: RunSpec,
    instance: PortfolioInstance,
    traces: dict[str, SearchTrace],
    spectral_profile: QUBOSpectralProfile | None = None,
) -> dict[str, Any]:
    empirical_reference = min(min(trace.raw_objective_history) for trace in traces.values())
    method_payload = {name: trace.as_summary() for name, trace in traces.items()}
    return {
        "schema_version": PAYLOAD_SCHEMA_VERSION,
        "project_positioning": generate_project_positioning(cfg),
        "config": asdict(cfg),
        "regime_characteristics": {
            "regime": cfg.regime,
            "n_assets": cfg.n_assets,
            "budget": cfg.budget,
            "shots": cfg.shots,
            "p_layers": cfg.p_layers,
            "execution_mode": cfg.execution_mode,
            "execution_billing_mode": cfg.execution_billing_mode,
            "job_queue_latency_seconds": cfg.job_queue_latency_seconds,
            "noise_model": cfg.noise_model,
            "measurement_mitigation": cfg.measurement_mitigation,
            "zne_mitigation": cfg.zne_mitigation,
            "twirling": cfg.twirling,
            "resilience_level": cfg.resilience_level,
            "transpile_topology": cfg.transpile_topology,
            "routing_method": cfg.routing_method,
            "seed_transpiler": cfg.seed_transpiler,
            "calibration_aware_routing": cfg.calibration_aware_routing,
            "bo_max_gp_dim": cfg.bo_max_gp_dim,
            "bo_high_dim_strategy": cfg.bo_high_dim_strategy,
            "periodic_parameter_wrap": cfg.periodic_parameter_wrap,
            "qpu_pricing_tier": cfg.qpu_pricing_tier,
            "qpu_price_per_second_usd": cfg.qpu_price_per_second_usd,
            "qpu_billing_basis": cfg.qpu_billing_basis,
        },
        "exact_feasible_energy": instance.exact_feasible_energy,
        "exact_reference_available": instance.exact_feasible_energy is not None,
        "exact_reference_warning": (
            None
            if instance.exact_feasible_energy is not None
            else f"Exact feasible reference disabled for n_assets={cfg.n_assets}; raise exact_reference_max_assets to restore it."
        ),
        "qubo_profile": asdict(spectral_profile) if spectral_profile is not None else None,
        "empirical_reference": empirical_reference,
        "methods": method_payload,
        "single_run_insights": generate_single_run_insights(cfg, instance, traces),
    }


def save_summary(
    cfg: RunSpec,
    instance: PortfolioInstance,
    traces: dict[str, SearchTrace],
    prefix: Path,
    spectral_profile: QUBOSpectralProfile | None = None,
) -> dict[str, Any]:
    payload = build_run_payload(cfg, instance, traces, spectral_profile=spectral_profile)
    _artifact_path(prefix, ".json").write_text(json.dumps(payload, indent=2))
    return payload


def flatten_run_for_csv(study_name: str, study_value: Any, seed: int, payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    method_summaries = payload["methods"]
    best_value = min(summary["best_raw_objective"] for summary in method_summaries.values())
    winners = [name for name, summary in method_summaries.items() if summary["best_raw_objective"] == best_value]
    winner_share = 1.0 / len(winners)
    for method, summary in method_summaries.items():
        rows.append(
            {
                "study_name": study_name,
                "study_value": study_value,
                "seed": seed,
                "regime": payload["config"]["regime"],
                "n_assets": payload["config"]["n_assets"],
                "budget": payload["config"]["budget"],
                "execution_mode": payload["config"]["execution_mode"],
                "execution_billing_mode": payload["config"]["execution_billing_mode"],
                "noise_model": payload["config"]["noise_model"],
                "depolarizing_strength_1q": payload["config"]["depolarizing_strength_1q"],
                "depolarizing_strength_2q": payload["config"]["depolarizing_strength_2q"],
                "measurement_error": payload["config"]["measurement_error"],
                "transpile_topology": payload["config"]["transpile_topology"],
                "mixer_type": payload["config"]["mixer_type"],
                "p_layers": payload["config"]["p_layers"],
                "evaluation_budget": payload["config"]["evaluation_budget"],
                "n_init_points": payload["config"]["n_init_points"],
                "shots": payload["config"]["shots"],
                "cvar_alpha": payload["config"]["cvar_alpha"],
                "invalid_penalty": payload["config"]["invalid_penalty"],
                "method": method,
                "best_raw_objective": summary["best_raw_objective"],
                "best_valid_energy": summary["best_valid_energy"],
                "feasible_hit_rate": summary["feasible_hit_rate"],
                "mean_objective_variance": summary["mean_objective_variance"],
                "mean_approx_gap": summary["mean_approx_gap"],
                "best_approx_ratio": summary.get("best_approx_ratio", float("nan")),
                "mean_approx_ratio": summary.get("mean_approx_ratio", float("nan")),
                "best_valid_regret_auc": summary.get("best_valid_regret_auc", float("nan")),
                "best_valid_energy_per_shot": summary.get("best_valid_energy_per_shot", float("nan")),
                "best_valid_energy_per_usd": summary.get("best_valid_energy_per_usd", float("nan")),
                "mean_shot_noise_variance_proxy": summary.get("mean_shot_noise_variance_proxy", 0.0),
                "mean_excess_variance": summary.get("mean_excess_variance", 0.0),
                "best_valid_sharpe_ratio": summary.get("best_valid_sharpe_ratio", float("nan")),
                "mean_best_valid_sharpe_ratio": summary.get("mean_best_valid_sharpe_ratio", float("nan")),
                "mean_budget_violation": summary.get("mean_budget_violation", 0.0),
                "violation_counts": json.dumps(summary.get("violation_counts", {}), sort_keys=True),
                "mean_zne_correction_magnitude": summary.get("mean_zne_correction_magnitude", 0.0),
                "shots_to_first_feasible": summary.get("shots_to_first_feasible", float("inf")),
                "elapsed_seconds": summary["elapsed_seconds"],
                "total_objective_calls": summary["total_objective_calls"],
                "effective_shots": summary.get("total_effective_shots", 0.0),
                "estimated_billed_seconds": summary.get("total_estimated_billed_seconds", 0.0),
                "estimated_qpu_cost_usd": summary.get("total_estimated_qpu_cost_usd", 0.0),
                "win_share": winner_share if method in winners else 0.0,
                "exact_reference_available": payload.get("exact_reference_available", False),
                "constraint_hardness": (payload.get("qubo_profile") or {}).get("constraint_hardness", float("nan")),
                "penalty_doublings": (payload.get("qubo_profile") or {}).get("penalty_doublings", 0),
                "best_params": json.dumps(summary.get("best_params", [])),
            }
        )
    return rows


_MIXER_PAIR_FIELDS = (
    "study_name",
    "seed",
    "regime",
    "n_assets",
    "budget",
    "execution_mode",
    "execution_billing_mode",
    "noise_model",
    "depolarizing_strength_1q",
    "depolarizing_strength_2q",
    "measurement_error",
    "transpile_topology",
    "p_layers",
    "evaluation_budget",
    "n_init_points",
    "shots",
    "cvar_alpha",
    "invalid_penalty",
    "method",
)

_MIXER_BALANCE_FIELDS = (
    "study_name",
    "regime",
    "n_assets",
    "budget",
    "execution_mode",
    "noise_model",
    "depolarizing_strength_2q",
    "p_layers",
    "evaluation_budget",
    "shots",
    "cvar_alpha",
    "invalid_penalty",
)


def build_mixer_dominance_rows(rows: list[dict[str, Any]], metric: str = "best_raw_objective") -> list[dict[str, Any]]:
    paired: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        mixer = str(row.get("mixer_type", ""))
        if mixer not in MIXER_COMPARISON_ORDER:
            continue
        key = tuple(row.get(field) for field in _MIXER_PAIR_FIELDS)
        paired[key][mixer] = row

    out: list[dict[str, Any]] = []
    for key, mixer_rows in paired.items():
        if not {"xy", "product_x"}.issubset(mixer_rows):
            continue
        xy_row = mixer_rows["xy"]
        product_x_row = mixer_rows["product_x"]
        xy_metric = _row_float(xy_row, metric)
        product_x_metric = _row_float(product_x_row, metric)
        delta = float(product_x_metric - xy_metric) if np.isfinite(xy_metric) and np.isfinite(product_x_metric) else float("nan")
        if np.isnan(delta):
            winner = "undetermined"
        elif delta > 1e-12:
            winner = "xy"
        elif delta < -1e-12:
            winner = "product_x"
        else:
            winner = "tie"
        row_out = {field: value for field, value in zip(_MIXER_PAIR_FIELDS, key, strict=True)}
        row_out.update(
            {
                "metric_name": metric,
                "xy_metric": xy_metric,
                "product_x_metric": product_x_metric,
                "mixer_delta": delta,
                "better_mixer": winner,
                "constraint_hardness": _row_float(xy_row, "constraint_hardness"),
                "penalty_doublings_xy": _row_float(xy_row, "penalty_doublings", 0.0),
                "penalty_doublings_product_x": _row_float(product_x_row, "penalty_doublings", 0.0),
            }
        )
        out.append(row_out)
    return sorted(
        out,
        key=lambda item: (
            str(item.get("study_name")),
            str(item.get("regime")),
            float(item.get("n_assets", 0.0)),
            float(item.get("depolarizing_strength_2q", 0.0)),
            str(item.get("method")),
            float(item.get("seed", 0.0)),
        ),
    )


def aggregate_mixer_dominance_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    group_fields = tuple(field for field in _MIXER_PAIR_FIELDS if field != "seed")
    for row in rows:
        key = tuple(row.get(field) for field in group_fields)
        grouped[key].append(row)

    out: list[dict[str, Any]] = []
    for key, group in grouped.items():
        deltas = [_row_float(item, "mixer_delta") for item in group]
        xy_metrics = [_row_float(item, "xy_metric") for item in group]
        product_x_metrics = [_row_float(item, "product_x_metric") for item in group]
        wins_xy = sum(1 for item in group if str(item.get("better_mixer")) == "xy")
        wins_product_x = sum(1 for item in group if str(item.get("better_mixer")) == "product_x")
        row_out = {field: value for field, value in zip(group_fields, key, strict=True)}
        row_out.update(
            {
                "runs": len(group),
                "mean_xy_metric": _mean_or_nan(xy_metrics),
                "mean_product_x_metric": _mean_or_nan(product_x_metrics),
                "mean_mixer_delta": _mean_or_nan(deltas),
                "abs_mean_mixer_delta": abs(_mean_or_nan(deltas)) if _finite_values(deltas) else float("nan"),
                "xy_win_rate": wins_xy / len(group),
                "product_x_win_rate": wins_product_x / len(group),
                "mean_constraint_hardness": _mean_or_nan([_row_float(item, "constraint_hardness") for item in group]),
            }
        )
        row_out["better_mixer"] = (
            "xy"
            if wins_xy > wins_product_x
            else "product_x"
            if wins_product_x > wins_xy
            else "tie"
        )
        out.append(row_out)
    return sorted(
        out,
        key=lambda item: (
            str(item.get("study_name")),
            str(item.get("regime")),
            float(item.get("n_assets", 0.0)),
            float(item.get("depolarizing_strength_2q", 0.0)),
            str(item.get("method")),
        ),
    )


def build_mixer_optimizer_balance_rows(rows: list[dict[str, Any]], metric: str = "best_raw_objective") -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = tuple(row.get(field) for field in _MIXER_BALANCE_FIELDS)
        grouped[key].append(row)

    out: list[dict[str, Any]] = []
    for key, group in grouped.items():
        method_cells: dict[tuple[str, str], list[float]] = defaultdict(list)
        for row in group:
            mixer = str(row.get("mixer_type", ""))
            method = str(row.get("method", ""))
            if mixer not in MIXER_COMPARISON_ORDER or method not in METHOD_COMPARISON_ORDER:
                continue
            value = _row_float(row, metric)
            if np.isfinite(value):
                method_cells[(mixer, method)].append(value)
        if not method_cells:
            continue
        xy_values = [_mean_or_nan(method_cells[("xy", method)]) for method in METHOD_COMPARISON_ORDER if ("xy", method) in method_cells]
        product_x_values = [_mean_or_nan(method_cells[("product_x", method)]) for method in METHOD_COMPARISON_ORDER if ("product_x", method) in method_cells]
        if not xy_values or not product_x_values:
            continue
        mean_xy = _mean_or_nan(xy_values)
        mean_product_x = _mean_or_nan(product_x_values)
        mixer_effect = abs(mean_xy - mean_product_x)
        optimizer_effect = mean(
            [
                max(values) - min(values)
                for values in [xy_values, product_x_values]
                if len(values) >= 2
            ]
        ) if any(len(values) >= 2 for values in [xy_values, product_x_values]) else 0.0
        row_out = {field: value for field, value in zip(_MIXER_BALANCE_FIELDS, key, strict=True)}
        row_out.update(
            {
                "metric_name": metric,
                "mean_xy_metric": mean_xy,
                "mean_product_x_metric": mean_product_x,
                "mixer_effect": mixer_effect,
                "optimizer_effect": float(optimizer_effect),
                "dominant_factor": (
                    "mixer"
                    if mixer_effect > optimizer_effect + 1e-12
                    else "optimizer"
                    if optimizer_effect > mixer_effect + 1e-12
                    else "tie"
                ),
                "better_mixer": (
                    "xy"
                    if mean_xy < mean_product_x - 1e-12
                    else "product_x"
                    if mean_product_x < mean_xy - 1e-12
                    else "tie"
                ),
                "mean_constraint_hardness": _mean_or_nan([_row_float(item, "constraint_hardness") for item in group]),
            }
        )
        out.append(row_out)
    return sorted(
        out,
        key=lambda item: (
            str(item.get("study_name")),
            str(item.get("regime")),
            float(item.get("n_assets", 0.0)),
            float(item.get("depolarizing_strength_2q", 0.0)),
        ),
    )


def build_mixer_variance_summary(rows: list[dict[str, Any]], metric: str = "best_raw_objective") -> dict[str, Any]:
    finite_rows = [
        row for row in rows
        if np.isfinite(_row_float(row, metric))
        and str(row.get("mixer_type", "")) in MIXER_COMPARISON_ORDER
        and str(row.get("method", "")) in METHOD_COMPARISON_ORDER
    ]
    if not finite_rows:
        return {
            "metric_name": metric,
            "row_count": 0,
            "variance_explained": {},
            "mixer_method_interaction_share": float("nan"),
        }
    values = np.asarray([_row_float(row, metric) for row in finite_rows], dtype=float)
    grand_mean = float(values.mean())
    total_ss = float(np.sum((values - grand_mean) ** 2))
    if total_ss <= 1e-12:
        total_ss = 1e-12

    def _factor_share(field: str) -> float:
        buckets: dict[str, list[float]] = defaultdict(list)
        for row in finite_rows:
            buckets[str(row.get(field, "NA"))].append(_row_float(row, metric))
        ss = 0.0
        for bucket_values in buckets.values():
            arr = np.asarray(bucket_values, dtype=float)
            ss += float(arr.size * (float(arr.mean()) - grand_mean) ** 2)
        return float(ss / total_ss)

    by_mixer: dict[str, list[float]] = defaultdict(list)
    by_method: dict[str, list[float]] = defaultdict(list)
    by_cell: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in finite_rows:
        mixer = str(row.get("mixer_type"))
        method = str(row.get("method"))
        value = _row_float(row, metric)
        by_mixer[mixer].append(value)
        by_method[method].append(value)
        by_cell[(mixer, method)].append(value)
    ss_interaction = 0.0
    for (mixer, method), cell_values in by_cell.items():
        arr = np.asarray(cell_values, dtype=float)
        cell_mean = float(arr.mean())
        mixer_mean = float(np.mean(by_mixer[mixer]))
        method_mean = float(np.mean(by_method[method]))
        ss_interaction += float(arr.size * (cell_mean - mixer_mean - method_mean + grand_mean) ** 2)

    return {
        "metric_name": metric,
        "row_count": len(finite_rows),
        "variance_explained": {
            "mixer_type": _factor_share("mixer_type"),
            "method": _factor_share("method"),
            "regime": _factor_share("regime"),
        },
        "mixer_method_interaction_share": float(ss_interaction / total_ss),
    }


def build_mixer_winner_crossover_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[float, float], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        hardness = _row_float(row, "constraint_hardness")
        noise = _row_float(row, "depolarizing_strength_2q")
        if np.isfinite(hardness) and np.isfinite(noise):
            grouped[(hardness, noise)].append(row)

    out: list[dict[str, Any]] = []
    for (hardness, noise), group in grouped.items():
        deltas = [_row_float(item, "mixer_delta") for item in group]
        mean_delta = _mean_or_nan(deltas)
        if np.isnan(mean_delta):
            winner = "undetermined"
        elif mean_delta > 1e-12:
            winner = "xy"
        elif mean_delta < -1e-12:
            winner = "product_x"
        else:
            winner = "tie"
        out.append(
            {
                "constraint_hardness": hardness,
                "depolarizing_strength_2q": noise,
                "mean_mixer_delta": mean_delta,
                "winner_mixer": winner,
                "samples": len(group),
            }
        )
    return sorted(out, key=lambda item: (float(item["depolarizing_strength_2q"]), float(item["constraint_hardness"])))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_mixer_dominance_report(
    path: Path,
    mixer_rows: list[dict[str, Any]],
    balance_rows: list[dict[str, Any]],
    variance_summary: dict[str, Any],
    crossover_rows: list[dict[str, Any]],
) -> None:
    lines = ["# Mixer Dominance Analysis", ""]
    shares = variance_summary.get("variance_explained", {})
    if shares:
        lines.extend(
            [
                "## Variance Summary",
                "",
                f"- Mixer-type share (marginal proxy): {_fmt_metric(shares.get('mixer_type', float('nan')), 4)}",
                f"- Optimizer share (marginal proxy): {_fmt_metric(shares.get('method', float('nan')), 4)}",
                f"- Regime share (marginal proxy): {_fmt_metric(shares.get('regime', float('nan')), 4)}",
                f"- Mixer×optimizer interaction share: {_fmt_metric(variance_summary.get('mixer_method_interaction_share', float('nan')), 4)}",
                "",
            ]
        )
    if balance_rows:
        mixer_dominant = sum(1 for row in balance_rows if row.get("dominant_factor") == "mixer")
        optimizer_dominant = sum(1 for row in balance_rows if row.get("dominant_factor") == "optimizer")
        lines.extend(
            [
                "## Factor Balance",
                "",
                f"- Contexts where mixer effect exceeds optimizer effect: {mixer_dominant}",
                f"- Contexts where optimizer effect exceeds mixer effect: {optimizer_dominant}",
                "",
            ]
        )
    if crossover_rows:
        lines.extend(["## H / Noise Crossover", "", "| Constraint hardness | 2q depolarizing | Winner | Mean delta (product_x - xy) | Samples |", "|---:|---:|---|---:|---:|"])
        for row in crossover_rows:
            lines.append(
                f"| {_fmt_metric(row['constraint_hardness'], 4)} | {_fmt_metric(row['depolarizing_strength_2q'], 4)} | "
                f"{row['winner_mixer']} | {_fmt_metric(row['mean_mixer_delta'], 4)} | {int(row['samples'])} |"
            )
        lines.append("")
    if mixer_rows:
        strongest = max(
            mixer_rows,
            key=lambda item: abs(float(item.get("mean_mixer_delta", float("nan")))) if np.isfinite(float(item.get("mean_mixer_delta", float("nan")))) else -1.0,
        )
        lines.extend(
            [
                "## Strongest Observed Mixer Shift",
                "",
                f"- Regime: {strongest.get('regime')}",
                f"- Method: {strongest.get('method')}",
                f"- n_assets: {strongest.get('n_assets')}",
                f"- Better mixer: {strongest.get('better_mixer')}",
                f"- Mean delta (product_x - xy): {_fmt_metric(strongest.get('mean_mixer_delta', float('nan')), 4)}",
                "",
            ]
        )
    path.write_text("\n".join(lines))


def aggregate_suite_rows(rows: list[dict[str, Any]], resamples: int = 1000) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_study_value: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["study_name"], row["study_value"], row["method"])].append(row)
        by_study_value[(row["study_name"], row["study_value"])].append(row)
    out: list[dict[str, Any]] = []
    for (study_name, study_value, method), group in grouped.items():
        study_group = by_study_value[(study_name, study_value)]
        method_samples = {
            candidate_method: [_row_float(item, "best_valid_energy") for item in candidate_group]
            for candidate_method, candidate_group in (
                (candidate_method, [row for row in study_group if row["method"] == candidate_method])
                for candidate_method in {row["method"] for row in study_group}
            )
        }
        pairwise = _pairwise_mann_whitney(method_samples)

        raw_values = [_row_float(item, "best_raw_objective") for item in group]
        feasible_values = [_row_float(item, "feasible_hit_rate", 0.0) for item in group]
        win_values = [_row_float(item, "win_share", 0.0) for item in group]
        elapsed_values = [_row_float(item, "elapsed_seconds", 0.0) for item in group]
        billed_values = [_row_float(item, "estimated_billed_seconds", 0.0) for item in group]
        cost_values = [_row_float(item, "estimated_qpu_cost_usd", 0.0) for item in group]
        best_valid_values = [_row_float(item, "best_valid_energy") for item in group]
        approx_gap_values = [_row_float(item, "mean_approx_gap") for item in group]
        approx_ratio_values = [_row_float(item, "best_approx_ratio") for item in group]
        regret_auc_values = [_row_float(item, "best_valid_regret_auc") for item in group]
        per_shot_values = [_row_float(item, "best_valid_energy_per_shot") for item in group]
        per_usd_values = [_row_float(item, "best_valid_energy_per_usd") for item in group]
        sharpe_values = [_row_float(item, "best_valid_sharpe_ratio") for item in group]
        shot_noise_values = [_row_float(item, "mean_shot_noise_variance_proxy", 0.0) for item in group]
        excess_values = [_row_float(item, "mean_excess_variance", 0.0) for item in group]
        budget_violation_values = [_row_float(item, "mean_budget_violation", 0.0) for item in group]
        zne_values = [_row_float(item, "mean_zne_correction_magnitude", 0.0) for item in group]
        effective_shot_values = [_row_float(item, "effective_shots", 0.0) for item in group]
        first_feasible_values = [_row_float(item, "shots_to_first_feasible") for item in group]
        penalty_doubling_values = [_row_float(item, "penalty_doublings", 0.0) for item in group]
        constraint_hardness_values = [_row_float(item, "constraint_hardness") for item in group]

        raw_ci = _bootstrap_ci(raw_values, resamples=resamples, seed=BOOTSTRAP_SEEDS['raw'])
        feasible_ci = _bootstrap_ci(feasible_values, resamples=resamples, seed=BOOTSTRAP_SEEDS['feasible'])
        win_ci = _bootstrap_ci(win_values, resamples=resamples, seed=BOOTSTRAP_SEEDS['win'])
        elapsed_ci = _bootstrap_ci(elapsed_values, resamples=resamples, seed=41)
        billed_ci = _bootstrap_ci(billed_values, resamples=resamples, seed=43)
        cost_ci = _bootstrap_ci(cost_values, resamples=resamples, seed=47)
        first_feasible_ci = _bootstrap_ci(first_feasible_values, resamples=resamples, seed=53)
        row_out = {
            "study_name": study_name,
            "study_value": study_value,
            "method": method,
            "runs": len(group),
            "mean_best_raw_objective": mean(raw_values),
            "std_best_raw_objective": pstdev(raw_values) if len(group) > 1 else 0.0,
            "mean_best_valid_energy": _mean_preserving_inf(best_valid_values),
            "mean_feasible_hit_rate": mean(feasible_values),
            "mean_approx_gap": _mean_preserving_inf(approx_gap_values),
            "mean_best_approx_ratio": _mean_preserving_inf(approx_ratio_values),
            "mean_best_valid_regret_auc": _mean_preserving_inf(regret_auc_values),
            "mean_best_valid_energy_per_shot": _mean_preserving_inf(per_shot_values),
            "mean_best_valid_energy_per_usd": _mean_preserving_inf(per_usd_values),
            "mean_best_valid_sharpe_ratio": _mean_or_nan(sharpe_values),
            "mean_shot_noise_variance_proxy": _mean_or_nan(shot_noise_values),
            "mean_excess_variance": _mean_or_nan(excess_values),
            "mean_budget_violation": mean(budget_violation_values),
            "aggregate_violation_counts": json.dumps(_merge_violation_count_rows(group), sort_keys=True),
            "mean_zne_correction_magnitude": mean(zne_values),
            "mean_shots_to_first_feasible": _mean_preserving_inf(first_feasible_values),
            "mean_elapsed_seconds": mean(elapsed_values),
            "mean_effective_shots": mean(effective_shot_values),
            "mean_estimated_billed_seconds": mean(billed_values),
            "mean_estimated_qpu_cost_usd": mean(cost_values),
            "mean_penalty_doublings": mean(penalty_doubling_values),
            "mean_constraint_hardness": _mean_or_nan(constraint_hardness_values),
            "win_rate": mean(win_values),
            "ci95_best_raw_objective_low": raw_ci[0],
            "ci95_best_raw_objective_high": raw_ci[1],
            "ci95_feasible_hit_rate_low": feasible_ci[0],
            "ci95_feasible_hit_rate_high": feasible_ci[1],
            "ci95_win_rate_low": win_ci[0],
            "ci95_win_rate_high": win_ci[1],
            "ci95_elapsed_seconds_low": elapsed_ci[0],
            "ci95_elapsed_seconds_high": elapsed_ci[1],
            "ci95_estimated_billed_seconds_low": billed_ci[0],
            "ci95_estimated_billed_seconds_high": billed_ci[1],
            "ci95_estimated_qpu_cost_usd_low": cost_ci[0],
            "ci95_estimated_qpu_cost_usd_high": cost_ci[1],
            "ci95_shots_to_first_feasible_low": first_feasible_ci[0],
            "ci95_shots_to_first_feasible_high": first_feasible_ci[1],
        }
        for other_method in METHOD_COMPARISON_ORDER:
            p_value, adjusted = pairwise.get((method, other_method), (float("nan"), float("nan")))
            row_out[f"p_value_best_valid_vs_{other_method}"] = p_value
            row_out[f"p_value_best_valid_vs_{other_method}_bonferroni"] = adjusted
        row_out["p_value_vs_random_best_valid"] = row_out.get("p_value_best_valid_vs_random", float("nan"))
        row_out["p_value_vs_random_best_valid_bonferroni"] = row_out.get(
            "p_value_best_valid_vs_random_bonferroni",
            float("nan"),
        )
        out.append(row_out)
    return sorted(out, key=lambda item: (item["study_name"], str(item["study_value"]), item["method"]))


def generate_suite_claims(rows: list[dict[str, Any]]) -> list[str]:
    claims: list[str] = []
    by_study_value: dict[tuple[str, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_study_value[(row["study_name"], row["study_value"])].append(row)
    for (study_name, study_value), group in sorted(by_study_value.items(), key=lambda item: (item[0][0], str(item[0][1]))):
        winner = min(group, key=lambda item: item["mean_best_raw_objective"])
        claims.append(
            f"For {study_name}={study_value}, {_method_label(winner['method'])} has the best mean raw objective "
            f"({_fmt_metric(winner['mean_best_raw_objective'])}, bootstrap 95% CI {_fmt_metric(winner['ci95_best_raw_objective_low'])}–{_fmt_metric(winner['ci95_best_raw_objective_high'])})."
        )
        win_leader = max(group, key=lambda item: item["win_rate"])
        if win_leader["method"] != winner["method"]:
            claims.append(
                f"For {study_name}={study_value}, seed-level win rate favors {_method_label(win_leader['method'])} "
                f"({win_leader['win_rate']:.2%}), showing a stability-versus-mean-performance split."
            )
        feasible = max(group, key=lambda item: item["mean_feasible_hit_rate"])
        if feasible["method"] != winner["method"]:
            claims.append(
                f"For {study_name}={study_value}, feasibility favors {_method_label(feasible['method'])} "
                f"({feasible['mean_feasible_hit_rate']:.2%}) even though the raw-objective winner is {_method_label(winner['method'])}."
            )
        significant = [
            item for item in group
            if item["method"] != "random"
            and np.isfinite(float(item.get("p_value_vs_random_best_valid_bonferroni", float("nan"))))
            and float(item["p_value_vs_random_best_valid_bonferroni"]) < 0.05
        ]
        for item in significant:
            claims.append(
                f"For {study_name}={study_value}, {_method_label(item['method'])} differs significantly from Random Search on best-valid energy after Bonferroni correction (Mann-Whitney U p={_fmt_metric(item['p_value_vs_random_best_valid_bonferroni'], 4)})."
            )
        cheapest = min(group, key=lambda item: item["mean_estimated_qpu_cost_usd"] + item["mean_elapsed_seconds"])
        if cheapest["method"] != winner["method"]:
            claims.append(
                f"For {study_name}={study_value}, {_method_label(cheapest['method'])} is cheapest by estimated runtime cost plus elapsed time, showing where sophisticated search may not justify its overhead."
            )
    return claims


def generate_suite_research_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "research_question": RESEARCH_QUESTION,
            "headline_answer": "No suite rows were available.",
            "contributions_demonstrated": [],
            "evidence_summary": [],
            "application_ready_summary": "No benchmark evidence was produced.",
        }

    best_overall = min(rows, key=lambda item: item["mean_best_raw_objective"])
    strongest_feasibility = max(rows, key=lambda item: item["mean_feasible_hit_rate"])
    strongest_cost = min(rows, key=lambda item: item["mean_estimated_qpu_cost_usd"] + item["mean_elapsed_seconds"])
    headline = (
        f"Across the completed suite, {_method_label(best_overall['method'])} delivered the strongest mean objective on "
        f"{best_overall['study_name']}={best_overall['study_value']}, while {_method_label(strongest_cost['method'])} provided the best cost-adjusted tradeoff on at least one study point."
    )
    evidence = [
        f"Best mean raw objective: {_method_label(best_overall['method'])} on {best_overall['study_name']}={best_overall['study_value']} with {_fmt_metric(best_overall['mean_best_raw_objective'])}.",
        f"Strongest feasibility: {_method_label(strongest_feasibility['method'])} reached mean feasible-hit rate {strongest_feasibility['mean_feasible_hit_rate']:.2%}.",
        f"Best cost-adjusted method: {_method_label(strongest_cost['method'])} minimized estimated cost plus elapsed time most effectively.",
    ]
    app_summary = (
        "This benchmark demonstrates the ability to build a reproducible, hardware-aware research instrument that connects constrained QAOA physics, optimizer design, and runtime-cost accounting into a single comparative framework."
    )
    return {
        "research_question": RESEARCH_QUESTION,
        "headline_answer": headline,
        "contributions_demonstrated": [
            "Constraint-aware QAOA benchmarking across multiple synthetic portfolio regimes.",
            "Fair optimizer comparison under shared runtime, shot, and billing accounting.",
            "Structured exports that preserve both benchmark claims and per-evaluation evidence.",
        ],
        "evidence_summary": evidence,
        "application_ready_summary": app_summary,
    }


def write_markdown_report(path: Path, title: str, aggregated_rows: list[dict[str, Any]], claims: list[str], research_summary: dict[str, Any] | None = None) -> None:
    summary = generate_suite_research_summary(aggregated_rows) if research_summary is None else research_summary
    lines = [f"# {title}", "", "## Research question", "", summary["research_question"], "", "## Why this benchmark matters", "", summary["headline_answer"], ""]
    if summary.get("contributions_demonstrated"):
        lines.extend(["## Technical contributions demonstrated", ""])
        for item in summary["contributions_demonstrated"]:
            lines.append(f"- {item}")
        lines.append("")
    if summary.get("evidence_summary"):
        lines.extend(["## Evidence summary", ""])
        for item in summary["evidence_summary"]:
            lines.append(f"- {item}")
        lines.append("")
    lines.extend(["## Headline claims", ""])
    for claim in claims:
        lines.append(f"- {claim}")
    lines.extend(
        [
            "",
            "## Aggregated results",
            "",
            "| Study | Value | Method | Mean raw objective | 95% CI raw | Mean approx ratio | Regret AUC | Best-valid/shot | Sharpe | Win rate | Feasible hit rate | p vs random (adj.) | Mean elapsed s | 95% CI elapsed | Mean billed s |",
            "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in aggregated_rows:
        lines.append(
            f"| {row['study_name']} | {row['study_value']} | {_method_label(row['method'])} | {_fmt_metric(row['mean_best_raw_objective'])} | "
            f"[{_fmt_metric(row['ci95_best_raw_objective_low'])}, {_fmt_metric(row['ci95_best_raw_objective_high'])}] | "
            f"{_fmt_metric(row.get('mean_best_approx_ratio', float('nan')))} | {_fmt_metric(row.get('mean_best_valid_regret_auc', float('nan')))} | "
            f"{_fmt_metric(row.get('mean_best_valid_energy_per_shot', float('nan')), 6)} | {_fmt_metric(row.get('mean_best_valid_sharpe_ratio', float('nan')))} | "
            f"{row['win_rate']:.2%} | {row['mean_feasible_hit_rate']:.2%} | "
            f"{_fmt_metric(row.get('p_value_vs_random_best_valid_bonferroni', float('nan')), 4)} | "
            f"{_fmt_metric(row['mean_elapsed_seconds'], 3)} | "
            f"[{_fmt_metric(row.get('ci95_elapsed_seconds_low', float('nan')), 3)}, {_fmt_metric(row.get('ci95_elapsed_seconds_high', float('nan')), 3)}] | "
            f"{_fmt_metric(row['mean_estimated_billed_seconds'], 3)} |"
        )
    lines.extend(["", "## Application-ready summary", "", summary["application_ready_summary"], ""])
    path.write_text("\n".join(lines))


__all__ = [
    'RESEARCH_QUESTION', 'compute_regret', 'generate_single_run_insights',
    'generate_project_positioning', 'build_run_payload', 'save_summary',
    'flatten_run_for_csv', 'build_mixer_dominance_rows', 'aggregate_mixer_dominance_rows',
    'build_mixer_optimizer_balance_rows', 'build_mixer_variance_summary',
    'build_mixer_winner_crossover_rows', 'write_csv', 'write_mixer_dominance_report', 'aggregate_suite_rows',
    'generate_suite_claims', 'generate_suite_research_summary', 'write_markdown_report',
]
