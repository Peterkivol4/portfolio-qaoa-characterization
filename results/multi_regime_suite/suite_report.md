# Portfolio QAOA characterisation suite

## Research question

When does a more sophisticated classical optimizer justify its runtime, shot, queue, and mitigation cost for constrained QAOA portfolio optimization?

## Why this benchmark matters

Across the completed suite, Classical Markowitz delivered the strongest mean objective on regime=sparse_covariance, while Classical Markowitz provided the best cost-adjusted tradeoff on at least one study point.

## Technical contributions demonstrated

- Constraint-aware QAOA benchmarking across multiple synthetic portfolio regimes.
- Fair optimizer comparison under shared runtime, shot, and billing accounting.
- Structured exports that preserve both benchmark claims and per-evaluation evidence.

## Evidence summary

- Best mean raw objective: Classical Markowitz on regime=sparse_covariance with -0.4625.
- Strongest feasibility: Bayesian Optimization reached mean feasible-hit rate 100.00%.
- Best cost-adjusted method: Classical Markowitz minimized estimated cost plus elapsed time most effectively.

## Headline claims

- For asset_scale=10, Classical Markowitz has the best mean raw objective (-0.4002, bootstrap 95% CI -0.4587–-0.3669).
- For asset_scale=10, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For asset_scale=12, Classical Markowitz has the best mean raw objective (-0.3781, bootstrap 95% CI -0.4240–-0.3485).
- For asset_scale=12, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For asset_scale=6, Classical Markowitz has the best mean raw objective (-0.3994, bootstrap 95% CI -0.4213–-0.3772).
- For asset_scale=6, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For asset_scale=8, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For asset_scale=8, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For cvar_alpha=0.05, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For cvar_alpha=0.05, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For cvar_alpha=0.1, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For cvar_alpha=0.1, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For cvar_alpha=0.2, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For cvar_alpha=0.2, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For depth=1, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For depth=1, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For depth=2, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For depth=2, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For depth=3, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For depth=3, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For depth=8, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For depth=8, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For eval_budget=12, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For eval_budget=12, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For eval_budget=20, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For eval_budget=20, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For eval_budget=8, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For eval_budget=8, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For invalid_penalty=100.0, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For invalid_penalty=100.0, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For invalid_penalty=20.0, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For invalid_penalty=20.0, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For invalid_penalty=50.0, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For invalid_penalty=50.0, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For regime=baseline, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For regime=baseline, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For regime=clustered_assets, Classical Markowitz has the best mean raw objective (-0.4300, bootstrap 95% CI -0.5173–-0.3658).
- For regime=clustered_assets, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For regime=hard_budget, Classical Markowitz has the best mean raw objective (-0.3140, bootstrap 95% CI -0.3350–-0.2915).
- For regime=hard_budget, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For regime=high_correlation, Classical Markowitz has the best mean raw objective (-0.3740, bootstrap 95% CI -0.4829–-0.3062).
- For regime=high_correlation, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For regime=low_correlation, Classical Markowitz has the best mean raw objective (-0.4289, bootstrap 95% CI -0.5205–-0.3624).
- For regime=low_correlation, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For regime=sparse_covariance, Classical Markowitz has the best mean raw objective (-0.4625, bootstrap 95% CI -0.5437–-0.4064).
- For regime=sparse_covariance, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For shot_budget=128, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For shot_budget=128, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For shot_budget=2048, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For shot_budget=2048, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.
- For shot_budget=512, Classical Markowitz has the best mean raw objective (-0.3615, bootstrap 95% CI -0.5086–-0.2641).
- For shot_budget=512, feasibility favors Bayesian Optimization (100.00%) even though the raw-objective winner is Classical Markowitz.

## Aggregated results

