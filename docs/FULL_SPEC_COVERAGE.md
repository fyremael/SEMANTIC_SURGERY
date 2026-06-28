# Full Spec Coverage

This repo now implements the intended controlled CSS research platform while preserving the safety boundary in `CERTIFIED_SEMANTIC_SURGERY.md`.

## Certification Ladder

- Level 1 typed: every probe emits a Semantic Surgery Packet with typed target state, operator form, bounds, rollback, verifier, audit, and evidence fields.
- Level 2 bounded: norm/cosine and declared bound checks are enforced by probe thresholds and packet policy.
- Level 3 behavioral: target and off-target effects are measured for activation, operator-vs-text, KV-cache, LoRA dry-run, cross-checkpoint, and real-model activation probes.
- Level 4 causal: causal locality is covered by synthetic locality probes and toy KV-cache locality accounting.
- Level 5 spectral/dynamical: spectral radius, singular value, pseudospectral proxy, and Koopman dynamics probes cover the dynamical checks.
- Level 6 rollback-safe: rollback residue and hook cleanup are required for accepted probes.
- Level 7 cross-model validated: deterministic cross-checkpoint transfer fixtures prove the packet/certificate path. Optional real cross-model smoke remains environment-gated.

## Operator Classes

- Ephemeral activation additive, projection/removal, and low-rank activation operators remain covered by synthetic probes.
- Toy KV-cache surgery is covered by copied-cache mutation, attention/key diagnostics, and exact rollback.
- Removable adapter behavior is covered by a LoRA dry-run that never merges, saves, or mutates base weights.
- Proof-state operators remain synthetic and auditable.
- Real-model activation hooks are optional, local-only, inference/no-grad, and rejected without per-case evidence.

## Rejection Coverage

The central packet policy rejects:

- persistent packets;
- network/download flags and `local_files_only: false`;
- missing rollback, audit, or verifier evidence;
- global or invalid target shapes;
- real-model packets without hook cleanup, stable weight fingerprints, per-case target/off-target evidence, or forbidden-effect evidence.

`adversarial_packet_fuzz_probe` exercises representative malformed and forbidden packet families and requires explicit rejection reasons.

## Public Commands

```bash
python -m css_probes.cli run-all --out reports/css_probe_report.json
python -m css_probes.cli packet validate --in reports/css_probe_report.json
python -m css_probes.cli packet render --in reports/css_probe_report.json --out reports/css_probe_report.packet_cards.md
python -m css_probes.cli certify --in reports/css_probe_report.json --out reports/certificate.json
python -m css_probes.cli aether roundtrip --in reports/css_probe_report.json --out reports/aether_roundtrip.json
python -m css_probes.cli real list-adapters
```

Optional local-only real-model commands:

```bash
python -m css_probes.cli real activation-surgery --backend huggingface --model /path/to/local/model --prompt-suite examples/prompt_suite_harmless.json --layer 0 --stream residual --out reports/real_activation_surgery.json
python -m css_probes.cli real envelope-audit --backend huggingface --model /path/to/local/model --prompt-suite examples/prompt_suite_harmless.json --layer 0 --stream residual --out reports/real_envelope.json
```

## Boundary

This is not production semantic surgery. The implementation does not permit persistent model edits, downloads by default, optimizer steps, `save_pretrained`, hidden side effects, verifier threshold mutation, or deployment paths.
