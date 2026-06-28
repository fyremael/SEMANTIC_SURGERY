import json
import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "render_results_presentation.py"
SPEC = importlib.util.spec_from_file_location("render_results_presentation", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


def test_results_presentation_renders_html_and_valid_svg():
    payload = json.loads(renderer.REPORT_PATH.read_text(encoding="utf-8"))

    html = renderer.render_html(payload)
    svg = renderer.render_svg(payload)

    assert "Certified Semantic Surgery Results" in html
    assert "Certification Coverage" in html
    assert "Operator vs Text Transfer" in html
    accepted = payload["summary"]["num_accepted"]
    total = payload["summary"]["num_probes"]
    max_level = max(int(key.split("_")[1]) for key, names in payload["certification_summary"]["coverage"].items() if names)
    assert f"{accepted}/{total} probes accepted" in svg
    assert f"certification Levels 1-{max_level} covered" in svg
    ET.fromstring(svg)
