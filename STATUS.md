# Status

First build stood up on 2026-06-27.

Validated surface:

- editable package install
- `python -m css_probes.cli list`
- `python -m css_probes.cli run-all --out reports/css_probe_report.json`
- `pytest -q`

Current result:

- 11 synthetic probes accepted
- Semantic Surgery Packets emitted for every probe
- suite certificate covers Levels 1-6
- spec-shaped JSON report emitted
- markdown operator-card sidecar emitted
- packet schema, Phase 0 rejection, and CLI entrypoints covered by tests

Controlled real-model adapter phase:

- optional Hugging Face and TransformerLens backend scaffolds added
- real-model CLI uses local-only ephemeral hooks
- missing backend/model failures do not relax packet/certificate gates
- optional smoke tests are skipped unless `CSS_HF_MODEL_PATH` or `CSS_TL_MODEL_PATH` is configured
