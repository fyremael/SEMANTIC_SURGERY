import numpy as np
import pytest

from css_probes.metrics import normalize
from css_probes.operators import ActivationAdditiveOperator
from css_probes.packets import (
    AuditSpec,
    OperatorSpec,
    OperatorTarget,
    SemanticSurgeryPacket,
    certification_from_result,
    packet_from_result,
    suite_certification_summary,
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


def test_suite_certificate_covers_phase0_levels_1_to_6():
    results = [load_probe(name)(seed=0) for name in PROBE_NAMES]
    summary = suite_certification_summary(results)

    assert summary["levels_1_to_6_covered"] is True
    assert set(summary["coverage"]) == {
        "level_1_typed",
        "level_2_bounded",
        "level_3_behavioral",
        "level_4_causal",
        "level_5_spectral",
        "level_6_rollback_safe",
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


def test_activation_operator_rejects_shape_mismatch():
    op = ActivationAdditiveOperator(vector=normalize(np.ones(4)), alpha=0.1)

    with pytest.raises(ValueError, match="last dimension"):
        op.apply(np.ones((2, 5)))
