import numpy as np
import pytest
import warnings

from portfolio_qaoa_bench.config import RunConfig
from portfolio_qaoa_bench.data import SyntheticMarket
from portfolio_qaoa_bench.objective import make_bounds
from portfolio_qaoa_bench.optimizers import BayesianOptimizer
from portfolio_qaoa_bench.qubo import QuboFactory
import portfolio_qaoa_bench.simulator as sim


@pytest.mark.parametrize("regime", ["baseline", "low_correlation", "high_correlation", "sparse_covariance", "clustered_assets", "hard_budget"])
def test_xy_mixer_preserves_budget_sector(regime: str) -> None:
    cfg = RunConfig(n_assets=6, budget=2, p_layers=2, mixer_type="xy", regime=regime).normalized()
    rng = np.random.default_rng(cfg.seed)
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)
    qaoa = sim.StatevectorQAOA(instance, cfg.p_layers, cfg)
    params = np.random.default_rng(123).uniform([0.0, 0.0, 0.0, 0.0], [2.0 * np.pi, np.pi, 2.0 * np.pi, np.pi])
    counts = qaoa.run(params, shots=256, rng=np.random.default_rng(123))
    assert counts
    assert all(bitstring.count("1") == cfg.budget for bitstring in counts)


@pytest.mark.parametrize("budget", [1, 5])
def test_xy_mixer_edge_cases(budget: int) -> None:
    cfg = RunConfig(n_assets=6, budget=budget, p_layers=2, mixer_type="xy", regime="baseline").normalized()
    rng = np.random.default_rng(cfg.seed)
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)
    qaoa = sim.StatevectorQAOA(instance, cfg.p_layers, cfg)
    params = np.random.default_rng(321).uniform([0.0, 0.0, 0.0, 0.0], [2.0 * np.pi, np.pi, 2.0 * np.pi, np.pi])
    counts = qaoa.run(params, shots=256, rng=np.random.default_rng(321))
    assert counts
    assert all(bitstring.count("1") == budget for bitstring in counts)


@pytest.mark.parametrize(
    ("n_assets", "budget", "p_layers", "beta"),
    [(5, 1, 3, np.pi / 6.0), (7, 6, 4, np.pi / 6.0)],
)
def test_xy_mixer_ring_connectivity_reaches_all_extreme_budget_states(
    n_assets: int,
    budget: int,
    p_layers: int,
    beta: float,
) -> None:
    cfg = RunConfig(
        n_assets=n_assets,
        budget=budget,
        p_layers=p_layers,
        mixer_type="xy",
        regime="baseline",
        dicke_init_max_assets=1,
    ).normalized()
    rng = np.random.default_rng(cfg.seed)
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)
    qaoa = sim.StatevectorQAOA(instance, cfg.p_layers, cfg)
    params = np.zeros(2 * cfg.p_layers, dtype=float)
    params[1::2] = beta
    probs = qaoa.probabilities(params)

    reachable = [
        format(idx, f"0{n_assets}b")
        for idx, prob in enumerate(probs)
        if format(idx, f"0{n_assets}b").count("1") == budget and prob > 1e-10
    ]
    assert len(reachable) == len(sim._dicke_basis_indices(n_assets, budget))


@pytest.mark.parametrize("regime", ["baseline", "low_correlation", "high_correlation", "sparse_covariance", "clustered_assets", "hard_budget"])
def test_penalty_calibration_separates_feasible_and_infeasible_energies(regime: str) -> None:
    cfg = RunConfig(n_assets=8, budget=3, regime=regime, seed=11).normalized()
    rng = np.random.default_rng(cfg.seed)
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)

    states = np.arange(1 << cfg.n_assets, dtype=np.uint64)
    bits = ((states[:, None] >> np.arange(cfg.n_assets, dtype=np.uint64)) & 1).astype(float)
    cardinalities = bits.sum(axis=1)
    energies = np.einsum("bi,ij,bj->b", bits, instance.qubo_matrix, bits, optimize=True)
    feasible = cardinalities == cfg.budget
    assert np.min(energies[~feasible]) > np.max(energies[feasible])


