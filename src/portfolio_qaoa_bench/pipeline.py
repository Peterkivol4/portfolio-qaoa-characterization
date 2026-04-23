from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from itertools import product
import json
from pathlib import Path
from typing import Any
import warnings

import numpy as np

from .config import RunSpec, SuiteSpec, apply_overrides
from .data import SyntheticMarket
from .landscape import profile_instance
from .objective import make_bounds
from .optimizers import run_bayesian_search, run_classical_markowitz, run_random_search, run_spsa_search
from .plotting import plot_results, plot_suite_dashboard
from .qubo import QuboFactory
from .reporting import (
    aggregate_suite_rows,
    aggregate_mixer_dominance_rows,
    build_mixer_dominance_rows,
    build_mixer_optimizer_balance_rows,
    build_mixer_variance_summary,
    build_mixer_winner_crossover_rows,
    flatten_run_for_csv,
    generate_project_positioning,
    generate_single_run_insights,
    generate_suite_claims,
    generate_suite_research_summary,
    save_summary,
    write_csv,
    write_mixer_dominance_report,
    write_markdown_report,
)
from .simulator import build_executor
from .logger import get_logger
from .plotting import plot_mixer_crossover


def _artifact_path(prefix: Path, suffix: str) -> Path:
    return Path(f"{prefix}{suffix}")


def _suite_job_payload(study_name: str, study_value: Any, seed: int, cfg: RunSpec) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = run_benchmark(cfg, verbose=False)
    return (
        {"study_name": study_name, "study_value": study_value, "seed": seed, "payload": payload},
        flatten_run_for_csv(study_name, study_value, seed, payload),
    )


def _suite_jobs(spec: SuiteSpec) -> list[tuple[str, Any, int, RunSpec]]:
    jobs: list[tuple[str, Any, int, RunSpec]] = []
    if spec.study_mode == "factorial":
        value_lists = [list(study["values"]) for study in spec.studies]
        for combo in product(*value_lists):
            overrides = {
                str(study["key"]): value
                for study, value in zip(spec.studies, combo, strict=True)
            }
            study_name = "factorial"
            study_value = " | ".join(
                f"{str(study['key'])}={value}"
                for study, value in zip(spec.studies, combo, strict=True)
            )
            safe_bits = [
                f"{str(study['key'])}_{str(value).replace('/', '-').replace(' ', '_')}"
                for study, value in zip(spec.studies, combo, strict=True)
            ]
            run_prefix = "__".join(safe_bits)
            for seed in spec.seeds:
                cfg = apply_overrides(spec.base, {**overrides, "seed": seed})
                cfg = apply_overrides(
                    cfg,
                    {"output_prefix": str(Path(spec.output_dir) / "factorial" / f"{run_prefix}_seed_{seed}")},
                )
                jobs.append((study_name, study_value, seed, cfg))
        return jobs
    for study in spec.studies:
        study_name = str(study["name"])
        key = str(study["key"])
        values = list(study["values"])
        for value in values:
            for seed in spec.seeds:
                cfg = apply_overrides(spec.base, {key: value, "seed": seed})
                safe_value = str(value).replace("/", "-")
                cfg = apply_overrides(cfg, {"output_prefix": str(Path(spec.output_dir) / study_name / f"{key}_{safe_value}_seed_{seed}")})
                jobs.append((study_name, value, seed, cfg))
    return jobs


