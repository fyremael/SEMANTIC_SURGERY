# Runs

Install the package, run the probe list, then run the full suite and tests.

```bash
python -m pip install -e .[dev]
css-probes list
css-probes run-all
pytest -q
```
