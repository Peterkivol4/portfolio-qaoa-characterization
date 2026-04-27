from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def split_qaoa_angles(params: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    flat = np.asarray(params, dtype=float).reshape(-1)
    if flat.size % 2 != 0:
        raise ValueError("QAOA parameter vector must have even length.")
    half = flat.size // 2
    return flat[:half], flat[half:]


def angle_smoothness(params: np.ndarray) -> float:
    gammas, betas = split_qaoa_angles(params)
    if gammas.size <= 1:
        return 0.0
    return float(np.mean(np.abs(np.diff(gammas))) + np.mean(np.abs(np.diff(betas))))


def angle_curvature(params: np.ndarray) -> float:
    gammas, betas = split_qaoa_angles(params)
    if gammas.size <= 2:
        return 0.0
    gamma_curve = np.mean(np.abs(np.diff(gammas, n=2)))
    beta_curve = np.mean(np.abs(np.diff(betas, n=2)))
    return float(gamma_curve + beta_curve)


def angle_distance(left: np.ndarray, right: np.ndarray) -> float:
    left_arr = np.asarray(left, dtype=float).reshape(-1)
    right_arr = np.asarray(right, dtype=float).reshape(-1)
    if left_arr.shape != right_arr.shape:
        raise ValueError("Angle vectors must have the same shape.")
    return float(np.linalg.norm(left_arr - right_arr))


def parameter_transfer_loss(source_angles: np.ndarray, target_angles: np.ndarray) -> float:
    return angle_distance(source_angles, target_angles)


def parameter_confusion_score(
    parameter_a: np.ndarray,
    parameter_b: np.ndarray,
    angle_a: np.ndarray,
    angle_b: np.ndarray,
    observable_a: np.ndarray,
    observable_b: np.ndarray,
) -> float:
    """Large when physics differs but optimized signatures remain too similar."""

    left = np.asarray(parameter_a, dtype=float).reshape(-1)
    right = np.asarray(parameter_b, dtype=float).reshape(-1)
    if np.allclose(left, right):
        return 0.0

    param_distance = float(np.linalg.norm(left - right))
    angle_gap = float(np.linalg.norm(np.asarray(angle_a, dtype=float) - np.asarray(angle_b, dtype=float)))
    obs_gap = float(np.linalg.norm(np.asarray(observable_a, dtype=float) - np.asarray(observable_b, dtype=float)))
    confusion = 1.0 - (angle_gap + obs_gap) / max(param_distance, 1e-12)
    return float(np.clip(confusion, 0.0, 1.0))


def minimum_p_for_threshold(records: list[dict[str, float]], metric: str, threshold: float) -> int | None:
    eligible = sorted((int(record["p_layers"]), float(record[metric])) for record in records if metric in record)
    for p_layers, value in eligible:
        if np.isfinite(value) and value <= threshold:
            return p_layers
    return None


@dataclass(slots=True)
class ConfusionPair:
    left_regime: str
    right_regime: str
    p_layers: int
    angle_distance: float
    observable_distance: float
    transfer_loss: float
    confusion_score: float


__all__ = [
    "ConfusionPair",
    "angle_curvature",
    "angle_distance",
    "angle_smoothness",
    "minimum_p_for_threshold",
    "parameter_confusion_score",
    "parameter_transfer_loss",
    "split_qaoa_angles",
]
