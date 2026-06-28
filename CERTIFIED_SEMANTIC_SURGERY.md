# Certified Semantic Surgery

## 1. Thesis and Threat Model

### 1.1 Thesis

Certified Semantic Surgery studies communication by **typed, bounded, verifiable operators** rather than by text alone.

A natural-language message describes a desired state change. A semantic-surgery packet proposes an explicit state-transforming map:

```math
\mathcal{O}: \mathcal{S}_{before} \rightarrow \mathcal{S}_{after}
```

where `S` may be an activation stream, KV-cache state, proof state, routing state, policy state, memory state, or latent world-model state.

The working hypothesis is:

> For some model-to-model communication tasks, a certified operator packet can induce the intended receiver state more compactly and reliably than a natural-language message, provided the operator is local, bounded, auditable, and rejectable.

This is not a license for arbitrary model editing. It is a disciplined protocol for small, reversible interventions with explicit contracts.

### 1.2 Communication Primitive

A packet is accepted only if it satisfies:

```math
\text{Accept}(\mathcal{O}) = 1[\text{typecheck} \wedge \text{bounds} \wedge \text{behavior} \wedge \text{rollback} \wedge \text{audit}]
```

The unit of communication is not a string but a proposed transformation.

Text remains the human audit and governance interface. Operators are the candidate machine-native transport layer.

### 1.3 Threat Model

The threat model assumes a sender may be mistaken, malicious, overfit, architecture-specific, or underspecified.

Threats include:

1. **Semantic misfire**: the operator induces an unintended belief, plan, or behavior.
2. **Blast radius**: the intended effect occurs but unrelated behavior degrades.
3. **Hidden capability shift**: the operator increases an unrequested capability or affordance.
4. **Non-normal amplification**: small norm changes cause large transient effects.
5. **Persistence hazard**: changes remain after supposed rollback.
6. **Architecture superstition**: the operator works only on one checkpoint or seed.
7. **Audit bypass**: latent transfer cannot be rendered into a meaningful human report.
8. **Trojan packet**: the operator contains dormant behavior triggered by narrow conditions.
9. **State contamination**: the operator corrupts cache, memory, router state, or proof state.
10. **Self-modification loop**: models exchange operators that recursively relax their own constraints.

### 1.4 Safety Boundary

Phase 0 explicitly forbids:

- autonomous persistent weight edits;
- hidden model-to-model latent channels without reports;
- operators that cannot be rolled back or sandboxed;
- self-modifying operator generators;
- capability-improving patches without off-target regression checks;
- deployment on production models.

The first implementation is a synthetic probe suite. It certifies the instrumentation, not any real-world semantic claim.

---

## 2. Operator Packet Schema

### 2.1 Packet Object

A Semantic Surgery Packet is:

```math
\mathsf{SSP} = (id, type, target, preconditions, operator, bounds, tests, intended\_effect, forbidden\_effects, rollback, audit)
```

The schema is intentionally conservative.

```json
{
  "packet_id": "ssp_001_activation_patch",
  "version": "0.1.0",
  "operator_type": "activation_additive",
  "persistence": "ephemeral",
  "target": {
    "model_family": "synthetic-linear-receiver",
    "layer": 0,
    "stream": "residual",
    "shape": [64]
  },
  "preconditions": {
    "allowed_tasks": ["synthetic_target_classification"],
    "activation_norm_min": 0.0,
    "activation_norm_max": 100.0,
    "requires_sandbox": true
  },
  "operator": {
    "form": "h_prime = h + alpha * v",
    "rank": 1,
    "parameters_ref": "inline_or_hash",
    "parameter_hash": "sha256:..."
  },
  "bounds": {
    "delta_norm_max": 1.0,
    "cosine_drift_min": 0.98,
    "spectral_radius_max": 1.05,
    "sigma_max": 1.10,
    "pseudospectral_proxy_max": 5.0
  },
  "intended_effect": {
    "description": "Increase target-task margin without degrading off-target tasks.",
    "target_metric": "target_success_delta",
    "minimum_delta": 0.05
  },
  "forbidden_effects": [
    "off_target_degradation_gt_0.02",
    "cosine_drift_below_0.98",
    "rollback_residue_gt_1e-9"
  ],
  "verifier": {
    "unit_tests": ["norm_drift_probe", "rollback_probe"],
    "behavioral_tests": ["off_target_regression_probe"],
    "spectral_tests": ["spectral_radius_probe", "pseudospectrum_probe"]
  },
  "audit": {
    "provenance": "synthetic-fixture",
    "human_rendering": "Small additive activation patch derived from contrastive mean difference.",
    "accepted": false,
    "rejection_reasons": []
  }
}
```

### 2.2 Required Fields

Every packet must specify:

- unique packet id;
- operator class;
- persistence class: `ephemeral`, `session`, `adapter`, or `persistent`;
- target state type;
- preconditions;
- postconditions;
- mathematical bounds;
- rollback plan;
- audit rendering;
- verifier list;
- acceptance decision.

### 2.3 Packet Lifecycle

1. **Propose**: construct candidate operator.
2. **Typecheck**: verify target state and shape.
3. **Sandbox**: apply only to copied state or context manager.
4. **Measure**: collect norm, spectral, behavioral, causal, and rollback metrics.
5. **Accept/reject**: emit certificate with reasons.
6. **Report**: render machine JSON and human markdown.

---

## 3. Certification Ladder

### Level 0: Descriptive

The operator has a verbal claim.

This level is not sufficient for application.

### Level 1: Typed

The operator declares its exact domain, codomain, target layer, stream, and shape.

```math
\mathcal{O}: H_{\ell,resid} \rightarrow H_{\ell,resid}
```

### Level 2: Bounded

The operator satisfies local numerical constraints:

```math
\|\mathcal{O}h - h\| \leq \delta
```

```math
\cos(h, \mathcal{O}h) \geq \tau
```

### Level 3: Behavioral

Target behavior improves and off-target behavior remains within tolerance.

### Level 4: Causal

Ablation, localization, and counterfactual tests support the claimed causal mechanism.

### Level 5: Spectral / Dynamical

The operator does not introduce unstable dynamics:

```math
\rho(\mathcal{O}) \leq 1 + \epsilon
```

and its pseudospectral proxy is below threshold.

### Level 6: Reversible / Rollback-Safe

Rollback leaves no measurable residue:

```math
\|state_{restored} - state_{original}\| \leq \epsilon
```

### Level 7: Cross-Model Validated

The operator or its construction rule generalizes across seeds, checkpoints, or related architectures.

Phase 0 only targets Levels 1-6 on synthetic probes.

---

## 4. Accepted Operator Classes

### 4.1 Ephemeral Activation Additive Operators

```math
h' = h + \alpha v
```

Accepted for first fixtures because they are local, inspectable, and easy to roll back.

### 4.2 Projection / Removal Operators

```math
h' = (I - UU^T)h
```

Useful for removing hypothesized features or testing causal dependence.

### 4.3 Low-Rank Activation Operators

```math
h' = h + U V^T h
```

Expressive enough to model small subspace edits while remaining measurable.

### 4.4 Sandboxed KV-Cache Operators

Permitted only in non-persistent contexts with attention-pattern diagnostics.

### 4.5 Router / Policy Bias Operators

```math
r' = softmax(log r + b)
```

Accepted for toy MoE and no-regret routing experiments with entropy and load-balance checks.

### 4.6 Proof-State Operators

Verifier-mediated symbolic transitions are accepted when an external checker validates the transition.

### 4.7 Removable Adapter Operators

LoRA-style modular deltas may be tested after ephemeral operators pass. Persistent merge is forbidden in Phase 0.

---

## 5. Rejected Operator Classes

Rejected in Phase 0:

1. **Persistent full-weight edits** without reversible adapter boundaries.
2. **Opaque binary operators** without schema, provenance, or human rendering.
3. **Self-modifying operators** that alter verifier or acceptance thresholds.
4. **Unbounded activation injections** with no norm or cosine drift limits.
5. **Global operators** targeting multiple layers without locality tests.
6. **Operators with hidden network calls** or runtime side effects.
7. **Operators that degrade off-target behavior beyond threshold**.
8. **Operators whose only evidence is a natural-language description**.
9. **Operators that cannot be serialized, hashed, and audited**.
10. **Operators that pass target tests but fail rollback**.

---

## 6. Fixture 001: Activation Surgery

### Goal

Show that a small activation patch can induce a target behavior while preserving off-target behavior and rollback.

### Synthetic Setup

Generate activations `X` in `R^d`, labels from a target direction `w_target`, and off-target labels from `w_off`. Build a contrastive vector:

```math
v = E[h | y=1] - E[h | y=0]
```

Apply:

```math
h' = h + \alpha \hat{v}
```

### Acceptance

Accept if:

- target success delta exceeds threshold;
- mean cosine drift remains above threshold;
- max norm drift remains below threshold;
- off-target degradation is bounded;
- rollback residue is zero or near-zero.

### Expected Report Fields

- target margin delta;
- off-target margin delta;
- norm drift mean/max;
- cosine drift mean/min;
- rollback residue;
- accepted flag.

---

## 7. Fixture 002: Operator vs Text Transfer

### Goal

Compare text-like symbolic transfer against operator-valued transfer.

### Synthetic Text Baseline

A text message is modeled as a noisy symbolic instruction that selects a direction estimate with limited precision.

### Operator Transfer

The operator packet transmits a low-rank or additive transformation directly.

### Metrics

```math
efficiency = \frac{\Delta target\_success}{bits\_transmitted}
```

