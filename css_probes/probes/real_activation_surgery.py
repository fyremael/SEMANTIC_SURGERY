"""Controlled real-model activation surgery probe."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from css_probes.core import PHASE0_DEFAULT_THRESHOLDS, ProbeResult, status_from_acceptance
from css_probes.hooks.base import ActivationSurgeryConfig, RealActivationResult
from css_probes.hooks.registry import get_adapter
from css_probes.operators import array_sha256


REAL_TARGET_DELTA_MIN = 1e-9


def load_vector(path: str | Path | None) -> list[float] | None:
    if path is None:
        return None
    path = Path(path)
    if path.suffix.lower() == ".npy":
        array = np.load(path)
        return [float(x) for x in np.ravel(array)]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("vector", [])
    return [float(x) for x in payload]


def run_real_activation_surgery(config: ActivationSurgeryConfig, adapter: Any | None = None) -> ProbeResult:
    if not config.local_files_only:
        return _rejected_result_from_exception(config, ValueError("local_files_only must remain true for controlled real-model adapters"))
    adapter = adapter or get_adapter(config.backend)
    try:
        adapter_result = adapter.run_activation_surgery(config)
    except Exception as exc:
        return _rejected_result_from_exception(config, exc)
    return result_from_adapter(config, adapter_result)


def result_from_adapter(config: ActivationSurgeryConfig, adapter_result: RealActivationResult) -> ProbeResult:
    metrics = dict(adapter_result.metrics)
    thresholds: dict[str, float | int | bool | str] = {
        "target_token_logprob_delta_min": REAL_TARGET_DELTA_MIN,
        "off_target_degradation_max": PHASE0_DEFAULT_THRESHOLDS["off_target_degradation_max"],
        "norm_delta_max": PHASE0_DEFAULT_THRESHOLDS["norm_delta_max"],
        "cosine_drift_min": PHASE0_DEFAULT_THRESHOLDS["cosine_drift_min"],
        "rollback_residue_max": PHASE0_DEFAULT_THRESHOLDS["rollback_residue_max"],
        "weight_fingerprint_changed_required": False,
        "hook_cleanup_required": True,
    }
    warnings = list(adapter_result.warnings)
    accepted = True
    required_metrics = [
        "target_token_logprob_delta",
        "off_target_degradation_max",
        "norm_delta_max",
        "cosine_drift_min",
        "rollback_residue",
        "weight_fingerprint_changed",
        "hook_cleanup_ok",
        "local_files_only",
    ]
    for metric_name in required_metrics:
        if metric_name not in metrics:
            accepted = False
            warnings.append(f"missing_verifier_evidence:{metric_name}")
    if adapter_result.operator.get("persistence") not in {None, "ephemeral"}:
        accepted = False
        warnings.append(f"persistence_warning:{adapter_result.operator.get('persistence')}")
    if not bool(metrics.get("local_files_only", False)):
        accepted = False
        warnings.append("local_files_only_disabled")
    if float(metrics.get("target_token_logprob_delta", 0.0)) < REAL_TARGET_DELTA_MIN:
        accepted = False
        warnings.append("target_token_logprob_delta_below_min")
    if float(metrics.get("off_target_degradation_max", 1.0)) > thresholds["off_target_degradation_max"]:
        accepted = False
        warnings.append("off_target_degradation_exceeded")
    if float(metrics.get("norm_delta_max", 1e9)) > thresholds["norm_delta_max"]:
        accepted = False
        warnings.append("norm_delta_exceeded")
    if float(metrics.get("cosine_drift_min", -1.0)) < thresholds["cosine_drift_min"]:
        accepted = False
        warnings.append("cosine_drift_below_min")
    if float(metrics.get("rollback_residue", 1.0)) > thresholds["rollback_residue_max"]:
        accepted = False
        warnings.append("rollback_residue_exceeded")
    if bool(metrics.get("weight_fingerprint_changed", True)):
        accepted = False
        warnings.append("weight_fingerprint_changed")
    if not bool(metrics.get("hook_cleanup_ok", False)):
        accepted = False
        warnings.append("hook_cleanup_failed")

    operator = {
        **adapter_result.operator,
        "operator_type": "real_activation_additive",
        "persistence": "ephemeral",
        "backend": adapter_result.backend,
        "model_family": adapter_result.model_family,
        "model_name_or_path": adapter_result.model_name_or_path,
        "declared_layer": adapter_result.layer,
        "stream": adapter_result.stream,
        "target_shape": adapter_result.shape,
        "state_type": "activation_stream",
        "local_files_only": config.local_files_only,
        "allowed_tasks": ["controlled_real_activation_surgery"],
    }
    return ProbeResult(
        name="real_activation_surgery_probe",
        status=status_from_acceptance(accepted, warnings),
        seed=config.seed,
        metrics=metrics,
        thresholds=thresholds,
        accepted=accepted,
        warnings=warnings,
        notes=list(adapter_result.notes),
        operator=operator,
    )


def _rejected_result_from_exception(config: ActivationSurgeryConfig, exc: Exception) -> ProbeResult:
    vector_hash = array_sha256(np.asarray(config.vector or [], dtype=float))
    metrics: dict[str, float | int | bool | str] = {
        "target_token_logprob_delta": 0.0,
        "target_success_delta": 0.0,
        "off_target_degradation_max": 1.0,
        "norm_delta_max": 0.0,
        "cosine_drift_min": 1.0,
        "rollback_residue": 1.0,
        "weight_fingerprint_changed": False,
        "hook_cleanup_ok": False,
        "local_files_only": config.local_files_only,
    }
    thresholds: dict[str, float | int | bool | str] = {
        "target_token_logprob_delta_min": REAL_TARGET_DELTA_MIN,
        "off_target_degradation_max": PHASE0_DEFAULT_THRESHOLDS["off_target_degradation_max"],
        "norm_delta_max": PHASE0_DEFAULT_THRESHOLDS["norm_delta_max"],
        "cosine_drift_min": PHASE0_DEFAULT_THRESHOLDS["cosine_drift_min"],
        "rollback_residue_max": PHASE0_DEFAULT_THRESHOLDS["rollback_residue_max"],
        "weight_fingerprint_changed_required": False,
        "hook_cleanup_required": True,
    }
    warnings = [f"real_adapter_failure:{type(exc).__name__}:{exc}"]
    operator = {
        "operator_type": "real_activation_additive",
        "persistence": "ephemeral",
        "backend": config.backend,
        "model_family": "unknown_real_model",
        "model_name_or_path": config.model_name_or_path,
        "declared_layer": config.layer,
        "stream": config.stream,
        "target_shape": [len(config.vector or [])],
        "state_type": "activation_stream",
        "form": "h_prime = h + alpha * v",
        "rank": 1,
        "parameters_ref": "inline",
        "parameter_hash": vector_hash,
        "local_files_only": config.local_files_only,
        "allowed_tasks": ["controlled_real_activation_surgery"],
    }
    return ProbeResult(
        name="real_activation_surgery_probe",
        status="fail",
        seed=config.seed,
        metrics=metrics,
        thresholds=thresholds,
        accepted=False,
        warnings=warnings,
        notes=["Rejected before or during real-model verifier execution."],
        operator=operator,
    )
