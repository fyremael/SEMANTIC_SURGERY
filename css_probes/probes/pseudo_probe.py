from __future__ import annotations

import numpy as np

from css_probes.core import PHASE0_DEFAULT_THRESHOLDS, ProbeResult, status_from_acceptance
from css_probes.metrics import non_normality_fro, pseudospectral_growth_proxy, spectral_norm, spectral_radius, transient_growth_proxy


def run(seed: int = 0, dim: int = 12) -> ProbeResult:
    block = np.array([[0.52, -0.17], [0.17, 0.52]])
    matrix = np.kron(np.eye(dim // 2), block)
    metrics = {
        "spectral_radius": spectral_radius(matrix),
        "sigma_max": spectral_norm(matrix),
        "non_normality_fro": non_normality_fro(matrix),
        "pseudospectral_proxy": pseudospectral_growth_proxy(matrix, grid_radius=1.4, grid_size=9),
        "transient_growth_proxy": transient_growth_proxy(matrix, max_power=8),
    }
    thresholds = {
        "spectral_radius_max": PHASE0_DEFAULT_THRESHOLDS["spectral_radius_max"],
        "sigma_max": PHASE0_DEFAULT_THRESHOLDS["sigma_max"],
        "pseudospectral_proxy_max": PHASE0_DEFAULT_THRESHOLDS["pseudospectral_proxy_max"],
        "transient_growth_proxy_max": 12.0,
    }
    warnings: list[str] = []
    accepted = (
        metrics["spectral_radius"] <= thresholds["spectral_radius_max"]
        and metrics["sigma_max"] <= thresholds["sigma_max"]
        and metrics["pseudospectral_proxy"] <= thresholds["pseudospectral_proxy_max"]
        and metrics["transient_growth_proxy"] <= thresholds["transient_growth_proxy_max"]
    )
    if not accepted:
        warnings.append("pseudo_threshold_failed")
    return ProbeResult(name="pseudospectrum_probe", status=status_from_acceptance(accepted, warnings), seed=seed, metrics=metrics, thresholds=thresholds, accepted=accepted, warnings=warnings, operator={"operator_type": "synthetic_linear_dynamics", "persistence": "ephemeral", "form": "block_rotation_scaling", "state_type": "linear_state", "stream": "state", "target_shape": [dim]})
