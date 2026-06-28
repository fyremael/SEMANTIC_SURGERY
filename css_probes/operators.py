"""Typed synthetic semantic operators."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
from typing import Iterator

import numpy as np

from .metrics import spectral_norm, spectral_radius


def array_sha256(array: np.ndarray) -> str:
    arr = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(str(arr.dtype).encode("utf-8"))
    digest.update(str(arr.shape).encode("utf-8"))
    digest.update(arr.tobytes())
    return f"sha256:{digest.hexdigest()}"


def combine_hashes(*parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
    return f"sha256:{digest.hexdigest()}"


class SemanticOperator:
    """Base protocol for state operators."""

    operator_type: str = "base"
    persistence: str = "ephemeral"

    def apply(self, state: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def invert(self, state: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def matrix(self, dim: int) -> np.ndarray:
        return np.eye(dim)

    def metadata(self) -> dict[str, object]:
        return {"operator_type": self.operator_type, "persistence": self.persistence}

    def _check_last_dim(self, state: np.ndarray, dim: int) -> None:
        if state.shape[-1] != dim:
            raise ValueError(f"state last dimension {state.shape[-1]} does not match operator dimension {dim}")


@dataclass(frozen=True)
class ActivationAdditiveOperator(SemanticOperator):
    vector: np.ndarray
    alpha: float = 1.0
    operator_type: str = "activation_additive"
    persistence: str = "ephemeral"

    def __post_init__(self) -> None:
        if self.vector.ndim != 1:
            raise ValueError("vector must be rank-1 with shape [dim]")

    def apply(self, state: np.ndarray) -> np.ndarray:
        self._check_last_dim(state, self.vector.shape[0])
        return state + self.alpha * self.vector

    def invert(self, state: np.ndarray) -> np.ndarray:
        self._check_last_dim(state, self.vector.shape[0])
        return state - self.alpha * self.vector

    def metadata(self) -> dict[str, object]:
        return {
            "operator_type": self.operator_type,
            "persistence": self.persistence,
            "alpha": float(self.alpha),
            "rank": None,
            "form": "h_prime = h + alpha * v",
            "target_shape": [int(self.vector.shape[0])],
            "parameters_ref": "inline",
            "parameter_hash": array_sha256(self.vector),
        }


@dataclass(frozen=True)
class LowRankOperator(SemanticOperator):
    u: np.ndarray
    v: np.ndarray
    alpha: float = 1.0
    operator_type: str = "activation_low_rank"
    persistence: str = "ephemeral"

    def __post_init__(self) -> None:
        if self.u.ndim != 2 or self.v.ndim != 2:
            raise ValueError("u and v must be rank-2 arrays with shape [dim, rank]")
        if self.u.shape != self.v.shape:
            raise ValueError("u and v must have matching shape")

    def transform_matrix(self) -> np.ndarray:
        d = self.u.shape[0]
        return np.eye(d) + self.alpha * (self.v @ self.u.T)

    def apply(self, state: np.ndarray) -> np.ndarray:
        self._check_last_dim(state, self.u.shape[0])
        return state @ self.transform_matrix()

    def invert(self, state: np.ndarray) -> np.ndarray:
        self._check_last_dim(state, self.u.shape[0])
        inv = np.linalg.inv(self.transform_matrix())
        return state @ inv

    def matrix(self, dim: int | None = None) -> np.ndarray:  # type: ignore[override]
        return self.transform_matrix()

    def metadata(self) -> dict[str, object]:
        mat = self.transform_matrix()
        return {
            "operator_type": self.operator_type,
            "persistence": self.persistence,
            "alpha": float(self.alpha),
            "rank": int(self.u.shape[1]),
            "form": "h_prime = h + alpha * V U^T h",
            "target_shape": [int(self.u.shape[0])],
            "parameters_ref": "inline",
            "parameter_hash": combine_hashes(array_sha256(self.u), array_sha256(self.v)),
            "spectral_radius": float(spectral_radius(mat)),
            "spectral_norm": float(spectral_norm(mat)),
        }


@dataclass(frozen=True)
class ProjectionRemovalOperator(SemanticOperator):
    basis: np.ndarray
    operator_type: str = "projection_removal"
    persistence: str = "ephemeral"

    def __post_init__(self) -> None:
        if self.basis.ndim != 2:
            raise ValueError("basis must have shape [dim, rank]")

    def projector(self) -> np.ndarray:
        q, _ = np.linalg.qr(self.basis)
        return q @ q.T

    def apply(self, state: np.ndarray) -> np.ndarray:
        self._check_last_dim(state, self.basis.shape[0])
        p = self.projector()
        return state @ (np.eye(p.shape[0]) - p)

    def invert(self, state: np.ndarray) -> np.ndarray:
        raise NotImplementedError("projection removal is not invertible; use checkpoint rollback")

    def matrix(self, dim: int | None = None) -> np.ndarray:  # type: ignore[override]
        p = self.projector()
        return np.eye(p.shape[0]) - p

    def metadata(self) -> dict[str, object]:
        return {
            "operator_type": self.operator_type,
            "persistence": self.persistence,
            "rank": int(self.basis.shape[1]),
            "invertible": False,
            "form": "h_prime = (I - U U^T) h",
            "target_shape": [int(self.basis.shape[0])],
            "parameters_ref": "inline",
            "parameter_hash": array_sha256(self.basis),
        }


@dataclass
class MutableStateBox:
    """Tiny mutable state holder for rollback tests."""

    state: np.ndarray


@contextmanager
def applied_temporarily(box: MutableStateBox, operator: SemanticOperator) -> Iterator[MutableStateBox]:
    """Apply an operator inside a context and restore exact previous state."""

    before = box.state.copy()
    box.state = operator.apply(box.state)
    try:
        yield box
    finally:
        box.state = before
