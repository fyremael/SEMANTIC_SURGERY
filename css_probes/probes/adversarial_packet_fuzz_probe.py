from __future__ import annotations

from css_probes.core import PHASE0_DEFAULT_THRESHOLDS, ProbeResult, status_from_acceptance
from css_probes.packets import (
    AuditSpec,
    OperatorSpec,
    OperatorTarget,
    SemanticSurgeryPacket,
    validate_packet_policy,
)


def run(seed: int = 0) -> ProbeResult:
    del seed
    cases = {
        "persistent": SemanticSurgeryPacket(
            packet_id="fuzz_persistent",
            operator_type="activation_additive",
            persistence="persistent",
            target=OperatorTarget(shape=[4]),
            preconditions={"requires_sandbox": True},
            postconditions={"accepted": False},
            operator=OperatorSpec(form="h_prime = h + v", parameter_hash="sha256:fuzz"),
            audit=AuditSpec(provenance="adversarial-fuzz", human_rendering="Persistent edit must be rejected."),
        ),
        "network": SemanticSurgeryPacket(
            packet_id="fuzz_network",
            operator_type="activation_additive",
            target=OperatorTarget(shape=[4]),
            preconditions={"requires_sandbox": True, "allow_downloads": True},
            postconditions={"accepted": False},
            operator=OperatorSpec(form="h_prime = h + v", parameter_hash="sha256:fuzz"),
            audit=AuditSpec(provenance="adversarial-fuzz", human_rendering="Download path must be rejected."),
        ),
        "global": SemanticSurgeryPacket(
            packet_id="fuzz_global",
            operator_type="activation_additive",
            target=OperatorTarget(shape=[4], stream="global"),
            preconditions={"requires_sandbox": True},
            postconditions={"accepted": False},
            operator=OperatorSpec(form="h_prime = h + v", parameter_hash="sha256:fuzz"),
            audit=AuditSpec(provenance="adversarial-fuzz", human_rendering="Global stream must be rejected."),
        ),
        "missing_rollback": SemanticSurgeryPacket(
            packet_id="fuzz_missing_rollback",
            operator_type="activation_additive",
            target=OperatorTarget(shape=[4]),
            preconditions={"requires_sandbox": True},
            postconditions={"accepted": False},
            operator=OperatorSpec(form="h_prime = h + v", parameter_hash="sha256:fuzz"),
            audit=AuditSpec(provenance="adversarial-fuzz", human_rendering="Missing rollback must be rejected."),
            rollback=None,  # type: ignore[arg-type]
        ),
        "unbounded": SemanticSurgeryPacket(
            packet_id="fuzz_unbounded",
            operator_type="activation_additive",
            target=OperatorTarget(shape=[0]),
            preconditions={"requires_sandbox": True},
            postconditions={"accepted": False},
            operator=OperatorSpec(form="h_prime = h + v", parameter_hash="sha256:fuzz"),
            audit=AuditSpec(provenance="adversarial-fuzz", human_rendering="Invalid target shape must be rejected."),
        ),
    }

    rejection_reasons: dict[str, list[str]] = {}
    for name, packet in cases.items():
        try:
            policy = validate_packet_policy(packet)
            rejection_reasons[name] = policy.warnings
        except AttributeError as exc:
            rejection_reasons[name] = [f"malformed_packet:{type(exc).__name__}:{exc}"]

    required_reason_present = {
        "persistent": any("persistence" in reason for reason in rejection_reasons["persistent"]),
        "network": any("network_or_download_forbidden" in reason for reason in rejection_reasons["network"]),
        "global": "global_operator_scope_rejected" in rejection_reasons["global"],
        "missing_rollback": any("malformed_packet" in reason or "rollback" in reason for reason in rejection_reasons["missing_rollback"]),
        "unbounded": "invalid_target_shape" in rejection_reasons["unbounded"],
    }
    cases_rejected = sum(1 for reasons in rejection_reasons.values() if reasons)
    metrics = {
        "target_success_delta": 1.0,
        "off_target_degradation_max": 0.0,
        "norm_delta_max": 0.0,
        "cosine_drift_min": 1.0,
        "rollback_residue": 0.0,
        "cases_generated": len(cases),
        "cases_rejected": cases_rejected,
        "rejection_rate": float(cases_rejected / len(cases)),
        "required_rejection_reasons_present": all(required_reason_present.values()),
        "adversarial_rejection_reasons": rejection_reasons,
    }
    thresholds = {
        "target_success_delta_min": PHASE0_DEFAULT_THRESHOLDS["target_success_delta_min"],
        "off_target_degradation_max": PHASE0_DEFAULT_THRESHOLDS["off_target_degradation_max"],
        "norm_delta_max": PHASE0_DEFAULT_THRESHOLDS["norm_delta_max"],
        "cosine_drift_min": PHASE0_DEFAULT_THRESHOLDS["cosine_drift_min"],
        "rollback_residue_max": PHASE0_DEFAULT_THRESHOLDS["rollback_residue_max"],
        "rejection_rate_min": 1.0,
    }
    warnings: list[str] = []
    accepted = True
    if metrics["rejection_rate"] < thresholds["rejection_rate_min"]:
        accepted = False
        warnings.append("adversarial_packets_not_all_rejected")
    if not metrics["required_rejection_reasons_present"]:
        accepted = False
        warnings.append("missing_required_adversarial_rejection_reason")

    operator = {
        "operator_type": "adversarial_packet_fuzzing",
        "persistence": "ephemeral",
        "form": "validate malformed and forbidden packet families through the central policy gate",
        "rank": None,
        "target_shape": [1],
        "state_type": "packet_policy",
        "declared_layer": 0,
        "stream": "validator",
        "parameters_ref": "inline",
        "parameter_hash": "sha256:adversarial_packet_fuzz_catalog_v1",
        "allowed_tasks": ["packet_policy_fuzzing"],
    }
    return ProbeResult(
        name="adversarial_packet_fuzz_probe",
        status=status_from_acceptance(accepted, warnings),
        seed=0,
        metrics=metrics,
        thresholds=thresholds,
        accepted=accepted,
        warnings=warnings,
        operator=operator,
    )
