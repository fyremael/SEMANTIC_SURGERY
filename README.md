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

This writes the machine report to `reports/css_probe_report.json` and a human-readable
operator-card sidecar to `reports/css_probe_report.operator_cards.md`.

The JSON report includes one Semantic Surgery Packet and one certification record per
probe. See `docs/PHASE0_COMPLIANCE.md` for the spec-to-implementation mapping.

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
- `koopman_dynamics_message_probe`
- `proof_state_surgery_probe`

## Safety posture

Phase-one CSS allows only synthetic, ephemeral, or removable transformations. It rejects autonomous permanent weight edits, opaque latent packets, verifier-bypassing operators, and self-modifying operator loops.

## Controlled real-model adapters

Real-model activation probes are available behind optional extras and local-only loaders:

```bash
python -m pip install -e .[real-hf]
python -m css_probes.cli real list-adapters
python -m css_probes.cli real activation-surgery \
  --backend huggingface \
  --model /path/to/local/model \
  --prompt-suite examples/prompt_suite_harmless.json \
  --layer 0 \
  --stream residual \
  --out reports/real_activation_surgery.json
```

These adapters use ephemeral inference hooks only. They do not download models, save models, mutate weights, run optimizer steps, or relax packet/certificate gates. See `docs/REAL_MODEL_ADAPTERS.md`.