Compare:

1. no message;
2. text-like instruction;
3. latent vector;
4. additive operator;
5. low-rank operator;
6. operator plus certificate.

---

## 8. Fixture 003: Koopman Dynamics Message

### Goal

Test whether a sender can transmit a local evolution operator rather than raw observations.

Given trajectories:

```math
x_{t+1} \approx A x_t
```

Estimate:

```math
\hat{A} = X_{next} X_{now}^{+}
```

Then send `A_hat` as a dynamics operator.

### Acceptance

Accept if:

- one-step prediction error improves over baseline;
- spectral radius remains bounded;
- rollout does not explode over the configured horizon;
- pseudospectral proxy remains below threshold.

---

## 9. Fixture 004: Proof-State Surgery

### Goal

Implement the safest symbolic version: a transition over proof states accepted only by a checker.

A proof state is represented as a tiny stack machine. A proof operator proposes a transition such as:

```text
Goal: prove A -> A
Operator: intro; exact assumption
```

### Acceptance

The checker must validate that the final state is closed.

This fixture establishes the pattern:

> The semantic intervention is accepted by a verifier, not by rhetorical plausibility.

---

## 10. Metrics

### Core Metrics

- `target_success_delta`
- `target_margin_delta`
- `off_target_delta`
- `off_target_degradation_max`
- `norm_delta_mean`
- `norm_delta_max`
- `cosine_drift_mean`
- `cosine_drift_min`
- `spectral_radius`
- `sigma_max`
- `pseudospectral_proxy`
- `causal_locality_score`
- `rollback_residue`
- `bits_transmitted`
- `efficiency_delta_per_bit`
- `accepted`

### Acceptance Defaults

```yaml
thresholds:
  target_success_delta_min: 0.05
  off_target_degradation_max: 0.02
  norm_delta_max: 1.0
  cosine_drift_min: 0.98
  spectral_radius_max: 1.05
  sigma_max: 1.10
  pseudospectral_proxy_max: 5.0
  rollback_residue_max: 1.0e-9
```

---

## 11. Report Format

### 11.1 JSON Report

```json
{
  "suite": "css-probes",
  "version": "0.1.0",
  "accepted": true,
  "summary": {
    "num_probes": 11,
    "num_accepted": 11,
    "num_rejected": 0
  },
  "probes": [
    {
      "name": "activation_patch_probe",
      "accepted": true,
      "metrics": {},
      "thresholds": {},
      "notes": []
    }
  ]
}
```

### 11.2 Operator Card

Every probe should emit an operator card:

```text
Operator name:
Target state:
Operator form:
Persistence:
Preconditions:
Intended effect:
Forbidden effects:
Norm bounds:
Spectral bounds:
Behavioral result:
Rollback result:
Accepted / rejected:
Rejection reasons:
Human rendering:
```

---

## 12. Codex Implementation Brief

### 12.1 Objective

Build a runnable repository that implements a first-pass probe suite for Certified Semantic Surgery.

The implementation must be dependency-light, deterministic, and testable on CPU.

### 12.2 Required Tree

```text
SEMANTIC_SURGERY/
  CERTIFIED_SEMANTIC_SURGERY.md
  README.md
  pyproject.toml
  Makefile
  css_probes/
    __init__.py
    cli.py
    core.py
    synthetic.py
    operators.py
    probes.py
    report.py
  css-probes/
    README.md
  tests/
    test_probes.py
  .github/workflows/ci.yml
```

### 12.3 CLI Contract

```bash
python -m css_probes.cli run-all --out reports/css_probe_report.json
python -m css_probes.cli run activation_patch_probe
python -m css_probes.cli list
```

### 12.4 Probe Contract

Every probe returns:

```python
ProbeResult(
    name: str,
    accepted: bool,
    metrics: dict[str, float | int | str | bool],
    thresholds: dict[str, float | int | str | bool],
    notes: list[str]
)
```

### 12.5 Implementation Constraints

- Use Python 3.10+.
- Use NumPy only for core probes.
- No network calls.
- No model downloads.
- Deterministic RNG seeds.
- CI must run `pytest -q` and the full CLI suite.
- Reports must be JSON-serializable.

### 12.6 Stretch Targets

After Phase 0 passes:

1. add TransformerLens activation hooks;
2. add Hugging Face hook backend;
3. add toy KV-cache surgery;
4. add LoRA adapter packet dry-run;
5. add cross-checkpoint transfer tests;
6. add markdown operator-card rendering;
7. add adversarial packet fuzzing;
8. add AETHER tuple serialization.

---

## Project Definition

Certified Semantic Surgery is the study and engineering of typed, bounded, auditable operators that transform receiver states more directly than language while preserving rollback, locality, behavioral safety, and human-verifiable reports.

Words describe. Operators transform. Certificates decide whether transformation is allowed.