def test_fast_noise_probability_scales_with_problem_size() -> None:
    small = RunConfig(n_assets=4, budget=2, p_layers=1, mixer_type="xy", noise_model="depolarizing").normalized()
    large = RunConfig(n_assets=12, budget=4, p_layers=4, mixer_type="xy", noise_model="depolarizing").normalized()
    p_small = sim._fast_noise_probability(small.n_assets, small, 1.0)
    p_large = sim._fast_noise_probability(large.n_assets, large, 1.0)
    assert p_large > p_small


def test_zne_requires_aer_backend_name() -> None:
    with pytest.raises(ValueError, match="backend_name='aer_simulator'"):
        RunConfig(zne_mitigation=True, backend_name="fake_jakarta").normalized()


def test_sklearn_surrogate_warm_starts_kernel(monkeypatch) -> None:
    monkeypatch.setattr(sim, "SingleTaskGP", None, raising=False)
    import portfolio_qaoa_bench.optimizers as opt

    monkeypatch.setattr(opt, "SingleTaskGP", None)
    cfg = RunConfig(n_assets=6, budget=2, n_init_points=2, evaluation_budget=4).normalized()
    loop = BayesianOptimizer(make_bounds(cfg), cfg)
    rng = np.random.default_rng(0)
    x1 = loop.suggest(rng)
    x2 = loop.suggest(rng)
    loop.observe(x1, 1.0, 0.01)
    loop.observe(x2, 0.5, 0.01)
    _ = loop.suggest(rng)
    assert loop._last_sklearn_kernel is not None


def test_richardson_weights_sum_to_one() -> None:
    weights = sim._richardson_weights((1.0, 3.0, 5.0))
    assert np.isclose(np.sum(weights), 1.0)


def test_richardson_weights_cancel_noise_terms() -> None:
    factors = (1.0, 3.0, 5.0)
    weights = sim._richardson_weights(factors)
    assert abs(float(np.sum(weights)) - 1.0) < 1e-10
    assert abs(sum(float(weight) * factor for weight, factor in zip(weights, factors, strict=False))) < 1e-10
    assert abs(sum(float(weight) * (factor**2) for weight, factor in zip(weights, factors, strict=False))) < 1e-10


def test_richardson_weights_warn_when_noise_factors_are_ill_conditioned() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        weights = sim._richardson_weights((1.0, 1.01, 1.02))
    assert caught
    assert any("ill-conditioned" in str(item.message) for item in caught)
    assert np.all(np.isfinite(weights))


def test_runtime_backend_resolution_uses_named_backend(monkeypatch) -> None:
    calls: list[tuple[str, str | None]] = []

    class FakeService:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def backend(self, name: str, instance: str | None = None):
            calls.append((name, instance))
            return {"name": name, "instance": instance}

    monkeypatch.setattr(sim, "QiskitRuntimeService", FakeService)
    monkeypatch.setenv("QISKIT_IBM_TOKEN", "token")
    monkeypatch.setenv("QISKIT_IBM_INSTANCE", "instance-crn")

    cfg = RunConfig(
        execution_mode="runtime_sampler",
        backend_name="ibm_brisbane",
        n_assets=6,
        budget=2,
    ).normalized()
    backend = sim._resolve_backend(cfg)
    assert backend == {"name": "ibm_brisbane", "instance": "instance-crn"}
    assert calls == [("ibm_brisbane", "instance-crn")]


