import numpy as np

from css_probes.metrics import cosine_drift, norm_drift, spectral_radius, spectral_norm


def test_norm_and_cosine_drift_identity():
    x = np.eye(4)
    metrics = {**norm_drift(x, x), **cosine_drift(x, x)}
    assert metrics["norm_delta_max"] == 0.0
    assert metrics["cosine_drift_min"] > 0.999999


def test_spectral_metrics_diagonal():
    a = np.diag([1.0, 2.0, -3.0])
    assert spectral_radius(a) == 3.0
    assert spectral_norm(a) == 3.0
