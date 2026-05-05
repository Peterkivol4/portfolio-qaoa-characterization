# Architecture

## Purpose

This repository is organized as a characterisation study for finite-depth QAOA on frustrated spin Hamiltonians. The code is split so that Hamiltonian construction, exact references, observable extraction, variational optimization, and reporting can evolve independently while still sharing coherent configuration and output formats.

## Main modules

- `config.py`: strongly typed spin-study and legacy compatibility configuration objects, YAML loading, and validation.
- `spin_hamiltonian.py`: dense `J1-J2-h-epsilon` Hamiltonian construction plus regime presets.
- `exact_diagonalization.py`: exact reference spectra and states for small spin systems.
- `physical_observables.py`: magnetization, correlation, structure-factor, and entanglement calculations.
- `p_layer_geometry.py`: QAOA ansatz state construction, parameter optimization, and `PLayerResolutionRecord` production.
- `parameter_emergence.py`: angle smoothness, curvature, transfer loss, and parameter-confusion diagnostics.
- `phase_maps.py`: sweep orchestration and `p`-resolution / confusion / cost report generation.
- `simulator.py`, `optimizers.py`, `pipeline.py`, `reporting.py`, and `plotting.py`: retained legacy benchmark infrastructure plus reusable execution/accounting utilities.

## Design notes

- The spin-physics subsystem is the primary public surface. Legacy portfolio modules remain only to preserve previously tested execution, reporting, and optimizer paths.
- Exact diagonalization is explicit and size-limited through `exact_reference_max_spins`, so every reported reference point has a clear computational boundary.
- Reporting preserves both energy metrics and physical-observable metrics so results can distinguish energy recovery from observable or state recovery.
- `monolith-full/layerfield_qaoa_monolith.py` is a generated mirror of the modular source tree, kept in sync by `scripts/build_monolith_full.py` and CI checks.
