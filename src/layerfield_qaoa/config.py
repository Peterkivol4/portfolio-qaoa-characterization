from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, replace
from math import pi
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from .constants import (
    DEFAULT_SUITE_OUTPUT_DIR,
    DEFAULT_SUITE_TITLE,
    FAST_SIM_MAX_ASSETS,
    VALID_BO_ACQUISITIONS,
    VALID_BO_HIGH_DIM_STRATEGIES,
    VALID_BO_TARGETS,
    VALID_EXECUTION_BILLING_MODES,
    VALID_EXECUTION_MODES,
    VALID_MIXER_TYPES,
    VALID_NOISE_MODELS,
    VALID_QPU_BILLING_BASIS,
    VALID_REGIMES,
    VALID_ROUTING_METHODS,
    VALID_TRANSPILE_OPTIMIZATION_LEVELS,
    VALID_TRANSPILE_TOPOLOGIES,
)

VALID_SUITE_STUDY_MODES = {"independent", "factorial"}
VALID_SPIN_BOUNDARIES = {"open", "periodic"}
VALID_SPIN_REGIMES = {
    "ferromagnetic",
    "near_critical",
    "frustrated",
    "strong_field",
    "disordered",
    "mixed_frustrated_disordered",
}
VALID_SPIN_ANSATZ_FAMILIES = {"standard_qaoa"}
VALID_SPIN_MIXERS = {"x"}
VALID_SPIN_OPTIMIZERS = {"random", "spsa", "bayesian_optimization"}


