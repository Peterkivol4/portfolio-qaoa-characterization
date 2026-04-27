from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .spin_hamiltonian import SpinHamiltonian


@dataclass(slots=True)
class ExactDiagonalizationResult:
    eigenvalues: np.ndarray
    ground_state: np.ndarray

    @property
    def ground_energy(self) -> float:
        return float(self.eigenvalues[0])

    @property
    def first_excited_energy(self) -> float:
        if self.eigenvalues.size < 2:
            return float(self.eigenvalues[0])
        return float(self.eigenvalues[1])

    @property
    def spectral_gap(self) -> float:
        if self.eigenvalues.size < 2:
            return 0.0
        return float(self.eigenvalues[1] - self.eigenvalues[0])


def exact_diagonalize_dense(hamiltonian: np.ndarray) -> ExactDiagonalizationResult:
    """Return the sorted dense exact spectrum and normalized ground state."""

    eigenvalues, eigenvectors = np.linalg.eigh(np.asarray(hamiltonian, dtype=np.float64))
    order = np.argsort(eigenvalues)
    values = np.asarray(eigenvalues[order], dtype=float)
    ground = np.asarray(eigenvectors[:, order[0]], dtype=np.complex128)
    norm = np.linalg.norm(ground)
    if norm > 0:
        ground = ground / norm
    return ExactDiagonalizationResult(eigenvalues=values, ground_state=ground)


def exact_diagonalize(model: SpinHamiltonian) -> ExactDiagonalizationResult:
    """Exact diagonalization helper for spin-study Hamiltonians."""

    return exact_diagonalize_dense(model.dense_hamiltonian)


__all__ = ["ExactDiagonalizationResult", "exact_diagonalize", "exact_diagonalize_dense"]
