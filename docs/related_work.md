# Related Work

This study sits at the intersection of QAOA theory, frustrated spin systems, finite-depth variational dynamics, and classical outer-loop optimization.

## Core references

- Farhi, Goldstone, and Gutmann (2014), *A Quantum Approximate Optimization Algorithm*.
  The original QAOA paper and the starting point for the circuit family used here.
- Hadfield et al. (2019), *From the Quantum Approximate Optimization Algorithm to a Quantum Alternating Operator Ansatz*.
  Important for understanding how problem structure, mixers, and constrained subspaces influence finite-depth variational behavior.
- McClean et al. (2018), *Barren plateaus in quantum neural network training landscapes*.
  Central background for interpreting whether increased depth improves expressivity faster than it harms trainability.
- Barkoutsos et al. (2020), *Improving Variational Quantum Optimization using CVaR*.
  Relevant whenever low-probability low-energy sectors are emphasized instead of raw expectation values.
- Balandat et al. (2020), *BoTorch: A Framework for Efficient Monte-Carlo Bayesian Optimization*.
  Reference point for the Bayesian outer-loop tooling retained in the repository.
- Spall (1998), *An Overview of the Simultaneous Perturbation Method for Efficient Optimization*.
  Canonical reference for the SPSA path used in low-budget noisy variational settings.
- Sachdev (2011), *Quantum Phase Transitions*.
  Background for interpreting transverse-field and frustrated-spin regimes in terms of phase structure rather than only objective values.

## Positioning of this repository

This repository does not claim quantum advantage. Its contribution is empirical characterisation: identifying how QAOA depth controls the recoverability of physical structure in frustrated spin Hamiltonians, and how optimizer/runtime overhead interacts with that recoverability. The core claim under study is that energy recovery can precede observable recovery, so finite-depth QAOA should be treated as a physical-resolution instrument rather than only an energy minimizer.
