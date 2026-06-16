from __future__ import annotations
import hashlib


def sid(prefix: str, text: str) -> str:
    return prefix + '-' + hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]


def build_hgfm(modules, probes):
    nodes, hyperedges, seen = [], [], set()

    def add(label, kind, payload=None):
        nid = sid('N', kind + ':' + label)
        if nid not in seen:
            seen.add(nid)
            nodes.append({'id': nid, 'label': label, 'kind': kind, 'payload': payload or {}})
        return nid

    module_ids = {}
    for m in modules:
        module_ids[m.id] = add(m.id, 'module', m.to_dict())
        fam = add(m.family, 'family')
        hyperedges.append({'id': sid('H', 'family:' + m.id), 'relation': 'belongs_to_family', 'nodes': [module_ids[m.id], fam], 'weight': 0.8})
        for cap in m.capabilities:
            capid = add(cap, 'capability')
            hyperedges.append({'id': sid('H', 'cap:' + m.id + ':' + cap), 'relation': 'has_capability', 'nodes': [module_ids[m.id], capid], 'weight': 1.0})

    cap_to_mods = {}
    for m in modules:
        for cap in m.capabilities:
            cap_to_mods.setdefault(cap, []).append(m.id)
    for cap, mids in cap_to_mods.items():
        if len(mids) >= 2:
            hyperedges.append({'id': sid('H', 'mycelium:' + cap), 'relation': 'shared_capability_mycelium', 'nodes': [module_ids[mid] for mid in mids] + [sid('N', 'capability:' + cap)], 'weight': 0.6 + 0.05 * len(mids)})

    root_nodes = [add('OAK', 'root_law'), add('HGFM', 'root_law'), add('CVCD', 'root_law'), add('TGNT', 'root_law')]
    hyperedges.append({'id': sid('H', 'root_laws'), 'relation': 'root_law_bundle', 'nodes': root_nodes + list(module_ids.values()), 'weight': 1.0})
    return {'nodes': nodes, 'hyperedges': hyperedges}
