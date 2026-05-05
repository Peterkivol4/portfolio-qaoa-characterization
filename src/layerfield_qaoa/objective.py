from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np

from .config import RunSpec
from .results import TailEstimate
from .simulator import BaseExecutor
from .native import tail_cvar_sorted_native


def _approx_ratio(best_valid: float, exact_reference: float | None) -> float:
    """Return a minimization ratio whose direction is stable across energy signs.

    The ratio is normalized so that ``1.0`` means exact recovery and values above
    one always mean "worse than the exact feasible optimum" when the signs of the
    found and exact energies match. For positive exact energies we use
    ``best_valid / exact_reference``; for negative exact energies we invert the
    ratio to ``exact_reference / best_valid`` so the interpretation stays the same.

    This metric is still only comparable within studies where the exact feasible
    reference keeps a consistent sign. If the found energy crosses zero while the
    reference does not, we return ``nan`` instead of pretending the ratio is
    meaningful.
    """

    if exact_reference is None:
        return float("nan")
    best = float(best_valid)
    ref = float(exact_reference)
    if not np.isfinite(best) or not np.isfinite(ref) or abs(ref) <= 1e-12:
        return float("nan")
    if abs(best) <= 1e-12 and abs(ref) > 1e-12:
        return float("nan")
    if np.signbit(best) != np.signbit(ref):
        return float("nan")
    if ref < 0.0:
        if abs(best) <= 1e-12:
            return float("nan")
        return float(ref / best)
    return float(best / ref)


def _legacy_portfolio_sharpe_ratio(instance, bitstring: str | None) -> float:
    if bitstring is None:
        return float("nan")
    x = np.fromiter((int(bit) for bit in bitstring), dtype=float)
    expected_return = float(instance.mu @ x)
    variance = float(x @ instance.sigma @ x)
    if variance <= 1e-12:
        return float("nan")
    return float(expected_return / np.sqrt(variance))


def _sample_snapshot(instance, counts: dict[str, int], cfg: RunSpec) -> dict[str, object]:
    weighted_samples: list[tuple[float, int]] = []
    best_valid = float("inf")
    valid_weight = 0
    best_valid_bitstring: str | None = None
    violation_counts: dict[int, int] = {}
    for bitstring, count in counts.items():
        violation = int(instance.violation(bitstring))
        violation_counts[violation] = violation_counts.get(violation, 0) + int(count)
        is_valid = violation == 0
        if is_valid:
            energy = float(instance.feasible_energy(bitstring))
            if energy < best_valid:
                best_valid = energy
                best_valid_bitstring = bitstring
            valid_weight += int(count)
        else:
            energy = float(instance.energy(bitstring) + cfg.invalid_penalty * violation)
        weighted_samples.append((energy, int(count)))
    raw_objective, variance, observation_noise_variance = weighted_cvar(weighted_samples, cfg.cvar_alpha)
    valid_ratio = valid_weight / max(1, cfg.shots)
    # NOTE: This is a SEM-style proxy, not a true shot/algorithmic decomposition.
    # A genuine decomposition would require repeated evaluations at fixed parameters.
    shot_noise_variance_proxy = max(float(variance) / max(cfg.shots, 1), 1e-12)
    return {
        "raw_objective": float(raw_objective),
        "variance": float(variance),
        "observation_noise_variance": float(observation_noise_variance),
        "shot_noise_variance_proxy": float(shot_noise_variance_proxy),
        "excess_variance": float(max(float(variance) - shot_noise_variance_proxy, 0.0)),
        "best_valid_energy": float(best_valid),
        "best_valid_bitstring": best_valid_bitstring,
        "best_valid_sharpe_ratio": _legacy_portfolio_sharpe_ratio(instance, best_valid_bitstring),
        "valid_ratio": float(valid_ratio),
        "feasible_hit": bool(valid_weight > 0),
        "violation_counts": dict(sorted(violation_counts.items())),
    }


def make_bounds(cfg: RunSpec) -> np.ndarray:
    """
    Parameter bounds with shape (2, 2 * p_layers).

    Parameter order is [gamma_0, beta_0, gamma_1, beta_1, ...].
    gamma in [0, 2pi), beta in [0, pi).
    """
    intervals = []
    for _ in range(cfg.p_layers):
        intervals.append((0.0, 2.0 * np.pi))
        intervals.append((0.0, np.pi))
    return np.asarray(intervals, dtype=float).T


def project_params(params: np.ndarray, bounds: np.ndarray, periodic_wrap: bool = True) -> np.ndarray:
    """Map QAOA angles back into the legal parameter domain."""

    params = np.asarray(params, dtype=float)
    lower = np.asarray(bounds[0], dtype=float)
    upper = np.asarray(bounds[1], dtype=float)
    span = np.maximum(upper - lower, 1e-12)
    if periodic_wrap:
        return np.mod(params - lower, span) + lower
    return np.clip(params, lower, upper)


