import re
from pathlib import Path

import numpy as np
import pytest

from portfolio_qaoa_bench.config import RunConfig, SuiteConfig
from portfolio_qaoa_bench.objective import project_params
from portfolio_qaoa_bench.pipeline import run_benchmark, run_suite
from portfolio_qaoa_bench.plotting import plot_mixer_crossover, plot_results, plot_suite_dashboard
from portfolio_qaoa_bench.qubo import QuboFactory
from portfolio_qaoa_bench.reporting import (
    aggregate_mixer_dominance_rows,
    aggregate_suite_rows,
    build_mixer_dominance_rows,
    build_mixer_optimizer_balance_rows,
    build_mixer_variance_summary,
    build_mixer_winner_crossover_rows,
    generate_project_positioning,
    generate_single_run_insights,
    generate_suite_claims,
    generate_suite_research_summary,
    write_markdown_report,
)
from portfolio_qaoa_bench.results import SearchTrace, TimingBreakdown


def _dummy_trace(method: str) -> SearchTrace:
    return SearchTrace(
        method=method,
        objective_history=[-1.0, -1.2],
        raw_objective_history=[-1.0, -1.2],
        best_valid_history=[-0.8, -1.1],
        valid_ratio_history=[0.0, 0.5],
        feasible_hit_history=[0.0, 1.0],
        variance_history=[0.1, 0.05],
        approx_gap_history=[float('inf'), 0.2],
        elapsed_seconds=0.01,
        total_objective_calls=2,
        timing_totals=TimingBreakdown(total_seconds=0.01),
    )


_LABEL_TO_METHOD = {
    "Classical Markowitz": "classical_markowitz",
    "Random Search": "random",
    "SPSA": "spsa",
    "Bayesian Optimization": "bayesian_optimization",
}


def test_reporting_handles_empty_rows_and_plotting_is_noop(tmp_path: Path) -> None:
    rows = aggregate_suite_rows([], resamples=50)
    assert rows == []
    claims = generate_suite_claims(rows)
    assert claims == []

    report_path = tmp_path / "empty_report.md"
    write_markdown_report(report_path, "Empty", rows, claims)
    assert report_path.exists()
    assert "# Empty" in report_path.read_text()

    dashboard_path = tmp_path / "empty_dashboard.png"
    plot_suite_dashboard([], dashboard_path)
    assert not dashboard_path.exists()


def test_reporting_handles_all_infeasible_runs() -> None:
    raw_rows = [
        {
            "study_name": "regime",
            "study_value": "hard_budget",
            "method": "random",
            "best_raw_objective": 5.0,
            "best_valid_energy": float("inf"),
            "feasible_hit_rate": 0.0,
            "mean_objective_variance": 0.2,
            "mean_approx_gap": float("inf"),
            "best_approx_ratio": float("nan"),
            "best_valid_regret_auc": float("inf"),
            "best_valid_energy_per_shot": float("inf"),
            "best_valid_energy_per_usd": float("nan"),
            "best_valid_sharpe_ratio": float("nan"),
            "mean_shot_noise_variance_proxy": 0.0,
            "mean_excess_variance": 0.0,
            "mean_budget_violation": 1.0,
            "violation_counts": "{\"1\": 128}",
            "mean_zne_correction_magnitude": 0.0,
            "elapsed_seconds": 0.1,
            "total_objective_calls": 3,
            "effective_shots": 128,
            "estimated_billed_seconds": 0.1,
            "estimated_qpu_cost_usd": 0.0,
            "win_share": 1.0,
            "penalty_doublings": 1,
            "constraint_hardness": 0.1,
            "best_params": "[]",
        }
    ]
    aggregated = aggregate_suite_rows(raw_rows, resamples=50)
    assert len(aggregated) == 1
    assert aggregated[0]["mean_feasible_hit_rate"] == 0.0
    claims = generate_suite_claims(aggregated)
    assert claims


def test_plot_results_writes_png(tmp_path: Path) -> None:
    traces = {
        "classical_markowitz": _dummy_trace("classical_markowitz"),
        "random": _dummy_trace("random"),
        "spsa": _dummy_trace("spsa"),
        "bayesian_optimization": _dummy_trace("bayesian_optimization"),
    }
    prefix = tmp_path / "plot_test.v1"
    plot_results(traces, prefix)
    assert Path(f"{prefix}.png").exists()


