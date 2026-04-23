import numpy as np
import pytest

from portfolio_qaoa_bench.config import RunConfig
from portfolio_qaoa_bench.data import SyntheticMarket
from portfolio_qaoa_bench.landscape import constraint_hardness, feasibility_subspace_size, profile_instance
from portfolio_qaoa_bench.qubo import QuboFactory


def test_constraint_hardness_matches_subspace_fraction() -> None:
    assert feasibility_subspace_size(6, 2) == 15
    assert np.isclose(constraint_hardness(6, 2), 15 / 64)


def test_profile_instance_returns_finite_structure_metrics() -> None:
    cfg = RunConfig(n_assets=6, budget=2, regime="clustered_assets").normalized()
    rng = np.random.default_rng(cfg.seed)
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)
    profile = profile_instance(instance)
    assert np.isfinite(profile.condition_number)
    assert profile.constraint_hardness > 0.0
    assert profile.ground_state_participation_ratio > 0.0
    assert profile.penalty_doublings >= 0
    assert profile.penalty_validation_attempted in {True, False}


@pytest.mark.parametrize("regime", ["baseline", "low_correlation", "high_correlation", "sparse_covariance", "clustered_assets", "hard_budget"])
def test_landscape_ground_state_participation_ratio_bounds(regime: str) -> None:
    cfg = RunConfig(n_assets=6, budget=2, regime=regime).normalized()
    rng = np.random.default_rng(cfg.seed)
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)
    profile = profile_instance(instance)
    assert 0.0 < profile.ground_state_participation_ratio <= 1.0
