from pathlib import Path

import numpy as np
import pytest

from layerfield_qaoa.config import RunConfig, SuiteConfig
from layerfield_qaoa.pipeline import run_benchmark, run_suite


def test_single_run_generates_json_and_png(tmp_path: Path) -> None:
    cfg = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=1,
        evaluation_budget=4,
        n_init_points=2,
        shots=64,
        qpu_price_per_second_usd=0.5,
        output_prefix=str(tmp_path / "single"),
    ).normalized()
    payload = run_benchmark(cfg, verbose=False)
    assert (tmp_path / "single.json").exists()
    assert (tmp_path / "single.png").exists()
    assert payload["schema_version"] == "1.6"
    assert payload["single_run_insights"]
    assert "classical_markowitz" in payload["methods"]
    assert payload["methods"]["random"]["total_estimated_qpu_cost_usd"] >= 0.0
    assert "best_valid_energy_per_shot" in payload["methods"]["random"]
    assert "best_valid_sharpe_ratio" in payload["methods"]["classical_markowitz"]
    assert "shots_to_first_feasible" in payload["methods"]["random"]
    assert "penalty_doublings" in payload["qubo_profile"]


def test_suite_generates_csv_markdown_and_payload(tmp_path: Path) -> None:
    base = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=1,
        evaluation_budget=3,
        n_init_points=2,
        shots=64,
        qpu_price_per_second_usd=0.5,
        save_individual_runs=False,
        bootstrap_resamples=200,
    ).normalized()
    spec = SuiteConfig(
        base=base,
        seeds=[1],
        studies=[
            {"name": "regime", "key": "regime", "values": ["baseline", "low_correlation"]},
            {"name": "shots", "key": "shots", "values": [32, 64]},
        ],
        output_dir=str(tmp_path / "suite"),
        title="Test Suite",
    )
    payload = run_suite(spec, verbose=False)
    assert (tmp_path / "suite" / "suite_runs.csv").exists()
    assert (tmp_path / "suite" / "suite_aggregated.csv").exists()
    assert (tmp_path / "suite" / "suite_report.md").exists()
    assert (tmp_path / "suite" / "suite_payload.json").exists()
    assert (tmp_path / "suite" / "suite_dashboard.png").exists()
    assert (tmp_path / "suite" / "suite_application_summary.md").exists()
    assert payload["claims"]
    assert payload["research_summary"]["application_ready_summary"]
    assert payload["aggregated"][0]["mean_estimated_qpu_cost_usd"] >= 0.0
    assert "ci95_best_raw_objective_low" in payload["aggregated"][0]
    assert "win_rate" in payload["aggregated"][0]
    assert "mean_best_valid_energy_per_shot" in payload["aggregated"][0]
    assert "mean_shots_to_first_feasible" in payload["aggregated"][0]
    assert "p_value_best_valid_vs_random_bonferroni" in payload["aggregated"][0]


def test_suite_parallel_workers_smoke(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "mplconfig"))
    base = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=1,
        evaluation_budget=3,
        n_init_points=2,
        shots=64,
        save_individual_runs=False,
        bootstrap_resamples=50,
    ).normalized()
    spec = SuiteConfig(
        base=base,
        seeds=[1],
        studies=[{"name": "regime", "key": "regime", "values": ["baseline", "hard_budget"]}],
        output_dir=str(tmp_path / "suite_parallel"),
        title="Parallel Suite",
        workers=2,
    )
    payload = run_suite(spec, verbose=False)
    assert len(payload["runs"]) == 2
    assert (tmp_path / "suite_parallel" / "suite_dashboard.png").exists()


def test_factorial_suite_generates_mixer_analysis_outputs(tmp_path: Path) -> None:
    base = RunConfig(
        n_assets=4,
        budget=1,
        p_layers=1,
        evaluation_budget=2,
        n_init_points=1,
        shots=32,
        save_individual_runs=False,
        bootstrap_resamples=50,
        noise_model="depolarizing",
    ).normalized()
    spec = SuiteConfig(
        base=base,
        seeds=[1],
        studies=[
            {"name": "regime", "key": "regime", "values": ["baseline"]},
            {"name": "mixer", "key": "mixer_type", "values": ["xy", "product_x"]},
            {"name": "noise", "key": "depolarizing_strength_2q", "values": [0.005, 0.02]},
        ],
        output_dir=str(tmp_path / "factorial_suite"),
        title="Factorial Mixer Suite",
        study_mode="factorial",
    )
    payload = run_suite(spec, verbose=False)
    assert payload["study_mode"] == "factorial"
    assert len(payload["runs"]) == 4
    assert payload["mixer_analysis"]["variance_summary"]["row_count"] > 0
    assert (tmp_path / "factorial_suite" / "mixer_dominance_pairs.csv").exists()
    assert (tmp_path / "factorial_suite" / "mixer_dominance_summary.csv").exists()
    assert (tmp_path / "factorial_suite" / "mixer_optimizer_balance.csv").exists()
    assert (tmp_path / "factorial_suite" / "mixer_variance_summary.json").exists()
    assert (tmp_path / "factorial_suite" / "mixer_dominance_report.md").exists()
    assert (tmp_path / "factorial_suite" / "mixer_crossover.png").exists()
    factorial_jsons = sorted((tmp_path / "factorial_suite" / "factorial").glob("*.json"))
    assert len(factorial_jsons) == 4
    names = {path.name for path in factorial_jsons}
    assert any("depolarizing_strength_2q_0.005" in name for name in names)
    assert any("depolarizing_strength_2q_0.02" in name for name in names)


