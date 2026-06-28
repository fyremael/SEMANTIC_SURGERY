"""Report serialization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import __version__
from .core import ProbeResult
from .packets import certification_from_result, packet_from_result, suite_certification_summary


def probe_payload(result: ProbeResult) -> dict[str, Any]:
    """Return the spec-facing JSON payload for one probe."""

    payload = result.to_dict()
    payload["notes"] = list(result.notes or result.warnings)
    payload["packet"] = result.packet or packet_from_result(result).to_dict()
    payload["certificate"] = result.certificate or certification_from_result(result)
    return payload


def suite_payload(results: list[ProbeResult]) -> dict[str, Any]:
    accepted = all(r.accepted for r in results)
    num_accepted = sum(1 for r in results if r.accepted)
    return {
        "suite": "css-probes",
        "version": __version__,
        "accepted": accepted,
        "summary": {
            "num_probes": len(results),
            "num_accepted": num_accepted,
            "num_rejected": len(results) - num_accepted,
        },
        "certification_summary": suite_certification_summary(results),
        "probes": [probe_payload(r) for r in results],
    }


def write_json_report(result: ProbeResult | list[ProbeResult], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(result, list):
        payload = suite_payload(result)
    else:
        payload = probe_payload(result)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    return path


def default_operator_cards_path(report_path: str | Path) -> Path:
    path = Path(report_path)
    return path.with_name(f"{path.stem}.operator_cards.md")


def _format_mapping(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True) if value else "not declared"


def render_operator_card(result: ProbeResult) -> str:
    payload = probe_payload(result)
    packet = payload["packet"]
    operator_type = result.operator.get("operator_type", "unspecified")
    persistence = result.operator.get("persistence", "unspecified")
    norm_bounds = {k: v for k, v in result.thresholds.items() if "norm" in k or "cosine" in k}
    spectral_bounds = {
        k: v
        for k, v in result.thresholds.items()
        if "spectral" in k or "sigma" in k or "transient" in k
    }
    behavioral_metrics = {
        k: v
        for k, v in result.metrics.items()
        if "target" in k or "success" in k or "locality" in k or "accepted" in k
    }
    rollback_metrics = {k: v for k, v in result.metrics.items() if "rollback" in k}
    rejection_reasons = ", ".join(result.warnings) if result.warnings else "none"
    accepted = "accepted" if result.accepted else "rejected"

    return "\n".join(
        [
            f"## {result.name}",
            "",
            f"Operator name: {operator_type}",
            "Target state: synthetic probe state",
            f"Operator form: {operator_type}",
            f"Persistence: {persistence}",
            f"Preconditions: {_format_mapping(packet['preconditions'])}",
            f"Intended effect: {_format_mapping(packet['intended_effect'])}",
            f"Forbidden effects: {', '.join(packet['forbidden_effects'])}",
            f"Norm bounds: {_format_mapping(norm_bounds)}",
            f"Spectral bounds: {_format_mapping(spectral_bounds)}",
            f"Behavioral result: {_format_mapping(behavioral_metrics)}",
            f"Rollback result: {_format_mapping(rollback_metrics)}",
            f"Accepted / rejected: {accepted}",
            f"Rejection reasons: {rejection_reasons}",
            f"Human rendering: {packet['audit']['human_rendering']}",
            "",
        ]
    )


def write_operator_cards(result: ProbeResult | list[ProbeResult], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    results = result if isinstance(result, list) else [result]
    content = ["# CSS Operator Cards", ""]
    for item in results:
        content.append(render_operator_card(item))
    path.write_text("\n".join(content), encoding="utf-8")
    return path


def render_packet_card(packet: dict[str, Any]) -> str:
    audit = packet.get("audit", {})
    target = packet.get("target", {})
    evidence = packet.get("evidence", {})
    return "\n".join(
        [
            f"## {packet.get('packet_id', 'unknown_packet')}",
            "",
            f"Operator name: {packet.get('operator_type', 'unspecified')}",
            f"Target state: {target.get('state_type', 'unspecified')} / {target.get('stream', 'unspecified')}",
            f"Persistence: {packet.get('persistence', 'unspecified')}",
            f"Preconditions: {_format_mapping(packet.get('preconditions', {}))}",
            f"Intended effect: {_format_mapping(packet.get('intended_effect', {}))}",
            f"Forbidden effects: {', '.join(packet.get('forbidden_effects', []))}",
            f"Verifier: {_format_mapping(packet.get('verifier', {}))}",
            f"Evidence: {_format_mapping(evidence)}",
            f"Accepted / rejected: {'accepted' if audit.get('accepted') else 'rejected'}",
            f"Rejection reasons: {', '.join(audit.get('rejection_reasons', [])) or 'none'}",
            f"Human rendering: {audit.get('human_rendering', '')}",
            "",
        ]
    )


def write_packet_cards(packets: list[dict[str, Any]], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = ["# CSS Packet Cards", ""]
    for packet in packets:
        content.append(render_packet_card(packet))
    path.write_text("\n".join(content), encoding="utf-8")
    return path