def test_project_params_is_vectorized_and_matches_expected() -> None:
    bounds = np.array([[0.0, 0.0], [2.0 * np.pi, np.pi]], dtype=float)
    params = np.array([2.0 * np.pi + 0.3, -0.2], dtype=float)
    wrapped = project_params(params, bounds, periodic_wrap=True)
    clipped = project_params(params, bounds, periodic_wrap=False)
    assert np.allclose(wrapped, np.array([0.3, np.pi - 0.2]))
    assert np.allclose(clipped, np.array([2.0 * np.pi, 0.0]))


def test_project_params_is_idempotent() -> None:
    bounds = np.array([[0.0, 0.0, 0.0, 0.0], [2.0 * np.pi, np.pi, 2.0 * np.pi, np.pi]], dtype=float)
    rng = np.random.default_rng(123)
    for _ in range(100):
        params = rng.normal(size=4) * 10.0
        wrapped_once = project_params(params, bounds, periodic_wrap=True)
        wrapped_twice = project_params(wrapped_once, bounds, periodic_wrap=True)
        assert np.allclose(wrapped_once, wrapped_twice)


def test_measurement_mitigation_guard_rejects_large_bitcount() -> None:
    cfg = RunConfig(
        n_assets=13,
        budget=4,
        execution_mode="aer_sampler",
        backend_name="aer_simulator",
        measurement_mitigation=True,
    )
    with pytest.raises(ValueError, match="measurement_mitigation"):
        cfg.normalized()


def test_measurement_mitigation_falls_back_when_linear_algebra_fails(monkeypatch) -> None:
    import portfolio_qaoa_bench.simulator as sim

    cfg = RunConfig(measurement_mitigation=True, measurement_error=0.01).normalized()
    counts = {"00": 40, "11": 24}

    def _boom(*args, **kwargs):
        raise np.linalg.LinAlgError("SVD did not converge")

    monkeypatch.setattr(sim.np.linalg, "inv", _boom)
    monkeypatch.setattr(sim.np.linalg, "pinv", _boom)
    assert sim._apply_measurement_mitigation(counts, 2, cfg) == counts


def test_degenerate_covariance_is_supported() -> None:
    cfg = RunConfig(n_assets=4, budget=2, risk_aversion=0.6).normalized()
    mu = np.array([0.1, 0.2, 0.15, 0.05], dtype=float)
    sigma = np.zeros((4, 4), dtype=float)
    instance = QuboFactory.build(mu, sigma, cfg)
    assert np.isfinite(instance.exact_feasible_energy)
    assert np.allclose(instance.qubo_matrix, instance.qubo_matrix.T)


def test_run_benchmark_does_not_touch_global_numpy_seed(monkeypatch, tmp_path: Path) -> None:
    import portfolio_qaoa_bench.pipeline as pipeline

    def _raise(*args, **kwargs):
        raise AssertionError("global np.random.seed should not be called")

    monkeypatch.setattr(pipeline.np.random, "seed", _raise)
    cfg = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=1,
        evaluation_budget=3,
        n_init_points=2,
        shots=32,
        output_prefix=str(tmp_path / "single"),
    ).normalized()
    payload = run_benchmark(cfg, verbose=False)
    assert payload["schema_version"] == "1.6"
    assert payload["project_positioning"]["research_question"]
    assert payload["single_run_insights"]


def test_generate_suite_claims_handles_all_infeasible_rows() -> None:
    rows = [
        {
            "study_name": "noise",
            "study_value": "ideal",
            "method": "random",
            "mean_best_raw_objective": 1.2,
            "ci95_best_raw_objective_low": 1.0,
            "ci95_best_raw_objective_high": 1.4,
            "win_rate": 0.5,
            "mean_feasible_hit_rate": 0.0,
            "mean_estimated_qpu_cost_usd": 0.0,
            "mean_elapsed_seconds": 0.1,
        },
        {
            "study_name": "noise",
            "study_value": "ideal",
            "method": "spsa",
            "mean_best_raw_objective": 1.0,
            "ci95_best_raw_objective_low": 0.9,
            "ci95_best_raw_objective_high": 1.1,
            "win_rate": 0.5,
            "mean_feasible_hit_rate": 0.0,
            "mean_estimated_qpu_cost_usd": 0.0,
            "mean_elapsed_seconds": 0.2,
        },
    ]
    claims = generate_suite_claims(rows)
    assert claims


