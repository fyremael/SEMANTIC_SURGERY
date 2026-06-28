# Validation

Run locally:

```bash
python -m pip install -e .[dev]
python -m css_probes.cli run-all --out reports/css_probe_report.json
python -m css_probes.cli real list-adapters
python scripts/render_results_presentation.py
pytest -q
```
