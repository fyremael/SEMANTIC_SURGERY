from __future__ import annotations

import numpy as np

from css_probes.core import PHASE0_DEFAULT_THRESHOLDS, ProbeResult, status_from_acceptance
from css_probes.metrics import pseudospectral_growth_proxy, spectral_norm, spectral_radius
from css_probes.operators import array_sha256
from css_probes.synthetic import rng


def run(seed: int = 0, n_samples: int = 512, horizon: int = 16) -> ProbeResult:
    gen = rng(seed)
    x0 = gen.normal(scale=0.5, size=(n_samples, 2))
    true_a = np.array([[0.875, -0.175], [0.175, 0.875]])
    x1 = x0 @ true_a.T + 0.02 * np.column_stack([x0[:, 0] * x0[:, 1], -x0[:, 0] ** 2])
    a_hat, *_ = np.linalg.lstsq(x0, x1, rcond=None)
    pred_x1 = x0 @ a_hat
    persistence_mse = float(np.mean((x0 - x1) ** 2))
    model_mse = float(np.mean((pred_x1 - x1) ** 2))
    rollout = x0[:16].copy()
    rollout_max_norm = 0.0
    for _ in range(horizon):
        rollout = rollout @ a_hat
        rollout_max_norm = max(rollout_max_norm, float(np.max(np.linalg.norm(rollout, axis=1))))
    metrics = {
        "persistence_mse": persistence_mse,
        "koopman_mse": model_mse,
        "one_step_mse_improvement": persistence_mse - model_mse,
        "spectral_radius": spectral_radius(a_hat),
        "sigma_max": spectral_norm(a_hat),
        "pseudospectral_proxy": pseudospectral_growth_proxy(a_hat, grid_radius=1.4, grid_size=9),
        "rollout_horizon": horizon,
        "rollout_max_norm": rollout_max_norm,
        "rollout_exploded": bool(rollout_max_norm > 5.0),
    }
    thresholds = {
        "one_step_mse_improvement_min": 0.005,
        "spectral_radius_max": PHASE0_DEFAULT_THRESHOLDS["spectral_radius_max"],
        "sigma_max": PHASE0_DEFAULT_THRESHOLDS["sigma_max"],
        "pseudospectral_proxy_max": PHASE0_DEFAULT_THRESHOLDS["pseudospectral_proxy_max"],
        "rollout_max_norm_max": 5.0,
    }
    accepted = (
        metrics["one_step_mse_improvement"] >= thresholds["one_step_mse_improvement_min"]
        and metrics["spectral_radius"] <= thresholds["spectral_radius_max"]
        and metrics["sigma_max"] <= thresholds["sigma_max"]
        and metrics["pseudospectral_proxy"] <= thresholds["pseudospectral_proxy_max"]
        and metrics["rollout_max_norm"] <= thresholds["rollout_max_norm_max"]
    )
    warnings: list[str] = [] if accepted else ["dynamics_threshold_failed"]
    return ProbeResult(
        name="koopman_dynamics_message_probe",
        status=status_from_acceptance(accepted, warnings),
        seed=seed,
        metrics=metrics,
        thresholds=thresholds,
        accepted=accepted,
        warnings=warnings,
        operator={
            "operator_type": "local_dynamics",
            "persistence": "removable",
            "form": "x_next = x @ A_hat",
            "state_type": "dynamics_state",
            "stream": "trajectory",
            "target_shape": [2],
            "parameters_ref": "inline",
            "parameter_hash": array_sha256(a_hat),
        },
    )
