from __future__ import annotations

from dataclasses import dataclass
from math import comb
import warnings

import numpy as np

from .qubo import PortfolioQUBO


def feasibility_subspace_size(n_assets: int, budget: int) -> int:
    """Return the number of budget-feasible computational-basis states."""

    return comb(n_assets, budget)


def constraint_hardness(n_assets: int, budget: int) -> float:
    """Return the feasible-subspace fraction inside the full Hilbert space."""

    return feasibility_subspace_size(n_assets, budget) / float(2**n_assets)


@dataclass
class QUBOSpectralProfile:
    """Lightweight structural diagnostics for a portfolio-QUBO instance."""

    condition_number: float
    spectral_gap: float | None
    energy_gap_to_infeasible: float | None
    ground_state_participation_ratio: float
    constraint_hardness: float
    penalty_doublings: int
    penalty_validation_attempted: bool


def profile_instance(instance: PortfolioQUBO) -> QUBOSpectralProfile:
    """Compute simple pre-optimization structure metrics for one QUBO instance."""

    if instance.n_assets > 20:
        warnings.warn(
            f"profile_instance enumerates 2^n={2**instance.n_assets} states for n_assets={instance.n_assets}. This may be very slow.",
            RuntimeWarning,
            stacklevel=2,
        )
    base = np.asarray(instance.base_matrix, dtype=float)
    eigenvalues = np.linalg.eigvalsh(base)
    nonzero = np.abs(eigenvalues[np.abs(eigenvalues) > 1e-12])
    if nonzero.size:
        condition_number = float(np.max(nonzero) / np.min(nonzero))
    else:
        condition_number = float("inf")

    n_assets = instance.n_assets
    states = np.arange(1 << n_assets, dtype=np.uint64)
    bits = ((states[:, None] >> np.arange(n_assets, dtype=np.uint64)) & 1).astype(float)
    cardinalities = bits.sum(axis=1)
    energies = np.einsum("bi,ij,bj->b", bits, instance.base_matrix, bits, optimize=True)
    feasible = cardinalities == instance.budget
    infeasible = ~feasible

    feasible_energies = np.sort(energies[feasible])
    if feasible_energies.size >= 2:
        spectral_gap = float(feasible_energies[1] - feasible_energies[0])
    else:
        spectral_gap = None

    if np.any(feasible) and np.any(infeasible):
        best_feasible = float(np.min(energies[feasible]))
        energy_gap_to_infeasible = float(np.min(energies[infeasible]) - best_feasible)
        degeneracy = int(np.sum(np.isclose(energies[feasible], best_feasible, atol=1e-12)))
        participation_ratio = 1.0 / float(max(degeneracy, 1))
    else:
        energy_gap_to_infeasible = None
        participation_ratio = 1.0

    return QUBOSpectralProfile(
        condition_number=condition_number,
        spectral_gap=spectral_gap,
        energy_gap_to_infeasible=energy_gap_to_infeasible,
        ground_state_participation_ratio=participation_ratio,
        constraint_hardness=constraint_hardness(instance.n_assets, instance.budget),
        penalty_doublings=int(instance.penalty_doublings),
        penalty_validation_attempted=bool(instance.penalty_validation_attempted),
    )


__all__ = ['QUBOSpectralProfile', 'constraint_hardness', 'feasibility_subspace_size', 'profile_instance']
