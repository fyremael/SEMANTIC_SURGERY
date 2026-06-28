from __future__ import annotations

import numpy as np

from css_probes.core import PHASE0_DEFAULT_THRESHOLDS, ProbeResult, status_from_acceptance
from css_probes.metrics import cosine_drift, normalize, norm_drift
from css_probes.operators import array_sha256
from css_probes.synthetic import rng


def run(seed: int = 0, layers: int = 2, heads: int = 2, seq: int = 8, head_dim: int = 16, alpha: float = 0.08) -> ProbeResult:
    gen = rng(seed)
    keys = gen.normal(scale=0.2, size=(layers, heads, seq, head_dim))
    values = gen.normal(scale=0.2, size=(layers, heads, seq, head_dim))
    before_keys = keys.copy()
    before_values = values.copy()

    layer = 1
    head = 0
    target_pos = 3
    protected_pos = 6
    query = normalize(gen.normal(size=head_dim))
    vector = normalize(query)

    target_score_before = float(query @ keys[layer, head, target_pos])
    protected_score_before = float(query @ keys[layer, head, protected_pos])
    cache_snapshot = {"keys": keys.copy(), "values": values.copy()}

    patched_keys = keys.copy()
    patched_keys[layer, head, target_pos] = patched_keys[layer, head, target_pos] + alpha * vector
    target_score_after = float(query @ patched_keys[layer, head, target_pos])
    protected_score_after = float(query @ patched_keys[layer, head, protected_pos])

    restored_keys = cache_snapshot["keys"]
    restored_values = cache_snapshot["values"]
    rollback_residue = float(max(np.max(np.abs(restored_keys - before_keys)), np.max(np.abs(restored_values - before_values))))
    locality_denominator = float(np.sum(np.abs(patched_keys - before_keys))) + 1.0e-12
    locality_numerator = float(np.sum(np.abs(patched_keys[layer, head, target_pos] - before_keys[layer, head, target_pos])))

    flat_before = before_keys.reshape(-1, head_dim)
    flat_after = patched_keys.reshape(-1, head_dim)
    metrics = {
        "target_success_delta": float(target_score_after - target_score_before),
        "target_margin_delta": float(target_score_after - target_score_before),
        "off_target_degradation_max": float(max(0.0, protected_score_before - protected_score_after)),
        "rollback_residue": rollback_residue,
        "causal_locality_score": float(locality_numerator / locality_denominator),
        "kv_cache_copy_used": True,
        "kv_cache_shape_match": list(keys.shape) == list(patched_keys.shape),
        **norm_drift(flat_before, flat_after),
        **cosine_drift(flat_before, flat_after),
    }
    thresholds = {
        "target_success_delta_min": PHASE0_DEFAULT_THRESHOLDS["target_success_delta_min"],
        "off_target_degradation_max": PHASE0_DEFAULT_THRESHOLDS["off_target_degradation_max"],
        "norm_delta_max": PHASE0_DEFAULT_THRESHOLDS["norm_delta_max"],
        "cosine_drift_min": PHASE0_DEFAULT_THRESHOLDS["cosine_drift_min"],
        "rollback_residue_max": PHASE0_DEFAULT_THRESHOLDS["rollback_residue_max"],
        "causal_locality_score_min": 0.99,
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
        warnings.append("cosine_drift_below_min")
    if metrics["rollback_residue"] > thresholds["rollback_residue_max"]:
        accepted = False
        warnings.append("rollback_residue_exceeded")
    if metrics["causal_locality_score"] < thresholds["causal_locality_score_min"]:
        accepted = False
        warnings.append("kv_cache_locality_below_min")
    if not metrics["kv_cache_shape_match"]:
        accepted = False
        warnings.append("kv_cache_shape_mismatch")

    operator = {
        "operator_type": "kv_cache_additive",
        "persistence": "ephemeral",
        "form": "K[layer, head, pos] <- K[layer, head, pos] + alpha * v",
        "rank": 1,
        "target_shape": [layers, heads, seq, head_dim],
        "state_type": "kv_cache",
        "declared_layer": layer,
        "stream": "key",
        "parameters_ref": "inline",
        "parameter_hash": array_sha256(vector),
        "allowed_tasks": ["toy_kv_cache_surgery"],
    }
    return ProbeResult(
        name="kv_cache_surgery_probe",
        status=status_from_acceptance(accepted, warnings),
        seed=seed,
        metrics=metrics,
        thresholds=thresholds,
        accepted=accepted,
        warnings=warnings,
        operator=operator,
    )
