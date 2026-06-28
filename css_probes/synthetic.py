"""Synthetic data generators for operator probes."""

from __future__ import annotations

import numpy as np

from .metrics import normalize


def rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def synthetic_state_batch(seed: int, n: int = 256, dim: int = 64) -> np.ndarray:
    gen = rng(seed)
    states = gen.normal(size=(n, dim))
    return states / (np.linalg.norm(states, axis=1, keepdims=True) + 1e-12)


def contrastive_activations(seed: int, n: int = 128, dim: int = 64, strength: float = 1.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    gen = rng(seed)
    direction = normalize(gen.normal(size=dim))
    base_pos = gen.normal(size=(n, dim))
    base_neg = gen.normal(size=(n, dim))
    pos = base_pos + strength * direction
    neg = base_neg - strength * direction
    return pos, neg, direction


def paired_target_offtarget(seed: int, dim: int = 64, orthogonalize: bool = True) -> tuple[np.ndarray, np.ndarray]:
    gen = rng(seed)
    target = normalize(gen.normal(size=dim))
    off = gen.normal(size=dim)
    if orthogonalize:
        off = off - np.dot(off, target) * target
    off = normalize(off)
    return target, off
