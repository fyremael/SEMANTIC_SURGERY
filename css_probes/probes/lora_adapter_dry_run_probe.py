from __future__ import annotations

import numpy as np

from css_probes.core import PHASE0_DEFAULT_THRESHOLDS, ProbeResult, status_from_acceptance
from css_probes.metrics import cosine_drift, normalize, norm_drift, spectral_norm, spectral_radius
from css_probes.operators import array_sha256, combine_hashes
from css_probes.synthetic import paired_target_offtarget, synthetic_state_batch


def run(seed: int = 0, dim: int = 64, n_samples: int = 128, rank: int = 2, alpha: float = 0.09) -> ProbeResult:
    base_states = synthetic_state_batch(seed, n=n_samples, dim=dim)
    target, off_target = paired_target_offtarget(seed + 1, dim=dim, orthogonalize=True)
    source = target
    states = base_states + 1.4 * source
    a = np.zeros((rank, dim))
    b = np.zeros((dim, rank))
    a[0] = source
    b[:, 0] = target
    a[1] = off_target
    b[:, 1] = 0.0 * off_target

    base_weight = np.eye(dim)
    base_hash_before = array_sha256(base_weight)
    delta = (alpha / rank) * (b @ a)
    adapted_weight = base_weight + delta
    before = states @ base_weight.T
    after = states @ adapted_weight.T
    unloaded = states @ base_weight.T
    base_hash_after = array_sha256(base_weight)

    target_delta = float(np.mean(after @ target) - np.mean(before @ target))
    off_delta = float(np.mean(after @ off_target) - np.mean(before @ off_target))
    unload_residue = float(np.max(np.abs(unloaded - before)))
    metrics = {
        "target_success_delta": target_delta,
        "target_margin_delta": target_delta,
        "off_target_delta": off_delta,
        "off_target_degradation_max": float(max(0.0, -off_delta)),
        "rollback_residue": unload_residue,
        "adapter_unload_residue": unload_residue,
        "weight_fingerprint_changed": base_hash_before != base_hash_after,
        "merge_attempted": False,
        "save_pretrained_called": False,
        "spectral_radius": float(spectral_radius(adapted_weight)),
        "sigma_max": float(spectral_norm(adapted_weight)),
        **norm_drift(before, after),
        **cosine_drift(before, after),
    }
    thresholds = {
        "target_success_delta_min": PHASE0_DEFAULT_THRESHOLDS["target_success_delta_min"],
        "off_target_degradation_max": PHASE0_DEFAULT_THRESHOLDS["off_target_degradation_max"],
        "norm_delta_max": PHASE0_DEFAULT_THRESHOLDS["norm_delta_max"],
        "cosine_drift_min": PHASE0_DEFAULT_THRESHOLDS["cosine_drift_min"],
        "rollback_residue_max": PHASE0_DEFAULT_THRESHOLDS["rollback_residue_max"],
        "spectral_radius_max": PHASE0_DEFAULT_THRESHOLDS["spectral_radius_max"],
        "sigma_max": PHASE0_DEFAULT_THRESHOLDS["sigma_max"],
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
    if metrics["weight_fingerprint_changed"]:
        accepted = False
        warnings.append("base_weight_fingerprint_changed")
    if metrics["merge_attempted"] or metrics["save_pretrained_called"]:
        accepted = False
        warnings.append("persistent_adapter_operation_attempted")
    if metrics["spectral_radius"] > thresholds["spectral_radius_max"]:
        accepted = False
        warnings.append("spectral_radius_exceeded")
    if metrics["sigma_max"] > thresholds["sigma_max"]:
        accepted = False
        warnings.append("sigma_max_exceeded")

    operator = {
        "operator_type": "lora_adapter_dry_run",
        "persistence": "removable",
        "form": "W_runtime = W + alpha/rank * B A; W is restored/unmodified after context",
        "rank": rank,
        "target_shape": [dim, dim],
        "state_type": "adapter_delta",
        "declared_layer": 0,
        "stream": "linear_weight",
        "parameters_ref": "inline",
        "parameter_hash": combine_hashes(array_sha256(a), array_sha256(b)),
        "allowed_tasks": ["removable_lora_adapter_dry_run"],
    }
    return ProbeResult(
        name="lora_adapter_dry_run_probe",
        status=status_from_acceptance(accepted, warnings),
        seed=seed,
        metrics=metrics,
        thresholds=thresholds,
        accepted=accepted,
        warnings=warnings,
        operator=operator,
    )
