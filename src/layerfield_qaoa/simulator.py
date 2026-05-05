from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from itertools import combinations
import os
from time import perf_counter
from typing import Any, Callable, Dict, List, Tuple, cast
import warnings

import numpy as np

from .config import RunSpec
from .interfaces import ExecutorPort
from .qubo import PortfolioInstance
from .results import BackendPulseCard, TimingBreakdown

# compatibility surface used by existing tests and callers
BackendPulseCard = BackendPulseCard

try:
    from qiskit import QuantumCircuit, transpile
    from qiskit.primitives import BackendSamplerV2
    from qiskit.transpiler import CouplingMap
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error, thermal_relaxation_error
    from qiskit_ibm_runtime import QiskitRuntimeService
    from qiskit_ibm_runtime import SamplerV2
    from qiskit_ibm_runtime import fake_provider as qiskit_fake_provider
except Exception:  # pragma: no cover - optional boundary
    QuantumCircuit = None
    BackendSamplerV2 = None
    CouplingMap = None
    generate_preset_pass_manager = None
    AerSimulator = None
    NoiseModel = None
    ReadoutError = None
    depolarizing_error = None
    thermal_relaxation_error = None
    QiskitRuntimeService = None
    SamplerV2 = None
    qiskit_fake_provider = None


class StatevectorQAOA:
    def __init__(self, instance: PortfolioInstance, p_layers: int, cfg: RunSpec):
        self.instance = instance
        self.n_assets = instance.n_assets
        self.p_layers = p_layers
        self.cfg = cfg
        self.dim = 1 << self.n_assets
        self.basis = np.arange(self.dim, dtype=np.uint32)
        self.cost_diagonal = self._cost_diagonal()
        self._dicke_indices = _dicke_basis_indices(instance.n_assets, instance.budget)
        self.initial_state = self._initial_state()
        self.mixer_pairs: List[Tuple[np.ndarray, np.ndarray]] = []
        self.xy_pairs: List[Tuple[np.ndarray, np.ndarray]] = []
        if self.cfg.mixer_type == "product_x":
            for qubit in range(self.n_assets):
                mask = 1 << (self.n_assets - 1 - qubit)
                idx0 = np.where((self.basis & mask) == 0)[0]
                idx1 = idx0 | mask
                self.mixer_pairs.append((idx0, idx1))
        else:
            self.xy_edges = _xy_mixer_edges(self.n_assets)
            for q0, q1 in self.xy_edges:
                mask0 = 1 << (self.n_assets - 1 - q0)
                mask1 = 1 << (self.n_assets - 1 - q1)
                idx01 = np.where(((self.basis & mask0) == 0) & ((self.basis & mask1) != 0))[0]
                idx10 = idx01 ^ (mask0 | mask1)
                self.xy_pairs.append((idx01, idx10))

    def _cost_diagonal(self) -> np.ndarray:
        bits = ((self.basis[:, None] >> np.arange(self.n_assets - 1, -1, -1)) & 1).astype(float)
        return np.einsum("bi,ij,bj->b", bits, self.instance.qubo_matrix, bits)

    def _initial_state(self) -> np.ndarray:
        state = np.zeros(self.dim, dtype=np.complex128)
        if self.cfg.mixer_type == "product_x":
            state[:] = 1.0 / np.sqrt(self.dim)
            return state
        if self.n_assets <= self.cfg.dicke_init_max_assets:
            amp = 1.0 / np.sqrt(max(1, len(self._dicke_indices)))
            state[self._dicke_indices] = amp
            return state
        initial_bits = "1" * self.instance.budget + "0" * (self.n_assets - self.instance.budget)
        state[int(initial_bits, 2)] = 1.0
        return state

    def probabilities(self, params: np.ndarray) -> np.ndarray:
        params = np.asarray(params, dtype=float)
        state = self.initial_state.copy()
        for layer in range(self.p_layers):
            gamma = params[2 * layer]
            beta = params[2 * layer + 1]
            state *= np.exp(-1j * gamma * self.cost_diagonal)
            if self.cfg.mixer_type == "product_x":
                self._apply_product_x_layer(state, beta)
            else:
                self._apply_xy_layer(state, beta)
        probs = np.abs(state) ** 2
        probs /= probs.sum()
        return probs

    def _apply_product_x_layer(self, state: np.ndarray, beta: float) -> None:
        cos_beta = np.cos(beta)
        sin_beta = np.sin(beta)
        for idx0, idx1 in self.mixer_pairs:
            v0 = state[idx0].copy()
            v1 = state[idx1].copy()
            state[idx0] = cos_beta * v0 - 1j * sin_beta * v1
            state[idx1] = -1j * sin_beta * v0 + cos_beta * v1

    def _apply_xy_layer(self, state: np.ndarray, beta: float) -> None:
        cos_term = np.cos(2.0 * beta)
        sin_term = np.sin(2.0 * beta)
        for idx01, idx10 in self.xy_pairs:
            if idx01.size == 0:
                continue
            v01 = state[idx01].copy()
            v10 = state[idx10].copy()
            state[idx01] = cos_term * v01 - 1j * sin_term * v10
            state[idx10] = cos_term * v10 - 1j * sin_term * v01

    def run(self, params: np.ndarray, shots: int, rng: np.random.Generator) -> Dict[str, int]:
        probs = self.probabilities(params)
        samples = rng.choice(self.dim, size=shots, p=probs)
        unique, counts = np.unique(samples, return_counts=True)
        return {format(int(idx), f"0{self.n_assets}b"): int(ct) for idx, ct in zip(unique, counts)}


