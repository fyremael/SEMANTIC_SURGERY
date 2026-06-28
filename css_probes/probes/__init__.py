"""Probe registry."""

from __future__ import annotations

from importlib import import_module
from typing import Callable

PROBE_NAMES = [
    "activation_patch_probe",
    "low_rank_operator_probe",
    "norm_drift_probe",
    "spectral_radius_probe",
    "pseudospectrum_probe",
    "causal_locality_probe",
    "off_target_regression_probe",
    "rollback_probe",
    "operator_vs_text_benchmark",
    "koopman_dynamics_message_probe",
    "proof_state_surgery_probe",
]


def load_probe(name: str) -> Callable[..., object]:
    if name not in PROBE_NAMES:
        raise KeyError(f"unknown probe: {name}")
    module = import_module(f"css_probes.probes.{name}")
    return module.run
