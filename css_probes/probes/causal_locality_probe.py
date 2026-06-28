from __future__ import annotations

import numpy as np

from css_probes.core import ProbeResult, status_from_acceptance
from css_probes.metrics import binary_margin_score, normalize
from css_probes.operators import ActivationAdditiveOperator
from css_probes.synthetic import rng


def run(seed: int = 0, layers: int = 6, n_samples: int = 128, dim: int = 48, alpha: float = 0.4) -> ProbeResult:
    gen = rng(seed)
    true_layer = 3
    target = normalize(gen.normal(size=dim))
    states = gen.normal(size=(layers, n_samples, dim))
    readouts = np.stack([normalize(gen.normal(size=dim)) for _ in range(layers)])
    readouts[true_layer] = target
    op = ActivationAdditiveOperator(vector=target, alpha=alpha)
    deltas = []
    for layer in range(layers):
        before = binary_margin_score(states[layer], readouts[layer])
        after = binary_margin_score(op.apply(states[layer]), readouts[layer])
        deltas.append(after - before)
    deltas_arr = np.array(deltas)
    best_layer = int(np.argmax(deltas_arr))
    target_delta = float(deltas_arr[true_layer])
    off_layer_max = float(np.max(np.delete(np.abs(deltas_arr), true_layer)))
    locality_ratio = float(target_delta / (off_layer_max + 1e-12))
    metrics = {"best_layer": best_layer, "true_layer": true_layer, "target_delta": target_delta, "off_layer_max_abs_delta": off_layer_max, "locality_ratio": locality_ratio}
    metrics["target_margin_delta"] = target_delta
    metrics["causal_locality_score"] = locality_ratio
    thresholds = {"causal_locality_score_min": 3.0, "target_margin_delta_min": 0.25}
    warnings: list[str] = []
    accepted = True
    if best_layer != true_layer:
        accepted = False; warnings.append("best_layer_not_declared_layer")
    if locality_ratio < thresholds["causal_locality_score_min"]:
        accepted = False; warnings.append("locality_ratio_below_min")
    if target_delta < thresholds["target_margin_delta_min"]:
        accepted = False; warnings.append("target_delta_below_min")
    return ProbeResult(name="causal_locality_probe", status=status_from_acceptance(accepted, warnings), seed=seed, metrics=metrics, thresholds=thresholds, accepted=accepted, warnings=warnings, operator={**op.metadata(), "declared_layer": true_layer})