@dataclass
class RunConfig:
    """Configuration for one legacy portfolio-QAOA compatibility run."""

    n_assets: int = 10
    budget: int = 4
    p_layers: int = 3
    risk_aversion: float = 0.6
    evaluation_budget: int = 40
    n_init_points: int = 8
    shots: int = 2048
    cvar_alpha: float = 0.1
    invalid_penalty: float = 50.0
    seed: int = 42
    output_prefix: str = "legacy_portfolio_qaoa"

    regime: str = "baseline"

    execution_mode: str = "fast_simulator"
    backend_name: str = "aer_simulator"
    execution_billing_mode: str = "job"
    qpu_billing_basis: str = "total"
    qpu_pricing_tier: str = "custom"
    qpu_price_per_second_usd: float = 0.0
    job_queue_latency_seconds: float = 2.0

    transpile_optimization_level: int = 1
    transpile_topology: str = "auto"
    routing_method: str = "sabre"
    basis_gates: tuple[str, ...] = ()
    seed_transpiler: int | None = None
    calibration_aware_routing: bool = False
    mock_edge_fidelity_sigma: float = 0.003
    mock_cnot_error_mean: float = 0.01

    noise_model: str = "ideal"
    depolarizing_strength_1q: float = 0.001
    depolarizing_strength_2q: float = 0.01
    t1: float = 100e-6
    t2: float = 80e-6
    gate_time_1q: float = 50e-9
    gate_time_2q: float = 300e-9
    measurement_error: float = 0.01
    measurement_mitigation: bool = False
    measurement_mitigation_max_bits: int = 12
    resilience_level: int = 0
    zne_mitigation: bool = False
    zne_noise_factors: tuple[int, ...] = (1, 3, 5)
    twirling: bool = False
    twirling_randomizations: int = 1

    qubo_penalty_multiplier: float = 2.0
    mixer_type: str = "xy"
    penalty_validation_max_assets: int = 14
    penalty_validation_max_tries: int = 8
    exact_reference_max_assets: int = 14
    dicke_init_max_assets: int = 12

    bo_acquisition: str = "ucb"
    bo_trust_region: bool = True
    bo_trust_region_radius: float = pi / 3.0
    bo_target: str = "raw"
    bo_feasibility_weight: float = 25.0
    bo_max_gp_dim: int = 16
    bo_high_dim_strategy: str = "random_embedding"
    periodic_parameter_wrap: bool = True
    warm_start_params: list[float] = field(default_factory=list)

    bootstrap_resamples: int = 1000
    save_individual_runs: bool = True

    def validate(self) -> None:
        if self.n_assets <= 0:
            raise ValueError("n_assets must be positive.")
        if self.execution_mode == "fast_simulator" and self.n_assets > FAST_SIM_MAX_ASSETS:
            raise ValueError("n_assets must be at most 12 for the built-in statevector simulator.")
        if not (0 < self.budget <= self.n_assets):
            raise ValueError("budget must lie in [1, n_assets].")
        if self.p_layers <= 0:
            raise ValueError("p_layers must be positive.")
        if self.evaluation_budget <= 0:
            raise ValueError("evaluation_budget must be positive.")
        if self.n_init_points <= 0:
            raise ValueError("n_init_points must be positive.")
        if self.n_init_points > self.evaluation_budget:
            raise ValueError("n_init_points cannot exceed evaluation_budget.")
        if self.shots <= 0:
            raise ValueError("shots must be positive.")
        if not (0.0 < self.cvar_alpha <= 1.0):
            raise ValueError("cvar_alpha must lie in (0, 1].")
        if self.invalid_penalty < 0.0:
            raise ValueError("invalid_penalty must be non-negative.")
        if self.regime not in VALID_REGIMES:
            raise ValueError(f"regime must be one of {sorted(VALID_REGIMES)}.")
        if self.execution_mode not in VALID_EXECUTION_MODES:
            raise ValueError(f"execution_mode must be one of {sorted(VALID_EXECUTION_MODES)}.")
        if self.execution_billing_mode not in VALID_EXECUTION_BILLING_MODES:
            raise ValueError(f"execution_billing_mode must be one of {sorted(VALID_EXECUTION_BILLING_MODES)}.")
        if self.noise_model not in VALID_NOISE_MODELS:
            raise ValueError(f"noise_model must be one of {sorted(VALID_NOISE_MODELS)}.")
        if self.bo_acquisition not in VALID_BO_ACQUISITIONS:
            raise ValueError(f"bo_acquisition must be one of {sorted(VALID_BO_ACQUISITIONS)}.")
        if self.bo_target not in VALID_BO_TARGETS:
            raise ValueError(f"bo_target must be one of {sorted(VALID_BO_TARGETS)}.")
        if self.bo_high_dim_strategy not in VALID_BO_HIGH_DIM_STRATEGIES:
            raise ValueError(f"bo_high_dim_strategy must be one of {sorted(VALID_BO_HIGH_DIM_STRATEGIES)}.")
        if self.qpu_billing_basis not in VALID_QPU_BILLING_BASIS:
            raise ValueError(f"qpu_billing_basis must be one of {sorted(VALID_QPU_BILLING_BASIS)}.")
        if self.transpile_topology not in VALID_TRANSPILE_TOPOLOGIES:
            raise ValueError(f"transpile_topology must be one of {sorted(VALID_TRANSPILE_TOPOLOGIES)}.")
        if self.routing_method not in VALID_ROUTING_METHODS:
            raise ValueError(f"routing_method must be one of {sorted(VALID_ROUTING_METHODS)}.")
        if self.transpile_optimization_level not in VALID_TRANSPILE_OPTIMIZATION_LEVELS:
            raise ValueError("transpile_optimization_level must be in {0,1,2,3}.")
        if self.depolarizing_strength_1q < 0 or self.depolarizing_strength_2q < 0:
            raise ValueError("Depolarizing strengths must be non-negative.")
        if self.measurement_error < 0 or self.measurement_error >= 1:
            raise ValueError("measurement_error must lie in [0, 1).")
        if self.t1 <= 0 or self.t2 <= 0:
            raise ValueError("t1 and t2 must be positive.")
        if self.gate_time_1q <= 0 or self.gate_time_2q <= 0:
            raise ValueError("gate_time_1q and gate_time_2q must be positive.")
        if self.measurement_mitigation_max_bits <= 0:
            raise ValueError("measurement_mitigation_max_bits must be positive.")
        if self.measurement_mitigation and self.n_assets > self.measurement_mitigation_max_bits:
            raise ValueError(
                f"measurement_mitigation is only supported up to {self.measurement_mitigation_max_bits} bits to avoid exponential transition-matrix blowups."
            )
        if self.resilience_level < 0:
            raise ValueError("resilience_level must be non-negative.")
        if not self.zne_noise_factors:
            raise ValueError("zne_noise_factors must not be empty.")
        if any(factor < 1 for factor in self.zne_noise_factors):
            raise ValueError("zne_noise_factors must all be >= 1.")
        if self.twirling_randomizations <= 0:
            raise ValueError("twirling_randomizations must be positive.")
        if self.qubo_penalty_multiplier <= 0:
            raise ValueError("qubo_penalty_multiplier must be positive.")
        if self.mixer_type not in VALID_MIXER_TYPES:
            raise ValueError(f"mixer_type must be one of {sorted(VALID_MIXER_TYPES)}.")
        if self.penalty_validation_max_assets <= 0:
            raise ValueError("penalty_validation_max_assets must be positive.")
        if self.penalty_validation_max_tries <= 0:
            raise ValueError("penalty_validation_max_tries must be positive.")
        if self.exact_reference_max_assets <= 0:
            raise ValueError("exact_reference_max_assets must be positive.")
        if self.dicke_init_max_assets <= 0:
            raise ValueError("dicke_init_max_assets must be positive.")
        if self.zne_mitigation and self.backend_name != "aer_simulator":
            raise ValueError("zne_mitigation is currently only supported with backend_name='aer_simulator'.")
        if self.bo_feasibility_weight < 0:
            raise ValueError("bo_feasibility_weight must be non-negative.")
        if self.bo_trust_region_radius <= 0:
            raise ValueError("bo_trust_region_radius must be positive.")
        if self.bo_max_gp_dim <= 0:
            raise ValueError("bo_max_gp_dim must be positive.")
        if self.warm_start_params and len(self.warm_start_params) != 2 * self.p_layers:
            raise ValueError(
                f"warm_start_params must contain exactly {2 * self.p_layers} parameters for p_layers={self.p_layers}."
            )
        if self.qpu_price_per_second_usd < 0:
            raise ValueError("qpu_price_per_second_usd must be non-negative.")
        if self.job_queue_latency_seconds < 0:
            raise ValueError("job_queue_latency_seconds must be non-negative.")
        if self.mock_edge_fidelity_sigma < 0:
            raise ValueError("mock_edge_fidelity_sigma must be non-negative.")
        if self.mock_cnot_error_mean < 0:
            raise ValueError("mock_cnot_error_mean must be non-negative.")
        if self.seed_transpiler is not None and self.seed_transpiler < 0:
            raise ValueError("seed_transpiler must be non-negative or None.")
        if self.bootstrap_resamples <= 0:
            raise ValueError("bootstrap_resamples must be positive.")

    def normalized(self) -> "RunConfig":
        updated = self
        if updated.seed_transpiler is None:
            updated = replace(updated, seed_transpiler=updated.seed)
        updated.validate()
        return updated

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SuiteConfig:
    """Configuration for a multi-run study sweep."""

    base: RunConfig
    seeds: list[int]
    studies: list[dict[str, Any]]
    output_dir: str = DEFAULT_SUITE_OUTPUT_DIR
    title: str = DEFAULT_SUITE_TITLE
    workers: int = 1
    study_mode: str = "independent"


