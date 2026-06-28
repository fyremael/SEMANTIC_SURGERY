from __future__ import annotations

import numpy as np

from css_probes.core import ProbeResult, status_from_acceptance
from css_probes.metrics import pseudospectral_growth_proxy, spectral_radius
from css_probes.synthetic import rng


def run(seed: int = 0, n_samples: int = 512) -> ProbeResult:
    gen = rng(seed)
    x0 = gen.normal(scale=0.5, size=(n_samples, 2))
    a = np.array([[0.96, 0.18], [-0.12, 0.93]])
    x1 = x0 @ a.T + 0.03 * np.column_stack([x0[:, 0] * x0[:, 1], -x0[:, 0] ** 2])
    phi0 = np.column_stack([x0[:, 0], x0[:, 1], x0[:, 0] ** 2, x0[:, 0] * x0[:, 1], x0[:, 1] ** 2, np.ones(len(x0))])
    phi1 = np.column_stack([x1[:, 0], x1[:, 1], x1[:, 0] ** 2, x1[:, 0] * x1[:, 1], x1[:, 1] ** 2, np.ones(len(x1))])
    k, *_ = np.linalg.lstsq(phi0, phi1, rcond=None)
    pred_phi1 = phi0 @ k
    persistence_mse = float(np.mean((phi0 - phi1) ** 2))
    model_mse = float(np.mean((pred_phi1 - phi1) ** 2))
    metrics = {"persistence_mse": persistence_mse, "koopman_mse": model_mse, "one_step_mse_improvement": persistence_mse - model_mse, "spectral_radius": spectral_radius(k), "pseudospectral_growth_proxy": pseudospectral_growth_proxy(k, grid_radius=1.4, grid_size=7)}
    thresholds = {"one_step_mse_improvement_min": 0.005, "spectral_radius_max": 1.25, "pseudospectral_growth_proxy_max": 1e5}
    accepted = metrics["one_step_mse_improvement"] >= thresholds["one_step_mse_improvement_min"] and metrics["spectral_radius"] <= thresholds["spectral_radius_max"] and metrics["pseudospectral_growth_proxy"] <= thresholds["pseudospectral_growth_proxy_max"]
    warnings: list[str] = [] if accepted else ["dynamics_threshold_failed"]
    return ProbeResult(name="koopman_dynamics_message_probe", status=status_from_acceptance(accepted, warnings), seed=seed, metrics=metrics, thresholds=thresholds, accepted=accepted, warnings=warnings, operator={"operator_type": "local_dynamics", "persistence": "removable"})
