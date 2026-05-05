#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=src python -m layerfield_qaoa.cli parameter-confusion \
  --config configs/layerfield_spin.yaml \
  --n-spins 8 \
  --p-values 1,2,3,4 \
  --regimes ferromagnetic,near_critical,frustrated,disordered \
  --optimizer spsa \
  --shots 1024 \
  --evaluation-budget 40 \
  --output results/p_layer_geometry/confusion_suite