@dataclass
class SpinRunConfig:
    """Configuration for p-layer geometry studies on frustrated spin Hamiltonians."""

    n_spins: int = 8
    p_layers: int = 3

    j1: float = 1.0
    j2: float = 0.0
    transverse_field: float = 1.0
    disorder_strength: float = 0.0
    boundary: str = "open"
    regime: str = "near_critical"

    mixer_type: str = "x"
    ansatz_family: str = "standard_qaoa"
    optimizer: str = "spsa"
    evaluation_budget: int = 80
    seeds: int = 10
    shots: int = 4096
    seed: int = 42

    exact_reference_max_spins: int = 12
    output_prefix: str = "layerfield_qaoa"

    def validate(self) -> None:
        if self.n_spins <= 0:
            raise ValueError("n_spins must be positive.")
        if self.p_layers <= 0:
            raise ValueError("p_layers must be positive.")
        if self.evaluation_budget <= 0:
            raise ValueError("evaluation_budget must be positive.")
        if self.seeds <= 0:
            raise ValueError("seeds must be positive.")
        if self.shots <= 0:
            raise ValueError("shots must be positive.")
        if self.boundary not in VALID_SPIN_BOUNDARIES:
            raise ValueError(f"boundary must be one of {sorted(VALID_SPIN_BOUNDARIES)}.")
        if self.regime not in VALID_SPIN_REGIMES:
            raise ValueError(f"regime must be one of {sorted(VALID_SPIN_REGIMES)}.")
        if self.mixer_type not in VALID_SPIN_MIXERS:
            raise ValueError(f"mixer_type must be one of {sorted(VALID_SPIN_MIXERS)}.")
        if self.ansatz_family not in VALID_SPIN_ANSATZ_FAMILIES:
            raise ValueError(f"ansatz_family must be one of {sorted(VALID_SPIN_ANSATZ_FAMILIES)}.")
        if self.optimizer not in VALID_SPIN_OPTIMIZERS:
            raise ValueError(f"optimizer must be one of {sorted(VALID_SPIN_OPTIMIZERS)}.")
        if self.exact_reference_max_spins <= 0:
            raise ValueError("exact_reference_max_spins must be positive.")

    def normalized(self) -> "SpinRunConfig":
        self.validate()
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_RUN_CONFIG_FIELDS = {field.name for field in fields(RunConfig)}
_SPIN_RUN_CONFIG_FIELDS = {field.name for field in fields(SpinRunConfig)}


