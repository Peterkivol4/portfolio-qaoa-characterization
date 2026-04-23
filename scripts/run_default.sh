#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=src python -m portfolio_qaoa_bench.cli --config configs/default_run.yaml
