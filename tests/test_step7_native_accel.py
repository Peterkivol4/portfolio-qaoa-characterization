from __future__ import annotations

import os
import shutil

import numpy as np
import pytest

from portfolio_qaoa_bench.objective import weighted_cvar
from portfolio_qaoa_bench.reporting import _bootstrap_ci


def test_weighted_cvar_python_path(monkeypatch):
    monkeypatch.delenv("PORTFOLIO_QAOA_NATIVE", raising=False)
    monkeypatch.setenv("PORTFOLIO_QAOA_NATIVE_DISABLE", "1")
    mean, var, noise = weighted_cvar([(1.0, 2), (3.0, 1), (2.0, 1)], 0.5)
    assert np.isfinite(mean)
    assert var >= 1e-12
    assert noise >= 1e-12


@pytest.mark.skipif(not any(shutil.which(x) for x in ["cc", "gcc", "clang"]), reason="no compiler")
def test_native_weighted_cvar_matches_python(monkeypatch):
    samples = [(0.1, 10), (0.2, 5), (0.3, 20), (-0.1, 4)]
    monkeypatch.delenv("PORTFOLIO_QAOA_NATIVE_DISABLE", raising=False)
    monkeypatch.setenv("PORTFOLIO_QAOA_NATIVE", "1")
    native = weighted_cvar(samples, 0.4)
    monkeypatch.delenv("PORTFOLIO_QAOA_NATIVE", raising=False)
    monkeypatch.setenv("PORTFOLIO_QAOA_NATIVE_DISABLE", "1")
    py = weighted_cvar(samples, 0.4)
    assert np.allclose(native, py, atol=1e-10)


@pytest.mark.skipif(not any(shutil.which(x) for x in ["cc", "gcc", "clang"]), reason="no compiler")
def test_native_bootstrap_ci_returns_finite(monkeypatch):
    monkeypatch.delenv("PORTFOLIO_QAOA_NATIVE_DISABLE", raising=False)
    monkeypatch.setenv("PORTFOLIO_QAOA_NATIVE", "1")
    low, high = _bootstrap_ci([1.0, 2.0, 3.0, 4.0], 200, 7)
    assert np.isfinite(low)
    assert np.isfinite(high)
    assert low <= high