def apply_overrides(cfg: RunConfig, overrides: dict[str, Any]) -> RunConfig:
    """Return a normalized copy of ``cfg`` with YAML/CLI overrides applied."""

    unknown = sorted(set(overrides) - _RUN_CONFIG_FIELDS)
    if unknown:
        raise KeyError(f"Unknown RunConfig fields: {unknown}")
    coerced = dict(overrides)
    if "zne_noise_factors" in coerced and isinstance(coerced["zne_noise_factors"], list):
        coerced["zne_noise_factors"] = tuple(int(value) for value in coerced["zne_noise_factors"])
    if "basis_gates" in coerced and isinstance(coerced["basis_gates"], list):
        coerced["basis_gates"] = tuple(str(value) for value in coerced["basis_gates"])
    updated = replace(cfg, **coerced).normalized()
    return updated


def load_runspec(path: str | Path) -> RunConfig:
    """Load a single-run YAML config from disk."""

    payload = yaml.safe_load(Path(path).read_text()) or {}
    cfg = apply_overrides(RunConfig(), payload)
    return cfg


def load_suite_spec(path: str | Path) -> SuiteConfig:
    """Load a suite-study YAML config from disk."""

    payload = yaml.safe_load(Path(path).read_text()) or {}
    base_payload = payload.get("base", {})
    base = apply_overrides(RunConfig(), base_payload)
    seeds = [int(value) for value in payload.get("seeds", [base.seed])]
    studies = list(payload.get("studies", []))
    if not studies:
        raise ValueError("Suite config must contain at least one study.")
    output_dir = str(payload.get("output_dir", DEFAULT_SUITE_OUTPUT_DIR))
    title = str(payload.get("title", DEFAULT_SUITE_TITLE))
    workers = int(payload.get("workers", 1))
    if workers <= 0:
        raise ValueError("Suite config workers must be positive.")
    study_mode = str(payload.get("study_mode", "independent"))
    if study_mode not in VALID_SUITE_STUDY_MODES:
        raise ValueError(f"Suite config study_mode must be one of {sorted(VALID_SUITE_STUDY_MODES)}.")
    return SuiteConfig(
        base=base,
        seeds=seeds,
        studies=studies,
        output_dir=output_dir,
        title=title,
        workers=workers,
        study_mode=study_mode,
    )


def apply_spin_overrides(cfg: SpinRunConfig, overrides: dict[str, Any]) -> SpinRunConfig:
    """Return a normalized copy of ``cfg`` with spin-study YAML/CLI overrides applied."""

    unknown = sorted(set(overrides) - _SPIN_RUN_CONFIG_FIELDS)
    if unknown:
        raise KeyError(f"Unknown SpinRunConfig fields: {unknown}")
    updated = replace(cfg, **dict(overrides)).normalized()
    return updated


def load_spin_runspec(path: str | Path) -> SpinRunConfig:
    """Load a spin-study YAML config from disk."""

    payload = yaml.safe_load(Path(path).read_text()) or {}
    return apply_spin_overrides(SpinRunConfig(), payload)


RunSpec = RunConfig
SuiteSpec = SuiteConfig


__all__ = [
    'VALID_REGIMES',
    'VALID_EXECUTION_MODES',
    'VALID_NOISE_MODELS',
    'VALID_BO_ACQUISITIONS',
    'VALID_BO_TARGETS',
    'VALID_BO_HIGH_DIM_STRATEGIES',
    'VALID_QPU_BILLING_BASIS',
    'VALID_EXECUTION_BILLING_MODES',
    'VALID_TRANSPILE_TOPOLOGIES',
    'VALID_ROUTING_METHODS',
    'VALID_MIXER_TYPES',
    'RunConfig',
    'SuiteConfig',
    'SpinRunConfig',
    'RunSpec',
    'SuiteSpec',
    'VALID_SUITE_STUDY_MODES',
    'VALID_SPIN_BOUNDARIES',
    'VALID_SPIN_REGIMES',
    'VALID_SPIN_ANSATZ_FAMILIES',
    'VALID_SPIN_MIXERS',
    'VALID_SPIN_OPTIMIZERS',
    'apply_overrides',
    'apply_spin_overrides',
    'load_runspec',
    'load_spin_runspec',
    'load_suite_spec',
]