class BaseExecutor(ExecutorPort, ABC):
    def __init__(self, instance: PortfolioInstance, cfg: RunSpec):
        self.instance = instance
        self.cfg = cfg

    @abstractmethod
    def run(self, params: np.ndarray, shots: int, rng: np.random.Generator) -> tuple[dict[str, int], TimingBreakdown, BackendPulseCard]:
        raise NotImplementedError


class FastSimulatorExecutor(BaseExecutor):
    def __init__(self, instance: PortfolioInstance, cfg: RunSpec):
        super().__init__(instance, cfg)
        self.qaoa = StatevectorQAOA(instance, cfg.p_layers, cfg)

    def run(self, params: np.ndarray, shots: int, rng: np.random.Generator) -> tuple[dict[str, int], TimingBreakdown, BackendPulseCard]:
        started = perf_counter()
        zne_pre_extrapolation_counts: dict[str, int] | None = None
        if self.cfg.zne_mitigation and self.cfg.noise_model != "ideal":
            factor_counts = []
            for factor in self.cfg.zne_noise_factors:
                ideal_counts = self.qaoa.run(params, shots, rng)
                factor_counts.append(
                    _apply_fast_sim_noise(
                        ideal_counts,
                        self.instance.n_assets,
                        self.cfg,
                        rng,
                        noise_scale_factor=float(factor),
                    )
                )
            if factor_counts:
                zne_pre_extrapolation_counts = dict(factor_counts[0])
                if self.cfg.measurement_mitigation:
                    zne_pre_extrapolation_counts = _apply_measurement_mitigation(
                        zne_pre_extrapolation_counts,
                        self.instance.n_assets,
                        self.cfg,
                    )
            counts = _zne_extrapolated_counts(
                factor_counts,
                tuple(float(factor) for factor in self.cfg.zne_noise_factors),
                self.instance.n_assets,
                shots,
            )
        else:
            counts = self.qaoa.run(params, shots, rng)
            counts = _apply_fast_sim_noise(counts, self.instance.n_assets, self.cfg, rng)
        execution_done = perf_counter()
        mitigation_started = perf_counter()
        counts = _apply_measurement_mitigation(counts, self.instance.n_assets, self.cfg)
        mitigation_done = perf_counter()
        timing = TimingBreakdown(
            execution_seconds=execution_done - started,
            mitigation_seconds=mitigation_done - mitigation_started,
            total_seconds=mitigation_done - started,
        )
        timing = _apply_job_queue_latency(timing, self.cfg)
        stats = _backend_stats(
            None,
            "fast_simulator",
            shots,
            self.cfg,
            timing,
            "analytical_statevector",
            [],
            instance=self.instance,
            zne_pre_extrapolation_counts=zne_pre_extrapolation_counts,
        )
        return counts, timing, stats


class AerSamplerExecutor(BaseExecutor):
    def __init__(self, instance: PortfolioInstance, cfg: RunSpec):
        super().__init__(instance, cfg)
        _ensure_qiskit_available()
        self.backend = _resolve_backend(cfg)

    def run(self, params: np.ndarray, shots: int, rng: np.random.Generator) -> tuple[dict[str, int], TimingBreakdown, BackendPulseCard]:
        return _run_qiskit_sampler(
            instance=self.instance,
            cfg=self.cfg,
            backend=self.backend,
            params=params,
            shots=shots,
            rng=rng,
            sampler_factory=lambda backend, _options: BackendSamplerV2(backend=backend),
            sampler_options=None,
        )


class RuntimeSamplerExecutor(BaseExecutor):
    def __init__(self, instance: PortfolioInstance, cfg: RunSpec):
        super().__init__(instance, cfg)
        _ensure_qiskit_available()
        self.backend = _resolve_backend(cfg)

    def run(self, params: np.ndarray, shots: int, rng: np.random.Generator) -> tuple[dict[str, int], TimingBreakdown, BackendPulseCard]:
        options: dict[str, object] | None = None
        if self.cfg.twirling:
            options = {"twirling": {"enable_gates": True, "enable_measure": True, "num_randomizations": self.cfg.twirling_randomizations}}
        return _run_qiskit_sampler(
            instance=self.instance,
            cfg=self.cfg,
            backend=self.backend,
            params=params,
            shots=shots,
            rng=rng,
            sampler_factory=lambda backend, opts: SamplerV2(mode=backend, options=opts),
            sampler_options=options,
        )


