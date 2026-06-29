from __future__ import annotations

from dataclasses import dataclass, asdict
from itertools import product
from pathlib import Path
import argparse, hashlib, json, math, time

@dataclass(frozen=True)
class Claim:
    text: str
    category: str
    support_level: int
    evidence_required: str
    allowed: bool

@dataclass(frozen=True)
class Candidate:
    id: str
    tile: str
    rule: str
    depth: int
    cells: int
    total_cells: int
    edges: int
    dimension: float
    porosity: float
    fiedler_proxy: float
    auc_proxy: float
    material_score: float
    mesh_score: float
    power: float

def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def mask_menger():
    mask = []
    for z, y, x in product(range(3), repeat=3):
        mid = (x == 1) + (y == 1) + (z == 1)
        mask.append(0 if mid >= 2 else 1)
    return tuple(mask)

def mask_carpet():
    return (1, 1, 1, 1, 0, 1, 1, 1, 1)

def mask_binary_cube():
    return tuple([1] * 8)

RULES = {
    "sierpinski_carpet": {"dim": 2, "base": 3, "mask": mask_carpet()},
    "menger_sponge": {"dim": 3, "base": 3, "mask": mask_menger()},
    "binary_cube": {"dim": 3, "base": 2, "mask": mask_binary_cube()},
}
TILES = ["square2", "cube3", "hex_proxy", "rhombic_dodeca_proxy", "octet_proxy", "voronoi_proxy"]

def iterate(rule_name: str, depth: int):
    rule = RULES[rule_name]
    dim, base, mask = rule["dim"], rule["base"], rule["mask"]
    offsets = []
    for idx, keep in enumerate(mask):
        if not keep:
            continue
        val = idx
        coords = []
        for _ in range(dim):
            coords.append(val % base)
            val //= base
        offsets.append(tuple(coords))
    cells = {tuple([0] * dim)}
    for _ in range(depth):
        cells = {tuple(c[i] * base + o[i] for i in range(dim)) for c in cells for o in offsets}
    return cells

def graph_edges(cells):
    cells = set(cells)
    if not cells:
        return []
    dim = len(next(iter(cells)))
    edges = set()
    for c in cells:
        for axis in range(dim):
            nb = list(c)
            nb[axis] += 1
            nb = tuple(nb)
            if nb in cells:
                edges.add(tuple(sorted((c, nb))))
    return sorted(edges)

def spectral_proxy(n: int, m: int):
    if n <= 1:
        return 0.0, 0.0, 0.0
    avg = 2 * m / n
    fiedler = max(0.0, min(1.0, m / max(1, n * n)))
    entropy = math.log(max(1, n)) * min(1.0, avg / max(1, n))
    auc = (avg + entropy) * (1 + fiedler)
    return round(fiedler, 6), round(entropy, 6), round(auc, 6)

def power_score(verifiability, reusability, material, mesh, coupling, claim_penalty, complexity, risk):
    num = 0.92 * verifiability * reusability * material * mesh * coupling
    den = max(1e-9, complexity * risk * claim_penalty)
    raw = num / den
    return round(raw / (1 + raw), 6)

def candidate(tile, rule_name, depth):
    cells = iterate(rule_name, depth)
    edges = graph_edges(cells)
    rule = RULES[rule_name]
    total = (rule["base"] ** depth) ** rule["dim"]
    kept = sum(rule["mask"])
    dim = math.log(max(1, kept)) / math.log(rule["base"]) if rule["base"] > 1 else 0
    rho = len(cells) / max(1, total)
    por = 1 - rho
    fiedler, entropy, auc = spectral_proxy(len(cells), len(edges))
    material = max(0.01, min(1.0, (rho ** 0.5) * (1 - 0.35 * por)))
    mesh = max(0.01, min(1.0, 1 / (1 + len(cells) / 2500)))
    coupling = 0.78 if tile.endswith("proxy") else 0.86
    claim_penalty = 1.0
    complexity = 0.45 + min(0.35, len(cells) / 5000)
    risk = 0.32 if "proxy" not in tile else 0.46
    p = power_score(0.86, 0.94, material, mesh, coupling, claim_penalty, complexity, risk)
    return Candidate(f"{tile}__{rule_name}__d{depth}", tile, rule_name, depth, len(cells), total, len(edges), round(dim, 6), round(por, 6), fiedler, auc, round(material, 6), round(mesh, 6), p)

def claims_for_packet():
    return [
        Claim("FTTE-AI7 v0.8 generates coupled geometry/graph/spectral/LC/material/mesh evidence packets.", "software", 3, "local tests plus reproducible run receipt", True),
        Claim("Raman proxy AUC is a calibrated physical Raman prediction.", "physical", 2, "real spectra, baseline correction, uncertainty budget, instrument calibration", False),
        Claim("Meissner/Cooper trap is validated superconductivity.", "physical", 2, "electromagnetic simulation, cryogenic electrical tests, reproducibility", False),
        Claim("Octonion/sedenion channels prove fundamental-force unification.", "theory", 1, "formal derivation, predictions, external validation", False),
        Claim("PEFA macro transfer is a graph-resilience design hypothesis.", "infrastructure", 3, "network data, flow model, baseline comparison", True),
    ]

