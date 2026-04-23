# Mixer Dominance Pilot v2

## Research question

When does a more sophisticated classical optimizer justify its runtime, shot, queue, and mitigation cost for constrained QAOA portfolio optimization?

## Why this benchmark matters

Across the completed suite, Classical Markowitz delivered the strongest mean objective on factorial=regime=baseline | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.001, while Classical Markowitz provided the best cost-adjusted tradeoff on at least one study point.

## Technical contributions demonstrated

- Constraint-aware QAOA benchmarking across multiple synthetic portfolio regimes.
- Fair optimizer comparison under shared runtime, shot, and billing accounting.
- Structured exports that preserve both benchmark claims and per-evaluation evidence.

## Evidence summary

- Best mean raw objective: Classical Markowitz on factorial=regime=baseline | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.001 with -0.5069.
- Strongest feasibility: Bayesian Optimization reached mean feasible-hit rate 100.00%.
- Best cost-adjusted method: Classical Markowitz minimized estimated cost plus elapsed time most effectively.

## Headline claims

- For factorial=regime=baseline | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.001, Classical Markowitz has the best mean raw objective (-0.4886, bootstrap 95% CI -0.5492–-0.4281).
- For factorial=regime=baseline | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.001, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For factorial=regime=baseline | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.02, Classical Markowitz has the best mean raw objective (-0.4886, bootstrap 95% CI -0.5492–-0.4281).
- For factorial=regime=baseline | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.02, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For factorial=regime=baseline | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.001, Classical Markowitz has the best mean raw objective (-0.4886, bootstrap 95% CI -0.5492–-0.4281).
- For factorial=regime=baseline | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.001, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For factorial=regime=baseline | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.02, Classical Markowitz has the best mean raw objective (-0.4886, bootstrap 95% CI -0.5492–-0.4281).
- For factorial=regime=baseline | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.02, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For factorial=regime=baseline | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.001, Classical Markowitz has the best mean raw objective (-0.5069, bootstrap 95% CI -0.5198–-0.4940).
- For factorial=regime=baseline | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.001, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For factorial=regime=baseline | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.02, Classical Markowitz has the best mean raw objective (-0.5069, bootstrap 95% CI -0.5198–-0.4940).
- For factorial=regime=baseline | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.02, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For factorial=regime=baseline | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.001, Bayesian Optimization has the best mean raw objective (-0.5069, bootstrap 95% CI -0.5198–-0.4940).
- For factorial=regime=baseline | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.001, Classical Markowitz is cheapest by estimated runtime cost plus elapsed time, showing where sophisticated search may not justify its overhead.
- For factorial=regime=baseline | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.02, Classical Markowitz has the best mean raw objective (-0.5069, bootstrap 95% CI -0.5198–-0.4940).
- For factorial=regime=baseline | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.02, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For factorial=regime=hard_budget | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.001, Classical Markowitz has the best mean raw objective (-0.4044, bootstrap 95% CI -0.4087–-0.4000).
- For factorial=regime=hard_budget | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.001, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For factorial=regime=hard_budget | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.02, Classical Markowitz has the best mean raw objective (-0.4044, bootstrap 95% CI -0.4087–-0.4000).
- For factorial=regime=hard_budget | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.02, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For factorial=regime=hard_budget | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.001, Classical Markowitz has the best mean raw objective (-0.4044, bootstrap 95% CI -0.4087–-0.4000).
- For factorial=regime=hard_budget | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.001, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For factorial=regime=hard_budget | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.02, Classical Markowitz has the best mean raw objective (-0.4044, bootstrap 95% CI -0.4087–-0.4000).
- For factorial=regime=hard_budget | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.02, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For factorial=regime=hard_budget | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.001, Classical Markowitz has the best mean raw objective (-0.4189, bootstrap 95% CI -0.4581–-0.3798).
- For factorial=regime=hard_budget | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.001, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For factorial=regime=hard_budget | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.02, Classical Markowitz has the best mean raw objective (-0.4189, bootstrap 95% CI -0.4581–-0.3798).
- For factorial=regime=hard_budget | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.02, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For factorial=regime=hard_budget | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.001, Classical Markowitz has the best mean raw objective (-0.4189, bootstrap 95% CI -0.4581–-0.3798).
- For factorial=regime=hard_budget | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.001, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For factorial=regime=hard_budget | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.02, Classical Markowitz has the best mean raw objective (-0.4189, bootstrap 95% CI -0.4581–-0.3798).
- For factorial=regime=hard_budget | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.02, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.

