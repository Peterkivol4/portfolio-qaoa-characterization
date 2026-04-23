import numpy as np

from portfolio_qaoa_bench.config import RunConfig
from portfolio_qaoa_bench.data import SyntheticMarket
from portfolio_qaoa_bench.qubo import QuboFactory


def test_regimes_are_psd_and_shapes_match() -> None:
    rng = np.random.default_rng(7)
    for regime in ["baseline", "low_correlation", "high_correlation", "sparse_covariance", "clustered_assets", "hard_budget"]:
        cfg = RunConfig(n_assets=8, budget=3, regime=regime).normalized()
        mu, sigma = SyntheticMarket.build(cfg, rng)
        assert mu.shape == (8,)
        assert sigma.shape == (8, 8)
        assert np.allclose(sigma, sigma.T)
        assert np.min(np.linalg.eigvalsh(sigma)) >= -1e-7


def test_qubo_matrix_is_symmetric_across_random_scales() -> None:
    rng = np.random.default_rng(11)
    for n_assets in range(4, 10):
        for _ in range(5):
            mu = rng.uniform(0.05, 0.2, n_assets)
            gaussian = rng.standard_normal((n_assets, n_assets))
            sigma = 0.01 * gaussian @ gaussian.T
            cfg = RunConfig(n_assets=n_assets, budget=max(1, n_assets // 3), risk_aversion=0.4 + 0.05 * n_assets).normalized()
            instance = QuboFactory.build(mu, sigma, cfg)
            assert np.allclose(instance.qubo_matrix, instance.qubo_matrix.T)
            assert instance.penalty > 0.0


def test_budget_penalty_increases_with_violation_count() -> None:
    rng = np.random.default_rng(101)
    cfg = RunConfig(n_assets=8, budget=3, regime="sparse_covariance").normalized()
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)
    by_violation: dict[int, list[float]] = {}
    for mask in range(1 << cfg.n_assets):
        bitstring = format(mask, f"0{cfg.n_assets}b")
        by_violation.setdefault(instance.violation(bitstring), []).append(instance.energy(bitstring))
    assert min(by_violation[0]) <= min(by_violation[1]) <= min(by_violation[2])


def test_hard_budget_regime_responds_to_budget() -> None:
    rng_a = np.random.default_rng(29)
    rng_b = np.random.default_rng(29)
    cfg_a = RunConfig(n_assets=8, budget=2, regime="hard_budget").normalized()
    cfg_b = RunConfig(n_assets=8, budget=4, regime="hard_budget").normalized()
    mu_a, sigma_a = SyntheticMarket.build(cfg_a, rng_a)
    mu_b, sigma_b = SyntheticMarket.build(cfg_b, rng_b)
    assert not np.allclose(mu_a, mu_b)
    assert not np.allclose(sigma_a, sigma_b)


def test_exact_feasible_energy_matches_bruteforce() -> None:
    rng = np.random.default_rng(5)
    cfg = RunConfig(n_assets=6, budget=2).normalized()
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)
    brute = float("inf")
    for mask in range(1 << cfg.n_assets):
        bitstring = format(mask, f"0{cfg.n_assets}b")
        if bitstring.count("1") == cfg.budget:
            brute = min(brute, instance.feasible_energy(bitstring))
    assert abs(brute - instance.exact_feasible_energy) < 1e-9


def test_exact_reference_is_omitted_above_configured_cutoff() -> None:
    rng = np.random.default_rng(13)
    cfg = RunConfig(
        n_assets=15,
        budget=4,
        regime="baseline",
        execution_mode="aer_sampler",
        backend_name="aer_simulator",
        exact_reference_max_assets=14,
    ).normalized()
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)
    assert instance.exact_feasible_energy is None
