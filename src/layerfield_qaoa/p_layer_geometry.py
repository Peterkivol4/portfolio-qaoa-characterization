from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import perf_counter

import numpy as np
from scipy.stats import qmc
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel

from .config import SpinRunConfig
from .exact_diagonalization import ExactDiagonalizationResult, exact_diagonalize
from .parameter_emergence import angle_curvature, angle_smoothness
from .physical_observables import PhysicalObservables, observe_state
from .spin_hamiltonian import SpinHamiltonian, build_spin_hamiltonian


@dataclass(slots=True)
class PLayerResolutionRecord:
    n_spins: int
    p_layers: int
    j1: float
    j2: float
    h: float
    disorder_strength: float
    regime: str
    optimizer: str
    seed: int
    energy_error: float
    approximation_ratio: float | None
    ground_state_fidelity: float | None
    magnetization_z_error: float
    magnetization_x_error: float
    zz_correlation_error: float
    structure_factor_error: float | None
    entanglement_entropy_error: float | None
    angle_smoothness: float
    angle_curvature: float
    parameter_transfer_loss: float | None
    parameter_confusion_score: float | None
    runtime_seconds: float
    objective_calls: int
    parameter_count: int
    circuit_depth: int
    nearest_neighbor_correlation_error: float = 0.0
    next_nearest_neighbor_correlation_error: float = 0.0
    best_energy: float = float("nan")
    exact_ground_energy: float = float("nan")
    best_params: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class SpinOptimizationResult:
    best_params: np.ndarray
    best_energy: float
    objective_calls: int
    runtime_seconds: float
    objective_history: list[float]


def qaoa_parameter_count(p_layers: int) -> int:
    return 2 * int(p_layers)


def qaoa_circuit_depth(p_layers: int) -> int:
    return 2 * int(p_layers)


def standard_qaoa_initial_state(n_spins: int) -> np.ndarray:
    dim = 1 << n_spins
    return np.full(dim, 1.0 / np.sqrt(dim), dtype=np.complex128)


def _apply_cost_layer(state: np.ndarray, gamma: float, model: SpinHamiltonian) -> np.ndarray:
    phase = np.exp(-1j * float(gamma) * model.cost_diagonal)
    return phase * state


def _apply_mixer_layer(state: np.ndarray, beta: float, model: SpinHamiltonian) -> np.ndarray:
    updated = np.asarray(state, dtype=np.complex128)
    c = np.cos(beta)
    s = 1j * np.sin(beta)
    for site in range(model.n_spins):
        updated = c * updated + s * updated[model.flip_indices[site]]
    return updated


def build_qaoa_state(params: np.ndarray, model: SpinHamiltonian, p_layers: int) -> np.ndarray:
    flat = np.asarray(params, dtype=float).reshape(-1)
    if flat.size != qaoa_parameter_count(p_layers):
        raise ValueError(f"Expected {qaoa_parameter_count(p_layers)} QAOA parameters for p_layers={p_layers}.")
    state = standard_qaoa_initial_state(model.n_spins)
    gammas = flat[:p_layers]
    betas = flat[p_layers:]
    for gamma, beta in zip(gammas, betas, strict=True):
        state = _apply_cost_layer(state, gamma, model)
        state = _apply_mixer_layer(state, beta, model)
    norm = np.linalg.norm(state)
    if norm > 0:
        state = state / norm
    return state


def _approximation_ratio(energy: float, reference: float) -> float | None:
    if abs(reference) <= 1e-12:
        return None
    return float(energy / reference)


def ground_state_fidelity(state: np.ndarray, exact_result: ExactDiagonalizationResult) -> float:
    state = np.asarray(state, dtype=np.complex128).reshape(-1)
    state = state / np.linalg.norm(state)
    overlap = np.vdot(exact_result.ground_state, state)
    return float(abs(overlap) ** 2)


def evaluate_qaoa_state(
    params: np.ndarray,
    model: SpinHamiltonian,
    exact_result: ExactDiagonalizationResult,
    p_layers: int,
) -> tuple[float, PhysicalObservables, float]:
    state = build_qaoa_state(params, model, p_layers)
    observables = observe_state(state, model)
    fidelity = ground_state_fidelity(state, exact_result)
    return observables.energy, observables, fidelity


def _bounds(dim: int) -> np.ndarray:
    return np.vstack([np.full(dim, -np.pi), np.full(dim, np.pi)])


def _random_params(rng: np.random.Generator, dim: int) -> np.ndarray:
    return rng.uniform(-np.pi, np.pi, size=dim)


def _fit_gp(samples: np.ndarray, values: np.ndarray) -> GaussianProcessRegressor:
    kernel = ConstantKernel(1.0, (1e-4, 1e3)) * Matern(length_scale=np.ones(samples.shape[1]), nu=2.5) + WhiteKernel(1e-5)
    gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True, alpha=1e-8, random_state=0)
    gp.fit(samples, values)
    return gp


