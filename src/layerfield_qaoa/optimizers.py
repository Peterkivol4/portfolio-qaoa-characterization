from __future__ import annotations

import copy
from dataclasses import dataclass
from itertools import combinations
from math import erf, sqrt
from time import perf_counter
from typing import Any, Callable

import numpy as np
from scipy.optimize import minimize
from scipy.stats import qmc
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel

try:
    import torch
    from botorch.acquisition import LogExpectedImprovement, UpperConfidenceBound
    from botorch.fit import fit_gpytorch_mll
    from botorch.models import SingleTaskGP
    from botorch.models.transforms import Normalize, Standardize
    from botorch.optim import optimize_acqf
    from gpytorch.mlls import ExactMarginalLogLikelihood
except Exception:  # pragma: no cover - optional dependency boundary
    torch = None  # type: ignore[assignment]
    LogExpectedImprovement = None  # type: ignore[misc,assignment]
    UpperConfidenceBound = None  # type: ignore[misc,assignment]
    fit_gpytorch_mll = None  # type: ignore[assignment]
    SingleTaskGP = None  # type: ignore[misc,assignment]
    Normalize = None  # type: ignore[misc,assignment]
    Standardize = None  # type: ignore[misc,assignment]
    optimize_acqf = None  # type: ignore[assignment]
    ExactMarginalLogLikelihood = None  # type: ignore[misc,assignment]

from .config import RunSpec
from .interfaces import SearchPort, TracePort
from .objective import _approx_ratio, evaluate_objective, project_params
from .qubo import PortfolioQUBO
from .results import BackendPulseCard, EvaluationRecord, SearchTrace, TimingBreakdown
from .simulator import BaseExecutor


def _periodic_feature_map(x: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)
    norm = 2.0 * np.pi * (x - lower) / np.maximum(upper - lower, 1e-12)
    return np.concatenate([np.cos(norm), np.sin(norm)], axis=-1)


def _observation_noise_variance(stats, cfg: RunSpec) -> float:
    return max(float(stats.observation_noise_variance), 1e-12)


