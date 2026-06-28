# Controlled Real-Model Adapters

Real-model adapters are optional and local-only. They extend the same packet and certificate gate used by the synthetic suite.

## Install

```bash
python -m pip install -e .[real-hf]
python -m pip install -e .[real-tl]
```

The core package remains NumPy-only. Default CI does not require these extras.

## List Backends

```bash
python -m css_probes.cli real list-adapters
```

The command reports whether `huggingface` and `transformer-lens` are available and prints the install hint for missing backends.

## Run Local Activation Surgery

```bash
python -m css_probes.cli real activation-surgery \
  --backend huggingface \
  --model /path/to/local/model \
  --prompt-suite examples/prompt_suite_harmless.json \
  --layer 0 \
  --stream residual \
  --alpha 0.0 \
  --out reports/real_activation_surgery.json
```

Use `--backend transformer-lens` for TransformerLens. `--stream residual` resolves to common residual-block hooks where possible; backend-specific module or hook names can also be passed directly. Use `--vector path/to/vector.json` or `--vector path/to/vector.npy` to supply an additive activation vector.

## Prompt Suite Schema

```json
{
  "description": "Short audit description.",
  "target": [
    {"label": "target_case", "prompt": "The capital of France is", "target_token": " Paris"}
  ],
  "off_target": [
    {"label": "off_target_case", "prompt": "2 + 2 =", "target_token": " 4"}
  ]
}
```

The verifier measures target-token log-probability deltas and off-target degradation.

## Safety Boundary

- Local-only loading is mandatory; there is no download flag.
- Hooks are scoped to verifier calls and removed in `finally`.
- Inference runs under no-grad/inference mode.
- The adapter must not mutate weights, optimizer state, tokenizer files, model config, cache directories, or verifier thresholds.
- Real-model reports can be accepted or rejected, but both paths emit packet and certificate records when verifier execution reaches the model.
- Persistent edits, `save_pretrained`, optimizer steps, and production deployment are out of scope.

## Optional Smoke Tests

These are skipped unless local model paths are configured:

```bash
$env:CSS_HF_MODEL_PATH = "C:\\path\\to\\local\\hf-model"
$env:CSS_TL_MODEL_PATH = "C:\\path\\to\\local\\tl-model"
pytest -q tests/test_real_smoke.py
```
