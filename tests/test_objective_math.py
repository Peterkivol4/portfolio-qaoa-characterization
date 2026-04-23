import numpy as np

from portfolio_qaoa_bench.config import RunConfig
from portfolio_qaoa_bench.data import SyntheticMarket
from portfolio_qaoa_bench.objective import _approx_ratio, evaluate_objective, make_bounds, weighted_cvar
from portfolio_qaoa_bench.qubo import QuboFactory
from portfolio_qaoa_bench.simulator import build_executor


def test_weighted_cvar_uses_lower_tail_for_minimization() -> None:
    mean, variance, obs_var = weighted_cvar([(1.0, 1), (10.0, 1)], alpha=0.5)
    assert mean == 1.0
    assert variance >= 1e-12
    assert obs_var >= 1e-12


def test_qubo_base_matrix_matches_markowitz_form() -> None:
    rng = np.random.default_rng(123)
    cfg = RunConfig(n_assets=6, budget=2, risk_aversion=0.7).normalized()
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)
    expected = cfg.risk_aversion * sigma - np.diag(mu)
    assert np.allclose(instance.base_matrix, expected)


def test_penalty_strength_is_positive_and_not_tiny() -> None:
    rng = np.random.default_rng(321)
    cfg = RunConfig(n_assets=8, budget=3, regime="clustered_assets", risk_aversion=0.6).normalized()
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)
    assert instance.penalty > 0.0
    assert instance.penalty >= np.max(np.abs(mu))


def test_weighted_cvar_returns_observation_noise_proxy() -> None:
    mean, tail_var, obs_var = weighted_cvar([(1.0, 5), (2.0, 5)], alpha=0.5)
    assert tail_var >= 0.0
    assert obs_var > 0.0
    assert obs_var <= max(tail_var, 1e-12)


def test_approx_ratio_keeps_worse_than_exact_above_one_for_both_signs() -> None:
    assert _approx_ratio(12.0, 10.0) == 1.2
    assert _approx_ratio(-8.0, -10.0) == 1.25
    assert _approx_ratio(10.0, 10.0) == 1.0
    assert _approx_ratio(-10.0, -10.0) == 1.0


def test_approx_ratio_returns_nan_when_best_and_reference_cross_zero() -> None:
    assert np.isnan(_approx_ratio(1.0, -2.0))
    assert np.isnan(_approx_ratio(-1.0, 2.0))
    assert np.isnan(_approx_ratio(0.0, -2.0))


def test_bo_feasibility_aware_target_penalizes_partial_feasibility() -> None:
    raw_cfg = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=1,
        shots=128,
        regime="hard_budget",
        mixer_type="product_x",
        bo_target="raw",
    ).normalized()
    penalized_cfg = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=1,
        shots=128,
        regime="hard_budget",
        mixer_type="product_x",
        bo_target="feasibility_aware",
        bo_feasibility_weight=25.0,
    ).normalized()
    rng = np.random.default_rng(raw_cfg.seed)
    mu, sigma = SyntheticMarket.build(raw_cfg, rng)
    instance = QuboFactory.build(mu, sigma, raw_cfg)
    executor = build_executor(instance, raw_cfg)
    bounds = make_bounds(raw_cfg)
    params = np.random.default_rng(0).uniform(bounds[0], bounds[1])

    raw_stats = evaluate_objective(executor, params, raw_cfg, bounds, np.random.default_rng(100))
    penalized_stats = evaluate_objective(executor, params, penalized_cfg, bounds, np.random.default_rng(100))

    assert raw_stats.valid_ratio < 1.0
    assert raw_stats.raw_objective == penalized_stats.raw_objective
    assert penalized_stats.objective > penalized_stats.raw_objective