@dataclass
class BayesianSurrogate(SearchPort):
    bounds: np.ndarray
    cfg: RunSpec

    def __post_init__(self) -> None:
        self.bounds = np.asarray(self.bounds, dtype=float)
        dim = int(self.bounds.shape[1])
        if self.cfg.warm_start_params and len(self.cfg.warm_start_params) != dim:
            raise ValueError(
                f"warm_start_params must contain exactly {dim} parameters for the active bounds."
            )
        self.train_x = np.empty((0, dim), dtype=float)
        self.train_y = np.empty((0,), dtype=float)
        self.train_yvar = np.empty((0,), dtype=float)
        self._dim = dim
        sobol = qmc.Sobol(d=dim, scramble=True, seed=self.cfg.seed)
        init = sobol.random(self.cfg.n_init_points)
        span = self.bounds[1] - self.bounds[0]
        self.init_design = init * span + self.bounds[0]
        if self.cfg.warm_start_params:
            warm_start = project_params(
                np.asarray(self.cfg.warm_start_params, dtype=float),
                self.bounds,
                periodic_wrap=self.cfg.periodic_parameter_wrap,
            )
            self.init_design[0] = warm_start
        self.backend_used = "sobol"
        self._high_dim_active = self._dim > self.cfg.bo_max_gp_dim and self.cfg.bo_high_dim_strategy == "random_embedding"
        if self._high_dim_active:
            dim_rng = np.random.default_rng(self.cfg.seed + 17)
            self.active_dims = np.array(sorted(dim_rng.choice(self._dim, size=self.cfg.bo_max_gp_dim, replace=False).tolist()), dtype=int)
        else:
            self.active_dims = np.arange(self._dim, dtype=int)
        self._last_sklearn_kernel = None

    def suggest(self, rng: np.random.Generator) -> np.ndarray:
        if len(self.train_x) < self.cfg.n_init_points:
            self.backend_used = "sobol"
            return self.init_design[len(self.train_x)].copy()
        suffix = f"_randemb{len(self.active_dims)}" if self._high_dim_active else ""
        if SingleTaskGP is not None and torch is not None:
            try:
                suggestion = self._suggest_botorch()
                self.backend_used = f"botorch_{self.cfg.bo_acquisition}{suffix}"
                return suggestion
            except Exception:
                pass
        self.backend_used = f"sklearn_{self.cfg.bo_acquisition}{suffix}"
        return self._suggest_sklearn(rng)

    def _current_center(self) -> np.ndarray:
        if len(self.train_x) == 0:
            return np.mean(self.bounds, axis=0)
        return self.train_x[int(np.argmin(self.train_y))].copy()

    def _reduced_bounds(self) -> np.ndarray:
        return self.bounds[:, self.active_dims].copy()

    def _reduced_train_x(self) -> np.ndarray:
        return self.train_x[:, self.active_dims]

    def _embed_candidate(self, reduced_candidate: np.ndarray) -> np.ndarray:
        full = self._current_center()
        full[self.active_dims] = np.asarray(reduced_candidate, dtype=float)
        return project_params(full, self.bounds, periodic_wrap=self.cfg.periodic_parameter_wrap)

    def _suggest_botorch(self) -> np.ndarray:
        reduced_train_x_np = self._reduced_train_x()
        reduced_bounds = self._reduced_bounds()
        train_x = torch.as_tensor(reduced_train_x_np, dtype=torch.float64)
        train_y = torch.as_tensor(self.train_y[:, None], dtype=torch.float64)
        train_yvar = torch.as_tensor(self.train_yvar[:, None], dtype=torch.float64).clamp_min(1e-12)
        model = SingleTaskGP(
            train_x,
            train_y,
            train_Yvar=train_yvar,
            input_transform=Normalize(d=reduced_train_x_np.shape[1]),
            outcome_transform=Standardize(m=1),
        )
        mll = ExactMarginalLogLikelihood(model.likelihood, model)
        fit_gpytorch_mll(mll)
        acquisition = UpperConfidenceBound(model, beta=2.0, maximize=False) if self.cfg.bo_acquisition == "ucb" else LogExpectedImprovement(model, best_f=float(np.min(self.train_y)), maximize=False)
        reduced_bounds_t = torch.as_tensor(reduced_bounds, dtype=torch.float64)
        if self.cfg.bo_trust_region:
            center = torch.as_tensor(self._current_center()[self.active_dims], dtype=torch.float64)
            radius = torch.full_like(center, float(self.cfg.bo_trust_region_radius))
            region = torch.stack([torch.maximum(reduced_bounds_t[0], center - radius), torch.minimum(reduced_bounds_t[1], center + radius)])
        else:
            region = reduced_bounds_t
        candidate, _ = optimize_acqf(acquisition, bounds=region, q=1, num_restarts=8, raw_samples=128)
        return self._embed_candidate(candidate.detach().cpu().numpy().reshape(-1))

    def _suggest_sklearn(self, rng: np.random.Generator) -> np.ndarray:
        reduced_train_x = self._reduced_train_x()
        dim = reduced_train_x.shape[1]
        reduced_bounds = self._reduced_bounds()
        lower = reduced_bounds[0]
        upper = reduced_bounds[1]
        transformed_train_x = _periodic_feature_map(reduced_train_x, lower, upper)
        if self._last_sklearn_kernel is None:
            kernel = ConstantKernel(1.0, (1e-6, 1e3)) * Matern(length_scale=np.ones(2 * dim), length_scale_bounds=(1e-3, 1e3), nu=2.5) + WhiteKernel(noise_level=max(float(np.mean(self.train_yvar)), 1e-5), noise_level_bounds=(1e-8, 1e1))
        else:
            kernel = copy.deepcopy(self._last_sklearn_kernel)
        gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True, alpha=1e-8, random_state=self.cfg.seed)
        gp.fit(transformed_train_x, self.train_y)
        self._last_sklearn_kernel = copy.deepcopy(gp.kernel_)

        cand_lower = lower.copy()
        cand_upper = upper.copy()
        if self.cfg.bo_trust_region and len(self.train_x) > 0:
            center = self._current_center()[self.active_dims]
            radius = np.full(dim, float(self.cfg.bo_trust_region_radius))
            cand_lower = np.maximum(cand_lower, center - radius)
            cand_upper = np.minimum(cand_upper, center + radius)
        candidates = rng.uniform(cand_lower, cand_upper, size=(512, dim))
        transformed_candidates = _periodic_feature_map(candidates, lower, upper)
        mean, std = gp.predict(transformed_candidates, return_std=True)
        std = np.maximum(std, 1e-9)
        if self.cfg.bo_acquisition == "ucb":
            score = mean - 2.0 * std
        else:
            best = float(np.min(self.train_y))
            z = (best - mean) / std
            phi = np.exp(-0.5 * z**2) / sqrt(2.0 * np.pi)
            Phi = 0.5 * (1.0 + np.vectorize(erf)(z / sqrt(2.0)))
            score = -((best - mean) * Phi + std * phi)
        return self._embed_candidate(candidates[int(np.argmin(score))])

    def observe(self, x: np.ndarray, y: float, yvar: float) -> None:
        x = np.asarray(x, dtype=float).reshape(1, -1)
        self.train_x = np.vstack([self.train_x, x])
        self.train_y = np.append(self.train_y, float(y))
        self.train_yvar = np.append(self.train_yvar, float(yvar))


