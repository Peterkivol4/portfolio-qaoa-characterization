from pathlib import Path

import yaml

from portfolio_qaoa_bench.cli import build_parser
from portfolio_qaoa_bench.config import RunConfig, apply_overrides, load_runspec, load_suite_spec


def test_runspec_rejects_excess_qubits_for_fast_sim() -> None:
    cfg = RunConfig(n_assets=13, execution_mode="fast_simulator")
    try:
        cfg.validate()
    except ValueError as exc:
        assert "at most 12" in str(exc)
    else:
        raise AssertionError("Expected ValueError for oversized fast-simulator problem.")


def test_runspec_accepts_small_valid_case_and_normalizes_seed() -> None:
    cfg = RunConfig(n_assets=8, budget=3, p_layers=2, evaluation_budget=10, n_init_points=4).normalized()
    cfg.validate()
    assert cfg.seed_transpiler == cfg.seed


def test_override_round_trip_for_tuple_fields() -> None:
    cfg = apply_overrides(
        RunConfig(),
        {
            "zne_noise_factors": [1, 3, 5],
            "basis_gates": ["rz", "sx", "x", "ecr"],
            "regime": "clustered_assets",
        },
    )
    assert cfg.zne_noise_factors == (1, 3, 5)
    assert cfg.basis_gates == ("rz", "sx", "x", "ecr")


def test_job_billing_and_bootstrap_validation() -> None:
    cfg = RunConfig(execution_billing_mode="job", job_queue_latency_seconds=1.5, bootstrap_resamples=200).normalized()
    assert cfg.execution_billing_mode == "job"
    assert cfg.job_queue_latency_seconds == 1.5
    assert cfg.bootstrap_resamples == 200


def test_warm_start_params_must_match_parameter_dimension() -> None:
    try:
        RunConfig(p_layers=2, warm_start_params=[0.1, 0.2]).normalized()
    except ValueError as exc:
        assert "warm_start_params" in str(exc)
    else:
        raise AssertionError("Expected ValueError for mismatched warm_start_params length.")


def test_yaml_config_round_trips() -> None:
    root = Path(__file__).resolve().parents[1]
    config_path = root / "configs" / "default_run.yaml"
    parser = build_parser()
    args = parser.parse_args(["--config", str(config_path)])
    cfg = load_runspec(args.config)
    payload = yaml.safe_load(config_path.read_text()) or {}
    for key, value in payload.items():
        assert getattr(cfg, key) == value
    round_trip_path = root / "configs" / "_tmp_round_trip_test.yaml"
    try:
        round_trip_path.write_text(yaml.safe_dump(cfg.to_dict(), sort_keys=True))
        reloaded = load_runspec(round_trip_path)
    finally:
        round_trip_path.unlink(missing_ok=True)
    for key in cfg.to_dict():
        assert getattr(cfg, key) == getattr(reloaded, key)


def test_factorial_suite_config_loads_study_mode() -> None:
    root = Path(__file__).resolve().parents[1]
    spec = load_suite_spec(root / "configs" / "mixer_dominance_suite.yaml")
    assert spec.study_mode == "factorial"
    assert any(study["key"] == "mixer_type" for study in spec.studies)
