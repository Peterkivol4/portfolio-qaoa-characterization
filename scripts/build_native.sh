#!/usr/bin/env bash
set -euo pipefail
export LAYERFIELD_QAOA_NATIVE=1
PYTHONPATH=src python - <<'PY'
from layerfield_qaoa.native import native_available
ok = native_available()
print('native_available=' + ('1' if ok else '0'))
raise SystemExit(0 if ok else 1)
PY