## Aggregated results

| Study | Value | Method | Mean raw objective | 95% CI raw | Mean approx ratio | Regret AUC | Best-valid/shot | Sharpe | Win rate | Feasible hit rate | p vs random (adj.) | Mean elapsed s | 95% CI elapsed | Mean billed s |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| factorial | regime=baseline | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.001 | Bayesian Optimization | -0.3367 | [-0.3667, -0.3067] | 1.0937 | 0.2343 | -0.000580 | 1.5230 | 0.00% | 100.00% | 1.0000 | 0.298 | [0.222, 0.374] | 12.007 |
| factorial | regime=baseline | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.001 | Classical Markowitz | -0.4886 | [-0.5492, -0.4281] | 1.0000 | 0.0000 | NA | 1.4972 | 100.00% | 100.00% | 1.0000 | 0.001 | [0.001, 0.001] | 0.000 |
| factorial | regime=baseline | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.001 | Random Search | -0.2994 | [-0.3168, -0.2820] | 1.0579 | 0.2436 | -0.000600 | 1.3863 | 0.00% | 100.00% | 1.0000 | 0.010 | [0.010, 0.010] | 12.007 |
| factorial | regime=baseline | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.001 | SPSA | -0.3610 | [-0.3902, -0.3317] | 1.0371 | 0.1011 | -0.000612 | 1.4609 | 0.00% | 100.00% | 1.0000 | 0.010 | [0.010, 0.010] | 12.007 |
| factorial | regime=baseline | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.02 | Bayesian Optimization | -0.2978 | [-0.3403, -0.2553] | 1.0482 | 0.1539 | -0.000605 | 1.3383 | 0.00% | 100.00% | 1.0000 | 0.195 | [0.188, 0.201] | 12.007 |
| factorial | regime=baseline | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.02 | Classical Markowitz | -0.4886 | [-0.5492, -0.4281] | 1.0000 | 0.0000 | NA | 1.4972 | 100.00% | 100.00% | 1.0000 | 0.001 | [0.001, 0.001] | 0.000 |
| factorial | regime=baseline | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.02 | Random Search | -0.3281 | [-0.3903, -0.2659] | 1.0568 | 0.1576 | -0.000606 | 1.4014 | 0.00% | 100.00% | 1.0000 | 0.011 | [0.011, 0.011] | 12.007 |
| factorial | regime=baseline | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.02 | SPSA | -0.3033 | [-0.3726, -0.2340] | 1.0857 | 0.1944 | -0.000586 | 1.1608 | 0.00% | 100.00% | 1.0000 | 0.011 | [0.010, 0.011] | 12.007 |
| factorial | regime=baseline | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.001 | Bayesian Optimization | -0.4443 | [-0.5157, -0.3728] | 1.0031 | 0.0314 | -0.000635 | 1.3562 | 0.00% | 100.00% | 1.0000 | 0.325 | [0.313, 0.336] | 12.006 |
| factorial | regime=baseline | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.001 | Classical Markowitz | -0.4886 | [-0.5492, -0.4281] | 1.0000 | 0.0000 | NA | 1.4972 | 100.00% | 100.00% | 1.0000 | 0.001 | [0.001, 0.001] | 0.000 |
| factorial | regime=baseline | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.001 | Random Search | -0.4196 | [-0.4648, -0.3743] | 1.0031 | 0.0576 | -0.000635 | 1.3562 | 0.00% | 100.00% | 1.0000 | 0.011 | [0.011, 0.011] | 12.006 |
| factorial | regime=baseline | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.001 | SPSA | -0.4230 | [-0.4618, -0.3842] | 1.0031 | 0.0545 | -0.000635 | 1.3562 | 0.00% | 100.00% | 1.0000 | 0.010 | [0.010, 0.011] | 12.006 |
| factorial | regime=baseline | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.02 | Bayesian Optimization | -0.3233 | [-0.3465, -0.3001] | 1.0949 | 0.2470 | -0.000579 | 1.1768 | 0.00% | 100.00% | 1.0000 | 0.293 | [0.269, 0.317] | 12.006 |
| factorial | regime=baseline | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.02 | Classical Markowitz | -0.4886 | [-0.5492, -0.4281] | 1.0000 | 0.0000 | NA | 1.4972 | 100.00% | 100.00% | 1.0000 | 0.001 | [0.001, 0.001] | 0.000 |
| factorial | regime=baseline | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.02 | Random Search | -0.3493 | [-0.3921, -0.3064] | 1.0930 | 0.2793 | -0.000586 | 1.3503 | 0.00% | 100.00% | 1.0000 | 0.010 | [0.009, 0.010] | 12.006 |
| factorial | regime=baseline | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.02 | SPSA | -0.3246 | [-0.3472, -0.3020] | 1.1052 | 0.2982 | -0.000578 | 1.3299 | 0.00% | 100.00% | 1.0000 | 0.010 | [0.009, 0.010] | 12.006 |
| factorial | regime=baseline | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.001 | Bayesian Optimization | -0.4278 | [-0.4580, -0.3976] | 1.0000 | 0.0000 | -0.000660 | 1.7149 | 0.00% | 100.00% | 1.0000 | 0.276 | [0.269, 0.283] | 12.002 |
| factorial | regime=baseline | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.001 | Classical Markowitz | -0.5069 | [-0.5198, -0.4940] | 1.0000 | 0.0000 | NA | 1.7149 | 100.00% | 100.00% | 1.0000 | 0.000 | [0.000, 0.000] | 0.000 |
| factorial | regime=baseline | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.001 | Random Search | -0.4502 | [-0.4735, -0.4269] | 1.0000 | 0.0000 | -0.000660 | 1.7149 | 0.00% | 100.00% | 1.0000 | 0.003 | [0.003, 0.003] | 12.002 |
| factorial | regime=baseline | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.001 | SPSA | -0.4698 | [-0.4971, -0.4425] | 1.0000 | 0.0661 | -0.000660 | 1.7149 | 0.00% | 100.00% | 1.0000 | 0.003 | [0.003, 0.003] | 12.002 |
| factorial | regime=baseline | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.02 | Bayesian Optimization | -0.4617 | [-0.4677, -0.4556] | 1.0000 | 0.0145 | -0.000660 | 1.7149 | 0.00% | 100.00% | 1.0000 | 0.247 | [0.241, 0.253] | 12.002 |
| factorial | regime=baseline | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.02 | Classical Markowitz | -0.5069 | [-0.5198, -0.4940] | 1.0000 | 0.0000 | NA | 1.7149 | 100.00% | 100.00% | 1.0000 | 0.000 | [0.000, 0.000] | 0.000 |
| factorial | regime=baseline | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.02 | Random Search | -0.4713 | [-0.4846, -0.4581] | 1.0000 | 0.0358 | -0.000660 | 1.7149 | 0.00% | 100.00% | 1.0000 | 0.004 | [0.004, 0.004] | 12.002 |
| factorial | regime=baseline | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.02 | SPSA | -0.4575 | [-0.4847, -0.4303] | 1.0000 | 0.0168 | -0.000660 | 1.7149 | 0.00% | 100.00% | 1.0000 | 0.003 | [0.003, 0.003] | 12.002 |
| factorial | regime=baseline | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.001 | Bayesian Optimization | -0.5069 | [-0.5198, -0.4940] | 1.0000 | 0.0119 | -0.000660 | 1.7149 | 29.17% | 100.00% | 1.0000 | 0.401 | [0.259, 0.542] | 12.002 |
| factorial | regime=baseline | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.001 | Classical Markowitz | -0.5069 | [-0.5198, -0.4940] | 1.0000 | 0.0000 | NA | 1.7149 | 12.50% | 100.00% | 1.0000 | 0.000 | [0.000, 0.000] | 0.000 |
| factorial | regime=baseline | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.001 | Random Search | -0.5069 | [-0.5198, -0.4940] | 1.0000 | 0.0000 | -0.000660 | 1.7149 | 29.17% | 100.00% | 1.0000 | 0.003 | [0.003, 0.003] | 12.002 |
| factorial | regime=baseline | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.001 | SPSA | -0.5069 | [-0.5198, -0.4940] | 1.0000 | 0.0000 | -0.000660 | 1.7149 | 29.17% | 100.00% | 1.0000 | 0.003 | [0.003, 0.003] | 12.002 |
| factorial | regime=baseline | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.02 | Bayesian Optimization | -0.4697 | [-0.4858, -0.4535] | 1.0000 | 0.0000 | -0.000660 | 1.7149 | 0.00% | 100.00% | 1.0000 | 0.255 | [0.247, 0.263] | 12.002 |
| factorial | regime=baseline | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.02 | Classical Markowitz | -0.5069 | [-0.5198, -0.4940] | 1.0000 | 0.0000 | NA | 1.7149 | 100.00% | 100.00% | 1.0000 | 0.000 | [0.000, 0.000] | 0.000 |
| factorial | regime=baseline | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.02 | Random Search | -0.4752 | [-0.5006, -0.4499] | 1.0000 | 0.0000 | -0.000660 | 1.7149 | 0.00% | 100.00% | 1.0000 | 0.004 | [0.004, 0.004] | 12.002 |
| factorial | regime=baseline | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.02 | SPSA | -0.4782 | [-0.4990, -0.4574] | 1.0000 | 0.0000 | -0.000660 | 1.7149 | 0.00% | 100.00% | 1.0000 | 0.004 | [0.003, 0.004] | 12.002 |
| factorial | regime=hard_budget | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.001 | Bayesian Optimization | -0.3889 | [-0.3944, -0.3834] | 1.0011 | 0.0164 | -0.000526 | 3.5662 | 0.00% | 100.00% | 1.0000 | 0.288 | [0.265, 0.311] | 12.007 |
| factorial | regime=hard_budget | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.001 | Classical Markowitz | -0.4044 | [-0.4087, -0.4000] | 1.0000 | 0.0000 | NA | 3.5194 | 100.00% | 100.00% | 1.0000 | 0.001 | [0.001, 0.001] | 0.000 |
| factorial | regime=hard_budget | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.001 | Random Search | 2.5091 | [-0.3875, 5.4057] | 1.0080 | 0.0441 | -0.000522 | 3.7635 | 0.00% | 100.00% | 1.0000 | 0.010 | [0.010, 0.010] | 12.007 |
| factorial | regime=hard_budget | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.001 | SPSA | -0.3875 | [-0.3895, -0.3855] | 1.0048 | 0.0412 | -0.000524 | 3.7644 | 0.00% | 100.00% | 1.0000 | 0.009 | [0.009, 0.009] | 12.006 |
| factorial | regime=hard_budget | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.02 | Bayesian Optimization | -0.3733 | [-0.3796, -0.3670] | 1.0112 | 0.0353 | -0.000521 | 3.3913 | 0.00% | 100.00% | 1.0000 | 0.277 | [0.221, 0.333] | 12.008 |
| factorial | regime=hard_budget | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.02 | Classical Markowitz | -0.4044 | [-0.4087, -0.4000] | 1.0000 | 0.0000 | NA | 3.5194 | 100.00% | 100.00% | 1.0000 | 0.001 | [0.001, 0.001] | 0.000 |
| factorial | regime=hard_budget | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.02 | Random Search | -0.3844 | [-0.3883, -0.3805] | 1.0157 | 0.0390 | -0.000518 | 3.7177 | 0.00% | 100.00% | 1.0000 | 0.011 | [0.010, 0.011] | 12.007 |
| factorial | regime=hard_budget | n_assets=12 | mixer_type=product_x | depolarizing_strength_2q=0.02 | SPSA | -0.3875 | [-0.3917, -0.3834] | 1.0081 | 0.0220 | -0.000522 | 3.3381 | 0.00% | 100.00% | 1.0000 | 0.011 | [0.011, 0.011] | 12.007 |
| factorial | regime=hard_budget | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.001 | Bayesian Optimization | -0.3972 | [-0.4015, -0.3929] | 1.0011 | 0.0132 | -0.000526 | 3.5662 | 0.00% | 100.00% | 1.0000 | 0.350 | [0.283, 0.417] | 12.006 |
| factorial | regime=hard_budget | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.001 | Classical Markowitz | -0.4044 | [-0.4087, -0.4000] | 1.0000 | 0.0000 | NA | 3.5194 | 100.00% | 100.00% | 1.0000 | 0.001 | [0.001, 0.001] | 0.000 |
| factorial | regime=hard_budget | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.001 | Random Search | -0.3971 | [-0.4014, -0.3928] | 1.0046 | 0.0101 | -0.000524 | 3.5649 | 0.00% | 100.00% | 1.0000 | 0.010 | [0.010, 0.010] | 12.006 |
| factorial | regime=hard_budget | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.001 | SPSA | -0.3972 | [-0.4026, -0.3919] | 1.0000 | 0.0045 | -0.000526 | 3.5194 | 0.00% | 100.00% | 1.0000 | 0.010 | [0.010, 0.010] | 12.006 |
| factorial | regime=hard_budget | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.02 | Bayesian Optimization | -0.3867 | [-0.3915, -0.3820] | 1.0000 | 0.0126 | -0.000526 | 3.5194 | 0.00% | 100.00% | 1.0000 | 0.276 | [0.260, 0.292] | 12.007 |
| factorial | regime=hard_budget | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.02 | Classical Markowitz | -0.4044 | [-0.4087, -0.4000] | 1.0000 | 0.0000 | NA | 3.5194 | 100.00% | 100.00% | 1.0000 | 0.001 | [0.001, 0.001] | 0.000 |
| factorial | regime=hard_budget | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.02 | Random Search | -0.3853 | [-0.3858, -0.3848] | 1.0011 | 0.0160 | -0.000526 | 3.5662 | 0.00% | 100.00% | 1.0000 | 0.010 | [0.010, 0.011] | 12.006 |
| factorial | regime=hard_budget | n_assets=12 | mixer_type=xy | depolarizing_strength_2q=0.02 | SPSA | -0.3856 | [-0.3900, -0.3812] | 1.0011 | 0.0132 | -0.000526 | 3.5662 | 0.00% | 100.00% | 1.0000 | 0.010 | [0.010, 0.010] | 12.006 |
| factorial | regime=hard_budget | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.001 | Bayesian Optimization | -0.4147 | [-0.4561, -0.3734] | 1.0000 | 0.0028 | -0.000545 | 4.0870 | 0.00% | 100.00% | 1.0000 | 0.337 | [0.300, 0.374] | 12.002 |
| factorial | regime=hard_budget | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.001 | Classical Markowitz | -0.4189 | [-0.4581, -0.3798] | 1.0000 | 0.0000 | NA | 4.0870 | 100.00% | 100.00% | 1.0000 | 0.000 | [0.000, 0.000] | 0.000 |
| factorial | regime=hard_budget | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.001 | Random Search | -0.4152 | [-0.4561, -0.3744] | 1.0000 | 0.0000 | -0.000545 | 4.0870 | 0.00% | 100.00% | 1.0000 | 0.003 | [0.003, 0.004] | 12.002 |
| factorial | regime=hard_budget | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.001 | SPSA | -0.4146 | [-0.4558, -0.3733] | 1.0000 | 0.0019 | -0.000545 | 4.0870 | 0.00% | 100.00% | 1.0000 | 0.003 | [0.003, 0.003] | 12.002 |
| factorial | regime=hard_budget | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.02 | Bayesian Optimization | -0.4154 | [-0.4547, -0.3762] | 1.0000 | 0.0023 | -0.000545 | 4.0870 | 0.00% | 100.00% | 1.0000 | 0.233 | [0.206, 0.260] | 12.002 |
| factorial | regime=hard_budget | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.02 | Classical Markowitz | -0.4189 | [-0.4581, -0.3798] | 1.0000 | 0.0000 | NA | 4.0870 | 100.00% | 100.00% | 1.0000 | 0.000 | [0.000, 0.000] | 0.000 |
| factorial | regime=hard_budget | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.02 | Random Search | -0.4152 | [-0.4564, -0.3739] | 1.0000 | 0.0002 | -0.000545 | 4.0870 | 0.00% | 100.00% | 1.0000 | 0.004 | [0.004, 0.004] | 12.002 |
| factorial | regime=hard_budget | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.02 | SPSA | -0.4163 | [-0.4572, -0.3755] | 1.0000 | 0.0003 | -0.000545 | 4.0870 | 0.00% | 100.00% | 1.0000 | 0.003 | [0.003, 0.004] | 12.002 |
| factorial | regime=hard_budget | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.001 | Bayesian Optimization | -0.4187 | [-0.4578, -0.3797] | 1.0000 | 0.0000 | -0.000545 | 4.0870 | 0.00% | 100.00% | 1.0000 | 0.304 | [0.262, 0.347] | 12.002 |
| factorial | regime=hard_budget | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.001 | Classical Markowitz | -0.4189 | [-0.4581, -0.3798] | 1.0000 | 0.0000 | NA | 4.0870 | 66.67% | 100.00% | 1.0000 | 0.000 | [0.000, 0.000] | 0.000 |
| factorial | regime=hard_budget | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.001 | Random Search | -0.4188 | [-0.4578, -0.3798] | 1.0000 | 0.0000 | -0.000545 | 4.0870 | 16.67% | 100.00% | 1.0000 | 0.003 | [0.003, 0.003] | 12.002 |
| factorial | regime=hard_budget | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.001 | SPSA | -0.4187 | [-0.4576, -0.3798] | 1.0000 | 0.0007 | -0.000545 | 4.0870 | 16.67% | 100.00% | 1.0000 | 0.003 | [0.003, 0.004] | 12.002 |
| factorial | regime=hard_budget | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.02 | Bayesian Optimization | -0.4171 | [-0.4566, -0.3776] | 1.0000 | 0.0000 | -0.000545 | 4.0870 | 0.00% | 100.00% | 1.0000 | 0.323 | [0.240, 0.405] | 12.002 |
| factorial | regime=hard_budget | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.02 | Classical Markowitz | -0.4189 | [-0.4581, -0.3798] | 1.0000 | 0.0000 | NA | 4.0870 | 100.00% | 100.00% | 1.0000 | 0.000 | [0.000, 0.000] | 0.000 |
| factorial | regime=hard_budget | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.02 | Random Search | -0.4160 | [-0.4558, -0.3763] | 1.0000 | 0.0000 | -0.000545 | 4.0870 | 0.00% | 100.00% | 1.0000 | 0.004 | [0.004, 0.004] | 12.002 |
| factorial | regime=hard_budget | n_assets=6 | mixer_type=xy | depolarizing_strength_2q=0.02 | SPSA | -0.4166 | [-0.4564, -0.3769] | 1.0000 | 0.0000 | -0.000545 | 4.0870 | 0.00% | 100.00% | 1.0000 | 0.004 | [0.004, 0.004] | 12.002 |

## Application-ready summary

This benchmark demonstrates the ability to build a reproducible, hardware-aware research instrument that connects constrained QAOA physics, optimizer design, and runtime-cost accounting into a single comparative framework.