def test_aggregate_suite_rows_keeps_infinite_best_valid_energy() -> None:
    rows = [
        {
            "study_name": "regime",
            "study_value": "hard_budget",
            "seed": 0,
            "method": "random",
            "best_raw_objective": 2.0,
            "best_valid_energy": float("inf"),
            "feasible_hit_rate": 0.0,
            "mean_approx_gap": float("inf"),
            "best_approx_ratio": float("nan"),
            "best_valid_regret_auc": float("inf"),
            "best_valid_energy_per_shot": float("inf"),
            "best_valid_energy_per_usd": float("nan"),
            "best_valid_sharpe_ratio": float("nan"),
            "mean_shot_noise_variance_proxy": 0.0,
            "mean_excess_variance": 0.0,
            "mean_budget_violation": 1.0,
            "violation_counts": "{\"1\": 128}",
            "mean_zne_correction_magnitude": 0.0,
            "elapsed_seconds": 0.1,
            "effective_shots": 128.0,
            "estimated_billed_seconds": 0.1,
            "estimated_qpu_cost_usd": 0.0,
            "win_share": 1.0,
            "penalty_doublings": 1,
            "constraint_hardness": 0.1,
            "best_params": "[]",
        }
    ]
    out = aggregate_suite_rows(rows, resamples=50)
    assert len(out) == 1
    assert out[0]["mean_best_valid_energy"] == float("inf")


def test_reporting_handles_mixed_finite_and_infinite_metrics(tmp_path: Path) -> None:
    rows = [
        {
            "study_name": "budget",
            "study_value": 2,
            "seed": 0,
            "method": "random",
            "best_raw_objective": 1.0,
            "best_valid_energy": float("inf"),
            "feasible_hit_rate": 0.0,
            "mean_approx_gap": float("inf"),
            "best_approx_ratio": float("nan"),
            "best_valid_regret_auc": float("inf"),
            "best_valid_energy_per_shot": float("inf"),
            "best_valid_energy_per_usd": float("nan"),
            "best_valid_sharpe_ratio": float("nan"),
            "mean_shot_noise_variance_proxy": 0.0,
            "mean_excess_variance": 0.0,
            "mean_budget_violation": 1.0,
            "violation_counts": "{\"1\": 64}",
            "mean_zne_correction_magnitude": 0.0,
            "elapsed_seconds": 0.1,
            "effective_shots": 64.0,
            "estimated_billed_seconds": 0.1,
            "estimated_qpu_cost_usd": 0.0,
            "win_share": 0.0,
            "penalty_doublings": 1,
            "constraint_hardness": 0.1,
            "best_params": "[]",
        },
        {
            "study_name": "budget",
            "study_value": 2,
            "seed": 1,
            "method": "random",
            "best_raw_objective": 0.8,
            "best_valid_energy": -0.2,
            "feasible_hit_rate": 0.5,
            "mean_approx_gap": 0.4,
            "best_approx_ratio": 1.2,
            "best_valid_regret_auc": 1.0,
            "best_valid_energy_per_shot": -0.003125,
            "best_valid_energy_per_usd": float("nan"),
            "best_valid_sharpe_ratio": 0.4,
            "mean_shot_noise_variance_proxy": 0.02,
            "mean_excess_variance": 0.03,
            "mean_budget_violation": 0.5,
            "violation_counts": "{\"0\": 32, \"1\": 32}",
            "mean_zne_correction_magnitude": 0.0,
            "elapsed_seconds": 0.2,
            "effective_shots": 64.0,
            "estimated_billed_seconds": 0.2,
            "estimated_qpu_cost_usd": 0.0,
            "win_share": 1.0,
            "penalty_doublings": 1,
            "constraint_hardness": 0.1,
            "best_params": "[]",
        },
    ]
    aggregated = aggregate_suite_rows(rows, resamples=50)
    assert len(aggregated) == 1
    assert np.isfinite(aggregated[0]["mean_best_valid_energy"])
    report_path = tmp_path / "mixed_report.md"
    write_markdown_report(report_path, "Mixed", aggregated, generate_suite_claims(aggregated))
    txt = report_path.read_text()
    assert "Mixed" in txt


def test_plot_suite_dashboard_skips_nonfinite_values(tmp_path: Path) -> None:
    rows = [
        {"study_name": "depth", "study_value": 1, "method": "random", "mean_best_raw_objective": float("inf")},
        {"study_name": "depth", "study_value": 2, "method": "random", "mean_best_raw_objective": 1.0},
    ]
    out = tmp_path / "suite.png"
    plot_suite_dashboard(rows, out)
    assert out.exists()