def _ensure_qiskit_available() -> None:
    if QuantumCircuit is None or BackendSamplerV2 is None or AerSimulator is None or SamplerV2 is None:
        raise RuntimeError("Qiskit, Qiskit Aer, and qiskit-ibm-runtime are required for aer_sampler/runtime_sampler execution modes.")


def _xy_mixer_edges(n_assets: int) -> list[tuple[int, int]]:
    if n_assets <= 1:
        return []
    even_edges = [(idx, idx + 1) for idx in range(0, n_assets - 1, 2)]
    odd_edges = [(idx, idx + 1) for idx in range(1, n_assets - 1, 2)]
    if n_assets > 2:
        odd_edges.append((n_assets - 1, 0))
    return even_edges + odd_edges




def _dicke_basis_indices(n_assets: int, budget: int) -> np.ndarray:
    if budget < 0 or budget > n_assets:
        raise ValueError("budget must lie in [0, n_assets].")
    if budget == 0:
        return np.asarray([0], dtype=np.uint32)
    idxs: list[int] = []
    for ones in combinations(range(n_assets), budget):
        val = 0
        for pos in ones:
            val |= 1 << (n_assets - 1 - pos)
        idxs.append(val)
    return np.asarray(idxs, dtype=np.uint32)


def _dicke_statevector(n_assets: int, budget: int) -> np.ndarray:
    dim = 1 << n_assets
    state = np.zeros(dim, dtype=np.complex128)
    idxs = _dicke_basis_indices(n_assets, budget)
    amp = 1.0 / np.sqrt(max(1, len(idxs)))
    state[idxs] = amp
    return state


def _prepare_xy_initial_state(qc: QuantumCircuit, instance: PortfolioInstance, cfg: RunSpec) -> None:
    if instance.n_assets <= cfg.dicke_init_max_assets:
        qc.initialize(_dicke_statevector(instance.n_assets, instance.budget), list(range(instance.n_assets)))
        return
    for qubit in range(instance.budget):
        qc.x(qubit)

def _qubo_to_ising(qubo: np.ndarray) -> tuple[np.ndarray, dict[tuple[int, int], float]]:
    n = qubo.shape[0]
    linear = np.zeros(n, dtype=float)
    quadratic: dict[tuple[int, int], float] = {}
    for i in range(n):
        linear[i] -= qubo[i, i] / 2.0
    for i in range(n):
        for j in range(i + 1, n):
            coeff = qubo[i, j]
            if abs(coeff) < 1e-12:
                continue
            coupling = coeff / 2.0
            quadratic[(i, j)] = coupling
            linear[i] -= coeff / 2.0
            linear[j] -= coeff / 2.0
    return linear, quadratic


def build_qaoa_circuit(instance: PortfolioInstance, p_layers: int, params: np.ndarray, cfg: RunSpec) -> QuantumCircuit:
    _ensure_qiskit_available()
    params = np.asarray(params, dtype=float)
    qc = QuantumCircuit(instance.n_assets)
    if cfg.mixer_type == "product_x":
        qc.h(range(instance.n_assets))
    else:
        _prepare_xy_initial_state(qc, instance, cfg)
    linear, quadratic = _qubo_to_ising(instance.qubo_matrix)
    xy_edges = _xy_mixer_edges(instance.n_assets)
    for layer in range(p_layers):
        gamma = float(params[2 * layer])
        beta = float(params[2 * layer + 1])
        for qubit, coeff in enumerate(linear):
            if abs(coeff) > 1e-12:
                qc.rz(2.0 * gamma * coeff, qubit)
        for (q0, q1), coeff in quadratic.items():
            if abs(coeff) > 1e-12:
                qc.rzz(2.0 * gamma * coeff, q0, q1)
        if cfg.mixer_type == "product_x":
            for qubit in range(instance.n_assets):
                qc.rx(2.0 * beta, qubit)
        else:
            for q0, q1 in xy_edges:
                qc.rxx(2.0 * beta, q0, q1)
                qc.ryy(2.0 * beta, q0, q1)
    qc.measure_all()
    return qc


def _estimated_gate_load(n_bits: int, cfg: RunSpec) -> tuple[float, float]:
    per_layer_cost_twoq = n_bits * (n_bits - 1) / 2.0
    per_layer_cost_oneq = float(n_bits)
    if cfg.mixer_type == "product_x":
        per_layer_mixer_oneq = float(n_bits)
        per_layer_mixer_twoq = 0.0
        init_oneq = float(n_bits)
    else:
        per_layer_mixer_oneq = 0.0
        per_layer_mixer_twoq = float(len(_xy_mixer_edges(n_bits)) * 2)  # RXX + RYY per edge
        init_oneq = float(cfg.budget)
    oneq_total = init_oneq + cfg.p_layers * (per_layer_cost_oneq + per_layer_mixer_oneq)
    twoq_total = cfg.p_layers * (per_layer_cost_twoq + per_layer_mixer_twoq)
    return oneq_total, twoq_total


