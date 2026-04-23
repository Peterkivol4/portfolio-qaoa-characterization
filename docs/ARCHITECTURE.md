# Architecture

## Purpose

This repository is organized as a characterisation study for constrained QAOA portfolio optimization. The code is split so that market generation, QUBO construction, execution backends, optimizer loops, and reporting can evolve independently while still sharing a common run configuration.

## Main modules

- `config.py`: strongly typed run and suite configuration objects, YAML loading, and validation.
- `data.py`: synthetic market regimes, including a budget-aware `hard_budget` regime.
- `qubo.py`: Markowitz-to-QUBO construction, penalty calibration, and optional exact feasible references.
- `landscape.py`: instance-level structure metrics such as constraint hardness and simple spectral diagnostics.
- `simulator.py`: fast statevector execution, Aer execution, runtime-style sampling, and backend accounting.
- `objective.py`: CVaR-style scoring, feasibility handling, and approximation-gap estimation.
- `optimizers.py`: classical Markowitz baseline, random search, SPSA, and Bayesian optimization.
- `reporting.py`: JSON payloads, CSV flattening, bootstrap confidence intervals, and Markdown report generation.
- `plotting.py`: per-run dashboards and suite dashboards.
- `pipeline.py`: end-to-end orchestration for one run or a suite.

## Design notes

- Public type names are descriptive and auditable. Legacy aliases remain temporarily for compatibility, but internal logic no longer depends on opaque identifiers.
- The exact feasible reference is explicit: it is computed only when the configured problem size stays within `exact_reference_max_assets`.
- Reporting preserves both methodological outputs and structural context so thesis writing can cite not just optimizer outcomes but also instance difficulty indicators.
- `monolith-full/portfolio_qaoa_bench_monolith.py` is a generated mirror of the modular source tree, kept in sync by `scripts/build_monolith_full.py` and CI checks.
