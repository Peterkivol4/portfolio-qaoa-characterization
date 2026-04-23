#!/usr/bin/env bash
set -euo pipefail
export PORTFOLIO_QAOA_NATIVE=1
PYTHONPATH=src python - <<'PY'
from portfolio_qaoa_bench.native import native_available
ok = native_available()
print('native_available=' + ('1' if ok else '0'))
raise SystemExit(0 if ok else 1)
PY
