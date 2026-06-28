"""Semantic Surgery Packet schema and simple verifier."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class OperatorTarget:
    receiver_id: str = "synthetic_receiver"
    model_family: str = "synthetic_linear_state"
    layer: int | None = None
    stream: str = "state"


@dataclass(frozen=True)
class OperatorBounds:
    delta_norm_max: float | None = None
    cosine_drift_min: float | None = None
    spectral_radius_max: float | None = None
    spectral_norm_max: float | None = None
    off_target_degradation_max: float | None = None


@dataclass(frozen=True)
class SemanticSurgeryPacket:
    packet_id: str
    operator_type: str
    target: OperatorTarget = field(default_factory=OperatorTarget)
    persistence: str = "ephemeral"
    preconditions: dict[str, Any] = field(default_factory=dict)
    postconditions: dict[str, Any] = field(default_factory=dict)
    bounds: OperatorBounds = field(default_factory=OperatorBounds)
    human_rendering: str = "Synthetic certified semantic surgery packet."
    provenance: str = "generated_by_css_probes"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def verify_packet_shape(packet: SemanticSurgeryPacket) -> tuple[bool, list[str]]:
    warnings: list[str] = []
    if not packet.packet_id:
        warnings.append("missing_packet_id")
    if not packet.operator_type:
        warnings.append("missing_operator_type")
    if not packet.human_rendering:
        warnings.append("missing_human_rendering")
    if packet.persistence not in {"ephemeral", "session", "removable", "persistent"}:
        warnings.append(f"unknown_persistence:{packet.persistence}")
    return not warnings, warnings
