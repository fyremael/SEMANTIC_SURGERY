# Commands

```bash
python -m pip install -e .[dev]
python -m css_probes.cli list
python -m css_probes.cli run-all --out reports/css_probe_report.json
python -m css_probes.cli real list-adapters
python scripts/render_results_presentation.py
python -m css_probes.cli run activation_patch_probe --out reports/activation_patch_probe.json
pytest -q
```
