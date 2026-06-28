"""Core result and configuration primitives for css-probes."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Mapping


@dataclass(frozen=True)
class ProbeResult:
    """JSON-serializable result for a single probe."""

    name: str
    status: str
    seed: int
    metrics: dict[str, float | int | bool | str]
    thresholds: dict[str, float | int | bool | str] = field(default_factory=dict)
    accepted: bool = False
    warnings: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    operator: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProbeConfig:
    """Common deterministic configuration for synthetic probes."""

    dim: int = 64
    n_samples: int = 256
    seed: int = 0


def status_from_acceptance(accepted: bool, warnings: list[str] | None = None) -> str:
    if accepted:
        return "pass" if not warnings else "pass_with_warnings"
    return "fail"


def all_thresholds_pass(metrics: Mapping[str, float], checks: Mapping[str, tuple[str, float]]) -> tuple[bool, list[str]]:
    """Evaluate simple named threshold checks."""

    warnings: list[str] = []
    ok = True
    for key, (op, threshold) in checks.items():
        value = float(metrics[key])
        passed = {
            ">=": value >= threshold,
            "<=": value <= threshold,
            ">": value > threshold,
            "<": value < threshold,
        }[op]
        if not passed:
            ok = False
            warnings.append(f"threshold_failed:{key}:{value:.6g}{op}{threshold:.6g}")
    return ok, warnings
