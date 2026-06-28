"""Command-line interface for css-probes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .hooks.base import BackendUnavailableError, load_prompt_suite
from .hooks.registry import list_adapters
from .probes import PROBE_NAMES, load_probe
from .probes.real_activation_surgery import load_vector, run_real_activation_surgery
from .report import (
    default_operator_cards_path,
    probe_payload,
    suite_payload,
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


def _run_real_command(args: list[str]) -> int:
    if not args:
        raise SystemExit("missing real command")
    command = args.pop(0)
    if command == "list-adapters":
        if args:
            raise SystemExit(f"unexpected argument for real list-adapters: {args[0]}")
        print(json.dumps([availability.__dict__ for availability in list_adapters()], indent=2, sort_keys=True))
        return 0
    if command != "activation-surgery":
        raise SystemExit(f"unknown real command: {command}")
    options = _parse_real_options(args)
    required = ["backend", "model", "prompt-suite", "layer", "stream", "out"]
    missing = [name for name in required if name not in options]
    if missing:
        raise SystemExit(f"missing required real activation-surgery option(s): {', '.join('--' + item for item in missing)}")
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


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        args = ["list"]
    command = args.pop(0)
    if command == "real":
        return _run_real_command(args)
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
