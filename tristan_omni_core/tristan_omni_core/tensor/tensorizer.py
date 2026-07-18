from __future__ import annotations

METRICS = ['presence', 'readme', 'tests', 'reports', 'risk_inverse', 'score_omega', 'capability_density']


def build_capability_axis(modules):
    return sorted({c for m in modules for c in m.capabilities})


def tensorize(modules, probes):
    probe_map = {p.module_id: p for p in probes}
    caps = build_capability_axis(modules)
    tensor = []
    for m in modules:
        p = probe_map.get(m.id)
        checks = p.checks if p else {}
        metric_values = [
            1.0 if checks.get('exists') else 0.0,
            1.0 if checks.get('has_readme') else 0.0,
            1.0 if checks.get('has_tests') else 0.0,
            1.0 if checks.get('has_reports') else 0.0,
            max(0.0, 1.0 - m.risk),
            m.score_omega(),
            len(m.capabilities) / max(1, len(caps)),
        ]
        tensor.append([[(1.0 if cap in m.capabilities else 0.0) * mv for mv in metric_values] for cap in caps])
    return {'shape': [len(modules), len(caps), len(METRICS)], 'module_axis': [m.id for m in modules], 'capability_axis': caps, 'metric_axis': METRICS, 'tensor': tensor}


def summarize_tensor(packet):
    caps = packet['capability_axis']
    totals = {cap: 0.0 for cap in caps}
    for module_rows in packet['tensor']:
        for ci, values in enumerate(module_rows):
            totals[caps[ci]] += sum(values)
    return {'shape': packet['shape'], 'top_capabilities': sorted(totals.items(), key=lambda x: x[1], reverse=True)[:16]}