def weighted_cvar(samples: Iterable[Tuple[float, int]], alpha: float) -> tuple[float, float, float]:
    """
    Lower-tail CVaR for a minimization objective.

    The tail variance is computed as E[X^2 | tail] - (E[X | tail])^2.
    """
    ordered = sorted(samples, key=lambda item: item[0])
    if not ordered:
        return 0.0, 1e-12, 1e-12
    energies = np.asarray([float(energy) for energy, _ in ordered], dtype=np.float64)
    weights = np.asarray([float(weight) for _, weight in ordered], dtype=np.float64)
    total_weight = float(weights.sum())
    if total_weight <= 0.0:
        return 0.0, 1e-12, 1e-12

    native = tail_cvar_sorted_native(energies, weights, alpha)
    if native is not None:
        return native

    target = max(alpha * total_weight, 1.0)
    cumulative = 0.0
    taken_weights = []
    taken_energies = []
    for energy, weight in zip(energies, weights, strict=True):
        share = min(float(weight), target - cumulative)
        if share <= 0.0:
            break
        taken_energies.append(float(energy))
        taken_weights.append(float(share))
        cumulative += share
        if cumulative >= target:
            break
    ew = np.asarray(taken_weights, dtype=np.float64)
    ex = np.asarray(taken_energies, dtype=np.float64)
    mean = float(np.dot(ex, ew) / cumulative)
    second = float(np.dot(ex * ex, ew) / cumulative)
    variance = max(1e-12, second - mean**2)
    # estimator noise proxy for the surrogate model; lower-tail dispersion alone is not
    # the same thing as measurement uncertainty, so we scale by the effective tail sample size
    observation_noise_variance = max(variance / cumulative, 1e-12)
    return float(mean), float(variance), float(observation_noise_variance)


def evaluate_objective(
    executor: BaseExecutor,
    params: np.ndarray,
    cfg: RunSpec,
    bounds: np.ndarray,
    rng: np.random.Generator,
) -> TailEstimate:
    """Estimate the CVaR-style QAOA objective for one parameter vector.

    Parameters are projected into the legal QAOA angle box, the executor produces
    bitstring counts, and the objective is formed from lower-tail energies with an
    additional feasibility penalty when BO is configured to target feasibility-aware
    search. The returned ``TailEstimate`` includes both optimization targets and the
    scientific diagnostics needed for benchmarking.
    """

    params = project_params(params, bounds, periodic_wrap=cfg.periodic_parameter_wrap)
    counts, timing, backend_stats = executor.run(params, cfg.shots, rng)
    snapshot = _sample_snapshot(executor.instance, counts, cfg)
    raw_objective = float(snapshot["raw_objective"])
    variance = float(snapshot["variance"])
    observation_noise_variance = float(snapshot["observation_noise_variance"])
    best_valid = float(snapshot["best_valid_energy"])
    valid_ratio = float(snapshot["valid_ratio"])
    objective = float(raw_objective)
    if cfg.bo_target == "feasibility_aware":
        objective = raw_objective + cfg.bo_feasibility_weight * (1.0 - valid_ratio)
    exact_reference = executor.instance.exact_feasible_energy
    if exact_reference is None:
        approx_gap = float("nan")
    elif np.isfinite(best_valid):
        approx_gap = float(best_valid - exact_reference)
    else:
        approx_gap = float("inf")
    zne_raw_objective_pre_extrapolation = float("nan")
    zne_correction_magnitude = 0.0
    if backend_stats.zne_pre_extrapolation_counts:
        zne_snapshot = _sample_snapshot(executor.instance, backend_stats.zne_pre_extrapolation_counts, cfg)
        zne_raw_objective_pre_extrapolation = float(zne_snapshot["raw_objective"])
        zne_correction_magnitude = float(abs(raw_objective - zne_raw_objective_pre_extrapolation))
    return TailEstimate(
        objective=float(objective),
        raw_objective=float(raw_objective),
        variance=float(variance),
        observation_noise_variance=float(observation_noise_variance),
        best_valid_energy=float(best_valid),
        valid_ratio=float(valid_ratio),
        feasible_hit=bool(snapshot["feasible_hit"]),
        approx_gap=approx_gap,
        timing=timing,
        backend_stats=backend_stats,
        approx_ratio=_approx_ratio(best_valid, exact_reference),
        shot_noise_variance_proxy=float(snapshot["shot_noise_variance_proxy"]),
        excess_variance=float(snapshot["excess_variance"]),
        best_valid_sharpe_ratio=float(snapshot["best_valid_sharpe_ratio"]),
        best_valid_bitstring=snapshot["best_valid_bitstring"],
        violation_counts=dict(snapshot["violation_counts"]),
        zne_raw_objective_pre_extrapolation=zne_raw_objective_pre_extrapolation,
        zne_correction_magnitude=zne_correction_magnitude,
    )


__all__ = ['make_bounds', 'project_params', 'weighted_cvar', 'evaluate_objective']
