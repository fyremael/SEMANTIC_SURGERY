"""Geometric, spectral, and synthetic behavioral metrics."""

from __future__ import annotations

import numpy as np

_EPS = 1e-12


def l2_norm(x: np.ndarray, axis: int | None = None) -> np.ndarray | float:
    return np.linalg.norm(x, axis=axis)


def cosine_similarity(a: np.ndarray, b: np.ndarray, axis: int = -1) -> np.ndarray:
    denom = np.linalg.norm(a, axis=axis) * np.linalg.norm(b, axis=axis) + _EPS
    return np.sum(a * b, axis=axis) / denom


def norm_drift(before: np.ndarray, after: np.ndarray) -> dict[str, float]:
    delta = after - before
    delta_norms = np.linalg.norm(delta, axis=-1) if delta.ndim > 1 else np.array([np.linalg.norm(delta)])
    before_norms = np.linalg.norm(before, axis=-1) if before.ndim > 1 else np.array([np.linalg.norm(before)])
    rel = delta_norms / (before_norms + _EPS)
    return {
        "norm_delta_mean": float(np.mean(delta_norms)),
        "norm_delta_max": float(np.max(delta_norms)),
        "relative_norm_delta_mean": float(np.mean(rel)),
        "relative_norm_delta_max": float(np.max(rel)),
    }


def cosine_drift(before: np.ndarray, after: np.ndarray) -> dict[str, float]:
    sims = cosine_similarity(before, after, axis=-1)
    sims = np.atleast_1d(sims)
    return {
        "cosine_drift_mean": float(np.mean(sims)),
        "cosine_drift_min": float(np.min(sims)),
    }


def spectral_radius(matrix: np.ndarray) -> float:
    eigvals = np.linalg.eigvals(matrix)
    return float(np.max(np.abs(eigvals)))


def spectral_norm(matrix: np.ndarray) -> float:
    return float(np.linalg.svd(matrix, compute_uv=False)[0])


def non_normality_fro(matrix: np.ndarray) -> float:
    return float(np.linalg.norm(matrix.T @ matrix - matrix @ matrix.T, ord="fro"))


def transient_growth_proxy(matrix: np.ndarray, max_power: int = 8) -> float:
    current = np.eye(matrix.shape[0])
    max_norm = spectral_norm(current)
    for _ in range(max_power):
        current = current @ matrix
        max_norm = max(max_norm, spectral_norm(current))
    return float(max_norm)


def pseudospectral_growth_proxy(matrix: np.ndarray, grid_radius: float = 1.5, grid_size: int = 11, imaginary: bool = True) -> float:
    """Sample max resolvent norm over a coarse grid. This is a proxy, not a full pseudospectrum."""

    xs = np.linspace(-grid_radius, grid_radius, grid_size)
    ys = xs if imaginary else np.array([0.0])
    eye = np.eye(matrix.shape[0], dtype=complex)
    max_resolvent = 0.0
    for x in xs:
        for y in ys:
            z = complex(x, y)
            try:
                svals = np.linalg.svd(z * eye - matrix, compute_uv=False)
                smallest = float(np.min(svals))
                if smallest <= _EPS:
                    return float("inf")
                max_resolvent = max(max_resolvent, 1.0 / smallest)
            except np.linalg.LinAlgError:
                return float("inf")
    return float(max_resolvent)


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -60.0, 60.0)))


def binary_margin_score(states: np.ndarray, direction: np.ndarray) -> float:
    return float(np.mean(states @ direction))


def binary_success_rate(states: np.ndarray, direction: np.ndarray, threshold: float = 0.0) -> float:
    return float(np.mean((states @ direction) > threshold))


def estimate_bits_for_array(array: np.ndarray, bits_per_float: int = 32) -> int:
    return int(array.size * bits_per_float)


def safe_delta_per_bit(target_delta: float, off_target_delta: float, bits: int, penalty: float = 1.0) -> float:
    safe_delta = target_delta - penalty * max(0.0, -off_target_delta)
    return float(safe_delta / max(1, bits))


def normalize(v: np.ndarray) -> np.ndarray:
    return v / (np.linalg.norm(v) + _EPS)
