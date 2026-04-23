# When BO Was Not Worth It

This page exists for the negative result on purpose.

The repo question is not "can Bayesian Optimization run?" It is:

> when does a more sophisticated outer-loop optimizer actually change the decision enough to justify its cost?

In the committed broad suite, there are several places where the answer is clearly **no**.

## Case 1: Baseline regime

Source: `results/multi_regime_suite/suite_aggregated.csv`

| Method | Mean best raw objective | Mean best valid energy | Mean elapsed seconds |
|---|---:|---:|---:|
| Classical Markowitz | `-0.3615` | `-0.3615` | `0.00014` |
| Bayesian Optimization | `-0.3146` | `-0.3615` | `0.66290` |
| SPSA | `-0.3101` | `-0.3615` | `0.01947` |
| Random Search | `-0.3018` | `-0.3615` | `0.01914` |

What happened:

- all four methods end at the same aggregated `mean_best_valid_energy`,
- the classical baseline still has the best raw objective,
- BO is about `34.6x` slower than Random Search and about `4895x` slower than Classical Markowitz.

What it taught this repo:

**When the best-valid answer is already saturated, extra surrogate-model complexity is just overhead.**

## Case 2: Hard-budget regime

Source: `results/multi_regime_suite/suite_aggregated.csv`

| Method | Mean best raw objective | Mean best valid energy | Mean elapsed seconds |
|---|---:|---:|---:|
| Classical Markowitz | `-0.3140` | `-0.3140` | `0.00014` |
| Random Search | `-0.3097` | `-0.3140` | `0.01948` |
| Bayesian Optimization | `-0.3096` | `-0.3140` | `0.43891` |
| SPSA | `-0.3090` | `-0.3140` | `0.01899` |

What happened:

- BO and Random Search are effectively tied on the raw objective here,
- both still lose to the classical baseline,
- BO is about `22.5x` slower than Random Search.

What it taught this repo:

**A hard constraint does not automatically make BO worthwhile if the practical decision is already unchanged.**

## Case 3: `n_assets = 12`

Source: `results/multi_regime_suite/suite_aggregated.csv`

| Method | Mean best raw objective | Mean best valid energy | Mean elapsed seconds |
|---|---:|---:|---:|
| Classical Markowitz | `-0.3781` | `-0.3781` | `0.00053` |
| Random Search | `-0.2492` | `-0.3781` | `0.03923` |
| Bayesian Optimization | `-0.2376` | `-0.3781` | `0.56578` |
| SPSA | `-0.2307` | `-0.3781` | `0.03860` |

What happened:

- BO is not only weaker than the classical baseline; it is also weaker than Random Search on the raw objective in this slice,
- all four methods still share the same aggregated best-valid energy,
- BO is about `14.4x` slower than Random Search and about `1075x` slower than Classical Markowitz.

What it taught this repo:

**At larger sizes in the retained suite, expensive optimizer logic can magnify runtime without producing a better final call.**

## Bottom line

The honest lesson is not "BO is bad." The honest lesson is narrower and more useful:

- when feasibility is already saturated,
- when best-valid energy has already converged to the same answer,
- or when a classical baseline already dominates the raw objective,

then BO is often **not worth it** in this artifact.

That is a useful research result. It tells the reader where not to spend extra hybrid-loop complexity.
