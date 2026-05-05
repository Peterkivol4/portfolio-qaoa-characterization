# QAOA Depth as a Physical Resolution Limit for Frustrated Spin Hamiltonians

LayerField QAOA studies finite-depth QAOA as a physical resolution limit rather than a generic approximation-ratio benchmark. The central question is not only whether the variational energy improves with depth `p`, but when additional layers begin to represent physically distinct Hamiltonian effects separately instead of compressing them into distorted QAOA angles.

The primary package surface is now `layerfield_qaoa`. A legacy portfolio-benchmark path remains inside the repository for compatibility and regression testing, but it is no longer the main scientific identity of the project.

If you want the less-polished version of how this changed shape, read [RESEARCH_JOURNAL.md](RESEARCH_JOURNAL.md).

This is the repo where the rest of the portfolio really started. I built [FieldLine VQE](https://github.com/Peterkivol4/Tfim-vqe-symmetry-bench) after this one made me realise that low energy was not the same thing as the right physical state. I built [SpinMesh Runtime](https://github.com/Peterkivol4/Runtime-Aware-QAOA-for-Constrained-J1-J2-Ising-Ground-State-Search) once it became obvious that execution conditions could deform the conclusion as much as the ansatz did. I built [TeleportDim](https://github.com/Peterkivol4/Teleportdim-hardware-study) when I wanted one cleaner place to hold the hardware fixed and study deformation directly.

## Concrete Example

On an 8-spin open chain with `J1 = 1.0`, `h = 1.0`, zero disorder, and frustration changed from `J2 = 0.3` to `J2 = 0.5`, shallow QAOA still treats the two Hamiltonians as only weakly separated. Over four SPSA seeds with evaluation budget `60`, the mean optimized-angle distance is only `0.5446` at `p = 1`, while mean fidelities stay low for both cases (`0.0302` and `0.0285`) and next-nearest-neighbor correlation errors remain large (`0.7191` and `0.8059`). At `p = 3`, the mean optimized-angle distance rises to `1.8861`, the `J2 = 0.5` mean fidelity rises to `0.1970`, and the two cases stop looking like the same shallow response. That is the repo’s main idea in miniature: low depth can reduce energy while still blurring the physical source of that energy.

See [results/p_layer_geometry/j2_resolution_example.md](/Users/hirrreshsundrq/Documents/New%20project/layerfield_qaoa_repo/results/p_layer_geometry/j2_resolution_example.md) for the per-seed table behind this example.

## Resolution Sketch

```text
physical parameter axis

J2 = 0.3 ----------------------------- J2 = 0.5

p = 1  angle space
            [ one broad shallow basin ]
                 ^ both cases land near here

p = 3  angle space
        [ basin for J2=0.3 ]     [ basin for J2=0.5 ]
                 ^                          ^
           separable response         separable response
```

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
- not a finance optimizer paper
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

## Repository Layout

- [`src/layerfield_qaoa/spin_hamiltonian.py`](/Users/hirrreshsundrq/Documents/New%20project/layerfield_qaoa_repo/src/layerfield_qaoa/spin_hamiltonian.py): dense `J1-J2-h-epsilon` Hamiltonian construction and regime presets
- [`src/layerfield_qaoa/exact_diagonalization.py`](/Users/hirrreshsundrq/Documents/New%20project/layerfield_qaoa_repo/src/layerfield_qaoa/exact_diagonalization.py): exact reference spectra and states
- [`src/layerfield_qaoa/physical_observables.py`](/Users/hirrreshsundrq/Documents/New%20project/layerfield_qaoa_repo/src/layerfield_qaoa/physical_observables.py): magnetization, correlation, structure-factor, and entanglement diagnostics
- [`src/layerfield_qaoa/p_layer_geometry.py`](/Users/hirrreshsundrq/Documents/New%20project/layerfield_qaoa_repo/src/layerfield_qaoa/p_layer_geometry.py): ansatz state construction, optimization, and `PLayerResolutionRecord`
- [`src/layerfield_qaoa/parameter_emergence.py`](/Users/hirrreshsundrq/Documents/New%20project/layerfield_qaoa_repo/src/layerfield_qaoa/parameter_emergence.py): angle-space geometry and confusion metrics
- [`src/layerfield_qaoa/phase_maps.py`](/Users/hirrreshsundrq/Documents/New%20project/layerfield_qaoa_repo/src/layerfield_qaoa/phase_maps.py): study orchestration and report emission
- [`configs/layerfield_spin.yaml`](/Users/hirrreshsundrq/Documents/New%20project/layerfield_qaoa_repo/configs/layerfield_spin.yaml): example spin-study configuration
- [`tests/test_spin_physics.py`](/Users/hirrreshsundrq/Documents/New%20project/layerfield_qaoa_repo/tests/test_spin_physics.py): Hamiltonian, observables, ansatz, reporting, and CLI regression tests
- [`monolith-full/layerfield_qaoa_monolith.py`](/Users/hirrreshsundrq/Documents/New%20project/layerfield_qaoa_repo/monolith-full/layerfield_qaoa_monolith.py): synchronized single-file snapshot of the repo implementation

## Current Limitations

- Exact diagonalization is only practical for small `n_spins`; the default ceiling is `exact_reference_max_spins = 12`.
- The spin subsystem currently uses dense linear algebra rather than tensor-network or sparse-Krylov backends.
- Practical optimizer performance can worsen with `p` even when the formal variational family grows.
- No claim is made here about universal phase identification, universal parameter transfer, or hardware advantage.
- A legacy portfolio-benchmark engine still exists in the repository for backward compatibility and regression coverage.

## Immediate Research Program

- Baseline `p`-sweeps across `n = 6, 8, 10`
- Frustration-emergence studies in `J2 / J1`
- Parameter-confusion maps between frustrated, near-critical, strong-field, and disordered regimes
- Threshold maps for the minimum `p` required to recover energy, magnetization, correlations, and fidelity
- Resolution-cost studies connecting physical recovery to objective calls, runtime, and circuit depth

## Legacy Note

This repository started as a runtime-aware QAOA benchmarking engine in a different application domain. That infrastructure is being reused rather than discarded. The current scientific direction is the spin-physics program described above; the older portfolio path is retained only as a legacy compatibility surface.