def _run_suite_job(job: tuple[str, Any, int, RunSpec]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    study_name, study_value, seed, cfg = job
    return _suite_job_payload(study_name, study_value, seed, cfg)


def run_benchmark(cfg: RunSpec, verbose: bool = True) -> dict[str, Any]:
    cfg = cfg.normalized()
    log = get_logger()
    try:
        import torch
        torch.manual_seed(cfg.seed)
    except Exception:
        pass
    rng = np.random.default_rng(cfg.seed)

    mu, sigma = SyntheticMarket.build(cfg, rng)
    instance = QuboFactory.build(mu, sigma, cfg)
    spectral_profile = profile_instance(instance)
    executor = build_executor(instance, cfg)
    bounds = make_bounds(cfg)

    if verbose:
        log.info("Running classical Markowitz baseline...")
    classical_trace = run_classical_markowitz(instance, cfg)

    if verbose:
        log.info("Running random search...")
    random_trace = run_random_search(executor, cfg, bounds, rng)

    if verbose:
        log.info("Running SPSA...")
    spsa_trace = run_spsa_search(executor, cfg, bounds, rng)

    if verbose:
        log.info("Running Bayesian optimization...")
    bo_trace = run_bayesian_search(executor, cfg, bounds, rng, progress=log.info if verbose else None)

    traces = {
        "classical_markowitz": classical_trace,
        "random": random_trace,
        "spsa": spsa_trace,
        "bayesian_optimization": bo_trace,
    }

    prefix = Path(cfg.output_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    plot_results(traces, prefix)
    payload = save_summary(cfg, instance, traces, prefix, spectral_profile=spectral_profile)

    if verbose:
        log.info("")
        log.info("Summary")
        if instance.exact_feasible_energy is None:
            log.info(
                "Exact feasible optimum : unavailable "
                f"(n_assets={cfg.n_assets} exceeds exact_reference_max_assets={cfg.exact_reference_max_assets})"
            )
        else:
            log.info(f"Exact feasible optimum : {instance.exact_feasible_energy:.4f}")
        for method, trace in traces.items():
            log.info(f"{method:22s}: best_valid={min(trace.best_valid_history):.4f} | best_raw={min(trace.raw_objective_history):.4f}")
        log.info(f"Saved plot             : {_artifact_path(prefix, '.png')}")
        log.info(f"Saved summary          : {_artifact_path(prefix, '.json')}")
        for insight in payload.get("single_run_insights", [])[:2]:
            log.info(f"Insight                : {insight}")
    return payload


def run_smoke_test() -> None:
    log = get_logger()
    run_benchmark(
        RunSpec(
            n_assets=6,
            budget=2,
            p_layers=1,
            evaluation_budget=4,
            n_init_points=2,
            shots=128,
            output_prefix="smoke_portfolio_qaoa/smoke_run",
        ).normalized(),
        verbose=False,
    )
    log.info("Smoke test passed.")


def run_suite(spec: SuiteSpec, verbose: bool = True) -> dict[str, Any]:
    log = get_logger()
    if spec.workers <= 0:
        raise ValueError("Suite workers must be positive.")
    out_dir = Path(spec.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    per_run_rows: list[dict[str, Any]] = []
    suite_runs: list[dict[str, Any]] = []
    jobs = _suite_jobs(spec)

    if verbose:
        if spec.study_mode == "factorial":
            for study_name, study_value, seed, _cfg in jobs:
                log.info(f"[{study_name}] {study_value} seed={seed}")
        else:
            for study in spec.studies:
                study_name = str(study["name"])
                key = str(study["key"])
                for value in list(study["values"]):
                    for seed in spec.seeds:
                        log.info(f"[{study_name}] {key}={value} seed={seed}")

    if spec.workers == 1:
        job_results = [_suite_job_payload(study_name, value, seed, cfg) for study_name, value, seed, cfg in jobs]
    else:
        max_workers = min(spec.workers, max(1, len(jobs)))
        try:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                job_results = list(executor.map(_run_suite_job, jobs))
        except (NotImplementedError, PermissionError, OSError) as exc:
            warnings.warn(
                f"Parallel suite execution is unavailable on this platform ({exc}). Falling back to sequential execution.",
                RuntimeWarning,
                stacklevel=2,
            )
            job_results = [_suite_job_payload(study_name, value, seed, cfg) for study_name, value, seed, cfg in jobs]

    for suite_run, run_rows in job_results:
        suite_runs.append(suite_run)
        per_run_rows.extend(run_rows)

    aggregated_rows = aggregate_suite_rows(per_run_rows, resamples=spec.base.bootstrap_resamples)
    claims = generate_suite_claims(aggregated_rows)
    research_summary = generate_suite_research_summary(aggregated_rows)
    write_csv(out_dir / "suite_runs.csv", per_run_rows)
    write_csv(out_dir / "suite_aggregated.csv", aggregated_rows)
    write_markdown_report(out_dir / "suite_report.md", spec.title, aggregated_rows, claims, research_summary=research_summary)
    (out_dir / "suite_application_summary.md").write_text(
        "# Application-ready project summary\n\n"
        + research_summary["application_ready_summary"]
        + "\n\n## Research question\n\n"
        + research_summary["research_question"]
        + "\n\n## Evidence summary\n\n"
        + "\n".join(f"- {item}" for item in research_summary.get("evidence_summary", []))
        + "\n"
    )
    plot_suite_dashboard(aggregated_rows, out_dir / "suite_dashboard.png")
    mixer_pairs = build_mixer_dominance_rows(per_run_rows)
    mixer_aggregated = aggregate_mixer_dominance_rows(mixer_pairs)
    mixer_balance = build_mixer_optimizer_balance_rows(per_run_rows)
    mixer_variance = build_mixer_variance_summary(per_run_rows)
    mixer_crossover = build_mixer_winner_crossover_rows(mixer_pairs)
    write_csv(out_dir / "mixer_dominance_pairs.csv", mixer_pairs)
    write_csv(out_dir / "mixer_dominance_summary.csv", mixer_aggregated)
    write_csv(out_dir / "mixer_optimizer_balance.csv", mixer_balance)
    (out_dir / "mixer_variance_summary.json").write_text(json.dumps(mixer_variance, indent=2))
    write_mixer_dominance_report(
        out_dir / "mixer_dominance_report.md",
        mixer_aggregated,
        mixer_balance,
        mixer_variance,
        mixer_crossover,
    )
    plot_mixer_crossover(mixer_crossover, out_dir / "mixer_crossover.png")
    payload = {
        "title": spec.title,
        "output_dir": str(out_dir),
        "study_mode": spec.study_mode,
        "runs": suite_runs,
        "aggregated": aggregated_rows,
        "claims": claims,
        "research_summary": research_summary,
        "project_positioning": generate_project_positioning(spec.base),
        "mixer_analysis": {
            "paired_rows": mixer_pairs,
            "aggregated_rows": mixer_aggregated,
            "optimizer_balance_rows": mixer_balance,
            "variance_summary": mixer_variance,
            "crossover_rows": mixer_crossover,
        },
    }
    (out_dir / "suite_payload.json").write_text(json.dumps(payload, indent=2))
    return payload


__all__ = ['run_benchmark', 'run_smoke_test', 'run_suite']
