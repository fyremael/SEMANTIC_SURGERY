# Real-Model Envelope Assessment

## Spec Review

- The governing rule remains: typed packet, bounded intervention, behavior check, rollback check, and human-auditable report.
- The real-model phase remains optional and local-only. No downloads, training, optimizer state, `save_pretrained`, persistent weight edits, or production deployment paths are used.
- The current certified real-model work reaches Levels 1, 2, 3, and 6 for this local model. It does not yet claim causal Level 4, spectral Level 5 on real transformer dynamics, or cross-model Level 7.

## Progress

- Synthetic Phase 0 suite remains the baseline certificate path.
- Hugging Face real-model adapter is functional on a local cached Pythia-70M assembly.
- TransformerLens remains unavailable in this environment, so that backend is not yet smoke-tested locally.
- Prior single-prompt and multi-prompt Paris steering packets were accepted with clean rollback and unchanged weight fingerprints.

## Envelope Push

This run tightened the audit by adding forbidden Paris-leakage checks. The vector was derived under no-grad math from final-stream log-prob directions, with three simultaneous aims:

- improve France prompts whose target token is ` Paris`;
- preserve correct off-target answers such as ` Berlin`, ` Madrid`, ` Rome`, ` Tokyo`, ` 4`, and ` cold`;
- avoid raising ` Paris` on non-France capital prompts beyond the leakage threshold.

## Result

- Official certificate accepted: `True`
- Strict envelope audit: `failed`
- Selected alpha: `0.8`
- Mean target token log-prob delta: `0.291015625`
- Minimum target-case delta: `-0.1171875`
- Off-target degradation: `0.0`
- Max per-case off-target degradation: `0.1875`
- Max forbidden Paris leakage: `0.421875`
- Norm delta max: `0.8055925369262695`
- Cosine drift min: `0.9999971389770508`
- Rollback residue: `0.0`
- Weight fingerprint changed: `False`
- Hook cleanup: `True`

## Interpretation

The envelope-pushed run found the current boundary. The official packet/certificate gate accepted the aggregate behavior, but the stricter per-case audit rejected the result. The same final-stream vector could not simultaneously maximize France/Paris uplift, preserve every individual guard answer, and suppress Paris leakage on non-France capital prompts. This is exactly the kind of blast-radius finding the certification protocol is meant to expose.

The remaining limitation is important: this is still a final-stream token-level intervention on one local checkpoint. It is not production semantic surgery and does not prove cross-model generalization or deep causal locality.

## Artifacts

- Prompt suite: `reports/real_envelope_prompt_suite.json`
- Forbidden suite: `reports/real_envelope_forbidden_paris_suite.json`
- Vector: `reports/real_envelope_vector_constrained.json`
- Sweep: `reports/real_envelope_sweep.json`
- Certified report: `reports/real_envelope_certified_report.json`
- Visual: `reports/real_envelope_summary.svg`