@dataclass
class SearchTraceAccumulator(TracePort):
    method: str
    objective_history: list[float]
    raw_objective_history: list[float]
    best_valid_history: list[float]
    valid_ratio_history: list[float]
    feasible_hit_history: list[float]
    variance_history: list[float]
    approx_gap_history: list[float]
    approx_ratio_history: list[float]
    shot_noise_proxy_history: list[float]
    excess_variance_history: list[float]
    best_valid_sharpe_history: list[float]
    zne_correction_history: list[float]
    records: list[EvaluationRecord]
    started: float
    timing_totals: TimingBreakdown
    exact_feasible_reference: float | None = None
    shots_to_first_feasible: float = float("inf")
    effective_shots_consumed: float = 0.0
    best_objective: float = float("inf")
    best_raw_objective: float = float("inf")
    best_valid: float = float("inf")

    @classmethod
    def create(cls, method: str, exact_feasible_reference: float | None = None) -> "SearchTraceAccumulator":
        return cls(
            method=method,
            objective_history=[],
            raw_objective_history=[],
            best_valid_history=[],
            valid_ratio_history=[],
            feasible_hit_history=[],
            variance_history=[],
            approx_gap_history=[],
            approx_ratio_history=[],
            shot_noise_proxy_history=[],
            excess_variance_history=[],
            best_valid_sharpe_history=[],
            zne_correction_history=[],
            records=[],
            started=perf_counter(),
            timing_totals=TimingBreakdown(),
            exact_feasible_reference=exact_feasible_reference,
        )

    def append(self, params: np.ndarray, stats) -> None:
        current_effective_shots = float(getattr(stats.backend_stats, "effective_shots", 0.0))
        if np.isinf(self.shots_to_first_feasible) and stats.feasible_hit:
            self.shots_to_first_feasible = self.effective_shots_consumed + current_effective_shots
        self.best_objective = min(self.best_objective, stats.objective)
        self.best_raw_objective = min(self.best_raw_objective, stats.raw_objective)
        self.best_valid = min(self.best_valid, stats.best_valid_energy)
        self.objective_history.append(float(self.best_objective))
        self.raw_objective_history.append(float(self.best_raw_objective))
        self.best_valid_history.append(float(self.best_valid))
        self.valid_ratio_history.append(float(stats.valid_ratio))
        self.feasible_hit_history.append(float(stats.feasible_hit))
        self.variance_history.append(float(stats.variance))
        self.approx_gap_history.append(float(stats.approx_gap))
        self.approx_ratio_history.append(float(stats.approx_ratio))
        self.shot_noise_proxy_history.append(float(stats.shot_noise_variance_proxy))
        self.excess_variance_history.append(float(stats.excess_variance))
        self.best_valid_sharpe_history.append(float(stats.best_valid_sharpe_ratio))
        self.zne_correction_history.append(float(stats.zne_correction_magnitude))
        self.timing_totals = self.timing_totals + stats.timing
        self.records.append(
            EvaluationRecord(
                evaluation_index=len(self.records) + 1,
                params=[float(value) for value in np.asarray(params, dtype=float)],
                objective=float(stats.objective),
                raw_objective=float(stats.raw_objective),
                variance=float(stats.variance),
                observation_noise_variance=float(stats.observation_noise_variance),
                best_valid_energy=float(stats.best_valid_energy),
                valid_ratio=float(stats.valid_ratio),
                feasible_hit=bool(stats.feasible_hit),
                approx_gap=float(stats.approx_gap),
                timing=stats.timing.as_dict(),
                backend_stats=stats.backend_stats.as_dict(),
                approx_ratio=float(stats.approx_ratio),
                shot_noise_variance_proxy=float(stats.shot_noise_variance_proxy),
                excess_variance=float(stats.excess_variance),
                best_valid_sharpe_ratio=float(stats.best_valid_sharpe_ratio),
                best_valid_bitstring=stats.best_valid_bitstring,
                violation_counts=dict(stats.violation_counts),
                zne_raw_objective_pre_extrapolation=float(stats.zne_raw_objective_pre_extrapolation),
                zne_correction_magnitude=float(stats.zne_correction_magnitude),
            )
        )
        self.effective_shots_consumed += current_effective_shots

    def add_standalone_overhead(self, overhead_seconds: float) -> None:
        if overhead_seconds <= 0.0:
            return
        self.timing_totals.classical_overhead_seconds += float(overhead_seconds)
        self.timing_totals.total_seconds += float(overhead_seconds)

    def build(self) -> SearchTrace:
        return SearchTrace(
            method=self.method,
            objective_history=self.objective_history,
            raw_objective_history=self.raw_objective_history,
            best_valid_history=self.best_valid_history,
            valid_ratio_history=self.valid_ratio_history,
            feasible_hit_history=self.feasible_hit_history,
            variance_history=self.variance_history,
            approx_gap_history=self.approx_gap_history,
            approx_ratio_history=self.approx_ratio_history,
            shot_noise_proxy_history=self.shot_noise_proxy_history,
            excess_variance_history=self.excess_variance_history,
            best_valid_sharpe_history=self.best_valid_sharpe_history,
            zne_correction_history=self.zne_correction_history,
            evaluation_records=self.records,
            elapsed_seconds=perf_counter() - self.started,
            total_objective_calls=len(self.records),
            timing_totals=self.timing_totals,
            exact_feasible_reference=self.exact_feasible_reference,
            shots_to_first_feasible=self.shots_to_first_feasible,
        )


