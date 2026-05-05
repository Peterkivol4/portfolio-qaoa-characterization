# Contributing

## Add a new spin regime

1. Add the regime name to `VALID_SPIN_REGIMES` in `src/layerfield_qaoa/config.py`.
2. Implement the preset or parameter mapping in `src/layerfield_qaoa/spin_hamiltonian.py`.
3. Make sure the regime can be exercised through `run_single_spin_instance()` or the sweep helpers in `phase_maps.py`.
4. Add at least one regression test in `tests/test_spin_physics.py`.
5. If the regime is intended for examples, add it to the relevant spin-study YAML or script entry point.

## Add a new physics metric

1. Implement the observable or diagnostic in `src/layerfield_qaoa/physical_observables.py` or `src/layerfield_qaoa/parameter_emergence.py`.
2. Surface it through `PLayerResolutionRecord` in `src/layerfield_qaoa/p_layer_geometry.py`.
3. Include it in the relevant report writer in `src/layerfield_qaoa/phase_maps.py`.
4. Add bounds or sanity tests in `tests/test_spin_physics.py`.

## Add or modify an optimizer

1. If the optimizer is for the spin-physics path, integrate it through `optimize_spin_qaoa()` in `src/layerfield_qaoa/p_layer_geometry.py`.
2. If the optimizer touches the legacy compatibility benchmark, keep its accounting wired through `TimingBreakdown`.
3. Add fallback or mocking tests if the optimizer depends on optional libraries.
4. Preserve deterministic seed handling.

## Preserve experiment realism

When modifying execution or reporting paths:
- keep QAOA angle periodicity intact
- preserve exact-reference limits and warnings
- preserve runtime/cost accounting semantics
- keep monolith generation in sync
- distinguish spin-primary features from legacy compatibility code in docs and comments