| Study | Value | Method | Mean raw objective | 95% CI raw | Win rate | 95% CI win | Mean feasible hit rate | 95% CI feasible | Mean approx gap | p vs random (best valid) | Mean elapsed s | Mean billed s | Mean est. QPU cost USD |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| asset_scale | 10 | Bayesian Optimization | -0.2969 | [-0.3612, -0.2567] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0328 | 1.0000 | 0.619 | 24.017 | 0.000000 |
| asset_scale | 10 | Classical Markowitz | -0.4002 | [-0.4587, -0.3669] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| asset_scale | 10 | Random Search | -0.2886 | [-0.3601, -0.2478] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0266 | 1.0000 | 0.028 | 24.015 | 0.000000 |
| asset_scale | 10 | SPSA | -0.2964 | [-0.3630, -0.2553] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0242 | 1.0000 | 0.028 | 24.015 | 0.000000 |
| asset_scale | 12 | Bayesian Optimization | -0.2376 | [-0.3009, -0.1965] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0535 | 1.0000 | 0.566 | 24.027 | 0.000000 |
| asset_scale | 12 | Classical Markowitz | -0.3781 | [-0.4240, -0.3485] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.001 | 0.000 | 0.000000 |
| asset_scale | 12 | Random Search | -0.2492 | [-0.3066, -0.1910] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0437 | 1.0000 | 0.039 | 24.025 | 0.000000 |
| asset_scale | 12 | SPSA | -0.2307 | [-0.2964, -0.1919] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0485 | 1.0000 | 0.039 | 24.025 | 0.000000 |
| asset_scale | 6 | Bayesian Optimization | -0.3864 | [-0.3941, -0.3747] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0007 | 1.0000 | 0.589 | 24.009 | 0.000000 |
| asset_scale | 6 | Classical Markowitz | -0.3994 | [-0.4213, -0.3772] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| asset_scale | 6 | Random Search | -0.3880 | [-0.4105, -0.3619] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0006 | 1.0000 | 0.011 | 24.008 | 0.000000 |
| asset_scale | 6 | SPSA | -0.3678 | [-0.3828, -0.3423] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0003 | 1.0000 | 0.011 | 24.008 | 0.000000 |
| asset_scale | 8 | Bayesian Optimization | -0.3146 | [-0.4440, -0.2444] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0138 | 1.0000 | 0.589 | 24.012 | 0.000000 |
| asset_scale | 8 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| asset_scale | 8 | Random Search | -0.3018 | [-0.4202, -0.2384] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0102 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| asset_scale | 8 | SPSA | -0.3101 | [-0.4280, -0.2390] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0027 | 1.0000 | 0.019 | 24.010 | 0.000000 |
| cvar_alpha | 0.05 | Bayesian Optimization | -0.3375 | [-0.4735, -0.2562] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0056 | 1.0000 | 0.584 | 24.012 | 0.000000 |
| cvar_alpha | 0.05 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| cvar_alpha | 0.05 | Random Search | -0.3265 | [-0.4420, -0.2554] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0102 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| cvar_alpha | 0.05 | SPSA | -0.3321 | [-0.4551, -0.2531] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0026 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| cvar_alpha | 0.1 | Bayesian Optimization | -0.3146 | [-0.4440, -0.2444] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0138 | 1.0000 | 0.534 | 24.012 | 0.000000 |
| cvar_alpha | 0.1 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| cvar_alpha | 0.1 | Random Search | -0.3018 | [-0.4202, -0.2384] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0102 | 1.0000 | 0.020 | 24.011 | 0.000000 |
| cvar_alpha | 0.1 | SPSA | -0.3101 | [-0.4280, -0.2390] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0027 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| cvar_alpha | 0.2 | Bayesian Optimization | -0.2823 | [-0.4087, -0.2143] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0104 | 1.0000 | 0.561 | 24.012 | 0.000000 |
| cvar_alpha | 0.2 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| cvar_alpha | 0.2 | Random Search | -0.2722 | [-0.3943, -0.2088] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0102 | 1.0000 | 0.020 | 24.011 | 0.000000 |
| cvar_alpha | 0.2 | SPSA | -0.2737 | [-0.3801, -0.2190] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0027 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| depth | 1 | Bayesian Optimization | -0.3241 | [-0.4507, -0.2540] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0049 | 1.0000 | 0.411 | 24.011 | 0.000000 |
| depth | 1 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| depth | 1 | Random Search | -0.3168 | [-0.4471, -0.2476] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0098 | 1.0000 | 0.018 | 24.010 | 0.000000 |
| depth | 1 | SPSA | -0.3188 | [-0.4641, -0.2458] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0054 | 1.0000 | 0.018 | 24.010 | 0.000000 |
| depth | 2 | Bayesian Optimization | -0.3146 | [-0.4440, -0.2444] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0138 | 1.0000 | 0.537 | 24.012 | 0.000000 |
| depth | 2 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| depth | 2 | Random Search | -0.3018 | [-0.4202, -0.2384] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0102 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| depth | 2 | SPSA | -0.3101 | [-0.4280, -0.2390] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0027 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| depth | 3 | Bayesian Optimization | -0.3005 | [-0.4150, -0.2395] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0110 | 1.0000 | 0.586 | 24.013 | 0.000000 |
| depth | 3 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| depth | 3 | Random Search | -0.3042 | [-0.4295, -0.2409] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0087 | 1.0000 | 0.021 | 24.012 | 0.000000 |
| depth | 3 | SPSA | -0.2940 | [-0.4057, -0.2329] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0095 | 1.0000 | 0.020 | 24.011 | 0.000000 |
| depth | 8 | Bayesian Optimization | -0.2899 | [-0.3973, -0.2349] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0082 | 1.0000 | 0.557 | 24.015 | 0.000000 |
| depth | 8 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| depth | 8 | Random Search | -0.2925 | [-0.4040, -0.2296] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0111 | 1.0000 | 0.024 | 24.014 | 0.000000 |
| depth | 8 | SPSA | -0.2967 | [-0.4218, -0.2323] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0092 | 1.0000 | 0.023 | 24.014 | 0.000000 |
| eval_budget | 12 | Bayesian Optimization | -0.3146 | [-0.4440, -0.2444] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0138 | 1.0000 | 0.609 | 24.012 | 0.000000 |
| eval_budget | 12 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| eval_budget | 12 | Random Search | -0.3018 | [-0.4202, -0.2384] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0102 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| eval_budget | 12 | SPSA | -0.3101 | [-0.4280, -0.2390] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0027 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| eval_budget | 20 | Bayesian Optimization | -0.3153 | [-0.4403, -0.2419] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0094 | 1.0000 | 1.024 | 40.020 | 0.000000 |
| eval_budget | 20 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| eval_budget | 20 | Random Search | -0.3047 | [-0.4226, -0.2384] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0070 | 1.0000 | 0.032 | 40.018 | 0.000000 |
| eval_budget | 20 | SPSA | -0.3076 | [-0.4408, -0.2352] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0073 | 1.0000 | 0.032 | 40.018 | 0.000000 |
| eval_budget | 8 | Bayesian Optimization | -0.3081 | [-0.4373, -0.2373] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0104 | 1.0000 | 0.277 | 16.008 | 0.000000 |
| eval_budget | 8 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| eval_budget | 8 | Random Search | -0.2977 | [-0.4168, -0.2381] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0079 | 1.0000 | 0.013 | 16.007 | 0.000000 |
| eval_budget | 8 | SPSA | -0.2885 | [-0.4087, -0.2181] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0188 | 1.0000 | 0.013 | 16.007 | 0.000000 |
| invalid_penalty | 100.0 | Bayesian Optimization | -0.3146 | [-0.4440, -0.2444] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0138 | 1.0000 | 0.619 | 24.012 | 0.000000 |
| invalid_penalty | 100.0 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| invalid_penalty | 100.0 | Random Search | -0.3018 | [-0.4202, -0.2384] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0102 | 1.0000 | 0.020 | 24.011 | 0.000000 |
| invalid_penalty | 100.0 | SPSA | -0.3101 | [-0.4280, -0.2390] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0027 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| invalid_penalty | 20.0 | Bayesian Optimization | -0.3146 | [-0.4440, -0.2444] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0138 | 1.0000 | 0.572 | 24.012 | 0.000000 |
| invalid_penalty | 20.0 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| invalid_penalty | 20.0 | Random Search | -0.3018 | [-0.4202, -0.2384] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0102 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| invalid_penalty | 20.0 | SPSA | -0.3101 | [-0.4280, -0.2390] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0027 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| invalid_penalty | 50.0 | Bayesian Optimization | -0.3146 | [-0.4440, -0.2444] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0138 | 1.0000 | 0.561 | 24.012 | 0.000000 |
| invalid_penalty | 50.0 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| invalid_penalty | 50.0 | Random Search | -0.3018 | [-0.4202, -0.2384] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0102 | 1.0000 | 0.020 | 24.011 | 0.000000 |
| invalid_penalty | 50.0 | SPSA | -0.3101 | [-0.4280, -0.2390] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0027 | 1.0000 | 0.020 | 24.011 | 0.000000 |
| regime | baseline | Bayesian Optimization | -0.3146 | [-0.4440, -0.2444] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0138 | 1.0000 | 0.663 | 24.012 | 0.000000 |
| regime | baseline | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| regime | baseline | Random Search | -0.3018 | [-0.4202, -0.2384] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0102 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| regime | baseline | SPSA | -0.3101 | [-0.4280, -0.2390] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0027 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| regime | clustered_assets | Bayesian Optimization | -0.3854 | [-0.4658, -0.3434] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0104 | 1.0000 | 0.527 | 24.012 | 0.000000 |
| regime | clustered_assets | Classical Markowitz | -0.4300 | [-0.5173, -0.3658] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| regime | clustered_assets | Random Search | -0.3741 | [-0.4444, -0.3275] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0094 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| regime | clustered_assets | SPSA | -0.3742 | [-0.4403, -0.3290] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0145 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| regime | hard_budget | Bayesian Optimization | -0.3096 | [-0.3288, -0.2880] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0006 | 1.0000 | 0.439 | 24.012 | 0.000000 |
| regime | hard_budget | Classical Markowitz | -0.3140 | [-0.3350, -0.2915] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| regime | hard_budget | Random Search | -0.3097 | [-0.3302, -0.2868] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0006 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| regime | hard_budget | SPSA | -0.3090 | [-0.3280, -0.2879] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0005 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| regime | high_correlation | Bayesian Optimization | -0.3341 | [-0.4444, -0.2770] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0092 | 1.0000 | 0.634 | 24.012 | 0.000000 |
| regime | high_correlation | Classical Markowitz | -0.3740 | [-0.4829, -0.3062] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| regime | high_correlation | Random Search | -0.3164 | [-0.4082, -0.2622] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0093 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| regime | high_correlation | SPSA | -0.3144 | [-0.3983, -0.2651] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0120 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| regime | low_correlation | Bayesian Optimization | -0.3847 | [-0.4706, -0.3334] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0119 | 1.0000 | 0.661 | 24.012 | 0.000000 |
| regime | low_correlation | Classical Markowitz | -0.4289 | [-0.5205, -0.3624] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| regime | low_correlation | Random Search | -0.3696 | [-0.4458, -0.3197] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0105 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| regime | low_correlation | SPSA | -0.3722 | [-0.4446, -0.3228] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0096 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| regime | sparse_covariance | Bayesian Optimization | -0.4179 | [-0.4971, -0.3696] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0114 | 1.0000 | 0.557 | 24.012 | 0.000000 |
| regime | sparse_covariance | Classical Markowitz | -0.4625 | [-0.5437, -0.4064] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| regime | sparse_covariance | Random Search | -0.4117 | [-0.4743, -0.3709] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0062 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| regime | sparse_covariance | SPSA | -0.4132 | [-0.5028, -0.3562] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0037 | 1.0000 | 0.019 | 24.011 | 0.000000 |
| shot_budget | 128 | Bayesian Optimization | -0.3161 | [-0.4338, -0.2456] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0197 | 1.0000 | 0.585 | 24.008 | 0.000000 |
| shot_budget | 128 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| shot_budget | 128 | Random Search | -0.3106 | [-0.4413, -0.2401] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0234 | 1.0000 | 0.013 | 24.007 | 0.000000 |
| shot_budget | 128 | SPSA | -0.3034 | [-0.4400, -0.2268] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0170 | 1.0000 | 0.012 | 24.007 | 0.000000 |
| shot_budget | 2048 | Bayesian Optimization | -0.3118 | [-0.4426, -0.2351] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.687 | 24.060 | 0.000000 |
| shot_budget | 2048 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| shot_budget | 2048 | Random Search | -0.3106 | [-0.4378, -0.2384] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.071 | 24.058 | 0.000000 |
| shot_budget | 2048 | SPSA | -0.2954 | [-0.4112, -0.2318] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.072 | 24.058 | 0.000000 |
| shot_budget | 512 | Bayesian Optimization | -0.3107 | [-0.4370, -0.2418] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0060 | 1.0000 | 0.452 | 24.019 | 0.000000 |
| shot_budget | 512 | Classical Markowitz | -0.3615 | [-0.5086, -0.2641] | 100.00% | [100.00%, 100.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.000 | 0.000 | 0.000000 |
| shot_budget | 512 | Random Search | -0.3089 | [-0.4412, -0.2381] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0051 | 1.0000 | 0.029 | 24.018 | 0.000000 |
| shot_budget | 512 | SPSA | -0.3076 | [-0.4363, -0.2382] | 0.00% | [0.00%, 0.00%] | 100.00% | [100.00%, 100.00%] | 0.0000 | 1.0000 | 0.029 | 24.018 | 0.000000 |

## Application-ready summary

This benchmark demonstrates the ability to build a reproducible, hardware-aware research instrument that connects constrained QAOA physics, optimizer design, and runtime-cost accounting into a single comparative framework.