def test_mixer_dominance_analysis_and_crossover_plot(tmp_path: Path) -> None:
    rows = [
        {
            "study_name": "factorial",
            "study_value": "regime=hard_budget|mixer_type=xy|depolarizing_strength_2q=0.005",
            "seed": 1,
            "regime": "hard_budget",
            "n_assets": 8,
            "budget": 3,
            "execution_mode": "fast_simulator",
            "execution_billing_mode": "job",
            "noise_model": "depolarizing",
            "depolarizing_strength_1q": 0.001,
            "depolarizing_strength_2q": 0.005,
            "measurement_error": 0.01,
            "transpile_topology": "auto",
            "mixer_type": "xy",
            "p_layers": 2,
            "evaluation_budget": 12,
            "n_init_points": 4,
            "shots": 256,
            "cvar_alpha": 0.1,
            "invalid_penalty": 50.0,
            "method": "random",
            "best_raw_objective": -1.20,
            "constraint_hardness": 0.08,
        },
        {
            "study_name": "factorial",
            "study_value": "regime=hard_budget|mixer_type=product_x|depolarizing_strength_2q=0.005",
            "seed": 1,
            "regime": "hard_budget",
            "n_assets": 8,
            "budget": 3,
            "execution_mode": "fast_simulator",
            "execution_billing_mode": "job",
            "noise_model": "depolarizing",
            "depolarizing_strength_1q": 0.001,
            "depolarizing_strength_2q": 0.005,
            "measurement_error": 0.01,
            "transpile_topology": "auto",
            "mixer_type": "product_x",
            "p_layers": 2,
            "evaluation_budget": 12,
            "n_init_points": 4,
            "shots": 256,
            "cvar_alpha": 0.1,
            "invalid_penalty": 50.0,
            "method": "random",
            "best_raw_objective": -1.00,
            "constraint_hardness": 0.08,
        },
        {
            "study_name": "factorial",
            "study_value": "regime=hard_budget|mixer_type=xy|depolarizing_strength_2q=0.020",
            "seed": 1,
            "regime": "hard_budget",
            "n_assets": 8,
            "budget": 3,
            "execution_mode": "fast_simulator",
            "execution_billing_mode": "job",
            "noise_model": "depolarizing",
            "depolarizing_strength_1q": 0.001,
            "depolarizing_strength_2q": 0.020,
            "measurement_error": 0.01,
            "transpile_topology": "auto",
            "mixer_type": "xy",
            "p_layers": 2,
            "evaluation_budget": 12,
            "n_init_points": 4,
            "shots": 256,
            "cvar_alpha": 0.1,
            "invalid_penalty": 50.0,
            "method": "random",
            "best_raw_objective": -0.80,
            "constraint_hardness": 0.08,
        },
        {
            "study_name": "factorial",
            "study_value": "regime=hard_budget|mixer_type=product_x|depolarizing_strength_2q=0.020",
            "seed": 1,
            "regime": "hard_budget",
            "n_assets": 8,
            "budget": 3,
            "execution_mode": "fast_simulator",
            "execution_billing_mode": "job",
            "noise_model": "depolarizing",
            "depolarizing_strength_1q": 0.001,
            "depolarizing_strength_2q": 0.020,
            "measurement_error": 0.01,
            "transpile_topology": "auto",
            "mixer_type": "product_x",
            "p_layers": 2,
            "evaluation_budget": 12,
            "n_init_points": 4,
            "shots": 256,
            "cvar_alpha": 0.1,
            "invalid_penalty": 50.0,
            "method": "random",
            "best_raw_objective": -0.90,
            "constraint_hardness": 0.08,
        },
        {
            "study_name": "factorial",
            "study_value": "regime=hard_budget|mixer_type=xy|depolarizing_strength_2q=0.005",
            "seed": 1,
            "regime": "hard_budget",
            "n_assets": 8,
            "budget": 3,
            "execution_mode": "fast_simulator",
            "execution_billing_mode": "job",
            "noise_model": "depolarizing",
            "depolarizing_strength_1q": 0.001,
            "depolarizing_strength_2q": 0.005,
            "measurement_error": 0.01,
            "transpile_topology": "auto",
            "mixer_type": "xy",
            "p_layers": 2,
            "evaluation_budget": 12,
            "n_init_points": 4,
            "shots": 256,
            "cvar_alpha": 0.1,
            "invalid_penalty": 50.0,
            "method": "spsa",
            "best_raw_objective": -1.15,
            "constraint_hardness": 0.08,
        },
        {
            "study_name": "factorial",
            "study_value": "regime=hard_budget|mixer_type=product_x|depolarizing_strength_2q=0.005",
            "seed": 1,
            "regime": "hard_budget",
            "n_assets": 8,
            "budget": 3,
            "execution_mode": "fast_simulator",
            "execution_billing_mode": "job",
            "noise_model": "depolarizing",
            "depolarizing_strength_1q": 0.001,
            "depolarizing_strength_2q": 0.005,
            "measurement_error": 0.01,
            "transpile_topology": "auto",
            "mixer_type": "product_x",
            "p_layers": 2,
            "evaluation_budget": 12,
            "n_init_points": 4,
            "shots": 256,
            "cvar_alpha": 0.1,
            "invalid_penalty": 50.0,
            "method": "spsa",
            "best_raw_objective": -0.95,
            "constraint_hardness": 0.08,
        },
    ]
    mixer_pairs = build_mixer_dominance_rows(rows)
    assert len(mixer_pairs) == 3
    assert mixer_pairs[0]["better_mixer"] in {"xy", "product_x"}
    mixer_summary = aggregate_mixer_dominance_rows(mixer_pairs)
    assert mixer_summary
    balance = build_mixer_optimizer_balance_rows(rows)
    assert balance
    variance = build_mixer_variance_summary(rows)
    assert variance["variance_explained"]["mixer_type"] >= 0.0
    crossover = build_mixer_winner_crossover_rows(mixer_pairs)
    assert crossover
    out = tmp_path / "mixer_crossover.png"
    plot_mixer_crossover(crossover, out)
    assert out.exists()