def _fast_noise_probability(n_bits: int, cfg: RunSpec, noise_scale_factor: float) -> float:
    oneq_total, twoq_total = _estimated_gate_load(n_bits, cfg)
    oneq_per_qubit = oneq_total / max(n_bits, 1)
    twoq_touch_per_qubit = 2.0 * twoq_total / max(n_bits, 1)
    if cfg.noise_model == "ideal":
        bit_flip_p = cfg.measurement_error
    elif cfg.noise_model == "depolarizing":
        bit_flip_p = cfg.measurement_error + oneq_per_qubit * cfg.depolarizing_strength_1q * noise_scale_factor + twoq_touch_per_qubit * cfg.depolarizing_strength_2q * noise_scale_factor
    else:
        relax1 = min(cfg.gate_time_1q * noise_scale_factor / max(cfg.t1, 1e-12), cfg.gate_time_1q * noise_scale_factor / max(cfg.t2, 1e-12))
        relax2 = min(cfg.gate_time_2q * noise_scale_factor / max(cfg.t1, 1e-12), cfg.gate_time_2q * noise_scale_factor / max(cfg.t2, 1e-12))
        bit_flip_p = cfg.measurement_error + oneq_per_qubit * relax1 + twoq_touch_per_qubit * relax2
    if cfg.twirling:
        bit_flip_p *= 0.85
    return float(min(0.45, max(0.0, bit_flip_p)))


def _apply_fast_sim_noise(
    counts: dict[str, int],
    n_bits: int,
    cfg: RunSpec,
    rng: np.random.Generator,
    *,
    noise_scale_factor: float = 1.0,
) -> dict[str, int]:
    bit_flip_p = _fast_noise_probability(n_bits, cfg, noise_scale_factor)
    if bit_flip_p <= 1e-12:
        return counts
    transformed: Counter[str] = Counter()
    for bitstring, count in counts.items():
        for _ in range(count):
            bits = list(bitstring)
            for idx in range(n_bits):
                if rng.random() < bit_flip_p:
                    bits[idx] = "1" if bits[idx] == "0" else "0"
            transformed["".join(bits)] += 1
    return dict(transformed)


def _apply_measurement_mitigation(counts: dict[str, int], n_bits: int, cfg: RunSpec) -> dict[str, int]:
    if not cfg.measurement_mitigation:
        return counts
    if n_bits > cfg.measurement_mitigation_max_bits:
        raise ValueError(
            f"measurement_mitigation requires a full 2^n transition matrix and is limited to {cfg.measurement_mitigation_max_bits} bits; got {n_bits}."
        )
    shots = int(sum(counts.values()))
    if shots <= 0:
        return counts
    epsilon = min(0.49, max(1e-9, cfg.measurement_error))
    single = np.array([[1 - epsilon, epsilon], [epsilon, 1 - epsilon]], dtype=float)
    obs = np.zeros(1 << n_bits, dtype=float)
    for bitstring, count in counts.items():
        obs[int(bitstring, 2)] = count / shots
    try:
        single_inv = np.linalg.inv(single)
    except np.linalg.LinAlgError:
        try:
            single_inv = np.linalg.pinv(single, rcond=1e-10)
        except np.linalg.LinAlgError:
            return counts
    corrected_tensor = obs.reshape((2,) * n_bits)
    for axis in range(n_bits):
        corrected_tensor = np.tensordot(single_inv, corrected_tensor, axes=(1, axis))
        corrected_tensor = np.moveaxis(corrected_tensor, 0, axis)
    corrected = corrected_tensor.reshape(-1)
    corrected = np.clip(corrected, 0.0, None)
    total_mass = float(corrected.sum())
    if total_mass <= 0.0:
        return counts
    corrected /= total_mass
    raw = corrected * shots
    ints = np.floor(raw).astype(int)
    remainder = shots - int(ints.sum())
    if remainder > 0:
        order = np.argsort(-(raw - ints))
        ints[order[:remainder]] += 1
    return {format(idx, f"0{n_bits}b"): int(count) for idx, count in enumerate(ints) if count > 0}


def _shot_cost_multiplier(cfg: RunSpec) -> float:
    multiplier = 1.0
    if cfg.measurement_mitigation:
        multiplier *= 1.25
    if cfg.twirling:
        multiplier *= max(1, cfg.twirling_randomizations)
    if cfg.zne_mitigation:
        multiplier *= float(sum(cfg.zne_noise_factors))
    if cfg.resilience_level > 0:
        multiplier *= 1.0 + 0.2 * cfg.resilience_level
    return multiplier


