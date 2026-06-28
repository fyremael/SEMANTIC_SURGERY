"""Command-line interface for css-probes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .probes import PROBE_NAMES, load_probe
from .report import write_json_report


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] == "list":
        print("\n".join(PROBE_NAMES))
        return 0
    command = args.pop(0)
    seed = 0
    out = None
    while args and args[0].startswith("--"):
        flag = args.pop(0)
        if flag == "--seed":
            seed = int(args.pop(0))
        elif flag == "--out":
            out = Path(args.pop(0))
        else:
            raise SystemExit(f"unknown flag: {flag}")
    if command == "run":
        if not args:
            raise SystemExit("missing probe name")
        result = load_probe(args[0])(seed=seed)
        if out:
            write_json_report(result, out)
        else:
            print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0 if result.accepted else 1
    if command == "run-all":
        results = [load_probe(name)(seed=seed) for name in PROBE_NAMES]
        if out:
            write_json_report(results, out)
        else:
            print(json.dumps({"suite": "css-probes", "results": [r.to_dict() for r in results]}, indent=2, sort_keys=True))
        return 0 if all(r.accepted for r in results) else 1
    raise SystemExit(f"unknown command: {command}")
