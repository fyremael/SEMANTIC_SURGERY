"""Command-line interface for css-probes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .hooks.base import BackendUnavailableError, load_prompt_suite
from .hooks.registry import list_adapters
from .packets import (
    aether_payload,
    certify_report_payload,
    extract_packet_payloads,
    packet_from_dict,
    stable_hash,
    validate_report_packets,
)
from .probes import PROBE_NAMES, load_probe
from .probes.real_activation_surgery import load_vector, run_real_activation_surgery
from .report import (
    default_operator_cards_path,
    probe_payload,
    suite_payload,
    write_packet_cards,
    write_json_report,
    write_operator_cards,
)


def _parse_options(args: list[str]) -> tuple[int, Path | None, Path | None, list[str]]:
    seed = 0
    out = None
    cards_out = None
    positionals: list[str] = []
    idx = 0
    while idx < len(args):
        token = args[idx]
        if token in {"--seed", "--out", "--cards-out"}:
            if idx + 1 >= len(args):
                raise SystemExit(f"missing value for {token}")
            value = args[idx + 1]
            if token == "--seed":
                seed = int(value)
            elif token == "--out":
                out = Path(value)
            else:
                cards_out = Path(value)
            idx += 2
            continue
        if token.startswith("--"):
            raise SystemExit(f"unknown flag: {token}")
        positionals.append(token)
        idx += 1
    return seed, out, cards_out, positionals


def _write_requested_reports(result, out: Path | None, cards_out: Path | None) -> None:
    if out is not None:
        write_json_report(result, out)
        write_operator_cards(result, cards_out or default_operator_cards_path(out))
    elif cards_out is not None:
        write_operator_cards(result, cards_out)


def _parse_real_options(args: list[str]) -> dict[str, str]:
    options: dict[str, str] = {}
    idx = 0
    while idx < len(args):
        token = args[idx]
        if not token.startswith("--"):
            raise SystemExit(f"unexpected argument for real activation-surgery: {token}")
        if idx + 1 >= len(args):
            raise SystemExit(f"missing value for {token}")
        options[token[2:]] = args[idx + 1]
        idx += 2
    return options


def _parse_key_options(args: list[str], command_name: str) -> dict[str, str]:
    options: dict[str, str] = {}
    idx = 0
    while idx < len(args):
        token = args[idx]
        if not token.startswith("--"):
            raise SystemExit(f"unexpected argument for {command_name}: {token}")
        if idx + 1 >= len(args):
            raise SystemExit(f"missing value for {token}")
        options[token[2:]] = args[idx + 1]
        idx += 2
    return options


def _read_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(payload: dict, path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return out


def _require_options(options: dict[str, str], required: list[str], command_name: str) -> None:
    missing = [name for name in required if name not in options]
    if missing:
        raise SystemExit(f"missing required {command_name} option(s): {', '.join('--' + item for item in missing)}")


def _run_real_command(args: list[str]) -> int:
    if not args:
        raise SystemExit("missing real command")
    command = args.pop(0)
    if command == "list-adapters":
        if args:
            raise SystemExit(f"unexpected argument for real list-adapters: {args[0]}")
        print(json.dumps([availability.__dict__ for availability in list_adapters()], indent=2, sort_keys=True))
        return 0
    if command == "envelope-audit":
        return _run_real_activation_command(args, command_name="real envelope-audit")
    if command != "activation-surgery":
        raise SystemExit(f"unknown real command: {command}")
    return _run_real_activation_command(args, command_name="real activation-surgery")


def _run_real_activation_command(args: list[str], command_name: str) -> int:
    options = _parse_real_options(args)
    required = ["backend", "model", "prompt-suite", "layer", "stream", "out"]
    _require_options(options, required, command_name)
    from .hooks.base import ActivationSurgeryConfig

    try:
        prompt_suite = load_prompt_suite(options["prompt-suite"])
        config = ActivationSurgeryConfig(
            backend=options["backend"],
            model_name_or_path=options["model"],
            prompt_suite=prompt_suite,
            layer=int(options["layer"]),
            stream=options["stream"],
            alpha=float(options.get("alpha", "0.0")),
            vector=load_vector(options.get("vector")),
            seed=int(options.get("seed", "0")),
            local_files_only=True,
        )
        result = run_real_activation_surgery(config)
    except BackendUnavailableError as exc:
        raise SystemExit(str(exc)) from exc
    except FileNotFoundError as exc:
        raise SystemExit(f"missing local prompt/vector file: {exc}") from exc
    out = Path(options["out"])
    cards_out = Path(options["cards-out"]) if "cards-out" in options else None
    _write_requested_reports(result, out, cards_out)
    return 0 if result.accepted else 1


def _run_packet_command(args: list[str]) -> int:
    if not args:
        raise SystemExit("missing packet command")
    command = args.pop(0)
    options = _parse_key_options(args, f"packet {command}")
    _require_options(options, ["in"], f"packet {command}")
    payload = _read_json(options["in"])
    if command == "validate":
        result = validate_report_packets(payload)
        if "out" in options:
            _write_json(result, options["out"])
        else:
            print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["accepted"] else 1
    if command == "render":
        _require_options(options, ["out"], "packet render")
        packets = extract_packet_payloads(payload)
        if not packets:
            raise SystemExit("no packets found to render")
        write_packet_cards(packets, options["out"])
        return 0
    raise SystemExit(f"unknown packet command: {command}")


def _run_certify_command(args: list[str]) -> int:
    options = _parse_key_options(args, "certify")
    _require_options(options, ["in"], "certify")
    payload = certify_report_payload(_read_json(options["in"]))
    if "out" in options:
        _write_json(payload, options["out"])
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["accepted"] else 1


def _run_aether_command(args: list[str]) -> int:
    if not args:
        raise SystemExit("missing aether command")
    command = args.pop(0)
    if command != "roundtrip":
        raise SystemExit(f"unknown aether command: {command}")
    options = _parse_key_options(args, "aether roundtrip")
    _require_options(options, ["in", "out"], "aether roundtrip")
    packets = extract_packet_payloads(_read_json(options["in"]))
    if not packets:
        raise SystemExit("no packets found for AETHER roundtrip")
    rows = []
    for packet_payload in packets:
        packet = packet_from_dict(packet_payload)
        serialized = aether_payload(packet)
        decoded = json.loads(serialized["canonical_packet_json"])
        rows.append(
            {
                "packet_id": packet.packet_id,
                "packet_hash": serialized["packet_hash"],
                "roundtrip_hash": stable_hash(decoded),
                "roundtrip_ok": serialized["packet_hash"] == stable_hash(decoded),
                "aether": serialized,
            }
        )
    payload = {"accepted": all(row["roundtrip_ok"] for row in rows), "roundtrips": rows}
    _write_json(payload, options["out"])
    return 0 if payload["accepted"] else 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        args = ["list"]
    command = args.pop(0)
    if command == "real":
        return _run_real_command(args)
    if command == "packet":
        return _run_packet_command(args)
    if command == "certify":
        return _run_certify_command(args)
    if command == "aether":
        return _run_aether_command(args)
    if command == "list":
        _seed, out, cards_out, positionals = _parse_options(args)
        if out is not None or cards_out is not None:
            raise SystemExit("list does not write reports")
        if positionals:
            raise SystemExit(f"unexpected argument for list: {positionals[0]}")
        print("\n".join(PROBE_NAMES))
        return 0
    seed, out, cards_out, positionals = _parse_options(args)
    if command == "run":
        if not positionals:
            raise SystemExit("missing probe name")
        if len(positionals) > 1:
            raise SystemExit(f"unexpected argument for run: {positionals[1]}")
        result = load_probe(positionals[0])(seed=seed)
        _write_requested_reports(result, out, cards_out)
        if out:
            return 0 if result.accepted else 1
        print(json.dumps(probe_payload(result), indent=2, sort_keys=True))
        return 0 if result.accepted else 1
    if command == "run-all":
        if positionals:
            raise SystemExit(f"unexpected argument for run-all: {positionals[0]}")
        results = [load_probe(name)(seed=seed) for name in PROBE_NAMES]
        _write_requested_reports(results, out, cards_out)
        if out:
            return 0 if all(r.accepted for r in results) else 1
        print(json.dumps(suite_payload(results), indent=2, sort_keys=True))
        return 0 if all(r.accepted for r in results) else 1
    raise SystemExit(f"unknown command: {command}")


if __name__ == "__main__":
    raise SystemExit(main())
