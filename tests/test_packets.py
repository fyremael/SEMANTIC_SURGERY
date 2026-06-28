import numpy as np
import pytest

from css_probes.metrics import normalize
from css_probes.operators import ActivationAdditiveOperator
from css_probes.packets import (
    AuditSpec,
    OperatorSpec,
    OperatorTarget,
    SemanticSurgeryPacket,
    aether_payload,
    certification_from_result,
    packet_from_dict,
    packet_from_result,
    suite_certification_summary,
    validate_packet_policy,
    verify_packet_shape,
)
from css_probes.probes import PROBE_NAMES, load_probe


def test_all_probe_packets_are_phase0_valid():
    for name in PROBE_NAMES:
        result = load_probe(name)(seed=0)
        packet = packet_from_result(result)
        ok, warnings = verify_packet_shape(packet)

        assert ok, (name, warnings)
        payload = packet.to_dict()
        assert payload["packet_id"] == f"ssp_{name}"
        assert payload["operator"]["parameter_hash"].startswith("sha256:")
        assert payload["audit"]["accepted"] is result.accepted
        assert payload["verifier"] != {
            "unit_tests": [],
            "behavioral_tests": [],
            "spectral_tests": [],
            "causal_tests": [],
        }


def test_suite_certificate_covers_levels_1_to_7():
    results = [load_probe(name)(seed=0) for name in PROBE_NAMES]
    summary = suite_certification_summary(results)

    assert summary["levels_1_to_6_covered"] is True
    assert summary["levels_1_to_7_covered"] is True
    assert set(summary["coverage"]) == {
        "level_1_typed",
        "level_2_bounded",
        "level_3_behavioral",
        "level_4_causal",
        "level_5_spectral",
        "level_6_rollback_safe",
        "level_7_cross_model_validated",
    }
    assert all(summary["coverage"].values())


def test_probe_certificate_embeds_packet_validity():
    result = load_probe("activation_patch_probe")(seed=0)
    certificate = certification_from_result(result)

    assert certificate["packet_valid"] is True
    assert certificate["levels"]["level_1_typed"] is True
    assert certificate["levels"]["level_2_bounded"] is True
    assert certificate["levels"]["level_3_behavioral"] is True
    assert certificate["levels"]["level_6_rollback_safe"] is True


def test_phase0_rejects_persistent_packets():
    packet = SemanticSurgeryPacket(
        packet_id="ssp_bad_persistent",
        operator_type="activation_additive",
        persistence="persistent",
        target=OperatorTarget(shape=[4]),
        preconditions={"requires_sandbox": True},
        postconditions={"accepted": False},
        operator=OperatorSpec(
            form="h_prime = h + v",
            parameter_hash="sha256:test",
        ),
        audit=AuditSpec(human_rendering="Bad persistent packet."),
    )

    ok, warnings = verify_packet_shape(packet)

    assert ok is False
    assert "phase0_rejected_persistence:persistent" in warnings


def test_level_7_requires_cross_model_evidence():
    activation = load_probe("activation_patch_probe")(seed=0)
    cross = load_probe("cross_checkpoint_transfer_probe")(seed=0)

    assert certification_from_result(activation)["levels"]["level_7_cross_model_validated"] is False
    assert certification_from_result(cross)["levels"]["level_7_cross_model_validated"] is True


def test_aether_roundtrip_preserves_packet_hash():
    packet = packet_from_result(load_probe("activation_patch_probe")(seed=0))
    serialized = aether_payload(packet)
    decoded = packet_from_dict(packet.to_dict())

    assert serialized["packet_hash"].startswith("sha256:")
    assert aether_payload(decoded)["packet_hash"] == serialized["packet_hash"]
    assert serialized["tuple"][0] == "AETHER-CSS-v1"


def test_packet_policy_rejects_network_global_and_missing_audit():
    packet = SemanticSurgeryPacket(
        packet_id="ssp_bad_policy",
        operator_type="activation_additive",
        target=OperatorTarget(shape=[4], stream="global"),
        preconditions={"requires_sandbox": True, "allow_downloads": True},
        postconditions={"accepted": False},
        operator=OperatorSpec(form="h_prime = h + v", parameter_hash="sha256:test"),
        audit=AuditSpec(provenance="", human_rendering="Bad policy packet."),
    )

    policy = validate_packet_policy(packet)

    assert policy.accepted is False
    assert "network_or_download_forbidden:allow_downloads" in policy.warnings
    assert "global_operator_scope_rejected" in policy.warnings
    assert "missing_audit_provenance" in policy.warnings


def test_activation_operator_rejects_shape_mismatch():
    op = ActivationAdditiveOperator(vector=normalize(np.ones(4)), alpha=0.1)

    with pytest.raises(ValueError, match="last dimension"):
        op.apply(np.ones((2, 5)))