def test_runtime_backend_resolution_can_select_least_busy(monkeypatch) -> None:
    class FakeStatus:
        operational = True

    class FakeBackend:
        simulator = False

        def status(self):
            return FakeStatus()

    least_busy_calls: list[tuple[int | None, str | None]] = []

    class FakeService:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def least_busy(self, min_num_qubits=None, instance=None, filters=None, **kwargs):
            least_busy_calls.append((min_num_qubits, instance))
            backend = FakeBackend()
            assert filters is not None
            assert filters(backend) is True
            return backend

    monkeypatch.setattr(sim, "QiskitRuntimeService", FakeService)
    monkeypatch.setenv("QISKIT_IBM_TOKEN", "token")
    monkeypatch.delenv("QISKIT_IBM_INSTANCE", raising=False)

    cfg = RunConfig(
        execution_mode="runtime_sampler",
        backend_name="least_busy",
        n_assets=7,
        budget=2,
    ).normalized()
    backend = sim._resolve_backend(cfg)
    assert isinstance(backend, FakeBackend)
    assert least_busy_calls == [(7, None)]


def test_thermal_relaxation_uses_tensor(monkeypatch) -> None:
    class FakeError:
        def __init__(self, label: str):
            self.label = label
            self.tensor_calls = 0
            self.expand_calls = 0

        def tensor(self, other):
            self.tensor_calls += 1
            return FakeError(f"tensor({self.label},{other.label})")

        def expand(self, other):  # pragma: no cover - should remain unused
            self.expand_calls += 1
            return FakeError(f"expand({self.label},{other.label})")

    class FakeNoiseModel:
        def __init__(self):
            self.errors = []
            self.readout = []

        def add_all_qubit_quantum_error(self, err, ops):
            self.errors.append((err, tuple(ops)))

        def add_all_qubit_readout_error(self, err):
            self.readout.append(err)

    created = []

    def fake_thermal(*args, **kwargs):
        err = FakeError("thermal")
        created.append(err)
        return err

    monkeypatch.setattr(sim, "NoiseModel", FakeNoiseModel)
    monkeypatch.setattr(sim, "ReadoutError", lambda *args, **kwargs: (args, kwargs))
    monkeypatch.setattr(sim, "thermal_relaxation_error", fake_thermal)

    cfg = RunConfig(noise_model="thermal_relaxation").normalized()
    model = sim._build_noise_model(cfg)
    assert isinstance(model, FakeNoiseModel)
    assert len(created) == 2
    assert created[1].tensor_calls == 1
    assert created[1].expand_calls == 0


def test_xy_mixer_precomputes_pairs() -> None:
    cfg = RunConfig(n_assets=8, budget=3, p_layers=2, mixer_type="xy").normalized()
    rng = np.random.default_rng(cfg.seed)
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)
    qaoa = sim.StatevectorQAOA(instance, cfg.p_layers, cfg)
    assert len(qaoa.xy_pairs) == len(sim._xy_mixer_edges(cfg.n_assets))
    assert all(len(pair) == 2 for pair in qaoa.xy_pairs)


def test_aer_seed_is_sampled_from_rng(monkeypatch) -> None:
    seeds = []

    class FakeBackend:
        name = "aer_simulator"
        def set_options(self, **kwargs):
            seeds.append(kwargs.get("seed_simulator"))

    monkeypatch.setattr(sim, "build_qaoa_circuit", lambda *args, **kwargs: object())
    monkeypatch.setattr(sim, "_transpile_for_backend", lambda circuit, backend, cfg: (object(), "all_to_all", []))
    monkeypatch.setattr(sim, "_run_qiskit_once", lambda **kwargs: ({"00": kwargs["shots"]}, 0.01))
    monkeypatch.setattr(sim, "_apply_measurement_mitigation", lambda counts, n_bits, cfg: counts)
    monkeypatch.setattr(sim, "_backend_stats", lambda *args, **kwargs: sim.BackendPulseCard(backend_name="aer_simulator"))

    cfg = RunConfig(n_assets=2, budget=1, execution_mode="aer_sampler", backend_name="aer_simulator").normalized()
    rng = np.random.default_rng(123)
    dummy_instance = type("DummyInstance", (), {"n_assets": 2})()
    sim._run_qiskit_sampler(
        instance=dummy_instance,
        cfg=cfg,
        backend=FakeBackend(),
        params=np.zeros(2 * cfg.p_layers),
        shots=16,
        rng=rng,
        sampler_factory=lambda backend, opts: None,
        sampler_options=None,
    )
    assert len(seeds) == 1
    assert isinstance(seeds[0], int)


