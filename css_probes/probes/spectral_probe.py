from __future__ import annotations

import numpy as np

from css_probes.core import ProbeResult, status_from_acceptance
from css_probes.metrics import non_normality_fro, spectral_norm, spectral_radius, transient_growth_proxy
from css_probes.operators import LowRankOperator
from css_probes.synthetic import rng


def run(seed: int = 0, dim: int = 24, rank: int = 2, alpha: float = 0.06) -> ProbeResult:
    gen = rng(seed)
    u = gen.normal(size=(dim, rank)) / np.sqrt(dim)
    v = gen.normal(size=(dim, rank)) / np.sqrt(dim)
    op = LowRankOperator(u=u, v=v, alpha=alpha)
    matrix = op.matrix()
    metrics = {"spectral_radius": spectral_radius(matrix), "spectral_norm": spectral_norm(matrix), "non_normality_fro": non_normality_fro(matrix), "transient_growth_proxy": transient_growth_proxy(matrix, max_power=6)}
    thresholds = {"spectral_radius_max": 1.10, "spectral_norm_max": 1.15, "transient_growth_max": 1.70}
    warnings: list[str] = []
    accepted = metrics["spectral_radius"] <= thresholds["spectral_radius_max"] and metrics["spectral_norm"] <= thresholds["spectral_norm_max"] and metrics["transient_growth_proxy"] <= thresholds["transient_growth_max"]
    if not accepted:
        warnings.append("spectral_threshold_failed")
    return ProbeResult(name="spectral_radius_probe", status=status_from_acceptance(accepted, warnings), seed=seed, metrics=metrics, thresholds=thresholds, accepted=accepted, warnings=warnings, operator=op.metadata())
