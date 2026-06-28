# Phase 0 Compliance

This build treats `CERTIFIED_SEMANTIC_SURGERY.md` as the governing contract for the controlled, non-persistent research suite. Phase 0 synthetic coverage remains intact, and the current implementation adds controlled full-spec coverage without moving into production or persistent edits.

Implemented contract points:

- Packet schema: every probe report includes an SSP with id, version, operator type, persistence, typed target, preconditions, postconditions, operator form, parameter hash, bounds, rollback plan, verifier lists, intended effect, forbidden effects, audit rendering, and acceptance decision.
- Certification ladder: the suite-level certificate verifies accepted coverage of Levels 1-7. Level 7 is covered by deterministic cross-checkpoint transfer fixtures; optional real-model cross-transfer remains skipped unless local paths are configured.
- Safety boundary: packet verification rejects persistent packets, network/download behavior, missing rollback/audit/verifier evidence, global unbounded operators, and missing real-model per-case evidence.
- Operator auditability: NumPy operator parameters are serialized into deterministic SHA-256 hashes.
- Metrics: reports include canonical names from the spec, including `target_success_delta`, `target_margin_delta`, `off_target_degradation_max`, `sigma_max`, `pseudospectral_proxy`, `causal_locality_score`, `rollback_residue`, `bits_transmitted`, and `efficiency_delta_per_bit`.
- Fixtures: activation surgery, operator-vs-text transfer, Koopman dynamics message, proof-state surgery, toy KV-cache surgery, removable LoRA adapter dry-run, cross-checkpoint transfer, and adversarial packet fuzzing are covered by registered probes.
- Reports: `reports/css_probe_report.json` is machine-readable; `reports/css_probe_report.operator_cards.md` is the human operator-card sidecar.
- Visual presentation: `reports/css_probe_results_presentation.html`, `reports/css_probe_results_summary.svg`, and optional `reports/css_probe_results_summary.png` render the same certificate data for inspection.
- Controlled real-model adapters: optional TransformerLens and Hugging Face adapters use local-only ephemeral hooks, require per-case target/off-target/forbidden evidence, and emit the same packet/certificate shape.

Validation commands:

```bash
python -m pip install -e .[dev]
python -m css_probes.cli run-all --out reports/css_probe_report.json
python -m css_probes.cli packet validate --in reports/css_probe_report.json
python -m css_probes.cli certify --in reports/css_probe_report.json --out reports/certificate.json
python -m css_probes.cli aether roundtrip --in reports/css_probe_report.json --out reports/aether_roundtrip.json
python -m css_probes.cli real list-adapters
python scripts/render_results_presentation.py
pytest -q
```
