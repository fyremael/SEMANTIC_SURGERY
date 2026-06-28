from __future__ import annotations

import numpy as np

from css_probes.core import PHASE0_DEFAULT_THRESHOLDS, ProbeResult, status_from_acceptance
from css_probes.metrics import normalize
from css_probes.operators import ActivationAdditiveOperator, MutableStateBox, applied_temporarily
from css_probes.synthetic import rng, synthetic_state_batch


def run(seed: int = 0, dim: int = 64, n_samples: int = 32) -> ProbeResult:
    gen = rng(seed)
    before = synthetic_state_batch(seed + 1, n=n_samples, dim=dim)
    box = MutableStateBox(state=before.copy())
    op = ActivationAdditiveOperator(vector=normalize(gen.normal(size=dim)), alpha=0.25)
    with applied_temporarily(box, op):
        inside_delta = float(np.max(np.abs(box.state - before)))
    rollback_residue = float(np.max(np.abs(box.state - before)))
    metrics = {"inside_delta": inside_delta, "rollback_residue": rollback_residue}
    thresholds = {
        "inside_delta_min": 0.05,
        "rollback_residue_max": PHASE0_DEFAULT_THRESHOLDS["rollback_residue_max"],
    }
    warnings: list[str] = []
    accepted = True
    if metrics["inside_delta"] < thresholds["inside_delta_min"]:
        accepted = False; warnings.append("operator_did_not_apply_inside_context")
    if metrics["rollback_residue"] > thresholds["rollback_residue_max"]:
        accepted = False; warnings.append("rollback_residue_exceeded")
    return ProbeResult(name="rollback_probe", status=status_from_acceptance(accepted, warnings), seed=seed, metrics=metrics, thresholds=thresholds, accepted=accepted, warnings=warnings, operator=op.metadata())
