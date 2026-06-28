from __future__ import annotations

import numpy as np

from css_probes.core import ProbeResult, status_from_acceptance
from css_probes.metrics import binary_margin_score, estimate_bits_for_array, safe_delta_per_bit
from css_probes.operators import ActivationAdditiveOperator
from css_probes.synthetic import paired_target_offtarget, synthetic_state_batch


def run(seed: int = 0, dim: int = 64, n_samples: int = 256) -> ProbeResult:
    states = synthetic_state_batch(seed, n=n_samples, dim=dim)
    target, off_target = paired_target_offtarget(seed + 1, dim=dim, orthogonalize=True)
    coarse_axes = np.eye(dim)[:4]
    best_axis = coarse_axes[int(np.argmax(coarse_axes @ target))]
    text_after = states + 0.35 * best_axis
    op = ActivationAdditiveOperator(vector=target, alpha=0.35)
    operator_after = op.apply(states)
    baseline_target = binary_margin_score(states, target)
    text_target_delta = binary_margin_score(text_after, target) - baseline_target
    operator_target_delta = binary_margin_score(operator_after, target) - baseline_target
    text_off_delta = binary_margin_score(text_after, off_target) - binary_margin_score(states, off_target)
    operator_off_delta = binary_margin_score(operator_after, off_target) - binary_margin_score(states, off_target)
    text_bits = 2
    operator_bits = estimate_bits_for_array(target)
    metrics = {
        "text_target_delta": float(text_target_delta),
        "operator_target_delta": float(operator_target_delta),
        "text_off_target_delta": float(text_off_delta),
        "operator_off_target_delta": float(operator_off_delta),
        "text_bits": int(text_bits),
        "operator_bits": int(operator_bits),
        "text_safe_delta_per_bit": safe_delta_per_bit(text_target_delta, text_off_delta, text_bits),
        "operator_safe_delta_per_bit": safe_delta_per_bit(operator_target_delta, operator_off_delta, operator_bits),
        "operator_absolute_advantage": float(operator_target_delta - text_target_delta),
    }
    thresholds = {"operator_absolute_advantage_min": 0.20}
    warnings: list[str] = []
    accepted = True
    if metrics["operator_absolute_advantage"] < thresholds["operator_absolute_advantage_min"]:
        accepted = False; warnings.append("operator_absolute_advantage_below_min")
    return ProbeResult(name="operator_vs_text_benchmark", status=status_from_acceptance(accepted, warnings), seed=seed, metrics=metrics, thresholds=thresholds, accepted=accepted, warnings=warnings, operator=op.metadata())
