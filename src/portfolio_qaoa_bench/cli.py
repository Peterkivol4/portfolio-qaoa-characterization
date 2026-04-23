from __future__ import annotations

import argparse
from dataclasses import replace

from .config import RunSpec, load_runspec, load_suite_spec
from .constants import DEFAULT_CLI_DESCRIPTION
from .pipeline import run_benchmark, run_smoke_test, run_suite


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


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
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


__all__ = ['build_parser', 'main']