def test_research_summary_and_positioning_are_populated() -> None:
    cfg = RunConfig(n_assets=6, budget=2).normalized()
    positioning = generate_project_positioning(cfg)
    assert "research_question" in positioning
    assert positioning["technical_contributions"]

    rows = [
        {
            "study_name": "regime",
            "study_value": "baseline",
            "method": "random",
            "mean_best_raw_objective": -1.0,
            "ci95_best_raw_objective_low": -1.2,
            "ci95_best_raw_objective_high": -0.8,
            "win_rate": 0.4,
            "mean_feasible_hit_rate": 0.5,
            "mean_estimated_qpu_cost_usd": 0.0,
            "mean_elapsed_seconds": 0.1,
        },
        {
            "study_name": "regime",
            "study_value": "baseline",
            "method": "spsa",
            "mean_best_raw_objective": -1.1,
            "ci95_best_raw_objective_low": -1.3,
            "ci95_best_raw_objective_high": -0.9,
            "win_rate": 0.6,
            "mean_feasible_hit_rate": 0.7,
            "mean_estimated_qpu_cost_usd": 0.0,
            "mean_elapsed_seconds": 0.2,
        },
    ]
    summary = generate_suite_research_summary(rows)
    assert summary["research_question"]
    assert summary["headline_answer"]
    assert summary["application_ready_summary"]