def optimize_spin_qaoa(
    model: SpinHamiltonian,
    cfg: SpinRunConfig,
    exact_result: ExactDiagonalizationResult,
    rng: np.random.Generator,
) -> SpinOptimizationResult:
    dim = qaoa_parameter_count(cfg.p_layers)
    started = perf_counter()
    history: list[float] = []

    def objective(params: np.ndarray) -> float:
        energy, _obs, _fid = evaluate_qaoa_state(params, model, exact_result, cfg.p_layers)
        best = energy if not history else min(history[-1], energy)
        history.append(float(best))
        return float(energy)

    if cfg.optimizer == "random":
        best_energy = float("inf")
        best_params = _random_params(rng, dim)
        for _ in range(cfg.evaluation_budget):
            params = _random_params(rng, dim)
            energy = objective(params)
            if energy < best_energy:
                best_energy = energy
                best_params = params.copy()
        return SpinOptimizationResult(best_params=best_params, best_energy=best_energy, objective_calls=cfg.evaluation_budget, runtime_seconds=perf_counter() - started, objective_history=history)

    if cfg.optimizer == "spsa":
        params = _random_params(rng, dim)
        best_params = params.copy()
        best_energy = objective(params)
        max_steps = max(1, (cfg.evaluation_budget - 1) // 2)
        a = 0.2
        c = 0.1
        A = max(5.0, cfg.evaluation_budget / 5.0)
        calls = 1
        for k in range(1, max_steps + 1):
            delta = rng.choice([-1.0, 1.0], size=dim)
            ck = c / (k ** 0.101)
            plus = np.clip(params + ck * delta, -np.pi, np.pi)
            minus = np.clip(params - ck * delta, -np.pi, np.pi)
            f_plus = objective(plus)
            f_minus = objective(minus)
            calls += 2
            ghat = (f_plus - f_minus) / (2.0 * ck * delta)
            ak = a / ((k + A) ** 0.602)
            params = np.clip(params - ak * ghat, -np.pi, np.pi)
            current = objective(params)
            calls += 1
            if current < best_energy:
                best_energy = current
                best_params = params.copy()
            if calls >= cfg.evaluation_budget:
                break
        return SpinOptimizationResult(best_params=best_params, best_energy=best_energy, objective_calls=min(calls, cfg.evaluation_budget), runtime_seconds=perf_counter() - started, objective_history=history)

    n_init = min(6, cfg.evaluation_budget)
    sobol = qmc.Sobol(d=dim, scramble=True, seed=cfg.seed)
    design = sobol.random(n_init)
    design = -np.pi + 2.0 * np.pi * design
    xs: list[np.ndarray] = []
    ys: list[float] = []
    best_energy = float("inf")
    best_params = design[0].copy()
    for params in design:
        energy = objective(params)
        xs.append(params.copy())
        ys.append(energy)
        if energy < best_energy:
            best_energy = energy
            best_params = params.copy()

    calls = len(xs)
    while calls < cfg.evaluation_budget:
        gp = _fit_gp(np.asarray(xs), np.asarray(ys))
        candidates = rng.uniform(-np.pi, np.pi, size=(256, dim))
        mean, std = gp.predict(candidates, return_std=True)
        score = mean - 1.96 * np.maximum(std, 1e-9)
        params = candidates[int(np.argmin(score))]
        energy = objective(params)
        xs.append(params.copy())
        ys.append(energy)
        calls += 1
        if energy < best_energy:
            best_energy = energy
            best_params = params.copy()

    return SpinOptimizationResult(best_params=best_params, best_energy=best_energy, objective_calls=calls, runtime_seconds=perf_counter() - started, objective_history=history)


def run_single_spin_instance(cfg: SpinRunConfig, rng: np.random.Generator | None = None) -> PLayerResolutionRecord:
    """Optimize one p-layer spin instance and summarize physical recovery."""

    cfg = cfg.normalized()
    rng = np.random.default_rng(cfg.seed) if rng is None else rng
    model = build_spin_hamiltonian(cfg, rng)
    exact_result = exact_diagonalize(model)
    exact_observables = observe_state(exact_result.ground_state, model)
    optimum = optimize_spin_qaoa(model, cfg, exact_result, rng)
    best_energy, best_observables, fidelity = evaluate_qaoa_state(optimum.best_params, model, exact_result, cfg.p_layers)
    errors = best_observables.error_against(exact_observables)

    return PLayerResolutionRecord(
        n_spins=cfg.n_spins,
        p_layers=cfg.p_layers,
        j1=cfg.j1,
        j2=cfg.j2,
        h=cfg.transverse_field,
        disorder_strength=cfg.disorder_strength,
        regime=model.regime,
        optimizer=cfg.optimizer,
        seed=cfg.seed,
        energy_error=float(errors["energy_error"]),
        approximation_ratio=_approximation_ratio(best_energy, exact_result.ground_energy),
        ground_state_fidelity=float(fidelity),
        magnetization_z_error=float(errors["magnetization_z_error"]),
        magnetization_x_error=float(errors["magnetization_x_error"]),
        zz_correlation_error=float(errors["nearest_neighbor_correlation_error"]),
        structure_factor_error=float(errors["structure_factor_error"]),
        entanglement_entropy_error=float(errors["entanglement_entropy_error"]),
        angle_smoothness=float(angle_smoothness(optimum.best_params)),
        angle_curvature=float(angle_curvature(optimum.best_params)),
        parameter_transfer_loss=None,
        parameter_confusion_score=None,
        runtime_seconds=float(optimum.runtime_seconds),
        objective_calls=int(optimum.objective_calls),
        parameter_count=qaoa_parameter_count(cfg.p_layers),
        circuit_depth=qaoa_circuit_depth(cfg.p_layers),
        nearest_neighbor_correlation_error=float(errors["nearest_neighbor_correlation_error"]),
        next_nearest_neighbor_correlation_error=float(errors["next_nearest_neighbor_correlation_error"]),
        best_energy=float(best_energy),
        exact_ground_energy=float(exact_result.ground_energy),
        best_params=[float(value) for value in optimum.best_params],
    )


__all__ = [
    "PLayerResolutionRecord",
    "SpinOptimizationResult",
    "build_qaoa_state",
    "evaluate_qaoa_state",
    "ground_state_fidelity",
    "optimize_spin_qaoa",
    "qaoa_circuit_depth",
    "qaoa_parameter_count",
    "run_single_spin_instance",
    "standard_qaoa_initial_state",
]
