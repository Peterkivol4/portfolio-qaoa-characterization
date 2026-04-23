# Mixer Dominance Analysis

## Variance Summary

- Mixer-type share (marginal proxy): 0.0113
- Optimizer share (marginal proxy): 0.0285
- Regime share (marginal proxy): 0.0134
- Mixer×optimizer interaction share: 0.0245

## Factor Balance

- Contexts where mixer effect exceeds optimizer effect: 2
- Contexts where optimizer effect exceeds mixer effect: 6

## H / Noise Crossover

| Constraint hardness | 2q depolarizing | Winner | Mean delta (product_x - xy) | Samples |
|---:|---:|---|---:|---:|
| 0.1208 | 0.0010 | xy | 0.4018 | 16 |
| 0.2344 | 0.0010 | xy | 0.0231 | 16 |
| 0.1208 | 0.0200 | xy | 0.0101 | 16 |
| 0.2344 | 0.0200 | xy | 0.0044 | 16 |

## Strongest Observed Mixer Shift

- Regime: hard_budget
- Method: random
- n_assets: 12
- Better mixer: xy
- Mean delta (product_x - xy): 2.9062