def _apply_optimizer_overhead(stats, overhead_seconds: float) -> None:
    if overhead_seconds <= 0.0:
        return
    stats.timing.classical_overhead_seconds += float(overhead_seconds)
    stats.timing.total_seconds += float(overhead_seconds)
    if getattr(stats.backend_stats, "execution_billing_mode", "job") == "session":
        current_billed = float(stats.backend_stats.estimated_billed_seconds)
        rate = float(stats.backend_stats.estimated_qpu_cost_usd) / max(current_billed, 1e-12) if current_billed > 0.0 else 0.0
        stats.backend_stats.estimated_billed_seconds += float(overhead_seconds)
        stats.backend_stats.estimated_qpu_cost_usd += float(overhead_seconds) * rate


def run_random_search(executor: BaseExecutor, cfg: RunSpec, bounds: np.ndarray, rng: np.random.Generator) -> SearchTrace:
    """Evaluate uniformly sampled QAOA angles under a fixed evaluation budget."""

    trace = SearchTraceAccumulator.create("random", exact_feasible_reference=executor.instance.exact_feasible_energy)
    lower = bounds[0]
    upper = bounds[1]
    for _ in range(cfg.evaluation_budget):
        started = perf_counter()
        params = rng.uniform(lower, upper)
        stats = evaluate_objective(executor, params, cfg, bounds, rng)
        _apply_optimizer_overhead(stats, perf_counter() - started)
        trace.append(params, stats)
    return trace.build()


