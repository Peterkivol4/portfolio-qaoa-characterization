from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .spin_hamiltonian import SpinHamiltonian


@dataclass(slots=True)
class PhysicalObservables:
    energy: float
    magnetization_z: float
    magnetization_x: float
    nearest_neighbor_correlation: float
    next_nearest_neighbor_correlation: float
    structure_factor: float
    entanglement_entropy: float

    def error_against(self, other: "PhysicalObservables") -> dict[str, float]:
        return {
            "energy_error": abs(self.energy - other.energy),
            "magnetization_z_error": abs(self.magnetization_z - other.magnetization_z),
            "magnetization_x_error": abs(self.magnetization_x - other.magnetization_x),
            "nearest_neighbor_correlation_error": abs(
                self.nearest_neighbor_correlation - other.nearest_neighbor_correlation
            ),
            "next_nearest_neighbor_correlation_error": abs(
                self.next_nearest_neighbor_correlation - other.next_nearest_neighbor_correlation
            ),
            "structure_factor_error": abs(self.structure_factor - other.structure_factor),
            "entanglement_entropy_error": abs(self.entanglement_entropy - other.entanglement_entropy),
        }


def _state_probabilities(state: np.ndarray) -> np.ndarray:
    state = np.asarray(state, dtype=np.complex128).reshape(-1)
    norm = np.linalg.norm(state)
    if norm <= 0:
        raise ValueError("state must have non-zero norm")
    normalized = state / norm
    return np.abs(normalized) ** 2


def magnetization_z(state: np.ndarray, model: SpinHamiltonian) -> float:
    probs = _state_probabilities(state)
    site_expectations = model.z_eigenvalues @ probs
    return float(np.mean(site_expectations))


def magnetization_x(state: np.ndarray, model: SpinHamiltonian) -> float:
    state = np.asarray(state, dtype=np.complex128).reshape(-1)
    state = state / np.linalg.norm(state)
    expectations = []
    for site in range(model.n_spins):
        flipped = state[model.flip_indices[site]]
        expectations.append(float(np.real(np.vdot(state, flipped))))
    return float(np.mean(expectations))


def mean_correlation_z(state: np.ndarray, model: SpinHamiltonian, distance: int) -> float:
    probs = _state_probabilities(state)
    n_spins = model.n_spins
    if distance <= 0 or distance >= n_spins:
        return 0.0
    pairs = []
    for site in range(n_spins - distance):
        pairs.append(model.z_eigenvalues[site] * model.z_eigenvalues[site + distance])
    if model.boundary == "periodic" and distance < n_spins:
        for site in range(n_spins - distance, n_spins):
            pairs.append(model.z_eigenvalues[site] * model.z_eigenvalues[(site + distance) % n_spins])
    if not pairs:
        return 0.0
    pair_mean = np.mean(np.stack(pairs, axis=0), axis=0)
    return float(pair_mean @ probs)


def structure_factor_z(state: np.ndarray, model: SpinHamiltonian, wavevector: float = np.pi) -> float:
    probs = _state_probabilities(state)
    z = model.z_eigenvalues
    n = model.n_spins
    accumulator = 0.0
    for i in range(n):
        for j in range(n):
            phase = np.cos(wavevector * (i - j))
            corr = float((z[i] * z[j]) @ probs)
            accumulator += phase * corr
    return float(max(accumulator / (n * n), 0.0))


def half_chain_entanglement_entropy(state: np.ndarray, n_spins: int) -> float:
    state = np.asarray(state, dtype=np.complex128).reshape(-1)
    state = state / np.linalg.norm(state)
    cut = n_spins // 2
    left_dim = 1 << cut
    right_dim = 1 << (n_spins - cut)
    reshaped = state.reshape(left_dim, right_dim)
    singular_values = np.linalg.svd(reshaped, compute_uv=False)
    probs = np.clip(singular_values**2, 1e-15, 1.0)
    return float(-np.sum(probs * np.log2(probs)))


def energy_expectation(state: np.ndarray, model: SpinHamiltonian) -> float:
    state = np.asarray(state, dtype=np.complex128).reshape(-1)
    state = state / np.linalg.norm(state)
    return float(np.real(np.vdot(state, model.dense_hamiltonian @ state)))


def observe_state(state: np.ndarray, model: SpinHamiltonian) -> PhysicalObservables:
    return PhysicalObservables(
        energy=energy_expectation(state, model),
        magnetization_z=magnetization_z(state, model),
        magnetization_x=magnetization_x(state, model),
        nearest_neighbor_correlation=mean_correlation_z(state, model, distance=1),
        next_nearest_neighbor_correlation=mean_correlation_z(state, model, distance=2),
        structure_factor=structure_factor_z(state, model),
        entanglement_entropy=half_chain_entanglement_entropy(state, model.n_spins),
    )


__all__ = [
    "PhysicalObservables",
    "energy_expectation",
    "half_chain_entanglement_entropy",
    "magnetization_x",
    "magnetization_z",
    "mean_correlation_z",
    "observe_state",
    "structure_factor_z",
]
