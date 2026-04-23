import numpy as np
import pytest

from portfolio_qaoa_bench.config import RunConfig
from portfolio_qaoa_bench.data import SyntheticMarket
from portfolio_qaoa_bench.objective import make_bounds
from portfolio_qaoa_bench.optimizers import (
    BayesianOptimizer,
    _periodic_feature_map,
    run_bayesian_search,
    run_classical_markowitz,
    run_random_search,
    run_spsa_search,
)
from portfolio_qaoa_bench.qubo import QuboFactory
from portfolio_qaoa_bench.simulator import build_executor


def test_periodic_feature_map_respects_boundary_equivalence() -> None:
    lower = np.array([0.0])
    upper = np.array([2.0 * np.pi])
    x1 = np.array([[0.1]])
    x2 = np.array([[2.0 * np.pi - 0.1]])
    f1 = _periodic_feature_map(x1, lower, upper)
    f2 = _periodic_feature_map(x2, lower, upper)
    assert np.linalg.norm(f1 - f2) < 0.25


def test_surrogate_loop_uses_sklearn_after_initial_design(monkeypatch) -> None:
    import portfolio_qaoa_bench.optimizers as opt

    monkeypatch.setattr(opt, "SingleTaskGP", None)
    cfg = RunConfig(n_assets=6, budget=2, n_init_points=2, evaluation_budget=4).normalized()
    bounds = make_bounds(cfg)
    loop = BayesianOptimizer(bounds, cfg)
    rng = np.random.default_rng(0)
    first = loop.suggest(rng)
    second = loop.suggest(rng)
    loop.observe(first, 1.0, 0.1)
    loop.observe(second, 0.5, 0.1)
    third = loop.suggest(rng)
    assert third.shape == first.shape
    assert loop.backend_used == "sklearn_ucb"


def test_surrogate_loop_falls_back_when_botorch_path_raises(monkeypatch) -> None:
    cfg = RunConfig(n_assets=6, budget=2, n_init_points=2, evaluation_budget=4).normalized()
    bounds = make_bounds(cfg)
    loop = BayesianOptimizer(bounds, cfg)
    rng = np.random.default_rng(0)
    first = loop.suggest(rng)
    second = loop.suggest(rng)
    loop.observe(first, 1.0, 0.1)
    loop.observe(second, 0.5, 0.1)
    monkeypatch.setattr(loop, "_suggest_botorch", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    third = loop.suggest(rng)
    assert third.shape == first.shape
    assert loop.backend_used.startswith("sklearn_")


def test_high_dim_bo_activates_random_embedding() -> None:
    cfg = RunConfig(n_assets=6, budget=2, p_layers=10, n_init_points=2, evaluation_budget=4, bo_max_gp_dim=8).normalized()
    bounds = make_bounds(cfg)
    loop = BayesianOptimizer(bounds, cfg)
    rng = np.random.default_rng(0)
    first = loop.suggest(rng)
    second = loop.suggest(rng)
    loop.observe(first, 1.0, 0.1)
    loop.observe(second, 0.5, 0.1)
    third = loop.suggest(rng)
    assert third.shape == first.shape
    assert len(loop.active_dims) == cfg.bo_max_gp_dim
    assert "randemb" in loop.backend_used


def test_bayesian_search_records_evaluation_details() -> None:
    cfg = RunConfig(n_assets=6, budget=2, p_layers=1, evaluation_budget=4, n_init_points=2, shots=64, qpu_price_per_second_usd=0.25).normalized()
    rng = np.random.default_rng(cfg.seed)
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)
    executor = build_executor(instance, cfg)
    bounds = make_bounds(cfg)
    trace = run_bayesian_search(executor, cfg, bounds, rng)
    assert trace.total_objective_calls == cfg.evaluation_budget
    assert len(trace.evaluation_records) == cfg.evaluation_budget
    assert trace.evaluation_records[0].backend_stats["effective_shots"] >= cfg.shots
    assert trace.evaluation_records[0].backend_stats["estimated_qpu_cost_usd"] >= 0.0


