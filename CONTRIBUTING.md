# Contributing

## Add a new benchmark regime

1. Add the regime name to `VALID_REGIMES` in `src/portfolio_qaoa_bench/config.py`.
2. Implement the generator in `src/portfolio_qaoa_bench/data.py`.
3. Route the regime through `SyntheticMarket.build()`.
4. Add at least one randomized property-style test in `tests/test_data_and_qubo.py`.
5. If the regime is intended for suites, add it to the relevant YAML study list.

## Add a new optimizer

1. Add `run_<optimizer>_search(...)` to `src/portfolio_qaoa_bench/optimizers.py`.
2. Populate results through `_TraceBuffer` so all exports stay consistent.
3. Make sure optimizer overhead is accounted for in `TimingBreakdown`.
4. Register the optimizer in `run_benchmark()`.
5. Add fallback / mocking tests if the optimizer depends on optional libraries.

## Preserve benchmark realism

When modifying runtime paths, preserve:
- topology-aware transpilation
- seed propagation into the transpiler
- job-vs-session billing semantics
- queue latency behavior in job mode
- mitigation shot multipliers and cost accounting
- calibration-aware proxy statistics when heavy-hex routing is used

## Preserve BO periodicity

QAOA angles are periodic. If you modify the surrogate layer:
- keep parameters inside valid bounds
- preserve the periodic feature handling for sklearn fallback
- do not regress the high-dimensional random-embedding path