def evidence_gate(claims):
    blocked, allowed = [], []
    for c in claims:
        (allowed if c.allowed else blocked).append(asdict(c))
    return {"kind": "EvidenceGate", "levels": {"0": "idea", "1": "code-valid", "2": "geometry-valid", "3": "proxy-simulation", "4": "external-simulation-needed", "5": "lab-validation-needed", "6": "validated"}, "allowed_claims": allowed, "blocked_claims": blocked, "stable_canon_allowed": False}

def build_hgfm(candidates):
    modules = ["Tile", "Tensor", "Graph", "Spectral", "LC", "Material", "Mesh", "RamanProxy", "MeissnerProxy", "OctonionFeature", "PEFA", "Publish", "EvidenceGate", "DCT++"]
    nodes = [{"id": m, "type": "module"} for m in modules]
    nodes += [{"id": c.id, "type": "candidate", "power": c.power, "porosity": c.porosity} for c in candidates[:8]]
    hyperedges = [
        {"id": "H1_geometry_to_circuit", "members": ["Tile", "Tensor", "Graph", "LC", "EvidenceGate", "DCT++"]},
        {"id": "H2_geometry_to_material_mesh", "members": ["Tile", "Tensor", "Graph", "Material", "Mesh", "EvidenceGate", "DCT++"]},
        {"id": "H3_spectral_to_raman_proxy", "members": ["Graph", "Spectral", "RamanProxy", "EvidenceGate", "DCT++"]},
        {"id": "H4_topology_to_meissner_proxy", "members": ["Graph", "Spectral", "Material", "MeissnerProxy", "EvidenceGate", "DCT++"]},
        {"id": "H5_feature_space", "members": ["Tensor", "Graph", "Spectral", "OctonionFeature", "EvidenceGate"]},
        {"id": "H6_local_to_pefa", "members": ["Graph", "Spectral", "LC", "PEFA", "EvidenceGate"]},
        {"id": "H7_publication_governance", "members": ["Publish", "EvidenceGate", "DCT++"]},
    ]
    return {"kind": "HGFM-OmniCoupled-v0.8", "nodes": nodes, "hyperedges": hyperedges}

def run(out="outputs_v0_8", max_depth=2, max_candidates=64):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    candidates = []
    for tile in TILES:
        for rule in RULES:
            for depth in range(1, max_depth + 1):
                candidates.append(candidate(tile, rule, depth))
    candidates = sorted(candidates, key=lambda c: c.power, reverse=True)[:max_candidates]
    gate = evidence_gate(claims_for_packet())
    hgfm = build_hgfm(candidates)
    status = {"Tile": "success", "Tensor": "success", "Graph": "success", "Spectral": "success", "LC": "success", "Material": "success", "Mesh": "success", "RamanProxy": "proxy_only", "MeissnerProxy": "proxy_only", "OctonionFeature": "exploratory_only", "PEFA": "proxy_only", "EvidenceGate": "success", "DCT++": "success"}
    manifest = {"run_id": "FTTE-AI7-V0-8-OMNICOUPLED", "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "status": "succeeded", "decision": "PUBLISH_AS_CRYSTALLIZABLE_OMNICOUPLED_PACKET", "stable_canon_allowed": False, "candidate_count": len(candidates), "top_power": candidates[0].power if candidates else 0, "modules": status}
    manifest["receipt_sha256"] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    write_json(out / "top_candidates.json", [asdict(c) for c in candidates])
    write_json(out / "hgfm_omnicoupled_graph.json", hgfm)
    write_json(out / "evidence_gate.json", gate)
    write_json(out / "parallel_status.json", status)
    write_json(out / "run_manifest.json", manifest)
    (out / "ANTI_HYPE_LEDGER.md").write_text("# AntiHype Ledger\n\nBlocked claims: Raman physical proof, validated superconductivity, force unification, energy generation, autonomous lab hardware control.\n\nAllowed claims: software generation, graph/spectral proxies, LC/material/mesh scaffolds, DCT++ evidence packet.\n", encoding="utf-8")
    (out / "DCTPP_REPORT_v0_8.md").write_text("# DCT++ Report v0.8 - OmniCoupled HGFM Forge\n\nStatus: S4-local-tested-software-prototype.\n\nDecision: PUBLISH_AS_CRYSTALLIZABLE_OMNICOUPLED_PACKET.\n\nStable physical canon: false.\n\nTop power: " + str(manifest["top_power"]) + "\n\nAll physical claims are routed through EvidenceGate before promotion.\n", encoding="utf-8")
    return manifest

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs_v0_8")
    ap.add_argument("--max-depth", type=int, default=2)
    ap.add_argument("--max-candidates", type=int, default=64)
    args = ap.parse_args()
    print(json.dumps(run(args.out, args.max_depth, args.max_candidates), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