def test_dicke_statevector_has_uniform_feasible_support() -> None:
    n_assets = 6
    budget = 2
    state = sim._dicke_statevector(n_assets, budget)
    nz = np.flatnonzero(np.abs(state) > 1e-12)
    assert len(nz) == 15
    weights = np.abs(state[nz]) ** 2
    assert np.allclose(weights, np.full_like(weights, 1.0 / 15.0))
    assert np.isclose(float(np.sum(np.abs(state) ** 2)), 1.0)


def test_xy_initial_state_uses_dicke_below_threshold() -> None:
    cfg = RunConfig(n_assets=6, budget=2, p_layers=1, mixer_type="xy", dicke_init_max_assets=12).normalized()
    rng = np.random.default_rng(cfg.seed)
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)
    qaoa = sim.StatevectorQAOA(instance, cfg.p_layers, cfg)
    nz = np.flatnonzero(np.abs(qaoa.initial_state) > 1e-12)
    assert len(nz) == 15


@pytest.mark.skipif(sim.QuantumCircuit is None or sim.AerSimulator is None, reason="Qiskit Aer not available")
def test_aer_ideal_tracks_statevector_xy_distribution() -> None:
    cfg = RunConfig(
        n_assets=4,
        budget=2,
        p_layers=1,
        mixer_type="xy",
        execution_mode="aer_sampler",
        backend_name="aer_simulator",
        noise_model="ideal",
        measurement_error=0.0,
        shots=4096,
        dicke_init_max_assets=12,
    ).normalized()
    rng = np.random.default_rng(cfg.seed)
    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)
    qaoa = sim.StatevectorQAOA(instance, cfg.p_layers, cfg)
    params = np.asarray([0.37, 0.21], dtype=float)
    probs = qaoa.probabilities(params)

    backend = sim._resolve_backend(cfg, seed_simulator=123)
    counts, timing, stats = sim._run_qiskit_sampler(
        instance=instance,
        cfg=cfg,
        backend=backend,
        params=params,
        shots=cfg.shots,
        rng=np.random.default_rng(12345),
        sampler_factory=lambda backend, _opts: sim.BackendSamplerV2(backend=backend),
        sampler_options=None,
    )
    empirical = np.zeros_like(probs)
    for bitstring, count in counts.items():
        empirical[int(bitstring, 2)] = count / cfg.shots
    tv = 0.5 * float(np.abs(empirical - probs).sum())
    assert tv < 0.12
    assert timing.execution_seconds >= 0.0
    assert stats.backend_name == "aer_simulator"


