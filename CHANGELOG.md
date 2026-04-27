# Changelog

## 0.5.0

- Added a spin-physics subsystem for studying QAOA depth as a physical resolution limit on J1-J2 transverse-field Ising Hamiltonians.
- Added `SpinRunConfig`, dense Hamiltonian construction, exact diagonalization, physical observable recovery metrics, and p-layer resolution records.
- Added `p-sweep`, `parameter-confusion`, and `resolution-cost` CLI commands plus the `layerfield-qaoa` console-script alias.
- Added new spin-study docs and tests covering Hamiltonian shape, Hermiticity, exact limits, observable bounds, and p-resolution artifact generation.

## 0.3.0

- Established the regime-aware QAOA benchmark pipeline, suite reporting, plotting, and backend-aware execution paths.

## 0.4.0

- Replaced opaque internal type names with descriptive research-facing names and kept temporary compatibility aliases.
- Removed placeholder secret-handling modules that were not part of the scientific artifact.
- Added a classical Markowitz baseline, QUBO structure diagnostics, and significance reporting against random search.
- Added precomputed suite outputs under `results/multi_regime_suite/`.
- Added related-work documentation, architecture/security notes, and a reproducibility notebook.
- Expanded tests across regimes, runtime accounting, statistical summaries, and exact-reference behavior.
- Added a generated `monolith-full/` mirror plus sync tooling so modular source changes can be reflected in a single-file build artifact.
- Added a reviewer-facing decision map, a one-page results-at-a-glance PDF, and a negative-results note showing where BO was not worth its overhead.
