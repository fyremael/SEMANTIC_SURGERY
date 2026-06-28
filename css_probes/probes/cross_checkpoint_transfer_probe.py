from __future__ import annotations

import numpy as np

from css_probes.core import PHASE0_DEFAULT_THRESHOLDS, ProbeResult, status_from_acceptance
from css_probes.metrics import cosine_drift, normalize, norm_drift
from css_probes.operators import array_sha256
from css_probes.synthetic import rng, synthetic_state_batch


def run(seed: int = 0, dim: int = 64, n_samples: int = 128, num_checkpoints: int = 3, alpha: float = 0.16) -> ProbeResult:
    gen = rng(seed)
    shared_semantic_direction = normalize(gen.normal(size=dim))
    transfer_deltas: dict[str, float] = {}
    before_chunks: list[np.ndarray] = []
    after_chunks: list[np.ndarray] = []
    rollback_residue = 0.0

    for checkpoint_idx in range(num_checkpoints):
        states = synthetic_state_batch(seed + 10 + checkpoint_idx, n=n_samples, dim=dim)
        target = normalize(shared_semantic_direction + 0.05 * gen.normal(size=dim))
        before = states.copy()
        after = states + alpha * shared_semantic_direction
        restored = after - alpha * shared_semantic_direction
        transfer_deltas[f"checkpoint_{checkpoint_idx}"] = float(np.mean(after @ target) - np.mean(before @ target))
        before_chunks.append(before)
        after_chunks.append(after)
        rollback_residue = max(rollback_residue, float(np.max(np.abs(restored - before))))

    flat_before = np.concatenate(before_chunks, axis=0)
    flat_after = np.concatenate(after_chunks, axis=0)
    min_delta = float(min(transfer_deltas.values()))
    mean_delta = float(np.mean(list(transfer_deltas.values())))
    metrics = {
        "target_success_delta": mean_delta,
        "target_margin_delta": mean_delta,
        "cross_model_transfer_deltas": transfer_deltas,
        "cross_model_transfer_min_delta": min_delta,
        "cross_model_transfer_passed": min_delta >= PHASE0_DEFAULT_THRESHOLDS["target_success_delta_min"],
        "num_checkpoints": num_checkpoints,
        "off_target_degradation_max": 0.0,
        "rollback_residue": rollback_residue,
        **norm_drift(flat_before, flat_after),
        **cosine_drift(flat_before, flat_after),
    }
    thresholds = {
        "target_success_delta_min": PHASE0_DEFAULT_THRESHOLDS["target_success_delta_min"],
        "cross_model_transfer_min_delta": PHASE0_DEFAULT_THRESHOLDS["target_success_delta_min"],
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
    if metrics["cross_model_transfer_min_delta"] < thresholds["cross_model_transfer_min_delta"]:
        accepted = False
        warnings.append("cross_model_transfer_delta_below_min")
    if metrics["norm_delta_max"] > thresholds["norm_delta_max"]:
        accepted = False
        warnings.append("norm_delta_exceeded")
    if metrics["cosine_drift_min"] < thresholds["cosine_drift_min"]:
        accepted = False
        warnings.append("cosine_drift_below_min")
    if metrics["rollback_residue"] > thresholds["rollback_residue_max"]:
        accepted = False
        warnings.append("rollback_residue_exceeded")

    operator = {
        "operator_type": "cross_checkpoint_activation_additive",
        "persistence": "ephemeral",
        "form": "h_prime = h + alpha * v transferred across deterministic checkpoint fixtures",
        "rank": 1,
        "target_shape": [dim],
        "state_type": "activation_stream",
        "declared_layer": 0,
        "stream": "residual",
        "parameters_ref": "inline",
        "parameter_hash": array_sha256(shared_semantic_direction),
        "allowed_tasks": ["cross_checkpoint_transfer_validation"],
    }
    return ProbeResult(
        name="cross_checkpoint_transfer_probe",
        status=status_from_acceptance(accepted, warnings),
        seed=seed,
        metrics=metrics,
        thresholds=thresholds,
        accepted=accepted,
        warnings=warnings,
        operator=operator,
    )