def _resolve_backend(cfg: RunSpec, *, seed_simulator: int | None = None, noise_scale_factor: float = 1.0):
    if cfg.backend_name == "aer_simulator":
        seed_value = cfg.seed if seed_simulator is None else int(seed_simulator)
        return AerSimulator(seed_simulator=seed_value, noise_model=_build_noise_model(cfg, noise_scale_factor=noise_scale_factor))
    if cfg.backend_name.lower().startswith("fake"):
        if qiskit_fake_provider is None:
            raise RuntimeError("qiskit_ibm_runtime.fake_provider is unavailable.")
        class_name = "".join(part.capitalize() for part in cfg.backend_name.split("_"))
        backend_cls = getattr(qiskit_fake_provider, class_name, None)
        if backend_cls is None:
            raise ValueError(f"Unknown fake backend: {cfg.backend_name}")
        return backend_cls()
    if cfg.execution_mode == "runtime_sampler":
        return _resolve_runtime_backend(cfg)
    raise ValueError(f"Unsupported backend_name: {cfg.backend_name}")


def _runtime_service_kwargs_from_env() -> dict[str, str]:
    token = (
        os.getenv("QISKIT_IBM_TOKEN")
        or os.getenv("IBM_QUANTUM_TOKEN")
        or os.getenv("IBM_CLOUD_API_KEY")
    )
    channel = os.getenv("QISKIT_IBM_CHANNEL")
    instance = os.getenv("QISKIT_IBM_INSTANCE") or os.getenv("QISKIT_IBM_CRN")
    kwargs: dict[str, str] = {}
    if token:
        kwargs["token"] = token
    if channel:
        kwargs["channel"] = channel
    if instance:
        kwargs["instance"] = instance
    return kwargs


def _runtime_backend_filter(backend: Any) -> bool:
    if getattr(backend, "simulator", False):
        return False
    try:
        status = backend.status()
    except Exception:
        return True
    return bool(getattr(status, "operational", True))


def _resolve_runtime_backend(cfg: RunSpec):
    if QiskitRuntimeService is None:
        raise RuntimeError("qiskit-ibm-runtime is required for execution_mode='runtime_sampler'.")
    service_kwargs = _runtime_service_kwargs_from_env()
    try:
        service = QiskitRuntimeService(**service_kwargs) if service_kwargs else QiskitRuntimeService()
    except Exception as exc:
        raise RuntimeError(
            "Failed to initialize QiskitRuntimeService. Set QISKIT_IBM_TOKEN and, if required by your account, "
            "QISKIT_IBM_CHANNEL/QISKIT_IBM_INSTANCE."
        ) from exc

    backend_name = str(cfg.backend_name).strip()
    if backend_name in {"least_busy", "ibm_least_busy", "auto"}:
        instance = service_kwargs.get("instance")
        return service.least_busy(
            min_num_qubits=cfg.n_assets,
            instance=instance,
            filters=_runtime_backend_filter,
        )
    instance = service_kwargs.get("instance")
    return service.backend(backend_name, instance=instance)


def _build_noise_model(cfg: RunSpec, *, noise_scale_factor: float = 1.0):
    if cfg.noise_model == "ideal":
        return None
    noise_model = NoiseModel()
    if cfg.noise_model == "depolarizing":
        err1 = depolarizing_error(min(0.99, cfg.depolarizing_strength_1q * noise_scale_factor), 1)
        err2 = depolarizing_error(min(0.99, cfg.depolarizing_strength_2q * noise_scale_factor), 2)
        noise_model.add_all_qubit_quantum_error(err1, ["rz", "rx", "h", "sx", "x"])
        noise_model.add_all_qubit_quantum_error(err2, ["rzz", "rxx", "ryy", "cx", "ecr"])
    elif cfg.noise_model == "thermal_relaxation":
        err1 = thermal_relaxation_error(cfg.t1, cfg.t2, cfg.gate_time_1q * noise_scale_factor)
        err_single_2q = thermal_relaxation_error(cfg.t1, cfg.t2, cfg.gate_time_2q * noise_scale_factor)
        err2 = err_single_2q.tensor(err_single_2q)
        noise_model.add_all_qubit_quantum_error(err1, ["rz", "rx", "h", "sx", "x"])
        noise_model.add_all_qubit_quantum_error(err2, ["rzz", "rxx", "ryy", "cx", "ecr"])
    if cfg.measurement_error > 0:
        ro = ReadoutError([[1 - cfg.measurement_error, cfg.measurement_error], [cfg.measurement_error, 1 - cfg.measurement_error]])
        noise_model.add_all_qubit_readout_error(ro)
    return noise_model


