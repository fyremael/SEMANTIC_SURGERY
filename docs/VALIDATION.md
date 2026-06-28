# Validation

Run locally:

```bash
python -m pip install -e .[dev]
python -m css_probes.cli run-all --out reports/css_probe_report.json
python -m css_probes.cli packet validate --in reports/css_probe_report.json
python -m css_probes.cli packet render --in reports/css_probe_report.json --out reports/css_probe_report.packet_cards.md
python -m css_probes.cli certify --in reports/css_probe_report.json --out reports/certificate.json
python -m css_probes.cli aether roundtrip --in reports/css_probe_report.json --out reports/aether_roundtrip.json
python -m css_probes.cli real list-adapters
python scripts/render_results_presentation.py
pytest -q
git diff --check
```
