#!/usr/bin/env bash
set -euo pipefail

python -m pip check

if command -v pip-audit >/dev/null 2>&1; then
  pip-audit || true
else
  echo "pip-audit not installed; skipping CVE audit"
fi

if command -v pip-licenses >/dev/null 2>&1; then
  pip-licenses || true
else
  echo "pip-licenses not installed; skipping license audit"
fi
