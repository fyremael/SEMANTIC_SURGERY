from __future__ import annotations

import numpy as np

from css_probes.core import PHASE0_DEFAULT_THRESHOLDS, ProbeResult, status_from_acceptance
from css_probes.metrics import binary_margin_score, cosine_drift, norm_drift, normalize, spectral_radius, spectral_norm
from css_probes.operators import LowRankOperator
from css_probes.synthetic import paired_target_offtarget, rng, synthetic_state_batch


def run(seed: int = 0, dim: int = 64, n_samples: int = 256, rank: int = 3, alpha: float = 0.04) -> ProbeResult:
    gen = rng(seed)
    target, off_target = paired_target_offtarget(seed + 1, dim=dim, orthogonalize=True)
    u = np.zeros((dim, rank))
    v = np.zeros((dim, rank))
    u[:, 0] = target
    v[:, 0] = target
    for j in range(1, rank):
        candidate = gen.normal(size=dim)
        candidate = candidate - np.dot(candidate, target) * target
        u[:, j] = normalize(candidate)
        v[:, j] = normalize(gen.normal(size=dim))
    op = LowRankOperator(u=u, v=v, alpha=alpha)
    states = synthetic_state_batch(seed + 2, n=n_samples, dim=dim)
    before_target = binary_margin_score(states, target)
    before_off = binary_margin_score(states, off_target)
    after = op.apply(states)
    restored = op.invert(after)
    matrix = op.matrix()
    metrics = {
        "target_margin_delta": float(binary_margin_score(after, target) - before_target),
        "off_target_delta": float(binary_margin_score(after, off_target) - before_off),
        "rollback_residue": float(np.max(np.abs(restored - states))),
        "spectral_radius": spectral_radius(matrix),
        "sigma_max": spectral_norm(matrix),
        **norm_drift(states, after),
        **cosine_drift(states, after),
    }
    thresholds = {
        "spectral_radius_max": PHASE0_DEFAULT_THRESHOLDS["spectral_radius_max"],
        "sigma_max": PHASE0_DEFAULT_THRESHOLDS["sigma_max"],
        "cosine_drift_min": PHASE0_DEFAULT_THRESHOLDS["cosine_drift_min"],
        "rollback_residue_max": PHASE0_DEFAULT_THRESHOLDS["rollback_residue_max"],
    }
    warnings: list[str] = []
    accepted = True
    if metrics["spectral_radius"] > thresholds["spectral_radius_max"]:
        accepted = False; warnings.append("spectral_radius_exceeded")
    if metrics["sigma_max"] > thresholds["sigma_max"]:
        accepted = False; warnings.append("sigma_max_exceeded")
    if metrics["cosine_drift_min"] < thresholds["cosine_drift_min"]:
        accepted = False; warnings.append("cosine_drift_too_large")
    if metrics["rollback_residue"] > thresholds["rollback_residue_max"]:
        accepted = False; warnings.append("rollback_residue_exceeded")
    return ProbeResult(name="low_rank_operator_probe", status=status_from_acceptance(accepted, warnings), seed=seed, metrics=metrics, thresholds=thresholds, accepted=accepted, warnings=warnings, operator=op.metadata())
