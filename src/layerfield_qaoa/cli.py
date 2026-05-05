from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from .config import RunSpec, SpinRunConfig, load_runspec, load_spin_runspec, load_suite_spec
from .constants import DEFAULT_CLI_DESCRIPTION
from .phase_maps import (
    load_resolution_records_csv,
    parse_thresholds,
    run_p_layer_sweep,
    run_parameter_confusion_study,
    write_resolution_cost_report,
)
from .pipeline import run_benchmark, run_smoke_test, run_suite


def _csv_ints(text: str) -> list[int]:
    return [int(item.strip()) for item in text.split(",") if item.strip()]


def _csv_floats(text: str) -> list[float]:
    return [float(item.strip()) for item in text.split(",") if item.strip()]


def _csv_strings(text: str) -> list[str]:
    return [item.strip() for item in text.split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    defaults = RunSpec()
    parser = argparse.ArgumentParser(description=DEFAULT_CLI_DESCRIPTION)
    parser.add_argument("--test", action="store_true", help="Run a minimal smoke test")
    parser.add_argument("--config", type=str, help="YAML config for a single run")
    parser.add_argument("--suite-config", type=str, help="YAML suite config for a batch run")

    parser.add_argument("--n-assets", type=int, default=defaults.n_assets)
    parser.add_argument("--budget", type=int, default=defaults.budget)
    parser.add_argument("--p-layers", type=int, default=defaults.p_layers)
    parser.add_argument("--risk-aversion", type=float, default=defaults.risk_aversion)
    parser.add_argument("--evaluation-budget", type=int, default=defaults.evaluation_budget)
    parser.add_argument("--n-init-points", type=int, default=defaults.n_init_points)
    parser.add_argument("--shots", type=int, default=defaults.shots)
    parser.add_argument("--cvar-alpha", type=float, default=defaults.cvar_alpha)
    parser.add_argument("--invalid-penalty", type=float, default=defaults.invalid_penalty)
    parser.add_argument("--seed", type=int, default=defaults.seed)
    parser.add_argument("--output-prefix", type=str, default=defaults.output_prefix)
    parser.add_argument("--regime", type=str, default=defaults.regime)

    parser.add_argument("--execution-mode", type=str, default=defaults.execution_mode)
    parser.add_argument("--backend-name", type=str, default=defaults.backend_name)
    parser.add_argument("--execution-billing-mode", type=str, default=defaults.execution_billing_mode)
    parser.add_argument("--qpu-billing-basis", type=str, default=defaults.qpu_billing_basis)
    parser.add_argument("--qpu-pricing-tier", type=str, default=defaults.qpu_pricing_tier)
    parser.add_argument("--qpu-price-per-second-usd", type=float, default=defaults.qpu_price_per_second_usd)
    parser.add_argument("--job-queue-latency-seconds", type=float, default=defaults.job_queue_latency_seconds)

    parser.add_argument("--transpile-topology", type=str, default=defaults.transpile_topology)
    parser.add_argument("--routing-method", type=str, default=defaults.routing_method)
    parser.add_argument("--seed-transpiler", type=int)
    parser.add_argument("--calibration-aware-routing", action="store_true")
    parser.add_argument("--mock-edge-fidelity-sigma", type=float, default=defaults.mock_edge_fidelity_sigma)
    parser.add_argument("--mock-cnot-error-mean", type=float, default=defaults.mock_cnot_error_mean)

    parser.add_argument("--noise-model", type=str, default=defaults.noise_model)
    parser.add_argument("--measurement-mitigation", action="store_true")
    parser.add_argument("--zne-mitigation", action="store_true")
    parser.add_argument("--twirling", action="store_true")
    parser.add_argument("--resilience-level", type=int, default=defaults.resilience_level)

    parser.add_argument("--bo-acquisition", type=str, default=defaults.bo_acquisition)
    parser.add_argument("--bo-target", type=str, default=defaults.bo_target)
    parser.add_argument("--bo-max-gp-dim", type=int, default=defaults.bo_max_gp_dim)
    parser.add_argument("--bo-high-dim-strategy", type=str, default=defaults.bo_high_dim_strategy)
    parser.add_argument("--bo-trust-region-radius", type=float, default=defaults.bo_trust_region_radius)
    parser.add_argument("--no-trust-region", action="store_true")
    parser.add_argument("--no-periodic-wrap", action="store_true")
    parser.add_argument("--bootstrap-resamples", type=int, default=defaults.bootstrap_resamples)
    parser.add_argument("--workers", type=int, default=1, help="Parallel worker count for suite runs")
    return parser


def build_spin_parser() -> argparse.ArgumentParser:
    defaults = SpinRunConfig()
    parser = argparse.ArgumentParser(description="LayerField QAOA spin-physics studies")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_sweep = subparsers.add_parser("p-sweep", help="Run a p-layer physical-resolution sweep")
    p_sweep.add_argument("--config", type=str, help="Optional YAML config for spin studies")
    p_sweep.add_argument("--n-spins", type=str, required=True)
    p_sweep.add_argument("--p-values", type=str, required=True)
    p_sweep.add_argument("--j2-values", type=str, required=True)
    p_sweep.add_argument("--h-values", type=str, required=True)
    p_sweep.add_argument("--j1", type=float, default=defaults.j1)
    p_sweep.add_argument("--optimizer", type=str, default=defaults.optimizer)
    p_sweep.add_argument("--seeds", type=int, default=defaults.seeds)
    p_sweep.add_argument("--shots", type=int, default=defaults.shots)
    p_sweep.add_argument("--evaluation-budget", type=int, default=defaults.evaluation_budget)
    p_sweep.add_argument("--boundary", type=str, default=defaults.boundary)
    p_sweep.add_argument("--output", type=str, required=True)
    p_sweep.add_argument("--thresholds", type=str, default="energy=0.02,magnetization=0.05,correlation=0.05,fidelity=0.10")

    confusion = subparsers.add_parser("parameter-confusion", help="Run a parameter-confusion study across spin regimes")
    confusion.add_argument("--config", type=str, help="Optional YAML config for spin studies")
    confusion.add_argument("--n-spins", type=int, default=defaults.n_spins)
    confusion.add_argument("--p-values", type=str, required=True)
    confusion.add_argument("--regimes", type=str, required=True)
    confusion.add_argument("--optimizer", type=str, default=defaults.optimizer)
    confusion.add_argument("--evaluation-budget", type=int, default=defaults.evaluation_budget)
    confusion.add_argument("--shots", type=int, default=defaults.shots)
    confusion.add_argument("--boundary", type=str, default=defaults.boundary)
    confusion.add_argument("--output", type=str, required=True)

    resolution = subparsers.add_parser("resolution-cost", help="Summarize the runtime cost of physical recovery thresholds")
    resolution.add_argument("--input", type=str, required=True)
    resolution.add_argument("--thresholds", type=str, required=True)
    resolution.add_argument("--output", type=str, required=True)
    return parser


def _run_spin_cli(argv: list[str]) -> None:
    parser = build_spin_parser()
    args = parser.parse_args(argv)
    if args.command == "p-sweep":
        base = SpinRunConfig().normalized() if not args.config else load_spin_runspec(args.config)
        base = replace(
            base,
            j1=args.j1,
            optimizer=args.optimizer,
            seeds=args.seeds,
            shots=args.shots,
            evaluation_budget=args.evaluation_budget,
            boundary=args.boundary,
        ).normalized()
        run_p_layer_sweep(
            base_cfg=base,
            n_spins_values=_csv_ints(args.n_spins),
            p_values=_csv_ints(args.p_values),
            j2_values=_csv_floats(args.j2_values),
            h_values=_csv_floats(args.h_values),
            output_dir=args.output,
            thresholds=parse_thresholds(args.thresholds),
        )
        return
    if args.command == "parameter-confusion":
        base = SpinRunConfig().normalized() if not args.config else load_spin_runspec(args.config)
        base = replace(
            base,
            optimizer=args.optimizer,
            shots=args.shots,
            evaluation_budget=args.evaluation_budget,
            boundary=args.boundary,
        ).normalized()
        run_parameter_confusion_study(
            base_cfg=base,
            n_spins=args.n_spins,
            p_values=_csv_ints(args.p_values),
            regimes=_csv_strings(args.regimes),
            output_dir=args.output,
        )
        return
    if args.command == "resolution-cost":
        records = load_resolution_records_csv(args.input)
        write_resolution_cost_report(records, thresholds=parse_thresholds(args.thresholds), output_dir=args.output)
        return
    parser.error(f"Unsupported command: {args.command}")


def main() -> None:
    argv = sys.argv[1:]
    if argv and argv[0] in {"p-sweep", "parameter-confusion", "resolution-cost"}:
        _run_spin_cli(argv)
        return

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.test:
        run_smoke_test()
        return
    if args.suite_config:
        spec = load_suite_spec(args.suite_config)
        if args.workers != 1:
            spec = replace(spec, workers=args.workers)
        run_suite(spec)
        return
    if args.config:
        run_benchmark(load_runspec(args.config))
        return

    cfg = RunSpec(
        n_assets=args.n_assets,
        budget=args.budget,
        p_layers=args.p_layers,
        risk_aversion=args.risk_aversion,
        evaluation_budget=args.evaluation_budget,
        n_init_points=args.n_init_points,
        shots=args.shots,
        cvar_alpha=args.cvar_alpha,
        invalid_penalty=args.invalid_penalty,
        seed=args.seed,
        output_prefix=args.output_prefix,
        regime=args.regime,
        execution_mode=args.execution_mode,
        backend_name=args.backend_name,
        execution_billing_mode=args.execution_billing_mode,
        qpu_billing_basis=args.qpu_billing_basis,
        qpu_pricing_tier=args.qpu_pricing_tier,
        qpu_price_per_second_usd=args.qpu_price_per_second_usd,
        job_queue_latency_seconds=args.job_queue_latency_seconds,
        transpile_topology=args.transpile_topology,
        routing_method=args.routing_method,
        seed_transpiler=args.seed_transpiler,
        calibration_aware_routing=args.calibration_aware_routing,
        mock_edge_fidelity_sigma=args.mock_edge_fidelity_sigma,
        mock_cnot_error_mean=args.mock_cnot_error_mean,
        noise_model=args.noise_model,
        measurement_mitigation=args.measurement_mitigation,
        zne_mitigation=args.zne_mitigation,
        twirling=args.twirling,
        resilience_level=args.resilience_level,
        bo_acquisition=args.bo_acquisition,
        bo_target=args.bo_target,
        bo_trust_region=not args.no_trust_region,
        bo_trust_region_radius=args.bo_trust_region_radius,
        bo_max_gp_dim=args.bo_max_gp_dim,
        bo_high_dim_strategy=args.bo_high_dim_strategy,
        periodic_parameter_wrap=not args.no_periodic_wrap,
        bootstrap_resamples=args.bootstrap_resamples,
    ).normalized()
    run_benchmark(cfg)


if __name__ == "__main__":
    main()


__all__ = ["build_parser", "build_spin_parser", "main"]