def test_bootstrap_ci_width_decreases_with_more_runs() -> None:
    small = [
        {
            "study_name": "budget",
            "study_value": 2,
            "seed": seed,
            "method": "random",
            "best_raw_objective": value,
            "best_valid_energy": value,
            "feasible_hit_rate": 1.0,
            "mean_approx_gap": 0.1,
            "best_approx_ratio": 1.0,
            "best_valid_regret_auc": 0.2,
            "best_valid_energy_per_shot": value / 64.0,
            "best_valid_energy_per_usd": float("nan"),
            "best_valid_sharpe_ratio": 0.5,
            "mean_shot_noise_variance_proxy": 0.01,
            "mean_excess_variance": 0.02,
            "mean_budget_violation": 0.0,
            "violation_counts": "{\"0\": 64}",
            "mean_zne_correction_magnitude": 0.0,
            "elapsed_seconds": 0.1,
            "effective_shots": 64.0,
            "estimated_billed_seconds": 0.1,
            "estimated_qpu_cost_usd": 0.0,
            "win_share": 1.0,
            "penalty_doublings": 0,
            "constraint_hardness": 0.2,
            "best_params": "[]",
        }
        for seed, value in enumerate([1.0, 1.1, 0.9])
    ]
    large = [
        {
            "study_name": "budget",
            "study_value": 2,
            "seed": seed,
            "method": "random",
            "best_raw_objective": value,
            "best_valid_energy": value,
            "feasible_hit_rate": 1.0,
            "mean_approx_gap": 0.1,
            "best_approx_ratio": 1.0,
            "best_valid_regret_auc": 0.2,
            "best_valid_energy_per_shot": value / 64.0,
            "best_valid_energy_per_usd": float("nan"),
            "best_valid_sharpe_ratio": 0.5,
            "mean_shot_noise_variance_proxy": 0.01,
            "mean_excess_variance": 0.02,
            "mean_budget_violation": 0.0,
            "violation_counts": "{\"0\": 64}",
            "mean_zne_correction_magnitude": 0.0,
            "elapsed_seconds": 0.1,
            "effective_shots": 64.0,
            "estimated_billed_seconds": 0.1,
            "estimated_qpu_cost_usd": 0.0,
            "win_share": 1.0,
            "penalty_doublings": 0,
            "constraint_hardness": 0.2,
            "best_params": "[]",
        }
        for seed, value in enumerate([1.0, 1.05, 0.95, 1.02, 0.98, 1.01, 0.99, 1.03, 0.97, 1.0])
    ]
    small_row = aggregate_suite_rows(small, resamples=100)[0]
    large_row = aggregate_suite_rows(large, resamples=100)[0]
    small_width = small_row["ci95_best_raw_objective_high"] - small_row["ci95_best_raw_objective_low"]
    large_width = large_row["ci95_best_raw_objective_high"] - large_row["ci95_best_raw_objective_low"]
    assert large_width < small_width


def test_markdown_report_includes_research_sections(tmp_path: Path) -> None:
    rows = [
        {
            "study_name": "regime",
            "study_value": "baseline",
            "method": "spsa",
            "mean_best_raw_objective": -1.2,
            "ci95_best_raw_objective_low": -1.3,
            "ci95_best_raw_objective_high": -1.0,
            "mean_best_approx_ratio": 1.1,
            "mean_best_valid_regret_auc": 0.2,
            "mean_best_valid_energy_per_shot": -0.01,
            "mean_best_valid_sharpe_ratio": 0.6,
            "win_rate": 0.6,
            "ci95_win_rate_low": 0.5,
            "ci95_win_rate_high": 0.7,
            "mean_feasible_hit_rate": 0.7,
            "ci95_feasible_hit_rate_low": 0.6,
            "ci95_feasible_hit_rate_high": 0.8,
            "mean_approx_gap": 0.1,
            "mean_elapsed_seconds": 0.1,
            "ci95_elapsed_seconds_low": 0.08,
            "ci95_elapsed_seconds_high": 0.12,
            "mean_estimated_billed_seconds": 0.1,
            "mean_estimated_qpu_cost_usd": 0.0,
            "p_value_vs_random_best_valid_bonferroni": 0.04,
        }
    ]
    report_path = tmp_path / "research_report.md"
    write_markdown_report(report_path, "Research", rows, generate_suite_claims(rows))
    txt = report_path.read_text()
    assert "## Research question" in txt
    assert "## Application-ready summary" in txt


def test_bootstrap_ci_is_valid_interval(tmp_path: Path) -> None:
    base = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=1,
        evaluation_budget=4,
        n_init_points=2,
        shots=64,
        bootstrap_resamples=100,
        save_individual_runs=False,
    ).normalized()
    spec = SuiteConfig(
        base=base,
        seeds=[1, 2],
        studies=[{"name": "regime", "key": "regime", "values": ["baseline", "hard_budget"]}],
        output_dir=str(tmp_path / "suite"),
        title="Interval Suite",
    )
    payload = run_suite(spec, verbose=False)
    for row in payload["aggregated"]:
        assert row["ci95_best_raw_objective_low"] <= row["mean_best_raw_objective"] <= row["ci95_best_raw_objective_high"]


