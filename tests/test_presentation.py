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

    assert "Certified Semantic Surgery Phase 0 Results" in html
    assert "Certification Coverage" in html
    assert "Operator vs Text Transfer" in html
    assert "11/11 probes accepted" in svg
    assert "certification Levels 1-6 covered" in svg
    ET.fromstring(svg)
