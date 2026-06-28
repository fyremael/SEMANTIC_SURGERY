from __future__ import annotations

import numpy as np

from css_probes.core import PHASE0_DEFAULT_THRESHOLDS, ProbeResult, status_from_acceptance
from css_probes.metrics import binary_margin_score, binary_success_rate, cosine_drift, norm_drift, normalize
from css_probes.operators import ActivationAdditiveOperator
from css_probes.synthetic import contrastive_activations, paired_target_offtarget, synthetic_state_batch


def run(seed: int = 0, dim: int = 64, n_samples: int = 256, alpha: float = 0.15) -> ProbeResult:
    pos, neg, _ = contrastive_activations(seed, n=n_samples // 2, dim=dim, strength=1.0)
    vector = normalize(pos.mean(axis=0) - neg.mean(axis=0))
    op = ActivationAdditiveOperator(vector=vector, alpha=alpha)
    states = synthetic_state_batch(seed + 1, n=n_samples, dim=dim)
    target, off_target = paired_target_offtarget(seed + 2, dim=dim, orthogonalize=True)
    target = normalize(0.75 * vector + 0.25 * target)
    before_target = binary_margin_score(states, target)
    before_success = binary_success_rate(states, target)
    before_off = binary_margin_score(states, off_target)
    after = op.apply(states)
    restored = op.invert(after)
    off_target_delta = float(binary_margin_score(after, off_target) - before_off)
    metrics = {
        "target_success_delta": float(binary_success_rate(after, target) - before_success),
        "target_margin_delta": float(binary_margin_score(after, target) - before_target),
        "off_target_delta": off_target_delta,
        "off_target_degradation_max": float(max(0.0, -off_target_delta)),
        "rollback_residue": float(np.max(np.abs(restored - states))),
        **norm_drift(states, after),
        **cosine_drift(states, after),
    }
    thresholds = {
        "target_success_delta_min": PHASE0_DEFAULT_THRESHOLDS["target_success_delta_min"],
        "off_target_degradation_max": PHASE0_DEFAULT_THRESHOLDS["off_target_degradation_max"],
        "norm_delta_max": PHASE0_DEFAULT_THRESHOLDS["norm_delta_max"],
        "cosine_drift_min": PHASE0_DEFAULT_THRESHOLDS["cosine_drift_min"],
        "rollback_residue_max": PHASE0_DEFAULT_THRESHOLDS["rollback_residue_max"],
    }
    warnings: list[str] = []
    accepted = True
    if metrics["target_success_delta"] < thresholds["target_success_delta_min"]:
        accepted = False
        warnings.append("target_success_delta_below_min")
    if metrics["off_target_degradation_max"] > thresholds["off_target_degradation_max"]:
        accepted = False
        warnings.append("off_target_degradation_exceeded")
    if metrics["norm_delta_max"] > thresholds["norm_delta_max"]:
        accepted = False
        warnings.append("norm_delta_exceeded")
    if metrics["cosine_drift_min"] < thresholds["cosine_drift_min"]:
        accepted = False
        warnings.append("cosine_drift_too_large")
    if metrics["rollback_residue"] > thresholds["rollback_residue_max"]:
        accepted = False
        warnings.append("rollback_residue_exceeded")
    return ProbeResult(
        name="activation_patch_probe",
        status=status_from_acceptance(accepted, warnings),
        seed=seed,
        metrics=metrics,
        thresholds=thresholds,
        accepted=accepted,
        warnings=warnings,
        operator=op.metadata(),
    )
