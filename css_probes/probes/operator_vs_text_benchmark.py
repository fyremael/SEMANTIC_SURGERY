from __future__ import annotations

import numpy as np

from css_probes.core import ProbeResult, status_from_acceptance
from css_probes.metrics import binary_margin_score, estimate_bits_for_array, normalize, safe_delta_per_bit
from css_probes.operators import ActivationAdditiveOperator, LowRankOperator
from css_probes.synthetic import paired_target_offtarget, rng, synthetic_state_batch


def run(seed: int = 0, dim: int = 64, n_samples: int = 256) -> ProbeResult:
    gen = rng(seed)
    states = synthetic_state_batch(seed, n=n_samples, dim=dim)
    target, off_target = paired_target_offtarget(seed + 1, dim=dim, orthogonalize=True)
    baseline_target = binary_margin_score(states, target)
    baseline_off = binary_margin_score(states, off_target)

    no_message_after = states.copy()

    coarse_axes = np.eye(dim)[:4]
    best_axis = coarse_axes[int(np.argmax(coarse_axes @ target))]
    text_after = states + 0.35 * best_axis

    latent_direction = normalize(0.85 * target + 0.15 * normalize(gen.normal(size=dim)))
    latent_after = states + 0.35 * latent_direction

    additive_op = ActivationAdditiveOperator(vector=target, alpha=0.35)
    additive_after = additive_op.apply(states)

    u = np.column_stack([target, normalize(gen.normal(size=dim))])
    v = np.column_stack([target, normalize(gen.normal(size=dim))])
    low_rank_op = LowRankOperator(u=u, v=v, alpha=0.04)
    low_rank_after = low_rank_op.apply(states)

    no_message_target_delta = binary_margin_score(no_message_after, target) - baseline_target
    text_target_delta = binary_margin_score(text_after, target) - baseline_target
    latent_target_delta = binary_margin_score(latent_after, target) - baseline_target
    additive_target_delta = binary_margin_score(additive_after, target) - baseline_target
    low_rank_target_delta = binary_margin_score(low_rank_after, target) - baseline_target
    text_off_delta = binary_margin_score(text_after, off_target) - baseline_off
    latent_off_delta = binary_margin_score(latent_after, off_target) - baseline_off
    additive_off_delta = binary_margin_score(additive_after, off_target) - baseline_off
    low_rank_off_delta = binary_margin_score(low_rank_after, off_target) - baseline_off
    text_bits = 2
    latent_bits = estimate_bits_for_array(latent_direction)
    additive_bits = estimate_bits_for_array(target)
    low_rank_bits = estimate_bits_for_array(u) + estimate_bits_for_array(v)
    metrics = {
        "no_message_target_margin_delta": float(no_message_target_delta),
        "text_target_margin_delta": float(text_target_delta),
        "latent_vector_target_margin_delta": float(latent_target_delta),
        "additive_operator_target_margin_delta": float(additive_target_delta),
        "low_rank_operator_target_margin_delta": float(low_rank_target_delta),
        "text_off_target_delta": float(text_off_delta),
        "latent_vector_off_target_delta": float(latent_off_delta),
        "additive_operator_off_target_delta": float(additive_off_delta),
        "low_rank_operator_off_target_delta": float(low_rank_off_delta),
        "operator_off_target_degradation_max": float(max(0.0, -additive_off_delta)),
        "text_bits": int(text_bits),
        "latent_vector_bits": int(latent_bits),
        "operator_bits": int(additive_bits),
        "low_rank_operator_bits": int(low_rank_bits),
        "text_safe_delta_per_bit": safe_delta_per_bit(text_target_delta, text_off_delta, text_bits),
        "latent_vector_safe_delta_per_bit": safe_delta_per_bit(latent_target_delta, latent_off_delta, latent_bits),
        "operator_safe_delta_per_bit": safe_delta_per_bit(additive_target_delta, additive_off_delta, additive_bits),
        "low_rank_operator_safe_delta_per_bit": safe_delta_per_bit(low_rank_target_delta, low_rank_off_delta, low_rank_bits),
        "operator_plus_certificate_target_margin_delta": float(additive_target_delta),
        "target_margin_delta": float(additive_target_delta),
        "off_target_degradation_max": float(max(0.0, -additive_off_delta)),
        "bits_transmitted": int(additive_bits),
        "efficiency_delta_per_bit": safe_delta_per_bit(additive_target_delta, additive_off_delta, additive_bits),
        "operator_absolute_advantage": float(additive_target_delta - text_target_delta),
    }
    thresholds = {"operator_absolute_advantage_min": 0.20, "off_target_degradation_max": 0.02}
    warnings: list[str] = []
    accepted = True
    if metrics["operator_absolute_advantage"] < thresholds["operator_absolute_advantage_min"]:
        accepted = False; warnings.append("operator_absolute_advantage_below_min")
    if metrics["off_target_degradation_max"] > thresholds["off_target_degradation_max"]:
        accepted = False; warnings.append("off_target_degradation_exceeded")
    return ProbeResult(name="operator_vs_text_benchmark", status=status_from_acceptance(accepted, warnings), seed=seed, metrics=metrics, thresholds=thresholds, accepted=accepted, warnings=warnings, operator=additive_op.metadata())
