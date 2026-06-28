"""Semantic Surgery Packet schema and simple verifier."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
import hashlib
import json
from typing import Any

from . import __version__
from .core import PHASE0_DEFAULT_THRESHOLDS, ProbeResult

ALLOWED_PERSISTENCE = {"ephemeral", "session", "adapter", "removable", "persistent"}
PHASE0_REJECTED_PERSISTENCE = {"persistent"}
NETWORK_FORBIDDEN_KEYS = {"allow_downloads", "downloads_allowed", "network_allowed", "remote_code_allowed"}
LEVEL_NAMES = [
    "level_1_typed",
    "level_2_bounded",
    "level_3_behavioral",
    "level_4_causal",
    "level_5_spectral",
    "level_6_rollback_safe",
    "level_7_cross_model_validated",
]


@dataclass(frozen=True)
class OperatorTarget:
    receiver_id: str = "synthetic_receiver"
    model_family: str = "synthetic-linear-receiver"
    state_type: str = "activation_stream"
    layer: int | None = 0
    stream: str = "residual"
    shape: list[int] = field(default_factory=lambda: [64])


@dataclass(frozen=True)
class OperatorBounds:
    delta_norm_max: float | None = None
    cosine_drift_min: float | None = None
    spectral_radius_max: float | None = None
    sigma_max: float | None = None
    pseudospectral_proxy_max: float | None = None
    rollback_residue_max: float | None = None
    off_target_degradation_max: float | None = None


@dataclass(frozen=True)
class OperatorSpec:
    form: str = "unspecified"
    rank: int | None = None
    parameters_ref: str = "inline"
    parameter_hash: str = "sha256:unspecified"


@dataclass(frozen=True)
class RollbackPlan:
    strategy: str = "copy_restore_context"
    required: bool = True
    residue_metric: str = "rollback_residue"


@dataclass(frozen=True)
class VerifierSpec:
    unit_tests: list[str] = field(default_factory=list)
    behavioral_tests: list[str] = field(default_factory=list)
    spectral_tests: list[str] = field(default_factory=list)
    causal_tests: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AuditSpec:
    provenance: str = "synthetic-fixture"
    human_rendering: str = "Synthetic certified semantic surgery packet."
    accepted: bool = False
    rejection_reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SemanticSurgeryPacket:
    packet_id: str
    operator_type: str
    version: str = __version__
    target: OperatorTarget = field(default_factory=OperatorTarget)
    persistence: str = "ephemeral"
    preconditions: dict[str, Any] = field(default_factory=dict)
    postconditions: dict[str, Any] = field(default_factory=dict)
    operator: OperatorSpec = field(default_factory=OperatorSpec)
    bounds: OperatorBounds = field(default_factory=OperatorBounds)
    intended_effect: dict[str, Any] = field(default_factory=dict)
    forbidden_effects: list[str] = field(default_factory=list)
    rollback: RollbackPlan = field(default_factory=RollbackPlan)
    verifier: VerifierSpec = field(default_factory=VerifierSpec)
    audit: AuditSpec = field(default_factory=AuditSpec)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PacketPolicyResult:
    accepted: bool
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {"accepted": self.accepted, "warnings": list(self.warnings)}


def verify_packet_shape(packet: SemanticSurgeryPacket) -> tuple[bool, list[str]]:
    warnings: list[str] = []
    if not packet.packet_id:
        warnings.append("missing_packet_id")
    if not packet.operator_type:
        warnings.append("missing_operator_type")
    if packet.persistence not in ALLOWED_PERSISTENCE:
        warnings.append(f"unknown_persistence:{packet.persistence}")
    if packet.persistence in PHASE0_REJECTED_PERSISTENCE:
        warnings.append(f"phase0_rejected_persistence:{packet.persistence}")
    if not packet.target.state_type:
        warnings.append("missing_target_state_type")
    if not packet.target.stream:
        warnings.append("missing_target_stream")
    if not packet.target.shape:
        warnings.append("missing_target_shape")
    if not packet.preconditions:
        warnings.append("missing_preconditions")
    if not packet.postconditions:
        warnings.append("missing_postconditions")
    if not packet.operator.form or packet.operator.form == "unspecified":
        warnings.append("missing_operator_form")
    if not packet.operator.parameter_hash.startswith("sha256:"):
        warnings.append("missing_parameter_hash")
    if not getattr(packet.rollback, "strategy", ""):
        warnings.append("missing_rollback_plan")
    if not packet.audit.human_rendering:
        warnings.append("missing_human_rendering")
    if not packet.verifier.unit_tests and not packet.verifier.behavioral_tests and not packet.verifier.spectral_tests and not packet.verifier.causal_tests:
        warnings.append("missing_verifier_list")
    warnings = _dedupe(warnings + _packet_policy_warnings(packet))
    return not warnings, warnings


def validate_packet_policy(packet: SemanticSurgeryPacket) -> PacketPolicyResult:
    ok, warnings = verify_packet_shape(packet)
    return PacketPolicyResult(accepted=ok, warnings=warnings)


def packet_from_dict(payload: dict[str, Any]) -> SemanticSurgeryPacket:
    """Load a packet from JSON while tolerating older reports without evidence."""

    rollback_payload = payload.get("rollback", {})
    if rollback_payload is None:
        rollback = RollbackPlan(strategy="", required=False)
    else:
        rollback = RollbackPlan(**rollback_payload)
    return SemanticSurgeryPacket(
        packet_id=str(payload.get("packet_id", "")),
        operator_type=str(payload.get("operator_type", "")),
        version=str(payload.get("version", __version__)),
        target=OperatorTarget(**(payload.get("target", {}) or {})),
        persistence=str(payload.get("persistence", "ephemeral")),
        preconditions=dict(payload.get("preconditions", {})),
        postconditions=dict(payload.get("postconditions", {})),
        operator=OperatorSpec(**(payload.get("operator", {}) or {})),
        bounds=OperatorBounds(**(payload.get("bounds", {}) or {})),
        intended_effect=dict(payload.get("intended_effect", {})),
        forbidden_effects=list(payload.get("forbidden_effects", [])),
        rollback=rollback,
        verifier=VerifierSpec(**(payload.get("verifier", {}) or {})),
        audit=AuditSpec(**(payload.get("audit", {}) or {})),
        evidence=dict(payload.get("evidence", {})),
    )


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def aether_tuple(packet: SemanticSurgeryPacket) -> tuple[Any, ...]:
    payload = packet.to_dict()
    return (
        "AETHER-CSS-v1",
        payload["packet_id"],
        payload["operator_type"],
        payload["version"],
        canonical_json(payload["target"]),
        payload["persistence"],
        canonical_json(payload["operator"]),
        canonical_json(payload["bounds"]),
        canonical_json(payload["intended_effect"]),
        canonical_json(payload["forbidden_effects"]),
        canonical_json(payload["rollback"]),
        canonical_json(payload["verifier"]),
        canonical_json(payload["audit"]),
        canonical_json(payload["evidence"]),
    )


def aether_payload(packet: SemanticSurgeryPacket) -> dict[str, Any]:
    payload = packet.to_dict()
    return {
        "format": "AETHER-CSS-v1",
        "packet_id": packet.packet_id,
        "packet_hash": stable_hash(payload),
        "canonical_packet_json": canonical_json(payload),
        "tuple": list(aether_tuple(packet)),
    }


def stable_hash(payload: Any) -> str:
    encoded = canonical_json(payload).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def packet_from_result(result: ProbeResult) -> SemanticSurgeryPacket:
    metadata = result.operator
    metrics = result.to_dict()["metrics"]
    thresholds = result.to_dict()["thresholds"]
    operator_type = str(metadata.get("operator_type", "unspecified"))
    persistence = str(metadata.get("persistence", "ephemeral"))
    target_shape = metadata.get("target_shape", [64])
    if not isinstance(target_shape, list):
        target_shape = list(target_shape) if isinstance(target_shape, tuple) else [int(target_shape)]

    bounds = OperatorBounds(
        delta_norm_max=_float_or_none(thresholds.get("norm_delta_max", PHASE0_DEFAULT_THRESHOLDS["norm_delta_max"])),
        cosine_drift_min=_float_or_none(thresholds.get("cosine_drift_min", PHASE0_DEFAULT_THRESHOLDS["cosine_drift_min"])),
        spectral_radius_max=_float_or_none(thresholds.get("spectral_radius_max")),
        sigma_max=_float_or_none(thresholds.get("sigma_max")),
        pseudospectral_proxy_max=_float_or_none(thresholds.get("pseudospectral_proxy_max")),
        rollback_residue_max=_float_or_none(thresholds.get("rollback_residue_max")),
        off_target_degradation_max=_float_or_none(thresholds.get("off_target_degradation_max")),
    )
    verifier = VerifierSpec(
        unit_tests=_unit_tests_for(metrics),
        behavioral_tests=_behavioral_tests_for(metrics),
        spectral_tests=_spectral_tests_for(metrics),
        causal_tests=_causal_tests_for(metrics),
    )
    return SemanticSurgeryPacket(
        packet_id=f"ssp_{result.name}",
        operator_type=operator_type,
        persistence=persistence,
        target=OperatorTarget(
            receiver_id=str(metadata.get("receiver_id", f"{metadata.get('backend', 'synthetic')}_receiver")),
            model_family=str(metadata.get("model_family", "synthetic-linear-receiver")),
            state_type=str(metadata.get("state_type", "activation_stream")),
            layer=_int_or_none(metadata.get("declared_layer", 0)),
            stream=str(metadata.get("stream", "residual")),
            shape=[int(x) for x in target_shape],
        ),
        preconditions={
            "allowed_tasks": metadata.get("allowed_tasks", ["synthetic_probe_suite"]),
            "deterministic_seed": result.seed,
            "requires_sandbox": True,
            "backend": metadata.get("backend", "synthetic"),
            "model_name_or_path": metadata.get("model_name_or_path"),
            "local_files_only": metadata.get("local_files_only", True),
        },
        postconditions={
            "accepted": result.accepted,
            "status": result.status,
            "notes": result.notes or result.warnings,
            "weight_fingerprint_changed": metrics.get("weight_fingerprint_changed"),
            "hook_cleanup_ok": metrics.get("hook_cleanup_ok"),
            "per_case_evidence_present": metrics.get("per_case_evidence_present"),
            "forbidden_effect_evidence_present": metrics.get("forbidden_effect_evidence_present"),
        },
        operator=OperatorSpec(
            form=str(metadata.get("form", operator_type)),
            rank=_int_or_none(metadata.get("rank")),
            parameters_ref=str(metadata.get("parameters_ref", "inline")),
            parameter_hash=str(metadata.get("parameter_hash", stable_hash(metadata))),
        ),
        bounds=bounds,
        intended_effect={
            "description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.",
            "target_metric": _target_metric_for(metrics, thresholds),
            "minimum_delta": thresholds.get("target_success_delta_min", thresholds.get("target_margin_delta_min")),
        },
        forbidden_effects=[
            "off_target_degradation_gt_0.02",
            "cosine_drift_below_0.98",
            "rollback_residue_gt_1e-9",
            "unstable_spectral_or_pseudospectral_growth",
        ],
        audit=AuditSpec(
            provenance="local-real-model-fixture" if "backend" in metadata else "synthetic-fixture",
            human_rendering=(
                f"Controlled local real-model semantic surgery packet for {result.name}."
                if "backend" in metadata
                else f"Synthetic certified semantic surgery packet for {result.name}."
            ),
            accepted=result.accepted,
            rejection_reasons=list(result.warnings),
        ),
        verifier=verifier,
        evidence=_evidence_for(metrics),
    )


def certification_from_result(result: ProbeResult) -> dict[str, Any]:
    metrics = result.to_dict()["metrics"]
    packet = packet_from_result(result)
    policy = validate_packet_policy(packet)
    levels = {
        "level_1_typed": policy.accepted,
        "level_2_bounded": _covered_and_passed(
            metrics,
            {
                "norm_delta_max": ("<=", PHASE0_DEFAULT_THRESHOLDS["norm_delta_max"]),
                "cosine_drift_min": (">=", PHASE0_DEFAULT_THRESHOLDS["cosine_drift_min"]),
            },
        ),
        "level_3_behavioral": _covered_and_passed(
            metrics,
            {
                "target_success_delta": (">=", PHASE0_DEFAULT_THRESHOLDS["target_success_delta_min"]),
                "off_target_degradation_max": ("<=", PHASE0_DEFAULT_THRESHOLDS["off_target_degradation_max"]),
            },
            any_of=True,
        ),
        "level_4_causal": "causal_locality_score" in metrics and result.accepted,
        "level_5_spectral": _covered_and_passed(
            metrics,
            {
                "spectral_radius": ("<=", PHASE0_DEFAULT_THRESHOLDS["spectral_radius_max"]),
                "sigma_max": ("<=", PHASE0_DEFAULT_THRESHOLDS["sigma_max"]),
                "pseudospectral_proxy": ("<=", PHASE0_DEFAULT_THRESHOLDS["pseudospectral_proxy_max"]),
            },
            any_of=True,
        ),
        "level_6_rollback_safe": _covered_and_passed(
            metrics,
            {"rollback_residue": ("<=", PHASE0_DEFAULT_THRESHOLDS["rollback_residue_max"])},
        ),
        "level_7_cross_model_validated": bool(metrics.get("cross_model_transfer_passed", False)) and result.accepted,
    }
    covered = [name for name, passed in levels.items() if passed]
    return {
        "phase": 1,
        "covered_levels": covered,
        "levels": levels,
        "packet_valid": policy.accepted,
        "packet_warnings": policy.warnings,
        "packet_policy": policy.to_dict(),
    }


def suite_certification_summary(results: list[ProbeResult]) -> dict[str, Any]:
    level_names = LEVEL_NAMES
    coverage = {name: [] for name in level_names}
    for result in results:
        cert = certification_from_result(result)
        for name in level_names:
            if cert["levels"][name]:
                coverage[name].append(result.name)
    return {
        "phase": 1,
        "levels_1_to_6_covered": all(bool(coverage[name]) for name in level_names[:6]),
        "levels_1_to_7_covered": all(bool(coverage[name]) for name in level_names),
        "coverage": coverage,
    }


def validate_report_packets(payload: dict[str, Any]) -> dict[str, Any]:
    packets = extract_packet_payloads(payload)
    rows = []
    for packet_payload in packets:
        packet = packet_from_dict(packet_payload)
        policy = validate_packet_policy(packet)
        rows.append(
            {
                "packet_id": packet.packet_id,
                "accepted": policy.accepted,
                "warnings": policy.warnings,
                "packet_hash": stable_hash(packet.to_dict()),
            }
        )
    return {
        "accepted": all(row["accepted"] for row in rows) if rows else False,
        "num_packets": len(rows),
        "packets": rows,
    }


def certify_report_payload(payload: dict[str, Any]) -> dict[str, Any]:
    packet_summary = validate_report_packets(payload)
    if "probes" not in payload:
        return {"accepted": packet_summary["accepted"], "packet_summary": packet_summary}
    level_coverage = {name: [] for name in LEVEL_NAMES}
    for probe in payload["probes"]:
        certificate = probe.get("certificate", {})
        levels = certificate.get("levels", {})
        for level_name in LEVEL_NAMES:
            if bool(levels.get(level_name, False)):
                level_coverage[level_name].append(probe.get("name", "unknown"))
    return {
        "suite": payload.get("suite", "css-probes"),
        "accepted": packet_summary["accepted"] and all(level_coverage[name] for name in LEVEL_NAMES),
        "packet_summary": packet_summary,
        "certification_summary": {
            "phase": 1,
            "levels_1_to_7_covered": all(level_coverage[name] for name in LEVEL_NAMES),
            "coverage": level_coverage,
        },
    }


def _extract_packets(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return extract_packet_payloads(payload)


def extract_packet_payloads(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if "packet" in payload:
        return [dict(payload["packet"])]
    if "probes" in payload:
        return [dict(probe["packet"]) for probe in payload["probes"] if "packet" in probe]
    if "packet_id" in payload:
        return [payload]
    return []


def _packet_policy_warnings(packet: SemanticSurgeryPacket) -> list[str]:
    warnings: list[str] = []
    if packet.persistence in PHASE0_REJECTED_PERSISTENCE:
        warnings.append(f"phase0_rejected_persistence:{packet.persistence}")
    if not getattr(packet.rollback, "required", False):
        warnings.append("rollback_not_required")
    if not packet.audit.provenance:
        warnings.append("missing_audit_provenance")
    if str(packet.target.stream).lower() in {"global", "all_layers", "*"}:
        warnings.append("global_operator_scope_rejected")
    if any(int(dim) <= 0 for dim in packet.target.shape):
        warnings.append("invalid_target_shape")
    for key in NETWORK_FORBIDDEN_KEYS:
        if bool(packet.preconditions.get(key, False)):
            warnings.append(f"network_or_download_forbidden:{key}")
    if packet.preconditions.get("local_files_only") is False:
        warnings.append("local_files_only_disabled")
    if _is_real_packet(packet):
        if packet.persistence != "ephemeral":
            warnings.append(f"real_model_non_ephemeral_persistence:{packet.persistence}")
        if not packet.postconditions.get("hook_cleanup_ok", False):
            warnings.append("real_model_missing_hook_cleanup_evidence")
        if packet.postconditions.get("weight_fingerprint_changed") is not False:
            warnings.append("real_model_weight_fingerprint_not_stable")
        if not packet.postconditions.get("per_case_evidence_present", False):
            warnings.append("missing_per_case_behavioral_evidence")
        if not packet.postconditions.get("forbidden_effect_evidence_present", False):
            warnings.append("missing_forbidden_effect_evidence")
        per_case = packet.evidence.get("per_case", {})
        if not per_case.get("target_case_deltas"):
            warnings.append("missing_target_case_deltas")
        if not per_case.get("off_target_case_deltas"):
            warnings.append("missing_off_target_case_deltas")
        if "forbidden_case_deltas" not in per_case:
            warnings.append("missing_forbidden_case_deltas")
    return _dedupe(warnings)


def _is_real_packet(packet: SemanticSurgeryPacket) -> bool:
    backend = packet.preconditions.get("backend")
    return (
        packet.operator_type.startswith("real_")
        or backend not in {None, "", "synthetic"}
        or packet.audit.provenance == "local-real-model-fixture"
    )


def _evidence_for(metrics: dict[str, Any]) -> dict[str, Any]:
    per_case_keys = [
        "target_case_deltas",
        "off_target_case_deltas",
        "forbidden_case_deltas",
        "target_case_delta_min",
        "off_target_case_degradation_max",
        "forbidden_leakage_max",
    ]
    per_case = {key: metrics[key] for key in per_case_keys if key in metrics}
    verifier_metrics = {
        key: metrics[key]
        for key in [
            "target_success_delta",
            "target_token_logprob_delta",
            "off_target_degradation_max",
            "norm_delta_max",
            "cosine_drift_min",
            "rollback_residue",
            "weight_fingerprint_changed",
            "hook_cleanup_ok",
            "cross_model_transfer_passed",
        ]
        if key in metrics
    }
    return {
        "per_case": per_case,
        "verifier_metrics": verifier_metrics,
    }


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _float_or_none(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    return float(value)


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _unit_tests_for(metrics: dict[str, Any]) -> list[str]:
    tests: list[str] = []
    if "norm_delta_max" in metrics:
        tests.append("norm_drift_probe")
    if "rollback_residue" in metrics:
        tests.append("rollback_probe")
    if "checker_accepted" in metrics or "proof_closed" in metrics:
        tests.append("proof_state_surgery_probe")
    if "hook_cleanup_ok" in metrics:
        tests.append("real_model_hook_cleanup")
    if "weight_fingerprint_changed" in metrics:
        tests.append("real_model_no_weight_mutation")
    return tests


def _behavioral_tests_for(metrics: dict[str, Any]) -> list[str]:
    tests: list[str] = []
    if "off_target_degradation_max" in metrics:
        tests.append("off_target_regression_probe")
    if "target_success_delta" in metrics or "target_margin_delta" in metrics:
        tests.append("activation_patch_probe")
    return tests


def _spectral_tests_for(metrics: dict[str, Any]) -> list[str]:
    tests: list[str] = []
    if "spectral_radius" in metrics or "sigma_max" in metrics:
        tests.append("spectral_radius_probe")
    if "pseudospectral_proxy" in metrics:
        tests.append("pseudospectrum_probe")
    return tests


def _causal_tests_for(metrics: dict[str, Any]) -> list[str]:
    return ["causal_locality_probe"] if "causal_locality_score" in metrics else []


def _target_metric_for(metrics: dict[str, Any], thresholds: dict[str, Any]) -> str:
    if "target_success_delta_min" in thresholds and "target_success_delta" in metrics:
        return "target_success_delta"
    if "target_margin_delta_min" in thresholds and "target_margin_delta" in metrics:
        return "target_margin_delta"
    if "operator_absolute_advantage_min" in thresholds and "operator_absolute_advantage" in metrics:
        return "operator_absolute_advantage"
    if "one_step_mse_improvement" in metrics:
        return "one_step_mse_improvement"
    if "proof_closed" in metrics:
        return "proof_closed"
    return "accepted"


def _covered_and_passed(metrics: dict[str, Any], checks: dict[str, tuple[str, float]], any_of: bool = False) -> bool:
    covered = False
    passed_any = False
    for metric, (op, threshold) in checks.items():
        if metric not in metrics:
            continue
        covered = True
        value = float(metrics[metric])
        passed = value <= threshold if op == "<=" else value >= threshold
        if not passed:
            return False
        passed_any = passed_any or passed
    return passed_any if any_of else covered
