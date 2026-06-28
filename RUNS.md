# Runs

Install the package, run the probe list, then run the full suite and tests.

```bash
python -m pip install -e .[dev]
python -m css_probes.cli list
python -m css_probes.cli run-all --out reports/css_probe_report.json
pytest -q
```