def _resolve_transpile_constraints(cfg: RunSpec, backend) -> tuple[object | None, list[str], str]:
    if cfg.transpile_topology == "all_to_all":
        return None, list(cfg.basis_gates), "all_to_all"
    if cfg.transpile_topology in {"backend_native", "auto"} and cfg.backend_name.lower().startswith("fake"):
        basis = list(cfg.basis_gates) if cfg.basis_gates else list(getattr(backend, "operation_names", []))
        coupling_map = getattr(backend, "coupling_map", None)
        return coupling_map, basis, "backend_native"
    if cfg.transpile_topology == "backend_native":
        return getattr(backend, "coupling_map", None), list(cfg.basis_gates), "backend_native"
    topology = "heavy_hex_3" if cfg.transpile_topology == "auto" else cfg.transpile_topology
    if topology.startswith("heavy_hex_") and CouplingMap is not None:
        distance = int(topology.split("_")[-1])
        coupling_map = CouplingMap.from_heavy_hex(distance)
        basis = list(cfg.basis_gates) if cfg.basis_gates else ["rz", "sx", "x", "ecr", "measure"]
        return coupling_map, basis, topology
    return None, list(cfg.basis_gates), topology


def _transpile_for_backend(circuit: QuantumCircuit, backend, cfg: RunSpec):
    coupling_map, basis_gates, topology_name = _resolve_transpile_constraints(cfg, backend)
    kwargs = {
        "backend": backend,
        "optimization_level": cfg.transpile_optimization_level,
        "seed_transpiler": cfg.seed_transpiler,
        "routing_method": None if cfg.routing_method == "none" else cfg.routing_method,
    }
    if coupling_map is not None:
        kwargs["coupling_map"] = coupling_map
    if basis_gates:
        kwargs["basis_gates"] = basis_gates
    try:
        pass_manager = generate_preset_pass_manager(**kwargs)
        return pass_manager.run(circuit), topology_name, basis_gates
    except Exception:
        return transpile(circuit, **kwargs), topology_name, basis_gates


def _apply_job_queue_latency(timing: TimingBreakdown, cfg: RunSpec) -> TimingBreakdown:
    if cfg.execution_billing_mode == "job" and cfg.job_queue_latency_seconds > 0.0:
        timing.queue_latency_seconds += cfg.job_queue_latency_seconds
        timing.total_seconds += cfg.job_queue_latency_seconds
    return timing


def _estimate_billed_seconds(timing: TimingBreakdown, cfg: RunSpec) -> float:
    if cfg.execution_billing_mode == "session":
        return float(timing.total_seconds)
    return float(timing.execution_seconds if cfg.qpu_billing_basis == "execution" else timing.total_seconds)


def _initial_state_strategy(instance: PortfolioInstance, cfg: RunSpec) -> str:
    if cfg.mixer_type == "product_x":
        return "uniform_superposition"
    if instance.n_assets <= cfg.dicke_init_max_assets:
        return "dicke"
    return "feasible_basis"


def _mock_calibration_metrics(transpiled, cfg: RunSpec, topology_name: str) -> tuple[float, float, float]:
    if not cfg.calibration_aware_routing:
        return 0.0, 0.0, 0.0
    if not (topology_name.startswith("heavy_hex") or topology_name == "backend_native"):
        return 0.0, 0.0, 0.0
    ops = transpiled.count_ops() if transpiled is not None else {}
    two_qubit = int(sum(int(count) for gate, count in ops.items() if gate in {"cx", "cz", "ecr", "rzz", "rxx", "ryy", "iswap", "swap"}))
    swap_gate_count = int(ops.get("swap", 0))
    sample_size = max(1, two_qubit)
    rng = np.random.default_rng((cfg.seed_transpiler or cfg.seed) + sample_size)
    edge_errors = rng.normal(loc=cfg.mock_cnot_error_mean, scale=cfg.mock_edge_fidelity_sigma, size=sample_size)
    edge_errors = np.clip(edge_errors, 1e-6, 0.25)
    mean_error = float(np.mean(edge_errors))
    max_error = float(np.max(edge_errors))
    risk_penalty = float(mean_error * max(1, swap_gate_count) + 0.25 * max_error * max(1, two_qubit))
    return mean_error, max_error, risk_penalty


