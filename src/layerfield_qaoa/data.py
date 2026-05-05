from __future__ import annotations

import numpy as np

from .config import RunSpec
from .interfaces import MarketPort


class SyntheticMarket(MarketPort):
    @staticmethod
    def build(cfg: RunSpec, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
        """Generate synthetic return and covariance estimates for the configured market regime."""

        regime = cfg.regime
        mu = rng.uniform(0.05, 0.20, cfg.n_assets)
        if regime == "baseline":
            sigma = SyntheticMarket._baseline_covariance(cfg.n_assets, rng)
        elif regime == "low_correlation":
            sigma = SyntheticMarket._correlation_regime(cfg.n_assets, rng, target=0.10)
        elif regime == "high_correlation":
            sigma = SyntheticMarket._correlation_regime(cfg.n_assets, rng, target=0.75)
        elif regime == "sparse_covariance":
            sigma = SyntheticMarket._sparse_covariance(cfg.n_assets, rng)
        elif regime == "clustered_assets":
            sigma = SyntheticMarket._clustered_covariance(cfg.n_assets, rng)
        elif regime == "hard_budget":
            mu, sigma = SyntheticMarket._hard_budget_regime(cfg, rng)
        else:
            raise ValueError(f"Unsupported regime: {regime}")
        sigma = SyntheticMarket._make_psd(sigma)
        return mu, sigma

    @staticmethod
    def _baseline_covariance(n_assets: int, rng: np.random.Generator) -> np.ndarray:
        gaussian = rng.standard_normal((n_assets, n_assets))
        sigma = 0.01 * (gaussian @ gaussian.T)
        return sigma

    @staticmethod
    def _correlation_regime(n_assets: int, rng: np.random.Generator, target: float) -> np.ndarray:
        vol = rng.uniform(0.08, 0.25, n_assets)
        corr = np.full((n_assets, n_assets), target)
        np.fill_diagonal(corr, 1.0)
        jitter = 0.03 * rng.standard_normal((n_assets, n_assets))
        jitter = (jitter + jitter.T) / 2.0
        corr = corr + jitter
        corr = np.clip(corr, -0.95, 0.95)
        np.fill_diagonal(corr, 1.0)
        sigma = np.outer(vol, vol) * corr
        return sigma

    @staticmethod
    def _sparse_covariance(n_assets: int, rng: np.random.Generator) -> np.ndarray:
        dense = rng.standard_normal((n_assets, n_assets))
        dense = dense @ dense.T
        mask = rng.random((n_assets, n_assets)) < 0.25
        mask = np.triu(mask, k=1)
        mask = mask + mask.T + np.eye(n_assets, dtype=bool)
        sigma = dense * mask
        sigma *= 0.01 / max(np.mean(np.diag(sigma)), 1e-6)
        return sigma

    @staticmethod
    def _clustered_covariance(n_assets: int, rng: np.random.Generator) -> np.ndarray:
        n_clusters = min(3, n_assets)
        assignments = rng.integers(0, n_clusters, size=n_assets)
        vol = rng.uniform(0.08, 0.20, n_assets)
        corr = np.full((n_assets, n_assets), 0.10)
        for i in range(n_assets):
            for j in range(n_assets):
                if assignments[i] == assignments[j]:
                    corr[i, j] = 0.70 if i != j else 1.0
        corr += 0.02 * rng.standard_normal((n_assets, n_assets))
        corr = (corr + corr.T) / 2.0
        corr = np.clip(corr, -0.95, 0.95)
        np.fill_diagonal(corr, 1.0)
        return np.outer(vol, vol) * corr

    @staticmethod
    def _hard_budget_regime(cfg: RunSpec, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
        """Construct a knife-edge regime whose statistics depend on the budget fraction.

        The expected returns are split into ``budget`` slightly favorable assets and the
        remaining assets with nearly indistinguishable means, while a strong common-factor
        covariance compresses the energy gap between near-feasible alternatives.
        """

        n_assets = cfg.n_assets
        budget_fraction = cfg.budget / max(cfg.n_assets, 1)
        middle_pressure = 1.0 - abs(0.5 - budget_fraction) * 2.0
        base_return = rng.uniform(0.09, 0.12)
        edge = 0.0025 - 0.0010 * middle_pressure
        signal = np.concatenate(
            [
                np.full(cfg.budget, edge, dtype=float),
                np.full(n_assets - cfg.budget, -edge, dtype=float),
            ]
        )
        rng.shuffle(signal)
        mu = base_return + signal + 0.0015 * rng.standard_normal(n_assets)

        common = rng.standard_normal((n_assets, 2))
        sigma = (0.010 + 0.006 * middle_pressure) * (common @ common.T)
        sigma /= max(float(np.mean(np.diag(sigma))), 1e-6)
        sigma *= 0.012
        sigma += (0.0015 + 0.0015 * middle_pressure) * np.eye(n_assets)
        return mu, sigma

    @staticmethod
    def _make_psd(matrix: np.ndarray) -> np.ndarray:
        matrix = np.asarray(matrix, dtype=float)
        matrix = (matrix + matrix.T) / 2.0
        eigenvalues = np.linalg.eigvalsh(matrix)
        min_eig = float(np.min(eigenvalues))
        if min_eig < 1e-9:
            matrix = matrix + np.eye(matrix.shape[0]) * (1e-9 - min_eig + 1e-9)
        return matrix


__all__ = ['SyntheticMarket']
