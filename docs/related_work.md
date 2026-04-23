# Related Work

This study sits at the intersection of constrained QAOA optimization, Bayesian outer-loop search, and portfolio-selection problems.

## Core references

- Farhi, Goldstone, and Gutmann (2014), *A Quantum Approximate Optimization Algorithm*.
  The original QAOA paper and the starting point for the circuit family used here.
- Barkoutsos et al. (2020), *Improving Variational Quantum Optimization using CVaR*.
  The key reference for using CVaR-style objectives instead of plain expectation values in variational optimization.
- Egger et al. (2021), *Warm-starting quantum optimization*.
  Important background for portfolio-style QUBO problems and for future warm-start experiments.
- Herman, Googin, Liu, and Galda (2022), *A Survey of Quantum Computing for Finance*.
  Places the portfolio-optimization problem in the broader quantum-finance landscape.
- Balandat et al. (2020), *BoTorch: A Framework for Efficient Monte-Carlo Bayesian Optimization*.
  Reference point for the Bayesian optimization path and the acquisition-function design space used here.

## Positioning of this repository

This repository does not claim quantum advantage. Its contribution is empirical characterisation: identifying when optimizer overhead, constraint hardness, and backend realism change the practical ranking between a classical baseline, random search, SPSA, and Bayesian optimization for constrained QAOA portfolio instances.