def test_suite_report_claims_are_directionally_correct(tmp_path: Path) -> None:
    base = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=1,
        evaluation_budget=4,
        n_init_points=2,
        shots=64,
        bootstrap_resamples=100,
        save_individual_runs=False,
    ).normalized()
    spec = SuiteConfig(
        base=base,
        seeds=[1, 2],
        studies=[{"name": "regime", "key": "regime", "values": ["baseline", "hard_budget"]}],
        output_dir=str(tmp_path / "suite"),
        title="Claim Suite",
    )
    payload = run_suite(spec, verbose=False)
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in payload["aggregated"]:
        grouped.setdefault((str(row["study_name"]), str(row["study_value"])), []).append(row)

    report_text = (tmp_path / "suite" / "suite_report.md").read_text()
    for line in report_text.splitlines():
        if not line.startswith("- For "):
            continue
        claim = line[2:]
        if " has the best mean raw objective " in claim:
            match = re.match(r"For ([^=]+)=([^,]+), (.+?) has the best mean raw objective ", claim)
            assert match is not None
            study_name, study_value, label = match.groups()
            winner = min(grouped[(study_name, study_value)], key=lambda item: float(item["mean_best_raw_objective"]))
            assert winner["method"] == _LABEL_TO_METHOD[label]
        elif " seed-level win rate favors " in claim:
            match = re.match(r"For ([^=]+)=([^,]+), seed-level win rate favors (.+?) \(", claim)
            assert match is not None
            study_name, study_value, label = match.groups()
            method = _LABEL_TO_METHOD[label]
            row = next(item for item in grouped[(study_name, study_value)] if item["method"] == method)
            assert float(row["win_rate"]) > 0.0


def test_aggregate_suite_rows_adds_pairwise_and_timing_columns() -> None:
    rows = [
        {
            "study_name": "depth",
            "study_value": 2,
            "seed": seed,
            "method": "random",
            "best_raw_objective": value,
            "best_valid_energy": value,
            "feasible_hit_rate": 1.0,
            "mean_approx_gap": 0.1,
            "best_approx_ratio": 1.1,
            "best_valid_regret_auc": 0.4,
            "best_valid_energy_per_shot": value / 128.0,
            "best_valid_energy_per_usd": float("nan"),
            "best_valid_sharpe_ratio": 0.5,
            "mean_shot_noise_variance_proxy": 0.02,
            "mean_excess_variance": 0.03,
            "mean_budget_violation": 0.0,
            "violation_counts": "{\"0\": 128}",
            "mean_zne_correction_magnitude": 0.0,
            "elapsed_seconds": 0.1 + 0.01 * seed,
            "effective_shots": 128.0,
            "estimated_billed_seconds": 0.1 + 0.01 * seed,
            "estimated_qpu_cost_usd": 0.0,
            "win_share": 0.0,
            "penalty_doublings": 1,
            "constraint_hardness": 0.2,
            "best_params": "[]",
        }
        for seed, value in enumerate([1.0, 1.1, 0.9], start=1)
    ] + [
        {
            "study_name": "depth",
            "study_value": 2,
            "seed": seed,
            "method": "spsa",
            "best_raw_objective": value,
            "best_valid_energy": value,
            "feasible_hit_rate": 1.0,
            "mean_approx_gap": 0.05,
            "best_approx_ratio": 1.05,
            "best_valid_regret_auc": 0.2,
            "best_valid_energy_per_shot": value / 128.0,
            "best_valid_energy_per_usd": float("nan"),
            "best_valid_sharpe_ratio": 0.6,
            "mean_shot_noise_variance_proxy": 0.01,
            "mean_excess_variance": 0.02,
            "mean_budget_violation": 0.0,
            "violation_counts": "{\"0\": 128}",
            "mean_zne_correction_magnitude": 0.0,
            "elapsed_seconds": 0.2 + 0.01 * seed,
            "effective_shots": 128.0,
            "estimated_billed_seconds": 0.2 + 0.01 * seed,
            "estimated_qpu_cost_usd": 0.0,
            "win_share": 1.0,
            "penalty_doublings": 1,
            "constraint_hardness": 0.2,
            "best_params": "[]",
        }
        for seed, value in enumerate([0.8, 0.85, 0.82], start=1)
    ]
    aggregated = aggregate_suite_rows(rows, resamples=100)
    assert aggregated
    target = next(row for row in aggregated if row["method"] == "spsa")
    assert "ci95_elapsed_seconds_low" in target
    assert "p_value_best_valid_vs_random_bonferroni" in target
    assert "mean_best_valid_energy_per_shot" in target
    assert "mean_shots_to_first_feasible" in target
