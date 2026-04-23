# Application-ready project summary

This benchmark demonstrates the ability to build a reproducible, hardware-aware research instrument that connects constrained QAOA physics, optimizer design, and runtime-cost accounting into a single comparative framework.

## Research question

When does a more sophisticated classical optimizer justify its runtime, shot, queue, and mitigation cost for constrained QAOA portfolio optimization?

## Evidence summary

- Best mean raw objective: Classical Markowitz on factorial=regime=baseline | n_assets=6 | mixer_type=product_x | depolarizing_strength_2q=0.001 with -0.5069.
- Strongest feasibility: Bayesian Optimization reached mean feasible-hit rate 100.00%.
- Best cost-adjusted method: Classical Markowitz minimized estimated cost plus elapsed time most effectively.
