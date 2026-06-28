from __future__ import annotations

from css_probes.core import PHASE0_DEFAULT_THRESHOLDS, ProbeResult, status_from_acceptance
from css_probes.metrics import cosine_drift, norm_drift, normalize
from css_probes.operators import ActivationAdditiveOperator
from css_probes.synthetic import rng, synthetic_state_batch


def run(seed: int = 0, dim: int = 64, n_samples: int = 256, alpha: float = 0.1) -> ProbeResult:
    gen = rng(seed)
    states = synthetic_state_batch(seed + 1, n=n_samples, dim=dim)
    op = ActivationAdditiveOperator(vector=normalize(gen.normal(size=dim)), alpha=alpha)
    after = op.apply(states)
    metrics = {**norm_drift(states, after), **cosine_drift(states, after)}
    thresholds = {
        "norm_delta_max": PHASE0_DEFAULT_THRESHOLDS["norm_delta_max"],
        "cosine_drift_min": PHASE0_DEFAULT_THRESHOLDS["cosine_drift_min"],
    }
    warnings: list[str] = []
    accepted = metrics["norm_delta_max"] <= thresholds["norm_delta_max"] and metrics["cosine_drift_min"] >= thresholds["cosine_drift_min"]
    if not accepted:
        warnings.append("geometry_threshold_failed")
    return ProbeResult(name="norm_drift_probe", status=status_from_acceptance(accepted, warnings), seed=seed, metrics=metrics, thresholds=thresholds, accepted=accepted, warnings=warnings, operator=op.metadata())
