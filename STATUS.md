# Status

First build stood up on 2026-06-27. Full controlled spec coverage was added on 2026-06-28.

Validated surface:

- editable package install
- `python -m css_probes.cli list`
- `python -m css_probes.cli run-all --out reports/css_probe_report.json`
- `python -m css_probes.cli packet validate --in reports/css_probe_report.json`
- `python -m css_probes.cli certify --in reports/css_probe_report.json --out reports/certificate.json`
- `python -m css_probes.cli aether roundtrip --in reports/css_probe_report.json --out reports/aether_roundtrip.json`
- `pytest -q`

Current result:

- 15 synthetic/offline probes accepted
- Semantic Surgery Packets emitted for every probe
- suite certificate covers Levels 1-7
- spec-shaped JSON report emitted
- markdown operator-card sidecar emitted
- packet schema, central policy rejection, AETHER round-trip, and CLI entrypoints covered by tests

Expanded coverage:

- toy KV-cache surgery probe
- removable LoRA adapter dry-run probe
- deterministic cross-checkpoint transfer probe for Level 7
- adversarial packet fuzzing probe
- packet validation, packet rendering, certification, and AETHER CLI commands

Controlled real-model adapter phase:

- optional Hugging Face and TransformerLens backend scaffolds added
- real-model CLI uses local-only ephemeral hooks
- real-model gate now requires per-case target, off-target, and forbidden-effect evidence
- missing backend/model failures do not relax packet/certificate gates
- optional smoke tests are skipped unless `CSS_HF_MODEL_PATH` or `CSS_TL_MODEL_PATH` is configured
