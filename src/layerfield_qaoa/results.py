from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np


def _safe_ratio(numerator: float, denominator: float) -> float:
    num = float(numerator)
    den = float(denominator)
    if not np.isfinite(den) or abs(den) <= 1e-12:
        return float("nan")
    if np.isposinf(num):
        return float("inf")
    if np.isneginf(num):
        return float("-inf")
    if not np.isfinite(num):
        return float("nan")
    return float(num / den)


def _history_auc(history: list[float], reference: float | None) -> float:
    if reference is None or not np.isfinite(float(reference)) or not history:
        return float("nan")
    finite_indices = [idx for idx, value in enumerate(history) if np.isfinite(float(value))]
    if not finite_indices:
        return float("nan")
    regret = [float(history[idx]) - float(reference) for idx in finite_indices]
    arr = np.asarray(regret, dtype=float)
    if arr.size == 1:
        return float(arr[0])
    if hasattr(np, "trapezoid"):
        return float(np.trapezoid(arr, x=np.asarray(finite_indices, dtype=float)))
    return float(np.trapz(arr, x=np.asarray(finite_indices, dtype=float)))


def _merge_violation_counts(records: list["EvaluationRecord"]) -> dict[int, int]:
    merged: dict[int, int] = {}
    for record in records:
        for key, value in record.violation_counts.items():
            violation = int(key)
            merged[violation] = merged.get(violation, 0) + int(value)
    return dict(sorted(merged.items()))


def _mean_violation(counts: dict[int, int]) -> float:
    total = sum(int(v) for v in counts.values())
    if total <= 0:
        return 0.0
    weighted = sum(int(k) * int(v) for k, v in counts.items())
    return float(weighted / total)


@dataclass
class TimingBreakdown:
    classical_overhead_seconds: float = 0.0
    circuit_construction_seconds: float = 0.0
    transpilation_seconds: float = 0.0
    execution_seconds: float = 0.0
    mitigation_seconds: float = 0.0
    queue_latency_seconds: float = 0.0
    total_seconds: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return asdict(self)

    def __add__(self, other: "TimingBreakdown") -> "TimingBreakdown":
        return TimingBreakdown(
            classical_overhead_seconds=self.classical_overhead_seconds + other.classical_overhead_seconds,
            circuit_construction_seconds=self.circuit_construction_seconds + other.circuit_construction_seconds,
            transpilation_seconds=self.transpilation_seconds + other.transpilation_seconds,
            execution_seconds=self.execution_seconds + other.execution_seconds,
            mitigation_seconds=self.mitigation_seconds + other.mitigation_seconds,
            queue_latency_seconds=self.queue_latency_seconds + other.queue_latency_seconds,
            total_seconds=self.total_seconds + other.total_seconds,
        )


@dataclass
class BackendPulseCard:
    backend_name: str
    initial_state_strategy: str = "uniform_superposition"
    simulator_seed: int | None = None
    zne_simulator_seeds: list[int] = field(default_factory=list)
    transpiled_depth: int = 0
    transpiled_size: int = 0
    two_qubit_gate_count: int = 0
    swap_gate_count: int = 0
    shot_multiplier: float = 1.0
    effective_shots: float = 0.0
    transpile_topology: str = "all_to_all"
    basis_gates: list[str] = field(default_factory=list)
    routing_method: str = "sabre"
    seed_transpiler: int | None = None
    execution_billing_mode: str = "job"
    calibration_aware_routing: bool = False
    mean_mock_cnot_error: float = 0.0
    max_mock_cnot_error: float = 0.0
    estimated_swap_risk_penalty: float = 0.0
    estimated_billed_seconds: float = 0.0
    estimated_qpu_cost_usd: float = 0.0
    zne_pre_extrapolation_counts: dict[str, int] | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TailEstimate:
    objective: float
    raw_objective: float
    variance: float
    observation_noise_variance: float
    best_valid_energy: float
    valid_ratio: float
    feasible_hit: bool
    approx_gap: float
    timing: TimingBreakdown
    backend_stats: BackendPulseCard
    approx_ratio: float = float("nan")
    shot_noise_variance_proxy: float = 0.0
    excess_variance: float = 0.0
    best_valid_sharpe_ratio: float = float("nan")
    best_valid_bitstring: str | None = None
    violation_counts: dict[int, int] = field(default_factory=dict)
    zne_raw_objective_pre_extrapolation: float = float("nan")
    zne_correction_magnitude: float = 0.0


