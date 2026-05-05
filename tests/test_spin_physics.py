from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import numpy as np

from layerfield_qaoa.config import SpinRunConfig
from layerfield_qaoa.exact_diagonalization import exact_diagonalize, exact_diagonalize_dense
from layerfield_qaoa.p_layer_geometry import (
    build_qaoa_state,
    qaoa_circuit_depth,
    qaoa_parameter_count,
    run_single_spin_instance,
    standard_qaoa_initial_state,
)
from layerfield_qaoa.parameter_emergence import (
    angle_distance,
    minimum_p_for_threshold,
    parameter_confusion_score,
    parameter_transfer_loss,
)
from layerfield_qaoa.phase_maps import run_p_layer_sweep
from layerfield_qaoa.physical_observables import (
    half_chain_entanglement_entropy,
    magnetization_x,
    magnetization_z,
    mean_correlation_z,
    structure_factor_z,
)
from layerfield_qaoa.spin_hamiltonian import build_spin_hamiltonian


def _manual_two_spin_dense(j1: float, h: float) -> np.ndarray:
    z = np.array([[1.0, 0.0], [0.0, -1.0]])
    x = np.array([[0.0, 1.0], [1.0, 0.0]])
    eye = np.eye(2)
    return -j1 * np.kron(z, z) - h * (np.kron(x, eye) + np.kron(eye, x))


def test_j1_j2_tfim_hamiltonian_shape_and_hermitian() -> None:
    cfg = SpinRunConfig(n_spins=5, p_layers=2, j1=1.0, j2=0.3, transverse_field=0.8, disorder_strength=0.2).normalized()
    model = build_spin_hamiltonian(cfg, np.random.default_rng(cfg.seed))
    assert model.dense_hamiltonian.shape == (2**cfg.n_spins, 2**cfg.n_spins)
    assert np.allclose(model.dense_hamiltonian, model.dense_hamiltonian.conj().T)


def test_j2_zero_reduces_to_standard_tfim() -> None:
    cfg = SpinRunConfig(n_spins=2, p_layers=1, j1=1.25, j2=0.0, transverse_field=0.7, disorder_strength=0.0).normalized()
    model = build_spin_hamiltonian(cfg, np.random.default_rng(cfg.seed))
    manual = _manual_two_spin_dense(cfg.j1, cfg.transverse_field)
    assert np.allclose(model.dense_hamiltonian, manual)


def test_exact_diagonalization_ground_energy_sorted_and_normalized() -> None:
    dense = _manual_two_spin_dense(1.0, 0.5)
    result = exact_diagonalize_dense(dense)
    assert np.all(np.diff(result.eigenvalues) >= -1e-12)
    assert np.isclose(np.linalg.norm(result.ground_state), 1.0)


def test_known_two_spin_limit() -> None:
    cfg = SpinRunConfig(n_spins=2, p_layers=1, j1=1.0, j2=0.0, transverse_field=0.0, disorder_strength=0.0).normalized()
    result = exact_diagonalize(build_spin_hamiltonian(cfg, np.random.default_rng(cfg.seed)))
    assert np.isclose(result.ground_energy, -1.0)


def test_magnetization_and_correlation_bounds() -> None:
    cfg = SpinRunConfig(n_spins=4, p_layers=1).normalized()
    model = build_spin_hamiltonian(cfg, np.random.default_rng(cfg.seed))
    state = standard_qaoa_initial_state(cfg.n_spins)
    assert -1.0 <= magnetization_z(state, model) <= 1.0
    assert -1.0 <= magnetization_x(state, model) <= 1.0
    assert -1.0 <= mean_correlation_z(state, model, distance=1) <= 1.0
    assert structure_factor_z(state, model) >= 0.0


def test_entanglement_entropy_zero_for_product_state() -> None:
    zero_state = np.zeros(2**4, dtype=np.complex128)
    zero_state[0] = 1.0
    assert np.isclose(half_chain_entanglement_entropy(zero_state, 4), 0.0)


def test_qaoa_parameter_count_and_depth_bookkeeping() -> None:
    assert qaoa_parameter_count(4) == 8
    assert qaoa_circuit_depth(4) == 8


def test_single_spin_instance_records_depth() -> None:
    cfg = SpinRunConfig(n_spins=4, p_layers=2, evaluation_budget=6, optimizer="random", seeds=1).normalized()
    record = run_single_spin_instance(cfg, np.random.default_rng(cfg.seed))
    assert record.p_layers == 2
    assert record.parameter_count == 4
    assert record.circuit_depth == 4
    assert np.isfinite(record.energy_error)


def test_parameter_confusion_and_transfer_sanity() -> None:
    params = np.array([0.1, 0.2, 0.3, 0.4])
    observables = np.array([0.5, 0.2, 0.1, 0.3])
    assert np.isclose(parameter_transfer_loss(params, params), 0.0)
    assert np.isclose(angle_distance(params, params), 0.0)
    assert np.isclose(
        parameter_confusion_score(
            np.array([1.0, 0.2, 0.5, 0.1]),
            np.array([1.0, 0.2, 0.5, 0.1]),
            params,
            params,
            observables,
            observables,
        ),
        0.0,
    )


def test_minimum_p_threshold_returns_none_when_unrecovered() -> None:
    records = [
        {"p_layers": 1, "energy_error": 0.2},
        {"p_layers": 2, "energy_error": 0.15},
        {"p_layers": 3, "energy_error": 0.11},
    ]
    assert minimum_p_for_threshold(records, "energy_error", 0.05) is None


def test_p_resolution_map_writes_csv_json_md(tmp_path: Path) -> None:
    cfg = SpinRunConfig(
        n_spins=3,
        p_layers=1,
        optimizer="random",
        evaluation_budget=4,
        seeds=1,
        shots=64,
        output_prefix=str(tmp_path / "layerfield"),
    ).normalized()
    payload = run_p_layer_sweep(
        base_cfg=cfg,
        n_spins_values=[3],
        p_values=[1],
        j2_values=[0.0],
        h_values=[0.8],
        output_dir=tmp_path,
    )
    assert Path(payload["records_path"]).exists()
    assert Path(payload["summary_path"]).exists()
    assert Path(payload["report_path"]).exists()
    rows = list(csv.DictReader(Path(payload["records_path"]).open()))
    assert rows


def test_cli_spin_p_sweep_subprocess(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    env = {**__import__("os").environ, "PYTHONPATH": str(root / "src")}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "layerfield_qaoa.cli",
            "p-sweep",
            "--n-spins",
            "3",
            "--p-values",
            "1",
            "--j2-values",
            "0.0",
            "--h-values",
            "0.8",
            "--optimizer",
            "random",
            "--seeds",
            "1",
            "--shots",
            "64",
            "--evaluation-budget",
            "4",
            "--output",
            str(tmp_path / "cli_p_sweep"),
        ],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0
    assert (tmp_path / "cli_p_sweep" / "p_resolution_records.csv").exists()


def test_build_qaoa_state_parameter_count_guard() -> None:
    cfg = SpinRunConfig(n_spins=3, p_layers=2).normalized()
    model = build_spin_hamiltonian(cfg, np.random.default_rng(cfg.seed))
    params = np.array([0.1, 0.2, 0.3, 0.4])
    state = build_qaoa_state(params, model, cfg.p_layers)
    assert np.isclose(np.linalg.norm(state), 1.0)
