from __future__ import annotations

from css_probes.core import ProbeResult, status_from_acceptance
from css_probes.metrics import binary_margin_score
from css_probes.operators import ActivationAdditiveOperator
from css_probes.synthetic import paired_target_offtarget, synthetic_state_batch


def run(seed: int = 0, dim: int = 64, n_samples: int = 256, alpha: float = 0.3) -> ProbeResult:
    states = synthetic_state_batch(seed, n=n_samples, dim=dim)
    target, off_target = paired_target_offtarget(seed + 1, dim=dim, orthogonalize=True)
    op = ActivationAdditiveOperator(vector=target, alpha=alpha)
    after = op.apply(states)
    target_delta = binary_margin_score(after, target) - binary_margin_score(states, target)
    off_target_delta = binary_margin_score(after, off_target) - binary_margin_score(states, off_target)
    locality_ratio = target_delta / (abs(off_target_delta) + 1e-12)
    metrics = {"target_delta": float(target_delta), "off_target_delta": float(off_target_delta), "off_target_degradation": float(max(0.0, -off_target_delta)), "locality_ratio": float(locality_ratio)}
    thresholds = {"off_target_degradation_max": 0.02, "target_delta_min": 0.20, "locality_ratio_min": 10.0}
    warnings: list[str] = []
    accepted = True
    if metrics["off_target_degradation"] > thresholds["off_target_degradation_max"]:
        accepted = False; warnings.append("off_target_degradation_exceeded")
    if metrics["target_delta"] < thresholds["target_delta_min"]:
        accepted = False; warnings.append("target_delta_below_min")
    if metrics["locality_ratio"] < thresholds["locality_ratio_min"]:
        accepted = False; warnings.append("locality_ratio_below_min")
    return ProbeResult(name="off_target_regression_probe", status=status_from_acceptance(accepted, warnings), seed=seed, metrics=metrics, thresholds=thresholds, accepted=accepted, warnings=warnings, operator=op.metadata())
