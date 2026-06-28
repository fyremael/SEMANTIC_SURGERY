"""Core result and configuration primitives for css-probes."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Mapping

PHASE0_DEFAULT_THRESHOLDS: dict[str, float] = {
    "target_success_delta_min": 0.05,
    "off_target_degradation_max": 0.02,
    "norm_delta_max": 1.0,
    "cosine_drift_min": 0.98,
    "spectral_radius_max": 1.05,
    "sigma_max": 1.10,
    "pseudospectral_proxy_max": 5.0,
    "rollback_residue_max": 1.0e-9,
}

METRIC_ALIASES = {
    "target_delta": "target_margin_delta",
    "off_target_degradation": "off_target_degradation_max",
    "rollback_error": "rollback_residue",
    "spectral_norm": "sigma_max",
    "pseudospectral_growth_proxy": "pseudospectral_proxy",
    "locality_ratio": "causal_locality_score",
    "operator_bits": "bits_transmitted",
    "operator_safe_delta_per_bit": "efficiency_delta_per_bit",
}

THRESHOLD_ALIASES = {
    "target_delta_min": "target_margin_delta_min",
    "rollback_error_max": "rollback_residue_max",
    "spectral_norm_max": "sigma_max",
    "pseudospectral_growth_proxy_max": "pseudospectral_proxy_max",
    "locality_ratio_min": "causal_locality_score_min",
}


@dataclass(frozen=True)
class ProbeResult:
    """JSON-serializable result for a single probe."""

    name: str
    status: str
    seed: int
    metrics: dict[str, Any]
    thresholds: dict[str, Any] = field(default_factory=dict)
    accepted: bool = False
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    operator: dict[str, Any] = field(default_factory=dict)
    packet: dict[str, Any] = field(default_factory=dict)
    certificate: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if not payload["notes"]:
            payload["notes"] = list(self.warnings)
        payload["metrics"] = with_metric_aliases(self.metrics)
        payload["thresholds"] = with_threshold_aliases(self.thresholds)
        return payload


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


def with_metric_aliases(metrics: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(metrics)
    for source, alias in METRIC_ALIASES.items():
        if source in result and alias not in result:
            result[alias] = result[source]
    return result


def with_threshold_aliases(thresholds: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(thresholds)
    for source, alias in THRESHOLD_ALIASES.items():
        if source in result and alias not in result:
            result[alias] = result[source]
    return result
