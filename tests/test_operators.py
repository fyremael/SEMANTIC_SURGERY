import numpy as np

from css_probes.metrics import normalize
from css_probes.operators import ActivationAdditiveOperator, LowRankOperator, MutableStateBox, applied_temporarily


def test_additive_operator_inverse():
    x = np.ones((3, 5))
    v = normalize(np.arange(5, dtype=float) + 1.0)
    op = ActivationAdditiveOperator(v, alpha=0.25)
    restored = op.invert(op.apply(x))
    assert np.max(np.abs(restored - x)) < 1e-12


def test_low_rank_operator_inverse():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(4, 8))
    u = rng.normal(size=(8, 2)) / 10
    v = rng.normal(size=(8, 2)) / 10
    op = LowRankOperator(u, v, alpha=0.1)
    restored = op.invert(op.apply(x))
    assert np.max(np.abs(restored - x)) < 1e-10


def test_context_rollback():
    x = np.zeros((2, 3))
    box = MutableStateBox(x.copy())
    op = ActivationAdditiveOperator(np.ones(3), alpha=1.0)
    with applied_temporarily(box, op):
        assert np.max(box.state) == 1.0
    assert np.max(np.abs(box.state - x)) == 0.0
