from __future__ import annotations

import numpy as np

from css_probes.core import ProbeResult, status_from_acceptance
from css_probes.metrics import non_normality_fro, pseudospectral_growth_proxy, spectral_radius, transient_growth_proxy


def run(seed: int = 0, dim: int = 12, coupling: float = 0.22) -> ProbeResult:
    matrix = 0.92 * np.eye(dim)
    for i in range(dim - 1):
        matrix[i, i + 1] = coupling
    metrics = {"spectral_radius": spectral_radius(matrix), "non_normality_fro": non_normality_fro(matrix), "pseudospectral_growth_proxy": pseudospectral_growth_proxy(matrix, grid_radius=1.4, grid_size=9), "transient_growth_proxy": transient_growth_proxy(matrix, max_power=8)}
    thresholds = {"spectral_radius_max": 1.0, "pseudospectral_growth_proxy_max": 1e6, "transient_growth_proxy_max": 12.0}
    warnings: list[str] = []
    accepted = metrics["spectral_radius"] <= thresholds["spectral_radius_max"] and metrics["pseudospectral_growth_proxy"] <= thresholds["pseudospectral_growth_proxy_max"] and metrics["transient_growth_proxy"] <= thresholds["transient_growth_proxy_max"]
    if not accepted:
        warnings.append("pseudo_threshold_failed")
    return ProbeResult(name="pseudospectrum_probe", status=status_from_acceptance(accepted, warnings), seed=seed, metrics=metrics, thresholds=thresholds, accepted=accepted, warnings=warnings, operator={"operator_type": "synthetic_non_normal_linear", "persistence": "ephemeral"})
