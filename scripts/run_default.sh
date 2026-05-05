#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=src python -m layerfield_qaoa.cli p-sweep \
  --config configs/layerfield_spin.yaml \
  --n-spins 6,8 \
  --p-values 1,2,3 \
  --j2-values 0.0,0.2 \
  --h-values 0.5,1.0 \
  --optimizer spsa \
  --seeds 2 \
  --shots 512 \
  --evaluation-budget 20 \
  --output results/p_layer_geometry/default_p_sweep