def _backend_stats(
    transpiled,
    backend_name: str,
    shots: int,
    cfg: RunSpec,
    timing: TimingBreakdown,
    topology_name: str,
    basis_gates: list[str],
    *,
    instance: PortfolioInstance | None = None,
    simulator_seed: int | None = None,
    zne_simulator_seeds: list[int] | None = None,
    zne_pre_extrapolation_counts: dict[str, int] | None = None,
) -> BackendPulseCard:
    two_qubit = 0
    swap_gate_count = 0
    transpiled_depth = 0
    transpiled_size = 0
    if transpiled is not None and hasattr(transpiled, "count_ops"):
        ops = transpiled.count_ops()
        for gate_name, count in ops.items():
            if gate_name in {"cx", "cz", "ecr", "rzz", "rxx", "ryy", "iswap", "swap"}:
                two_qubit += int(count)
            if gate_name == "swap":
                swap_gate_count += int(count)
        transpiled_depth = int(transpiled.depth()) if hasattr(transpiled, "depth") else 0
        transpiled_size = int(transpiled.size()) if hasattr(transpiled, "size") else 0
    multiplier = _shot_cost_multiplier(cfg)
    mean_mock_cnot_error, max_mock_cnot_error, risk_penalty = _mock_calibration_metrics(transpiled, cfg, topology_name)
    billed_seconds = _estimate_billed_seconds(timing, cfg)
    return BackendPulseCard(
        backend_name=backend_name,
        initial_state_strategy="uniform_superposition" if instance is None else _initial_state_strategy(instance, cfg),
        simulator_seed=simulator_seed,
        zne_simulator_seeds=[] if zne_simulator_seeds is None else list(zne_simulator_seeds),
        transpiled_depth=transpiled_depth,
        transpiled_size=transpiled_size,
        two_qubit_gate_count=two_qubit,
        swap_gate_count=swap_gate_count,
        shot_multiplier=multiplier,
        effective_shots=shots * multiplier,
        transpile_topology=topology_name,
        basis_gates=list(basis_gates),
        routing_method=cfg.routing_method,
        seed_transpiler=cfg.seed_transpiler,
        execution_billing_mode=cfg.execution_billing_mode,
        calibration_aware_routing=cfg.calibration_aware_routing,
        mean_mock_cnot_error=mean_mock_cnot_error,
        max_mock_cnot_error=max_mock_cnot_error,
        estimated_swap_risk_penalty=risk_penalty,
        estimated_billed_seconds=billed_seconds,
        estimated_qpu_cost_usd=billed_seconds * cfg.qpu_price_per_second_usd,
        zne_pre_extrapolation_counts=None if zne_pre_extrapolation_counts is None else dict(zne_pre_extrapolation_counts),
    )


def _extract_counts(pub) -> dict[str, int]:
    data = pub.data
    if hasattr(data, 'meas'):
        return dict(data.meas.get_counts())
    for name in dir(data):
        if name.startswith('_'):
            continue
        reg = getattr(data, name)
        if hasattr(reg, 'get_counts'):
            return dict(reg.get_counts())
    raise RuntimeError('Sampler result did not expose measurement counts.')


def _sample_seed(rng: np.random.Generator) -> int:
    return int(rng.integers(0, np.iinfo(np.int32).max))


def _counts_to_probs(counts: dict[str, int], n_bits: int) -> np.ndarray:
    shots = max(1, int(sum(counts.values())))
    probs = np.zeros(1 << n_bits, dtype=float)
    for bitstring, count in counts.items():
        probs[int(bitstring, 2)] = count / shots
    return probs


def _probs_to_counts(probabilities: np.ndarray, n_bits: int, shots: int) -> dict[str, int]:
    probs = np.asarray(probabilities, dtype=float)
    probs = np.clip(probs, 0.0, None)
    total = float(probs.sum())
    if total <= 0.0:
        raise ValueError("Extrapolated quasi-probabilities collapsed to zero mass.")
    probs /= total
    raw = probs * shots
    ints = np.floor(raw).astype(int)
    remainder = shots - int(ints.sum())
    if remainder > 0:
        order = np.argsort(-(raw - ints))
        ints[order[:remainder]] += 1
    return {format(idx, f"0{n_bits}b"): int(count) for idx, count in enumerate(ints) if count > 0}


def _richardson_weights(noise_factors: tuple[float, ...]) -> np.ndarray:
    factors = np.asarray(noise_factors, dtype=float)
    order = len(factors)
    vand = np.vander(factors, N=order, increasing=True).T
    cond = float(np.linalg.cond(vand))
    if not np.isfinite(cond) or cond > 1e4:
        warnings.warn(
            f"Richardson extrapolation is ill-conditioned for noise_factors={tuple(float(factor) for factor in factors)} "
            f"(condition number {_format_float(cond)}). Results may be numerically unstable.",
            RuntimeWarning,
            stacklevel=2,
        )
    rhs = np.zeros(order, dtype=float)
    rhs[0] = 1.0
    try:
        return np.linalg.solve(vand, rhs)
    except np.linalg.LinAlgError:
        solution, *_ = np.linalg.lstsq(vand, rhs, rcond=None)
        return solution


def _format_float(value: float) -> str:
    if not np.isfinite(value):
        return str(value)
    return f"{value:.3e}"


def _zne_extrapolated_counts(factor_counts: list[dict[str, int]], noise_factors: tuple[float, ...], n_bits: int, shots: int) -> dict[str, int]:
    weights = _richardson_weights(noise_factors)
    quasi = np.zeros(1 << n_bits, dtype=float)
    for weight, counts in zip(weights, factor_counts):
        quasi += float(weight) * _counts_to_probs(counts, n_bits)
    return _probs_to_counts(quasi, n_bits, shots)


