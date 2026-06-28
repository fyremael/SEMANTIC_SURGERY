import json
import subprocess
import sys
from pathlib import Path

from css_probes import __version__
from css_probes.probes import PROBE_NAMES


ROOT = Path(__file__).resolve().parents[1]


def run_module_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "css_probes.cli", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_module_cli_list_prints_probe_names():
    result = run_module_cli("list")

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == PROBE_NAMES


def test_module_cli_run_all_writes_spec_report_and_operator_cards(tmp_path):
    report_path = tmp_path / "css_probe_report.json"
    result = run_module_cli("run-all", "--out", str(report_path))

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["suite"] == "css-probes"
    assert payload["version"] == __version__
    assert payload["accepted"] is True
    assert payload["summary"] == {
        "num_probes": len(PROBE_NAMES),
        "num_accepted": len(PROBE_NAMES),
        "num_rejected": 0,
    }
    assert payload["certification_summary"]["levels_1_to_6_covered"] is True
    assert "probes" in payload
    assert "results" not in payload
    assert [probe["name"] for probe in payload["probes"]] == PROBE_NAMES
    assert all({"accepted", "certificate", "metrics", "notes", "packet", "thresholds"} <= probe.keys() for probe in payload["probes"])

    cards_path = tmp_path / "css_probe_report.operator_cards.md"
    cards = cards_path.read_text(encoding="utf-8")
    assert "# CSS Operator Cards" in cards
    assert "Operator name:" in cards
    assert "Accepted / rejected: accepted" in cards


def test_module_cli_run_accepts_out_after_probe_name(tmp_path):
    report_path = tmp_path / "activation_patch_probe.json"
    result = run_module_cli("run", "activation_patch_probe", "--out", str(report_path))

    assert result.returncode == 0, result.stderr
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["name"] == "activation_patch_probe"
    assert payload["accepted"] is True
    assert payload["notes"] == []
    assert payload["packet"]["operator"]["parameter_hash"].startswith("sha256:")
    assert payload["certificate"]["packet_valid"] is True
    assert (tmp_path / "activation_patch_probe.operator_cards.md").exists()