@dataclass
class EvaluationRecord:
    evaluation_index: int
    params: list[float]
    objective: float
    raw_objective: float
    variance: float
    observation_noise_variance: float
    best_valid_energy: float
    valid_ratio: float
    feasible_hit: bool
    approx_gap: float
    timing: dict[str, float]
    backend_stats: dict[str, Any]
    approx_ratio: float = float("nan")
    shot_noise_variance_proxy: float = 0.0
    excess_variance: float = 0.0
    best_valid_sharpe_ratio: float = float("nan")
    best_valid_bitstring: str | None = None
    violation_counts: dict[int, int] = field(default_factory=dict)
    zne_raw_objective_pre_extrapolation: float = float("nan")
    zne_correction_magnitude: float = 0.0


@dataclass
class SearchTrace:
    method: str
    objective_history: list[float]
    raw_objective_history: list[float]
    best_valid_history: list[float]
    valid_ratio_history: list[float]
    feasible_hit_history: list[float]
    variance_history: list[float]
    approx_gap_history: list[float]
    approx_ratio_history: list[float] = field(default_factory=list)
    shot_noise_proxy_history: list[float] = field(default_factory=list)
    excess_variance_history: list[float] = field(default_factory=list)
    best_valid_sharpe_history: list[float] = field(default_factory=list)
    zne_correction_history: list[float] = field(default_factory=list)
    evaluation_records: list[EvaluationRecord] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    total_objective_calls: int = 0
    timing_totals: TimingBreakdown = field(default_factory=TimingBreakdown)
    exact_feasible_reference: float | None = None
    shots_to_first_feasible: float = float("inf")

    def as_summary(self) -> dict[str, Any]:
        """Return a flat summary used by JSON payloads and suite exports.

        ``best_approx_ratio`` is normalized so that values above one mean "worse than
        exact" for both positive- and negative-energy regimes, but it is still only
        comparable within studies where the exact feasible reference keeps a
        consistent sign.
        """

        best_raw_record = min(self.evaluation_records, key=lambda record: float(record.raw_objective), default=None)
        best_valid_record = min(self.evaluation_records, key=lambda record: float(record.best_valid_energy), default=None)
        best_params = [] if best_raw_record is None else best_raw_record.params
        total_effective_shots = sum(record.backend_stats.get("effective_shots", 0.0) for record in self.evaluation_records)
        total_estimated_qpu_cost = sum(record.backend_stats.get("estimated_qpu_cost_usd", 0.0) for record in self.evaluation_records)
        total_estimated_billed_seconds = sum(record.backend_stats.get("estimated_billed_seconds", 0.0) for record in self.evaluation_records)
        aggregate_violation_counts = _merge_violation_counts(self.evaluation_records)
        best_valid_energy = float(min(self.best_valid_history)) if self.best_valid_history else float("inf")
        approx_ratio_values = [float(value) for value in self.approx_ratio_history if np.isfinite(float(value))]
        shot_noise_values = [float(value) for value in self.shot_noise_proxy_history if np.isfinite(float(value))]
        excess_values = [float(value) for value in self.excess_variance_history if np.isfinite(float(value))]
        zne_values = [float(value) for value in self.zne_correction_history if np.isfinite(float(value))]
        sharpe_values = [float(value) for value in self.best_valid_sharpe_history if np.isfinite(float(value))]
        return {
            "method": self.method,
            "best_objective": float(min(self.objective_history)) if self.objective_history else float("inf"),
            "best_raw_objective": float(min(self.raw_objective_history)) if self.raw_objective_history else float("inf"),
            "best_valid_energy": best_valid_energy,
            "best_valid_ratio": float(max(self.valid_ratio_history)) if self.valid_ratio_history else 0.0,
            "feasible_hit_rate": float(sum(self.feasible_hit_history) / len(self.feasible_hit_history)) if self.feasible_hit_history else 0.0,
            "mean_objective_variance": float(sum(self.variance_history) / len(self.variance_history)) if self.variance_history else 0.0,
            "mean_approx_gap": float(sum(self.approx_gap_history) / len(self.approx_gap_history)) if self.approx_gap_history else float("inf"),
            "best_approx_ratio": float("nan") if best_valid_record is None else float(best_valid_record.approx_ratio),
            "mean_approx_ratio": float(sum(approx_ratio_values) / len(approx_ratio_values)) if approx_ratio_values else float("nan"),
            "approx_ratio_note": "Ratio is normalized so >1 means worse than exact, but compare only within study slices whose exact-feasible reference sign is consistent.",
            "best_valid_regret_auc": _history_auc(self.best_valid_history, self.exact_feasible_reference),
            "mean_shot_noise_variance_proxy": float(sum(shot_noise_values) / len(shot_noise_values)) if shot_noise_values else 0.0,
            "mean_excess_variance": float(sum(excess_values) / len(excess_values)) if excess_values else 0.0,
            "best_valid_sharpe_ratio": float("nan") if best_valid_record is None else float(best_valid_record.best_valid_sharpe_ratio),
            "mean_best_valid_sharpe_ratio": float(sum(sharpe_values) / len(sharpe_values)) if sharpe_values else float("nan"),
            "best_valid_bitstring": None if best_valid_record is None else best_valid_record.best_valid_bitstring,
            "violation_counts": aggregate_violation_counts,
            "mean_budget_violation": _mean_violation(aggregate_violation_counts),
            "mean_zne_correction_magnitude": float(sum(zne_values) / len(zne_values)) if zne_values else 0.0,
            "max_zne_correction_magnitude": float(max(zne_values)) if zne_values else 0.0,
            "best_valid_energy_per_shot": _safe_ratio(best_valid_energy, total_effective_shots),
            "best_valid_energy_per_usd": _safe_ratio(best_valid_energy, total_estimated_qpu_cost),
            "shots_to_first_feasible": float(self.shots_to_first_feasible),
            "objective_history": self.objective_history,
            "raw_objective_history": self.raw_objective_history,
            "best_valid_history": self.best_valid_history,
            "valid_ratio_history": self.valid_ratio_history,
            "feasible_hit_history": self.feasible_hit_history,
            "variance_history": self.variance_history,
            "approx_gap_history": self.approx_gap_history,
            "approx_ratio_history": self.approx_ratio_history,
            "shot_noise_proxy_history": self.shot_noise_proxy_history,
            "excess_variance_history": self.excess_variance_history,
            "best_valid_sharpe_history": self.best_valid_sharpe_history,
            "zne_correction_history": self.zne_correction_history,
            "elapsed_seconds": self.elapsed_seconds,
            "total_objective_calls": self.total_objective_calls,
            "timing_totals": self.timing_totals.as_dict(),
            "total_effective_shots": total_effective_shots,
            "total_estimated_billed_seconds": total_estimated_billed_seconds,
            "total_estimated_qpu_cost_usd": total_estimated_qpu_cost,
            "exact_feasible_reference": self.exact_feasible_reference,
            "best_params": best_params,
            "evaluation_records": [asdict(record) for record in self.evaluation_records],
        }


__all__ = [
    'TimingBreakdown',
    'BackendPulseCard',
    'TailEstimate',
    'EvaluationRecord',
    'SearchTrace',
]
