# Codex Implementation Brief

Implement and extend Certified Semantic Surgery as a runnable probe suite.

Immediate commands:

```bash
python -m pip install -e .[dev]
css-probes run-all
pytest -q
```

Next work:

1. Add real-model hook adapters behind optional dependencies.
2. Add markdown operator cards.
3. Add cross-checkpoint transfer fixtures.
4. Add AETHER tuple serialization.
