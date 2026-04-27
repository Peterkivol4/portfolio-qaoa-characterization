from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from .config import SpinRunConfig


Boundary = Literal["open", "periodic"]


@dataclass(slots=True)
class SpinHamiltonian:
    """Dense bookkeeping object for J1-J2 transverse-field Ising studies."""

    n_spins: int
    j1: float
    j2: float
    transverse_field: float
    disorder_strength: float
    boundary: Boundary
    regime: str
    disorder_profile: np.ndarray
    cost_diagonal: np.ndarray
    z_eigenvalues: np.ndarray
    flip_indices: np.ndarray
    dense_hamiltonian: np.ndarray

    @property
    def dimension(self) -> int:
        return int(self.cost_diagonal.size)

    @property
    def parameter_vector(self) -> np.ndarray:
        return np.array(
            [self.j1, self.j2, self.transverse_field, self.disorder_strength],
            dtype=float,
        )

    @property
    def frustration_index(self) -> float:
        denom = max(abs(self.j1), 1e-12)
        return float(abs(self.j2) / denom)


def regime_parameters(regime: str) -> dict[str, float]:
    presets = {
        "ferromagnetic": {"j1": 1.0, "j2": 0.0, "transverse_field": 0.35, "disorder_strength": 0.0},
        "near_critical": {"j1": 1.0, "j2": 0.0, "transverse_field": 1.0, "disorder_strength": 0.0},
        "frustrated": {"j1": 1.0, "j2": 0.45, "transverse_field": 0.8, "disorder_strength": 0.0},
        "strong_field": {"j1": 1.0, "j2": 0.0, "transverse_field": 1.7, "disorder_strength": 0.0},
        "disordered": {"j1": 1.0, "j2": 0.1, "transverse_field": 1.0, "disorder_strength": 0.45},
        "mixed_frustrated_disordered": {"j1": 1.0, "j2": 0.35, "transverse_field": 0.9, "disorder_strength": 0.35},
    }
    if regime not in presets:
        raise KeyError(f"Unknown spin regime: {regime}")
    return dict(presets[regime])


def classify_regime(j2: float, transverse_field: float, disorder_strength: float, j1: float = 1.0) -> str:
    ratio = abs(j2) / max(abs(j1), 1e-12)
    if disorder_strength >= 0.3 and ratio >= 0.25:
        return "mixed_frustrated_disordered"
    if disorder_strength >= 0.3:
        return "disordered"
    if transverse_field >= 1.4:
        return "strong_field"
    if ratio >= 0.25:
        return "frustrated"
    if abs(transverse_field - abs(j1)) <= 0.2:
        return "near_critical"
    return "ferromagnetic"


def _z_eigenvalues(n_spins: int) -> np.ndarray:
    basis = np.arange(1 << n_spins, dtype=np.int64)
    bits = ((basis[None, :] >> np.arange(n_spins, dtype=np.int64)[:, None]) & 1).astype(np.int8)
    return 1.0 - 2.0 * bits


def _flip_indices(n_spins: int) -> np.ndarray:
    basis = np.arange(1 << n_spins, dtype=np.int64)
    return np.vstack([basis ^ (1 << site) for site in range(n_spins)]).astype(np.int64)


def build_disorder_profile(cfg: SpinRunConfig, rng: np.random.Generator) -> np.ndarray:
    if cfg.disorder_strength <= 0:
        return np.zeros(cfg.n_spins, dtype=float)
    return rng.uniform(-cfg.disorder_strength, cfg.disorder_strength, size=cfg.n_spins)


def _cost_diagonal(
    z_eigs: np.ndarray,
    *,
    j1: float,
    j2: float,
    disorder_profile: np.ndarray,
    boundary: Boundary,
) -> np.ndarray:
    n_spins = int(z_eigs.shape[0])
    diag = np.zeros(z_eigs.shape[1], dtype=float)

    for site in range(n_spins - 1):
        diag -= j1 * z_eigs[site] * z_eigs[site + 1]
    if boundary == "periodic" and n_spins > 2:
        diag -= j1 * z_eigs[-1] * z_eigs[0]

    for site in range(n_spins - 2):
        diag -= j2 * z_eigs[site] * z_eigs[site + 2]
    if boundary == "periodic" and n_spins > 3:
        diag -= j2 * z_eigs[-2] * z_eigs[0]
        diag -= j2 * z_eigs[-1] * z_eigs[1]

    if disorder_profile.size:
        diag -= disorder_profile @ z_eigs
    return diag


def build_spin_hamiltonian(cfg: SpinRunConfig, rng: np.random.Generator | None = None) -> SpinHamiltonian:
    """Construct the full J1-J2 TFIM Hamiltonian and QAOA cost bookkeeping."""

    cfg = cfg.normalized()
    rng = np.random.default_rng(cfg.seed) if rng is None else rng
    disorder_profile = build_disorder_profile(cfg, rng)
    z_eigs = _z_eigenvalues(cfg.n_spins)
    flips = _flip_indices(cfg.n_spins)
    diag = _cost_diagonal(
        z_eigs,
        j1=cfg.j1,
        j2=cfg.j2,
        disorder_profile=disorder_profile,
        boundary=cfg.boundary,
    )

    dense = np.diag(diag.astype(np.float64, copy=True))
    basis = np.arange(diag.size, dtype=np.int64)
    for site in range(cfg.n_spins):
        dense[basis, flips[site]] += -float(cfg.transverse_field)
    dense = 0.5 * (dense + dense.T)

    regime = cfg.regime
    if regime not in {"ferromagnetic", "near_critical", "frustrated", "strong_field", "disordered", "mixed_frustrated_disordered"}:
        regime = classify_regime(cfg.j2, cfg.transverse_field, cfg.disorder_strength, cfg.j1)

    return SpinHamiltonian(
        n_spins=cfg.n_spins,
        j1=float(cfg.j1),
        j2=float(cfg.j2),
        transverse_field=float(cfg.transverse_field),
        disorder_strength=float(cfg.disorder_strength),
        boundary=cfg.boundary,
        regime=regime,
        disorder_profile=disorder_profile.astype(float),
        cost_diagonal=diag.astype(float),
        z_eigenvalues=z_eigs.astype(float),
        flip_indices=flips,
        dense_hamiltonian=dense.astype(np.float64),
    )


__all__ = [
    "Boundary",
    "SpinHamiltonian",
    "build_disorder_profile",
    "build_spin_hamiltonian",
    "classify_regime",
    "regime_parameters",
]
