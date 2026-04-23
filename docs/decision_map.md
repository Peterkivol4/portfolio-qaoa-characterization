# Decision Map

This page is the shortest route from the repository question to a practical reading of the retained suite:

> When is a more sophisticated classical optimizer worth its runtime, shot, queue, and mitigation cost for constrained QAOA?

The broad answer from the committed multi-regime suite is simple:

- **For the final portfolio decision, the raw-objective winner stays classical across every reported study slice.**
- **For feasibility alone, the retained broad-suite artifact is already saturated at 100% mean feasible-hit rate across all four methods.**
- **For the quantum-only mixer question, the `xy` mixer is usually the stronger choice in the committed pilot.**

The generated visual summary lives at [docs/figures/decision_map.png](figures/decision_map.png).

## How to read it

- `Best mean raw objective` means the lowest `mean_best_raw_objective` in `results/multi_regime_suite/suite_aggregated.csv`.
- `Feasibility-first` means the highest `mean_feasible_hit_rate` in the same aggregated artifact.
- A `Tie` means the data does not support a unique winner on that metric.

## Broad-suite winners by regime

| Regime | Best raw-objective method | Practical reading |
|---|---|---|
| `baseline` | Classical Markowitz | The downstream decision is already settled by the classical baseline. |
| `clustered_assets` | Classical Markowitz | BO improves neither the final choice nor feasibility in the retained artifact. |
| `hard_budget` | Classical Markowitz | The regime is harder conceptually, but the broad suite still does not justify BO overhead. |
| `high_correlation` | Classical Markowitz | Constraint-aware QAOA tuning does not overturn the classical recommendation here. |
| `low_correlation` | Classical Markowitz | The classical solve remains the cleanest answer. |
| `sparse_covariance` | Classical Markowitz | This is also the strongest raw-objective slice for the classical baseline. |

## Broad-suite winners by asset count

| Asset count | Best raw-objective method | Practical reading |
|---|---|---|
| `n_assets = 6` | Classical Markowitz | Small instances do not justify expensive outer-loop search. |
| `n_assets = 8` | Classical Markowitz | Same decision as the baseline slice. |
| `n_assets = 10` | Classical Markowitz | BO does not close the classical gap. |
| `n_assets = 12` | Classical Markowitz | BO is slower and still weaker than the classical baseline. |

## Broad-suite winners by evaluation budget

| Evaluation budget | Best raw-objective method | Practical reading |
|---|---|---|
| `8` | Classical Markowitz | BO overhead arrives before a better decision does. |
| `12` | Classical Markowitz | Increasing the budget does not change the recommendation. |
| `20` | Classical Markowitz | The broad suite still does not show BO becoming worth its cost. |

## Feasibility-first view

In the retained broad-suite artifact, **all four methods reach a `100%` mean feasible-hit rate** in the aggregated CSV. That means the suite does **not** support a strong claim that BO is uniquely better when feasibility is the only metric. The more honest conclusion is:

- use the classical baseline when you need the final portfolio decision,
- use simpler outer-loop methods when the best-valid energy has already saturated,
- reserve BO for slices where you specifically want to study outer-loop behavior rather than merely pick the cheapest winning method.

## Quantum-only rider

The mixer pilot changes the story slightly. In `results/mixer_dominance_pilot_v2/mixer_dominance_summary.csv`:

- `xy` wins `17/24` quantum-only paired summaries,
- `6/24` are ties,
- `product_x` wins `1/24`.

That does **not** overturn the broad classical result, but it does say that once the question becomes purely quantum-side design, mixer choice can matter more than the README headline alone suggests.