@pytest.mark.parametrize("regime", ["baseline", "low_correlation", "high_correlation", "sparse_covariance", "clustered_assets", "hard_budget"])
def test_end_to_end_benchmark_runs_across_regimes(tmp_path: Path, regime: str) -> None:
    cfg = RunConfig(
        n_assets=6,
        budget=2,
        regime=regime,
        p_layers=1,
        evaluation_budget=6,
        n_init_points=2,
        shots=64,
        output_prefix=str(tmp_path / f"run_{regime}"),
    ).normalized()
    payload = run_benchmark(cfg, verbose=False)
    assert payload["methods"]
    assert payload["qubo_profile"]["constraint_hardness"] > 0.0
    for summary in payload["methods"].values():
        assert np.isfinite(summary["best_raw_objective"])
        assert np.isfinite(summary["elapsed_seconds"])
        assert summary["total_objective_calls"] >= 1


def test_same_seed_produces_identical_output(tmp_path: Path) -> None:
    cfg_a = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=1,
        evaluation_budget=4,
        n_init_points=2,
        shots=64,
        seed=123,
        output_prefix=str(tmp_path / "run_a"),
    ).normalized()
    cfg_b = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=1,
        evaluation_budget=4,
        n_init_points=2,
        shots=64,
        seed=123,
        output_prefix=str(tmp_path / "run_b"),
    ).normalized()

    first = run_benchmark(cfg_a, verbose=False)
    second = run_benchmark(cfg_b, verbose=False)

    for method in first["methods"]:
        assert first["methods"][method]["best_raw_objective"] == second["methods"][method]["best_raw_objective"]
        assert first["methods"][method]["total_objective_calls"] == second["methods"][method]["total_objective_calls"]


def test_no_single_optimizer_dominates_all_regimes(tmp_path: Path) -> None:
    base = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=1,
        evaluation_budget=8,
        n_init_points=2,
        shots=64,
        save_individual_runs=False,
        bootstrap_resamples=100,
    ).normalized()
    spec = SuiteConfig(
        base=base,
        seeds=[1],
        studies=[
            {"name": "regime", "key": "regime", "values": ["baseline", "clustered_assets", "hard_budget"]},
        ],
        output_dir=str(tmp_path / "mini_suite"),
        title="Mini Regime Suite",
    )
    payload = run_suite(spec, verbose=False)
    by_method: dict[str, list[float]] = {}
    for row in payload["aggregated"]:
        by_method.setdefault(row["method"], []).append(float(row["win_rate"]))
    assert by_method
    for values in by_method.values():
        assert float(np.mean(values)) < 1.0


def test_depolarizing_noise_reduces_feasibility(tmp_path: Path) -> None:
    ideal_cfg = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=1,
        evaluation_budget=4,
        n_init_points=2,
        shots=128,
        noise_model="ideal",
        output_prefix=str(tmp_path / "ideal"),
    ).normalized()
    noisy_cfg = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=1,
        evaluation_budget=4,
        n_init_points=2,
        shots=128,
        noise_model="depolarizing",
        output_prefix=str(tmp_path / "depolarizing"),
    ).normalized()

    ideal = run_benchmark(ideal_cfg, verbose=False)
    noisy = run_benchmark(noisy_cfg, verbose=False)

    ideal_valid = float(np.mean(ideal["methods"]["random"]["valid_ratio_history"]))
    noisy_valid = float(np.mean(noisy["methods"]["random"]["valid_ratio_history"]))
    assert noisy_valid < ideal_valid


def test_dimension_scaling_smoke_across_asset_counts(tmp_path: Path) -> None:
    observed_dimensions: list[int] = []
    for n_assets in [4, 6, 8, 10, 12]:
        cfg = RunConfig(
            n_assets=n_assets,
            budget=max(1, n_assets // 3),
            p_layers=1,
            evaluation_budget=3,
            n_init_points=2,
            shots=32,
            output_prefix=str(tmp_path / f"scale_{n_assets}"),
        ).normalized()
        payload = run_benchmark(cfg, verbose=False)
        observed_dimensions.append(2**n_assets)
        assert payload["regime_characteristics"]["n_assets"] == n_assets
        assert payload["methods"]["random"]["total_objective_calls"] == cfg.evaluation_budget
        assert np.isfinite(payload["methods"]["random"]["best_raw_objective"])
        assert payload["qubo_profile"]["constraint_hardness"] > 0.0
    assert observed_dimensions == sorted(observed_dimensions)
    assert observed_dimensions[-1] == 4096
