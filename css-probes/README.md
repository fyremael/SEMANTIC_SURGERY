# Companion suite

Python package code is in `css_probes` because import package names cannot contain hyphens.

Run:

```bash
python -m pip install -e .[dev]
css-probes run-all
pytest -q
```
