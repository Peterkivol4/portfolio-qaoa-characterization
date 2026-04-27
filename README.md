# QAOA Depth as a Physical Resolution Limit for Frustrated Spin Hamiltonians

LayerField QAOA studies finite-depth QAOA as a physical resolution limit rather than a generic approximation-ratio benchmark. The central question is not only whether the variational energy improves with depth `p`, but when additional layers begin to represent physically distinct Hamiltonian effects separately instead of compressing them into distorted QAOA angles.

The repo is currently in transition: the package path remains `portfolio_qaoa_bench` so the existing benchmark engine, scripts, and monolith tooling keep working, while the new spin-physics subsystem is promoted to the main scientific identity.

## One-Sentence Thesis

QAOA depth `p` is treated here as a physical resolution limit for approximating frustrated spin Hamiltonians.

## Core Question

As QAOA depth increases, which Hamiltonian parameters become separately representable, and which physical effects are still confounded inside a low-dimensional angle manifold?

Concretely, the repo studies the family

`H(J1, J2, h, epsilon) = -J1 Σ_i Z_i Z_{i+1} - J2 Σ_i Z_i Z_{i+2} - h Σ_i X_i - Σ_i epsilon_i Z_i`

and asks whether shallow QAOA can distinguish nearest-neighbor coupling, next-nearest-neighbor frustration, transverse field strength, and disorder using energy, observables, and learned angles.

## Physical Systems

- Transverse-field Ising model (TFIM)
- Frustrated `J1-J2` spin chains
- Disordered longitudinal-field variants
- Open and periodic one-dimensional boundary conditions

## Main Outputs

- `p`-resolution sweeps written as `p_resolution_records.csv`, `p_resolution_summary.json`, and `p_resolution_report.md`
- Parameter-confusion studies written as `parameter_confusion_records.csv`, `parameter_confusion_summary.json`, and `parameter_confusion_report.md`
- Resolution-cost summaries written as `resolution_cost_summary.json` and `resolution_cost_report.md`
- Per-run physical recovery metrics:
  - energy error
  - ground-state fidelity
  - magnetization error in `x` and `z`
  - nearest-neighbor and next-nearest-neighbor correlation error
  - structure-factor error
  - entanglement-entropy error
- `p`-layer geometry diagnostics:
  - angle smoothness
  - angle curvature
  - angle distance between regimes
  - parameter transfer loss
  - parameter confusion score
- Runtime accounting interpreted as the cost of resolving physical structure

## Scientific Framing

The intended result is not “higher `p` gets lower energy.” The stronger claim under study is:

- energy recovery can appear before observable recovery
- shallow QAOA may reduce energy while still confusing frustration, field strength, and disorder
- the minimum `p` required for energy recovery is generally smaller than the minimum `p` required for correlation or fidelity recovery
- runtime, circuit depth, and optimizer effort should be interpreted as the cost of physical resolution

## What This Is Not

- not a quantum-advantage claim
- not a finance optimizer paper, even though the legacy benchmark engine is still present in the codebase
- not only an approximation-ratio benchmark
- not a claim that one classical outer-loop optimizer universally dominates
- not a guarantee that practical optimization improves monotonically with `p`

## Reproduce

Install the package in editable mode:

```bash
pip install -e .
```

Run the focused spin-physics tests:

```bash
PYTHONPATH=src pytest -q tests/test_spin_physics.py tests/test_cli_smoke.py
```

Run a baseline `p`-sweep:

```bash
layerfield-qaoa p-sweep \
  --config configs/layerfield_spin.yaml \
  --n-spins 6,8 \
  --p-values 1,2,3,4 \
  --j2-values 0.0,0.2,0.4 \
  --h-values 0.5,1.0,1.5 \
  --optimizer spsa \
  --seeds 4 \
  --shots 1024 \
  --evaluation-budget 40 \
  --output results/p_layer_geometry/frustration_sweep
```

Run a parameter-confusion study:

```bash
layerfield-qaoa parameter-confusion \
  --config configs/layerfield_spin.yaml \
  --n-spins 8 \
  --p-values 1,2,3,4 \
  --regimes ferromagnetic,near_critical,frustrated,disordered \
  --optimizer spsa \
  --shots 1024 \
  --evaluation-budget 40 \
  --output results/p_layer_geometry/confusion_map
```