def _run_qiskit_once(
    *,
    backend,
    transpiled,
    shots: int,
    sampler_factory: Callable[[object, dict[str, object] | None], object],
    sampler_options: dict[str, object] | None,
) -> tuple[dict[str, int], float]:
    started = perf_counter()
    sampler = cast(Any, sampler_factory(backend, sampler_options))
    pub = sampler.run([transpiled], shots=shots).result()[0]
    elapsed = perf_counter() - started
    return _extract_counts(pub), elapsed


def _run_qiskit_sampler(
    *,
    instance: PortfolioInstance,
    cfg: RunSpec,
    backend,
    params: np.ndarray,
    shots: int,
    rng: np.random.Generator,
    sampler_factory: Callable[[object, dict[str, object] | None], object],
    sampler_options: dict[str, object] | None,
) -> tuple[dict[str, int], TimingBreakdown, BackendPulseCard]:
    start = perf_counter()
    circuit = build_qaoa_circuit(instance, cfg.p_layers, params, cfg)
    after_circuit = perf_counter()
    transpiled, topology_name, basis_gates = _transpile_for_backend(circuit, backend, cfg)
    after_transpile = perf_counter()

    counts: dict[str, int]
    execution_seconds = 0.0
    simulator_seed = None
    zne_simulator_seeds: list[int] = []
    zne_pre_extrapolation_counts: dict[str, int] | None = None
    if cfg.zne_mitigation:
        if cfg.backend_name != "aer_simulator":
            raise RuntimeError("True ZNE is only implemented for backend_name='aer_simulator'.")
        factor_counts: list[dict[str, int]] = []
        for factor in cfg.zne_noise_factors:
            factor_seed = _sample_seed(rng)
            zne_simulator_seeds.append(factor_seed)
            run_backend = _resolve_backend(cfg, seed_simulator=factor_seed, noise_scale_factor=float(factor))
            factor_result, factor_elapsed = _run_qiskit_once(
                backend=run_backend,
                transpiled=transpiled,
                shots=shots,
                sampler_factory=sampler_factory,
                sampler_options=sampler_options,
            )
            factor_counts.append(factor_result)
            execution_seconds += factor_elapsed
        if factor_counts:
            zne_pre_extrapolation_counts = dict(factor_counts[0])
            if cfg.measurement_mitigation:
                zne_pre_extrapolation_counts = _apply_measurement_mitigation(
                    zne_pre_extrapolation_counts,
                    instance.n_assets,
                    cfg,
                )
        counts = _zne_extrapolated_counts(factor_counts, tuple(float(f) for f in cfg.zne_noise_factors), instance.n_assets, shots)
    else:
        run_backend = backend
        if getattr(run_backend, "set_options", None) is not None and cfg.backend_name == "aer_simulator":
            try:
                simulator_seed = _sample_seed(rng)
                run_backend.set_options(seed_simulator=simulator_seed)
            except Exception:
                simulator_seed = None
                pass
        counts, execution_seconds = _run_qiskit_once(
            backend=run_backend,
            transpiled=transpiled,
            shots=shots,
            sampler_factory=sampler_factory,
            sampler_options=sampler_options,
        )

    after_run = after_transpile + execution_seconds
    counts = _apply_measurement_mitigation(counts, instance.n_assets, cfg)
    after_mitigation = perf_counter()
    timing = TimingBreakdown(
        circuit_construction_seconds=after_circuit - start,
        transpilation_seconds=after_transpile - after_circuit,
        execution_seconds=execution_seconds,
        mitigation_seconds=max(0.0, after_mitigation - after_run),
        total_seconds=(after_circuit - start) + (after_transpile - after_circuit) + execution_seconds + max(0.0, after_mitigation - after_run),
    )
    timing = _apply_job_queue_latency(timing, cfg)
    stats = _backend_stats(
        transpiled,
        getattr(backend, 'name', None) or cfg.backend_name,
        shots,
        cfg,
        timing,
        topology_name,
        basis_gates,
        instance=instance,
        simulator_seed=simulator_seed,
        zne_simulator_seeds=zne_simulator_seeds,
        zne_pre_extrapolation_counts=zne_pre_extrapolation_counts,
    )
    return counts, timing, stats


def build_executor(instance: PortfolioInstance, cfg: RunSpec) -> BaseExecutor:
    if cfg.execution_mode == "fast_simulator":
        return FastSimulatorExecutor(instance, cfg)
    if cfg.execution_mode == "aer_sampler":
        return AerSamplerExecutor(instance, cfg)
    if cfg.execution_mode == "runtime_sampler":
        return RuntimeSamplerExecutor(instance, cfg)
    raise ValueError(f"Unsupported execution_mode: {cfg.execution_mode}")


__all__ = [
    'StatevectorQAOA', 'BaseExecutor', 'FastSimulatorExecutor',
    'AerSamplerExecutor', 'RuntimeSamplerExecutor', 'build_qaoa_circuit', 'build_executor',
    'BackendPulseCard',
]
