from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import warnings

import numpy as np

from .config import RunSpec
from .interfaces import QuboPort


@dataclass
class PortfolioQUBO:
    """Binary legacy portfolio-QUBO instance with optional exact reference data."""

    mu: np.ndarray
    sigma: np.ndarray
    budget: int
    risk_aversion: float
    penalty: float
    qubo_matrix: np.ndarray
    exact_feasible_energy: float | None
    penalty_doublings: int
    penalty_validation_attempted: bool

    @property
    def n_assets(self) -> int:
        return int(self.mu.shape[0])

    @property
    def base_matrix(self) -> np.ndarray:
        # Markowitz-style logical objective: q * x^T Sigma x - mu^T x
        return self.risk_aversion * self.sigma - np.diag(self.mu)

    def energy(self, bitstring: str) -> float:
        x = np.fromiter((int(b) for b in bitstring), dtype=int)
        return float(x @ self.qubo_matrix @ x)

    def feasible_energy(self, bitstring: str) -> float:
        x = np.fromiter((int(b) for b in bitstring), dtype=int)
        return float(x @ self.base_matrix @ x)

    def violation(self, bitstring: str) -> int:
        return abs(bitstring.count("1") - self.budget)


class QuboFactory(QuboPort):
    @staticmethod
    def build(mu: np.ndarray, sigma: np.ndarray, cfg: RunSpec) -> PortfolioQUBO:
        """Build the penalized legacy portfolio QUBO for a cardinality-constrained Markowitz objective.

        The unconstrained quadratic objective is
        ``risk_aversion * x^T Sigma x - mu^T x`` for binary asset-selection vector ``x``.
        A quadratic penalty enforces the cardinality constraint ``sum_i x_i = budget``.
        """

        mu = np.asarray(mu, dtype=float)
        sigma = np.asarray(sigma, dtype=float)
        sigma = (sigma + sigma.T) / 2.0
        base = cfg.risk_aversion * sigma - np.diag(mu)
        penalty = QuboFactory._auto_budget_penalty(mu, sigma, cfg) * cfg.qubo_penalty_multiplier
        penalty, qubo, penalty_doublings, validation_attempted = QuboFactory._calibrated_penalty_and_qubo(base, penalty, cfg)
        exact = QuboFactory._exact_feasible_optimum(base, cfg.budget) if cfg.n_assets <= cfg.exact_reference_max_assets else None
        return PortfolioQUBO(
            mu=mu,
            sigma=sigma,
            budget=cfg.budget,
            risk_aversion=cfg.risk_aversion,
            penalty=float(penalty),
            qubo_matrix=qubo,
            exact_feasible_energy=exact,
            penalty_doublings=int(penalty_doublings),
            penalty_validation_attempted=bool(validation_attempted),
        )

    @staticmethod
    def _auto_budget_penalty(mu: np.ndarray, sigma: np.ndarray, cfg: RunSpec) -> float:
        abs_sigma = np.abs(sigma)
        diag = np.abs(np.diag(sigma))
        row_sums = np.sum(abs_sigma, axis=1) - diag
        marginal_bounds = np.abs(mu) + cfg.risk_aversion * (diag + 2.0 * row_sums)
        return max(1e-6, float(np.max(marginal_bounds)))

    @staticmethod
    def _build_qubo(base: np.ndarray, budget: int, penalty: float) -> np.ndarray:
        qubo = base.copy()
        diag_idx = np.diag_indices(base.shape[0])
        qubo[diag_idx] += penalty * (1 - 2 * budget)
        off_diag_mask = ~np.eye(base.shape[0], dtype=bool)
        qubo[off_diag_mask] += penalty
        return (qubo + qubo.T) / 2.0

    @staticmethod
    def _penalty_is_sufficient(qubo: np.ndarray, budget: int) -> bool:
        n_assets = int(qubo.shape[0])
        if n_assets > 20:
            warnings.warn(
                f"_penalty_is_sufficient enumerates 2^n={2**n_assets} states for n_assets={n_assets}. This may be very slow.",
                RuntimeWarning,
                stacklevel=2,
            )
        states = np.arange(1 << n_assets, dtype=np.uint64)
        bits = ((states[:, None] >> np.arange(n_assets, dtype=np.uint64)) & 1).astype(float)
        cardinalities = bits.sum(axis=1)
        energies = np.einsum("bi,ij,bj->b", bits, qubo, bits, optimize=True)
        feasible = cardinalities == budget
        infeasible = ~feasible
        if not np.any(feasible) or not np.any(infeasible):
            return True
        max_feasible = float(np.max(energies[feasible]))
        min_infeasible = float(np.min(energies[infeasible]))
        return min_infeasible > max_feasible + 1e-12

    @staticmethod
    def _calibrated_penalty_and_qubo(base: np.ndarray, penalty: float, cfg: RunSpec) -> tuple[float, np.ndarray, int, bool]:
        current = float(penalty)
        qubo = QuboFactory._build_qubo(base, cfg.budget, current)
        if base.shape[0] > cfg.penalty_validation_max_assets:
            return current, qubo, 0, False
        doublings = 0
        for _ in range(cfg.penalty_validation_max_tries):
            if QuboFactory._penalty_is_sufficient(qubo, cfg.budget):
                return current, qubo, doublings, True
            current *= 2.0
            doublings += 1
            qubo = QuboFactory._build_qubo(base, cfg.budget, current)
        raise ValueError(
            "Failed to find a sufficient budget penalty within penalty_validation_max_tries. "
            "Increase qubo_penalty_multiplier or penalty_validation_max_tries."
        )

    @staticmethod
    def _exact_feasible_optimum(base_matrix: np.ndarray, budget: int) -> float:
        n_assets = int(base_matrix.shape[0])
        best = float("inf")
        # This brute-force reference only enumerates C(n, budget) feasible portfolios.
        # For the benchmark sizes used here (for example n=12, budget=4 -> 495 states),
        # this is intentionally small enough to remain cheap while still giving a true
        # exact-feasible optimum for regret and approximation-gap calculations.
        for chosen in combinations(range(n_assets), budget):
            x = np.zeros(n_assets, dtype=int)
            x[list(chosen)] = 1
            best = min(best, float(x @ base_matrix @ x))
        return best

PortfolioInstance = PortfolioQUBO


__all__ = ['PortfolioQUBO', 'QuboFactory', 'PortfolioInstance']
