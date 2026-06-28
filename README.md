# Certified Semantic Surgery / css-probes

Certified Semantic Surgery (CSS) explores **operator-valued communication**: exchanging typed, bounded, verifiable transformations over receiver states rather than only exchanging natural-language messages.

This repository contains:

- `CERTIFIED_SEMANTIC_SURGERY.md` — full project specification;
- `css_probes/` — runnable NumPy probe suite;
- `tests/` — deterministic unit tests;
- `.github/workflows/ci.yml` — basic CI.

The suite is intentionally synthetic and conservative. It proves the plumbing first: packets, operators, certificates, metrics, rollback, spectra, pseudospectra, locality, and operator-vs-text transfer benchmarks. Real transformer hooks are the next extension.

## Install

```bash
python -m pip install -e .[dev]
```

## Run all probes

```bash
python -m css_probes.cli run-all --out reports/css_probe_report.json
```

## Run one probe

```bash
python -m css_probes.cli run activation_patch_probe --out reports/activation_patch_probe.json
```

## List probes

```bash
python -m css_probes.cli list
```

## Test

```bash
pytest -q
```

## Probe suite

- `activation_patch_probe`
- `low_rank_operator_probe`
- `norm_drift_probe`
- `spectral_radius_probe`
- `pseudospectrum_probe`
- `causal_locality_probe`
- `off_target_regression_probe`
- `rollback_probe`
- `operator_vs_text_benchmark`

## Safety posture

Phase-one CSS allows only synthetic, ephemeral, or removable transformations. It rejects autonomous permanent weight edits, opaque latent packets, verifier-bypassing operators, and self-modifying operator loops.

## Next implementation step

Add optional real-model integration behind separate adapters:

```text
css_probes/hooks/transformer_lens_adapter.py
examples/real_model_activation_surgery.py
```

The real-model adapter should collect activation streams, apply ephemeral hooks, evaluate target/off-target prompt suites, and emit the same certificate schema as the synthetic suite.