@pytest.mark.skipif(sim.QuantumCircuit is None or sim.AerSimulator is None, reason="Qiskit Aer not available")
def test_fast_simulator_and_aer_sampler_agree_statistically() -> None:
    cfg_fast = RunConfig(
        n_assets=4,
        budget=2,
        p_layers=1,
        mixer_type="xy",
        execution_mode="fast_simulator",
        noise_model="ideal",
        measurement_error=0.0,
        shots=4096,
        dicke_init_max_assets=12,
    ).normalized()
    rng = np.random.default_rng(cfg_fast.seed)
    mu, sigma = SyntheticMarket.build(cfg_fast, rng)
    instance = QuboFactory.build(mu, sigma, cfg_fast)
    params = np.asarray([0.37, 0.21], dtype=float)

    fast_counts, _, _ = sim.build_executor(instance, cfg_fast).run(params, cfg_fast.shots, np.random.default_rng(12345))
    cfg_aer = RunConfig(
        n_assets=4,
        budget=2,
        p_layers=1,
        mixer_type="xy",
        execution_mode="aer_sampler",
        backend_name="aer_simulator",
        noise_model="ideal",
        measurement_error=0.0,
        shots=4096,
        dicke_init_max_assets=12,
    ).normalized()
    aer_counts, _, _ = sim.build_executor(instance, cfg_aer).run(params, cfg_aer.shots, np.random.default_rng(12345))

    def _probs(counts: dict[str, int], n_bits: int) -> np.ndarray:
        probs = np.zeros(1 << n_bits, dtype=float)
        total = sum(counts.values())
        for bitstring, count in counts.items():
            probs[int(bitstring, 2)] = count / total
        return probs

    tv = 0.5 * float(np.abs(_probs(fast_counts, cfg_fast.n_assets) - _probs(aer_counts, cfg_fast.n_assets)).sum())
    assert tv < 0.05


def test_zne_on_trivial_distribution_recovers_ideal_counts() -> None:
    shots = 10_000
    noise_factors = (1.0, 3.0, 5.0)
    base_bit_flip = 0.02
    factor_counts = []
    for factor in noise_factors:
        p_flip = base_bit_flip * factor
        noisy_ones = int(round(shots * p_flip))
        factor_counts.append({"0": shots - noisy_ones, "1": noisy_ones})
    recovered = sim._zne_extrapolated_counts(factor_counts, noise_factors, 1, shots)
    assert recovered == {"0": shots}


def test_penalty_calibration_handles_near_degenerate_covariance() -> None:
    cfg = RunConfig(n_assets=8, budget=3, risk_aversion=0.6, regime="baseline").normalized()
    mu = np.array([0.12, 0.11, 0.10, 0.095, 0.09, 0.085, 0.08, 0.075], dtype=float)
    sigma = 1e-4 * np.ones((8, 8), dtype=float) + np.diag([1e-8, 2e-8, 3e-8, 4e-8, 5e-8, 6e-8, 7e-8, 8e-8])
    instance = QuboFactory.build(mu, sigma, cfg)
    assert instance.penalty_doublings <= 2
    assert QuboFactory._penalty_is_sufficient(instance.qubo_matrix, cfg.budget)


def test_backend_stats_capture_initial_state_and_seed(monkeypatch) -> None:
    seeds = []

    class FakeBackend:
        name = "aer_simulator"
        def set_options(self, **kwargs):
            seeds.append(kwargs.get("seed_simulator"))

    monkeypatch.setattr(sim, "build_qaoa_circuit", lambda *args, **kwargs: object())
    monkeypatch.setattr(sim, "_transpile_for_backend", lambda circuit, backend, cfg: (object(), "all_to_all", []))
    monkeypatch.setattr(sim, "_run_qiskit_once", lambda **kwargs: ({"00": kwargs["shots"]}, 0.01))
    monkeypatch.setattr(sim, "_apply_measurement_mitigation", lambda counts, n_bits, cfg: counts)

    def _stats(*args, **kwargs):
        return sim._backend_stats(*args, **kwargs)

    cfg = RunConfig(n_assets=2, budget=1, execution_mode="aer_sampler", backend_name="aer_simulator").normalized()
    dummy_instance = type("DummyInstance", (), {"n_assets": 2, "budget": 1})()
    counts, timing, stats = sim._run_qiskit_sampler(
        instance=dummy_instance,
        cfg=cfg,
        backend=FakeBackend(),
        params=np.zeros(2 * cfg.p_layers),
        shots=16,
        rng=np.random.default_rng(123),
        sampler_factory=lambda backend, opts: None,
        sampler_options=None,
    )
    assert stats.initial_state_strategy == "dicke"
    assert isinstance(stats.simulator_seed, int)
    assert stats.zne_simulator_seeds == []