Summarize the cost of reaching physical thresholds:

```bash
layerfield-qaoa resolution-cost \
  --input results/p_layer_geometry/frustration_sweep/p_resolution_records.csv \
  --thresholds energy=0.02,magnetization=0.05,correlation=0.05,fidelity=0.10 \
  --output results/p_layer_geometry/resolution_cost
```

The CLI currently lives in `portfolio_qaoa_bench.cli`; `layerfield-qaoa` is the new user-facing entry point added on top of the existing package.

## Repository Layout

- [`src/portfolio_qaoa_bench/spin_hamiltonian.py`](/Users/hirrreshsundrq/Documents/New%20project/portfolio_qaoa_bench_repo/src/portfolio_qaoa_bench/spin_hamiltonian.py): dense `J1-J2-h-epsilon` Hamiltonian construction and regime presets
- [`src/portfolio_qaoa_bench/exact_diagonalization.py`](/Users/hirrreshsundrq/Documents/New%20project/portfolio_qaoa_bench_repo/src/portfolio_qaoa_bench/exact_diagonalization.py): exact reference spectra and states
- [`src/portfolio_qaoa_bench/physical_observables.py`](/Users/hirrreshsundrq/Documents/New%20project/portfolio_qaoa_bench_repo/src/portfolio_qaoa_bench/physical_observables.py): magnetization, correlation, structure-factor, and entanglement diagnostics
- [`src/portfolio_qaoa_bench/p_layer_geometry.py`](/Users/hirrreshsundrq/Documents/New%20project/portfolio_qaoa_bench_repo/src/portfolio_qaoa_bench/p_layer_geometry.py): ansatz state construction, optimization, and `PLayerResolutionRecord`
- [`src/portfolio_qaoa_bench/parameter_emergence.py`](/Users/hirrreshsundrq/Documents/New%20project/portfolio_qaoa_bench_repo/src/portfolio_qaoa_bench/parameter_emergence.py): angle-space geometry and confusion metrics
- [`src/portfolio_qaoa_bench/phase_maps.py`](/Users/hirrreshsundrq/Documents/New%20project/portfolio_qaoa_bench_repo/src/portfolio_qaoa_bench/phase_maps.py): study orchestration and report emission
- [`configs/layerfield_spin.yaml`](/Users/hirrreshsundrq/Documents/New%20project/portfolio_qaoa_bench_repo/configs/layerfield_spin.yaml): example spin-study configuration
- [`tests/test_spin_physics.py`](/Users/hirrreshsundrq/Documents/New%20project/portfolio_qaoa_bench_repo/tests/test_spin_physics.py): Hamiltonian, observables, ansatz, reporting, and CLI regression tests
- [`monolith-full/portfolio_qaoa_bench_monolith.py`](/Users/hirrreshsundrq/Documents/New%20project/portfolio_qaoa_bench_repo/monolith-full/portfolio_qaoa_bench_monolith.py): synchronized single-file snapshot of the repo implementation

## Current Limitations

- Exact diagonalization is only practical for small `n_spins`; the default ceiling is `exact_reference_max_spins = 12`.
- The spin subsystem currently uses dense linear algebra rather than tensor-network or sparse-Krylov backends.
- Practical optimizer performance can worsen with `p` even when the formal variational family grows.
- No claim is made here about universal phase identification, universal parameter transfer, or hardware advantage.
- The legacy portfolio-benchmark code still exists in the repository for backward compatibility while the spin-physics path matures.

## Immediate Research Program

- Baseline `p`-sweeps across `n = 6, 8, 10`
- Frustration-emergence studies in `J2 / J1`
- Parameter-confusion maps between frustrated, near-critical, strong-field, and disordered regimes
- Threshold maps for the minimum `p` required to recover energy, magnetization, correlations, and fidelity
- Resolution-cost studies connecting physical recovery to objective calls, runtime, and circuit depth

## Legacy Note

This repository started as a runtime-aware QAOA benchmarking engine in a different application domain. That infrastructure is being reused rather than discarded. The current scientific direction is the spin-physics program described above; the older portfolio path is retained temporarily for backward compatibility while the new studies mature.
