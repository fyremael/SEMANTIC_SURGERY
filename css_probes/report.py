"""Report serialization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core import ProbeResult


def write_json_report(result: ProbeResult | list[ProbeResult], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(result, list):
        payload: dict[str, Any] = {
            "suite": "css-probes",
            "accepted": all(r.accepted for r in result),
            "results": [r.to_dict() for r in result],
        }
    else:
        payload = result.to_dict()
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    return path
