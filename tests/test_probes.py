from css_probes.probes import PROBE_NAMES, load_probe


def test_all_probes_accept_default_seed():
    failed = []
    for name in PROBE_NAMES:
        result = load_probe(name)(seed=0)
        if not result.accepted:
            failed.append((name, result.warnings, result.metrics))
    assert not failed
