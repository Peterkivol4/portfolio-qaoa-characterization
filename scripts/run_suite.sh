#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=src python -m portfolio_qaoa_bench.cli --suite-config configs/multi_regime_suite.yaml
