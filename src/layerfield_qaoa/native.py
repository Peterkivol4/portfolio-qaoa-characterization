from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

_LIB = None
_LIB_STATE = "untried"
_ENABLE_ENV = "LAYERFIELD_QAOA_NATIVE"
_DISABLE_ENV = "LAYERFIELD_QAOA_NATIVE_DISABLE"
_C_SRC = r"""
#include <math.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>

static uint64_t splitmix64_next(uint64_t *state) {
    uint64_t z = (*state += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

int pqb_tail_cvar(const double *energies, const double *weights, size_t n, double alpha,
                  double *out_mean, double *out_var, double *out_noise) {
    if (!energies || !weights || !out_mean || !out_var || !out_noise || n == 0) return 1;
    double total = 0.0;
    for (size_t i = 0; i < n; ++i) total += weights[i];
    if (total <= 0.0) {
        *out_mean = 0.0;
        *out_var = 1e-12;
        *out_noise = 1e-12;
        return 0;
    }
    double target = alpha * total;
    if (target < 1.0) target = 1.0;
    double cumulative = 0.0;
    double s1 = 0.0;
    double s2 = 0.0;
    for (size_t i = 0; i < n; ++i) {
        double rem = target - cumulative;
        if (rem <= 0.0) break;
        double take = weights[i] < rem ? weights[i] : rem;
        if (take <= 0.0) break;
        s1 += energies[i] * take;
        s2 += energies[i] * energies[i] * take;
        cumulative += take;
        if (cumulative >= target) break;
    }
    if (cumulative <= 0.0) {
        *out_mean = 0.0;
        *out_var = 1e-12;
        *out_noise = 1e-12;
        return 0;
    }
    double mean = s1 / cumulative;
    double second = s2 / cumulative;
    double var = second - mean * mean;
    if (var < 1e-12) var = 1e-12;
    double noise = var / cumulative;
    if (noise < 1e-12) noise = 1e-12;
    *out_mean = mean;
    *out_var = var;
    *out_noise = noise;
    return 0;
}

int pqb_bootstrap_mean_ci(const double *values, size_t n, int resamples, uint64_t seed,
                          double *out_low, double *out_high) {
    if (!values || !out_low || !out_high || n == 0 || resamples <= 0) return 1;
    if (n == 1) {
        *out_low = values[0];
        *out_high = values[0];
        return 0;
    }
    double *means = (double *)malloc((size_t)resamples * sizeof(double));
    if (!means) return 2;
    uint64_t state = seed ? seed : 1ULL;
    for (int i = 0; i < resamples; ++i) {
        double acc = 0.0;
        for (size_t j = 0; j < n; ++j) {
            uint64_t r = splitmix64_next(&state);
            size_t idx = (size_t)(r % n);
            acc += values[idx];
        }
        means[i] = acc / (double)n;
    }
    for (int i = 0; i < resamples - 1; ++i) {
        int min_idx = i;
        for (int j = i + 1; j < resamples; ++j) {
            if (means[j] < means[min_idx]) min_idx = j;
        }
        if (min_idx != i) {
            double tmp = means[i]; means[i] = means[min_idx]; means[min_idx] = tmp;
        }
    }
    int low_idx = (int)floor(0.025 * (resamples - 1));
    int high_idx = (int)floor(0.975 * (resamples - 1));
    if (low_idx < 0) low_idx = 0;
    if (high_idx < 0) high_idx = 0;
    if (high_idx >= resamples) high_idx = resamples - 1;
    *out_low = means[low_idx];
    *out_high = means[high_idx];
    free(means);
    return 0;
}
"""


def _native_requested() -> bool:
    if os.environ.get(_DISABLE_ENV, "").strip() in {"1", "true", "TRUE", "yes", "YES"}:
        return False
    return os.environ.get(_ENABLE_ENV, "").strip() in {"1", "true", "TRUE", "yes", "YES"}


def _lib_name() -> str:
    if os.name == "nt":
        return "pqb_native.dll"
    if os.uname().sysname == "Darwin":
        return "libpqb_native.dylib"
    return "libpqb_native.so"


def _compile_shared(target_dir: Path) -> Path | None:
    cc = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if not cc:
        return None
    target_dir.mkdir(parents=True, exist_ok=True)
    c_path = target_dir / "pqb_native.c"
    so_path = target_dir / _lib_name()
    c_path.write_text(_C_SRC, encoding="utf-8")
    cmd = [cc, "-O3", "-shared", "-fPIC", str(c_path), "-lm", "-o", str(so_path)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return None
    return so_path if so_path.exists() else None


def _load_library():
    global _LIB, _LIB_STATE
    if _LIB_STATE != "untried":
        return _LIB
    _LIB_STATE = "unavailable"
    if not _native_requested():
        return None
    cache_dir = Path(tempfile.gettempdir()) / "layerfield_qaoa_native"
    so_path = cache_dir / _lib_name()
    if not so_path.exists():
        built = _compile_shared(cache_dir)
        if built is None:
            return None
        so_path = built
    try:
        lib = ctypes.CDLL(str(so_path))
    except Exception:
        return None

    lib.pqb_tail_cvar.argtypes = [
        ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_size_t, ctypes.c_double,
        ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
    ]
    lib.pqb_tail_cvar.restype = ctypes.c_int
    lib.pqb_bootstrap_mean_ci.argtypes = [
        ctypes.POINTER(ctypes.c_double), ctypes.c_size_t, ctypes.c_int, ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
    ]
    lib.pqb_bootstrap_mean_ci.restype = ctypes.c_int
    _LIB = lib
    _LIB_STATE = "loaded"
    return _LIB


def native_available() -> bool:
    return _load_library() is not None


def tail_cvar_sorted_native(energies: np.ndarray, weights: np.ndarray, alpha: float):
    lib = _load_library()
    if lib is None:
        return None
    e = np.ascontiguousarray(energies, dtype=np.float64)
    w = np.ascontiguousarray(weights, dtype=np.float64)
    out_mean = ctypes.c_double()
    out_var = ctypes.c_double()
    out_noise = ctypes.c_double()
    rc = lib.pqb_tail_cvar(
        e.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        w.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        e.size,
        float(alpha),
        ctypes.byref(out_mean), ctypes.byref(out_var), ctypes.byref(out_noise),
    )
    if rc != 0:
        return None
    return float(out_mean.value), float(out_var.value), float(out_noise.value)


def bootstrap_mean_ci_native(values: np.ndarray, resamples: int, seed: int):
    lib = _load_library()
    if lib is None:
        return None
    arr = np.ascontiguousarray(values, dtype=np.float64)
    out_low = ctypes.c_double()
    out_high = ctypes.c_double()
    rc = lib.pqb_bootstrap_mean_ci(
        arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), arr.size, int(resamples), int(seed),
        ctypes.byref(out_low), ctypes.byref(out_high),
    )
    if rc != 0:
        return None
    return float(out_low.value), float(out_high.value)


__all__ = ["native_available", "tail_cvar_sorted_native", "bootstrap_mean_ci_native"]