def test_bayesian_optimizer_uses_warm_start_as_first_design_point() -> None:
    cfg = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=2,
        n_init_points=3,
        warm_start_params=[0.1, 0.2, 0.3, 0.4],
    ).normalized()
    bounds = make_bounds(cfg)
    loop = BayesianOptimizer(bounds, cfg)
    first = loop.suggest(np.random.default_rng(7))
    assert np.allclose(first, np.array(cfg.warm_start_params, dtype=float))


def test_warm_start_params_change_initial_suggestion() -> None:
    warm_cfg = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=2,
        n_init_points=3,
        warm_start_params=[0.1, 0.2, 0.3, 0.4],
    ).normalized()
    cold_cfg = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=2,
        n_init_points=3,
    ).normalized()
    bounds = make_bounds(warm_cfg)
    warm_first = BayesianOptimizer(bounds, warm_cfg).suggest(np.random.default_rng(7))
    cold_first = BayesianOptimizer(bounds, cold_cfg).suggest(np.random.default_rng(7))
    assert np.allclose(warm_first, np.array(warm_cfg.warm_start_params, dtype=float))
    assert not np.allclose(warm_first, cold_first)


def test_bayesian_surrogate_rejects_mismatched_warm_start_dimension() -> None:
    cfg = RunConfig(n_assets=6, budget=2, p_layers=2).normalized()
    cfg.warm_start_params = [0.1, 0.2]
    with pytest.raises(ValueError, match="warm_start_params"):
        BayesianOptimizer(make_bounds(cfg), cfg)


def test_spsa_search_records_trace() -> None:
    cfg = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=1,
        evaluation_budget=6,
        n_init_points=2,
        shots=64,
    ).normalized()
    rng = np.random.default_rng(cfg.seed)
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)
    executor = build_executor(instance, cfg)
    bounds = make_bounds(cfg)

    trace = run_spsa_search(executor, cfg, bounds, rng)

    assert trace.total_objective_calls == cfg.evaluation_budget
    assert len(trace.evaluation_records) == cfg.evaluation_budget
    assert all(np.isfinite(trace.best_valid_history))
    timing = trace.timing_totals
    subtotal = (
        float(timing.classical_overhead_seconds)
        + float(timing.circuit_construction_seconds)
        + float(timing.transpilation_seconds)
        + float(timing.execution_seconds)
        + float(timing.mitigation_seconds)
        + float(timing.queue_latency_seconds)
    )
    assert abs(subtotal - float(timing.total_seconds)) < 1e-6


def test_classical_markowitz_finds_feasible_solution() -> None:
    cfg = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=1,
        evaluation_budget=6,
        n_init_points=2,
        shots=64,
    ).normalized()
    rng = np.random.default_rng(cfg.seed)
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)

    trace = run_classical_markowitz(instance, cfg)

    assert np.isfinite(trace.best_valid_history[0])
    assert trace.feasible_hit_history == [1.0]
    assert trace.best_valid_history[0] == instance.exact_feasible_energy


def test_bo_outperforms_random_on_average_on_clustered_assets() -> None:
    bo_scores = []
    random_scores = []
    for seed in [1, 2, 3]:
        cfg = RunConfig(
            n_assets=12,
            budget=4,
            p_layers=3,
            regime="clustered_assets",
            evaluation_budget=20,
            n_init_points=6,
            shots=256,
            seed=seed,
        ).normalized()
        rng = np.random.default_rng(cfg.seed)
        mu, sigma = SyntheticMarket.build(cfg, rng)
        instance = QuboFactory.build(mu, sigma, cfg)
        executor = build_executor(instance, cfg)
        bounds = make_bounds(cfg)

        random_trace = run_random_search(executor, cfg, bounds, np.random.default_rng(cfg.seed))
        bo_trace = run_bayesian_search(executor, cfg, bounds, np.random.default_rng(cfg.seed))
        random_scores.append(float(min(random_trace.raw_objective_history)))
        bo_scores.append(float(min(bo_trace.raw_objective_history)))

    assert float(np.mean(bo_scores)) < float(np.mean(random_scores))