def run_spsa_search(executor: BaseExecutor, cfg: RunSpec, bounds: np.ndarray, rng: np.random.Generator) -> SearchTrace:
    """Run SPSA on the QAOA parameter landscape with periodic angle projection."""

    trace = SearchTraceAccumulator.create("spsa", exact_feasible_reference=executor.instance.exact_feasible_energy)
    if cfg.warm_start_params:
        x = project_params(
            np.asarray(cfg.warm_start_params, dtype=float),
            bounds,
            periodic_wrap=cfg.periodic_parameter_wrap,
        )
    else:
        x = rng.uniform(bounds[0], bounds[1])
    call_idx = 0
    a = 0.2
    c = 0.1
    A = max(5, cfg.evaluation_budget // 5)
    while call_idx < cfg.evaluation_budget:
        prep_started = perf_counter()
        k = 1 + call_idx // 2
        delta = rng.choice([-1.0, 1.0], size=x.size)
        ck = c / (k**0.101)
        x_plus = project_params(x + ck * delta, bounds, periodic_wrap=cfg.periodic_parameter_wrap)
        overhead = perf_counter() - prep_started
        stats_plus = evaluate_objective(executor, x_plus, cfg, bounds, rng)
        _apply_optimizer_overhead(stats_plus, overhead)
        trace.append(x_plus, stats_plus)
        call_idx += 1
        if call_idx >= cfg.evaluation_budget:
            break

        prep_started = perf_counter()
        x_minus = project_params(x - ck * delta, bounds, periodic_wrap=cfg.periodic_parameter_wrap)
        overhead = perf_counter() - prep_started
        stats_minus = evaluate_objective(executor, x_minus, cfg, bounds, rng)
        _apply_optimizer_overhead(stats_minus, overhead)
        trace.append(x_minus, stats_minus)
        call_idx += 1

        ghat = (stats_plus.objective - stats_minus.objective) / (2.0 * ck * delta)
        if k == 1:
            grad_norm = float(np.linalg.norm(ghat))
            if grad_norm > 1e-8:
                a = 0.1 * float(np.mean(bounds[1] - bounds[0])) / grad_norm
        ak = a / ((k + A) ** 0.602)
        update_started = perf_counter()
        x = project_params(x - ak * ghat, bounds, periodic_wrap=cfg.periodic_parameter_wrap)
        trace.add_standalone_overhead(perf_counter() - update_started)

    return trace.build()


def run_bayesian_search(
    executor: BaseExecutor,
    cfg: RunSpec,
    bounds: np.ndarray,
    rng: np.random.Generator,
    progress: Callable[[str], None] | None = None,
) -> SearchTrace:
    """Run Bayesian optimization over QAOA angles using a GP surrogate model."""

    optimizer = BayesianSurrogate(bounds, cfg)
    trace = SearchTraceAccumulator.create("bayesian_optimization", exact_feasible_reference=executor.instance.exact_feasible_energy)
    for iteration in range(cfg.evaluation_budget):
        suggest_started = perf_counter()
        params = optimizer.suggest(rng)
        suggest_overhead = perf_counter() - suggest_started
        stats = evaluate_objective(executor, params, cfg, bounds, rng)
        observe_started = perf_counter()
        optimizer.observe(
            project_params(params, bounds, periodic_wrap=cfg.periodic_parameter_wrap),
            stats.objective,
            _observation_noise_variance(stats, cfg),
        )
        observe_overhead = perf_counter() - observe_started
        _apply_optimizer_overhead(stats, suggest_overhead + observe_overhead)
        trace.append(params, stats)
        if progress is not None:
            progress(
                f"BO {iteration + 1:03d} | objective={stats.objective:9.4f} | "
                f"best={min(trace.raw_objective_history):9.4f} | valid_ratio={stats.valid_ratio:6.2%} | backend={optimizer.backend_used}"
            )
    return trace.build()


def run_classical_markowitz(instance: PortfolioQUBO, cfg: RunSpec) -> SearchTrace:
    """Solve a classical Markowitz baseline for comparison.

    Small instances are solved exactly by enumerating all budget-feasible supports.
    Larger instances fall back to an SLSQP continuous relaxation and top-k rounding.
    """

    started = perf_counter()
    base = instance.base_matrix

    if instance.n_assets <= cfg.exact_reference_max_assets:
        best_energy = float("inf")
        best_vector = np.zeros(instance.n_assets, dtype=float)
        for chosen in combinations(range(instance.n_assets), instance.budget):
            candidate = np.zeros(instance.n_assets, dtype=float)
            candidate[list(chosen)] = 1.0
            energy = float(candidate @ base @ candidate)
            if energy < best_energy:
                best_energy = energy
                best_vector = candidate
        solver_name = "classical_exact_enumeration"
        stored_params = best_vector
    else:
        x0 = np.full(instance.n_assets, instance.budget / instance.n_assets, dtype=float)
        result = minimize(
            lambda x: float(x @ base @ x),
            x0=x0,
            method="SLSQP",
            bounds=[(0.0, 1.0)] * instance.n_assets,
            constraints=[{"type": "eq", "fun": lambda x: float(np.sum(x) - instance.budget)}],
            options={"maxiter": 200, "ftol": 1e-9},
        )
        relaxed = np.asarray(result.x if result.success else x0, dtype=float)
        support = np.argsort(relaxed)[-instance.budget:]
        best_vector = np.zeros(instance.n_assets, dtype=float)
        best_vector[support] = 1.0
        best_energy = float(best_vector @ base @ best_vector)
        solver_name = "classical_slsqp_relaxation"
        stored_params = relaxed

    elapsed = perf_counter() - started
    if instance.exact_feasible_energy is None:
        approx_gap = float("nan")
        approx_ratio = float("nan")
    else:
        approx_gap = float(best_energy - instance.exact_feasible_energy)
        approx_ratio = _approx_ratio(best_energy, instance.exact_feasible_energy)
    best_bitstring = "".join(str(int(value)) for value in best_vector.astype(int).tolist())
    expected_return = float(instance.mu @ best_vector)
    portfolio_variance = float(best_vector @ instance.sigma @ best_vector)
    sharpe_ratio = float(expected_return / np.sqrt(portfolio_variance)) if portfolio_variance > 1e-12 else float("nan")

    timing = TimingBreakdown(classical_overhead_seconds=elapsed, total_seconds=elapsed)
    backend = BackendPulseCard(backend_name=solver_name, execution_billing_mode="classical")
    record = EvaluationRecord(
        evaluation_index=1,
        params=[float(value) for value in stored_params],
        objective=float(best_energy),
        raw_objective=float(best_energy),
        variance=0.0,
        observation_noise_variance=1e-12,
        best_valid_energy=float(best_energy),
        valid_ratio=1.0,
        feasible_hit=True,
        approx_gap=float(approx_gap),
        timing=timing.as_dict(),
        backend_stats=backend.as_dict(),
        approx_ratio=float(approx_ratio),
        shot_noise_variance_proxy=0.0,
        excess_variance=0.0,
        best_valid_sharpe_ratio=float(sharpe_ratio),
        best_valid_bitstring=best_bitstring,
        violation_counts={0: 1},
        zne_raw_objective_pre_extrapolation=float("nan"),
        zne_correction_magnitude=0.0,
    )
    return SearchTrace(
        method="classical_markowitz",
        objective_history=[float(best_energy)],
        raw_objective_history=[float(best_energy)],
        best_valid_history=[float(best_energy)],
        valid_ratio_history=[1.0],
        feasible_hit_history=[1.0],
        variance_history=[0.0],
        approx_gap_history=[float(approx_gap)],
        approx_ratio_history=[float(approx_ratio)],
        shot_noise_proxy_history=[0.0],
        excess_variance_history=[0.0],
        best_valid_sharpe_history=[float(sharpe_ratio)],
        zne_correction_history=[0.0],
        evaluation_records=[record],
        elapsed_seconds=elapsed,
        total_objective_calls=1,
        timing_totals=timing,
        exact_feasible_reference=instance.exact_feasible_energy,
        shots_to_first_feasible=0.0,
    )


BayesianOptimizer = BayesianSurrogate


__all__ = [
    'BayesianOptimizer', 'BayesianSurrogate', 'SearchTraceAccumulator',
    'run_classical_markowitz', 'run_random_search', 'run_spsa_search', 'run_bayesian_search',
]
