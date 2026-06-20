#!/usr/bin/env python3
"""
AIT Universe Folder Engine.

Stdlib-only, deterministic, OAK-safe generator for bounded fractal / hypergraph /
mycelial folder universes.

Boundary:
- This engine does not claim to create physical, mathematical, or scientific truth.
- It creates inspectable folder/file scaffolds and machine-readable hypergraph traces.
- Expansion is always bounded by max_depth, branching, and node_limit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_DOMAIN_PACK: Dict[str, Any] = {
    "version": "omega.ait_universe.seed_pack.v1",
    "root": "AIT-Universe",
    "domains": [
        {
            "id": "sciences_naturelles",
            "label": "Sciences Naturelles",
            "children": ["Physique", "Chimie", "Biologie", "Terre", "Astronomie", "Environnement"],
            "invariants": ["measurement", "model", "law", "scale", "residue"],
        },
        {
            "id": "sciences_humaines",
            "label": "Sciences Humaines",
            "children": ["Psychologie", "Sociologie", "Anthropologie", "Histoire", "Linguistique", "Economie", "Humanites"],
            "invariants": ["context", "interpretation", "structure", "agency", "residue"],
        },
        {
            "id": "sciences_formelles",
            "label": "Sciences Formelles",
            "children": ["Mathematiques", "Logique", "Statistiques", "Informatique_Theorique", "Information", "Complexite"],
            "invariants": ["proof", "definition", "structure", "computation", "residue"],
        },
        {
            "id": "sciences_appliquees",
            "label": "Sciences Appliquees",
            "children": ["Medecine", "Ingenierie", "Agriculture", "Architecture", "Informatique_Appliquee", "Gestion"],
            "invariants": ["prototype", "constraint", "test", "utility", "residue"],
        },
    ],
    "global_invariants": [
        "OAK_boundary",
        "bounded_recursion",
        "deterministic_trace",
        "hypergraph_links",
        "mycelial_propagation",
        "negative_memory_residue",
    ],
}


@dataclass(frozen=True)
class EngineConfig:
    root: Path
    max_depth: int = 2
    branching: int = 3
    node_limit: int = 128
    seed: str = "tristan-ait-universe"
    dry_run: bool = False
    force: bool = False


@dataclass
class GeneratedNode:
    node_id: str
    label: str
    path: str
    depth: int
    parent_id: Optional[str]
    invariants: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)


@dataclass
class GenerationTrace:
    version: str = "omega.ait_universe_trace.v1"
    nodes: List[GeneratedNode] = field(default_factory=list)
    hyperedges: List[List[str]] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def to_jsonable(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "node_count": len(self.nodes),
            "hyperedge_count": len(self.hyperedges),
            "file_count": len(self.files),
            "nodes": [node.__dict__ for node in self.nodes],
            "hyperedges": self.hyperedges,
            "files": self.files,
            "skipped": self.skipped,
            "oak_boundary": {
                "score_is_not_truth": True,
                "folders_are_not_claims": True,
                "generated_links_are_structural": True,
                "expansion_is_bounded": True,
            },
        }


def stable_slug(text: str) -> str:
    text = text.strip().replace("'", "")
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "node"


def stable_hash(*parts: str, length: int = 12) -> str:
    payload = "||".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:length]


def load_domain_pack(path: Optional[str]) -> Dict[str, Any]:
    if path is None:
        return DEFAULT_DOMAIN_PACK
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def ensure_safe_root(root: Path) -> Path:
    resolved = root.expanduser().resolve()
    forbidden = {Path("/").resolve(), Path.home().resolve()}
    if resolved in forbidden:
        raise ValueError(f"Refusing unsafe root path: {resolved}")
    if len(str(resolved)) < 8:
        raise ValueError(f"Refusing suspiciously short root path: {resolved}")
    return resolved


def write_text(path: Path, content: str, trace: GenerationTrace, cfg: EngineConfig) -> None:
    trace.files.append(str(path))
    if cfg.dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not cfg.force:
        trace.skipped.append(str(path))
        return
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Dict[str, Any], trace: GenerationTrace, cfg: EngineConfig) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n", trace, cfg)


def build_children(label: str, depth: int, branching: int, pack_children: Optional[List[str]] = None) -> List[str]:
    if depth == 0 and pack_children:
        return pack_children[:branching]
    return [f"{label}_Sublevel_{i}" for i in range(branching)]


def node_payload(node: GeneratedNode, trace: GenerationTrace) -> Dict[str, Any]:
    child_edges = [edge for edge in trace.hyperedges if node.node_id in edge]
    return {
        "node": node.__dict__,
        "local_hyperedges": child_edges,
        "boundary": {
            "meaning": "structural scaffold only",
            "no_truth_claim": True,
            "no_scientific_certification": True,
        },
    }


def graphml(trace: GenerationTrace) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '  <graph edgedefault="undirected">',
    ]
    for node in trace.nodes:
        lines.append(f'    <node id="{node.node_id}"/>')
    for idx, edge in enumerate(trace.hyperedges):
        for jdx, node_id in enumerate(edge):
            hub = f"hyperedge_{idx}"
            if jdx == 0:
                lines.append(f'    <node id="{hub}"/>')
            lines.append(f'    <edge source="{hub}" target="{node_id}"/>')
    lines.extend(["  </graph>", "</graphml>", ""])
    return "\n".join(lines)


def build_local_files(base: Path, node: GeneratedNode, trace: GenerationTrace, cfg: EngineConfig) -> None:
    hyper_dir = base / "Hypergraph"
    stability_dir = base / "Stability"
    sublevels_dir = base / "Sublevels"

    nodes_json = {
        "version": "omega.local_hypergraph_nodes.v1",
        "node": node.__dict__,
        "zoom_rule": "Each node may expand into another bounded hypergraph under Sublevels/.",
    }
    edges_json = {
        "version": "omega.local_hypergraph_edges.v1",
        "hyperedges": [edge for edge in trace.hyperedges if node.node_id in edge],
        "links": node.links,
    }
    invariants_json = {
        "version": "omega.local_invariants.v1",
        "core": node.invariants,
        "structural": ["folder", "file", "hyperedge", "relative_link"],
        "emergent": ["cross_level_trace", "mycelial_propagation"],
        "residual": ["unexpanded_children", "unknown_semantics", "future_OAK_tests"],
        "recursive": "inherits from parent level",
    }
    fractal_json = {
        "version": "omega.fractal_rule.v1",
        "depth": node.depth,
        "self_similarity": True,
        "bounded": True,
        "next_zoom": "Sublevels/",
    }
    mycelium_json = {
        "version": "omega.mycelium_rule.v1",
        "propagation": ["horizontal", "vertical", "diagonal"],
        "links": node.links,
        "rules": [
            "propagate invariants to children",
            "connect siblings through meta-hypergraph",
            "preserve OAK boundary markers",
        ],
    }
    row_json = {
        "version": "omega.stability_row.v1",
        "node_id": node.node_id,
        "depth": node.depth,
        "axes": {
            "historical_stability": 0,
            "formal_stability": 0,
            "genealogical_stability": max(0, 10 - node.depth),
            "structural_stability": 5,
            "universality_stability": 5,
            "fertility_stability": 7,
            "recurrence_stability": 8,
            "invariance_stability": 6,
            "evolution_stability": 0,
            "continuum_stability": 0,
            "meta_stability": 0,
            "global_residue": node.depth,
        },
        "boundary": "heuristic scaffold; not a truth or proof score",
    }
    residue_json = {
        "version": "omega.residue.v1",
        "node_id": node.node_id,
        "residues": ["semantic_gap", "unverified_links", "bounded_depth_cutoff"],
    }
    continuum_json = {
        "version": "omega.continuum.v1",
        "node_id": node.node_id,
        "parent_id": node.parent_id,
        "children_expected_under": str(sublevels_dir),
        "status": "AIT_UNIVERSE_SCAFFOLD_GREEN",
    }
    readme = f"""# {node.label}

This folder is an AIT-Universe hypergraph node.

- Node id: `{node.node_id}`
- Depth: `{node.depth}`
- Parent: `{node.parent_id or "ROOT"}`
- Boundary: structural scaffold only; no scientific certification.

## Zoom rule

Open `Sublevels/` to inspect the next bounded fractal layer.

## Local artifacts

- `Hypergraph/nodes.json`
- `Hypergraph/edges.json`
- `Hypergraph/invariants.json`
- `Hypergraph/fractal.json`
- `Hypergraph/mycelium.json`
- `Hypergraph/graph.hypergraph`
- `Stability/row.json`
- `Stability/residue.json`
- `Stability/continuum.json`
"""

    write_json(hyper_dir / "nodes.json", nodes_json, trace, cfg)
    write_json(hyper_dir / "edges.json", edges_json, trace, cfg)
    write_json(hyper_dir / "invariants.json", invariants_json, trace, cfg)
    write_json(hyper_dir / "fractal.json", fractal_json, trace, cfg)
    write_json(hyper_dir / "mycelium.json", mycelium_json, trace, cfg)
    write_json(hyper_dir / "graph.hypergraph", node_payload(node, trace), trace, cfg)
    write_json(stability_dir / "row.json", row_json, trace, cfg)
    write_json(stability_dir / "residue.json", residue_json, trace, cfg)
    write_json(stability_dir / "continuum.json", continuum_json, trace, cfg)
    write_text(base / "README.md", readme, trace, cfg)
    if not cfg.dry_run:
        sublevels_dir.mkdir(parents=True, exist_ok=True)


def generate_universe(cfg: EngineConfig, domain_pack: Dict[str, Any]) -> GenerationTrace:
    root = ensure_safe_root(cfg.root)
    trace = GenerationTrace()

    root_label = domain_pack.get("root", "AIT-Universe")
    root_node = GeneratedNode(
        node_id="root_" + stable_hash(cfg.seed, root_label),
        label=root_label,
        path=str(root),
        depth=0,
        parent_id=None,
        invariants=list(domain_pack.get("global_invariants", [])),
        links=[],
    )
    trace.nodes.append(root_node)

    queue: List[Tuple[GeneratedNode, Path, Optional[List[str]]]] = [(root_node, root, None)]

    domain_specs = domain_pack.get("domains", [])
    if domain_specs:
        queue = []
        for spec in domain_specs[: cfg.branching]:
            label = spec.get("label", spec.get("id", "Domain"))
            node = GeneratedNode(
                node_id="node_" + stable_hash(cfg.seed, label, "0"),
                label=label,
                path=str(root / "Domains" / stable_slug(label)),
                depth=1,
                parent_id=root_node.node_id,
                invariants=list(spec.get("invariants", [])) + list(domain_pack.get("global_invariants", [])),
                links=["../../Meta-Hypergraph/meta.json"],
            )
            trace.nodes.append(node)
            trace.hyperedges.append([root_node.node_id, node.node_id, "meta_domains"])
            queue.append((node, root / "Domains" / stable_slug(label), list(spec.get("children", []))))

    index = 0
    while queue and len(trace.nodes) < cfg.node_limit:
        node, base, pack_children = queue.pop(0)
        build_local_files(base, node, trace, cfg)

        if node.depth >= cfg.max_depth:
            continue

        child_labels = build_children(node.label, node.depth, cfg.branching, pack_children)
        for child_label in child_labels:
            if len(trace.nodes) >= cfg.node_limit:
                break
            child_id = "node_" + stable_hash(cfg.seed, node.node_id, child_label, str(index))
            index += 1
            child = GeneratedNode(
                node_id=child_id,
                label=child_label,
                path=str(base / "Sublevels" / stable_slug(child_label)),
                depth=node.depth + 1,
                parent_id=node.node_id,
                invariants=list(node.invariants),
                links=[
                    "../Hypergraph/graph.hypergraph",
                    "../../../Meta-Hypergraph/meta.json",
                ],
            )
            trace.nodes.append(child)
            trace.hyperedges.append([node.node_id, child.node_id, "fractal_zoom"])
            if len(child_labels) > 1:
                trace.hyperedges.append([node.node_id, child.node_id, "sibling_mycelium"])
            queue.append((child, base / "Sublevels" / stable_slug(child_label), None))

    meta_dir = root / "Meta-Hypergraph"
    meta_payload = trace.to_jsonable()
    meta_payload["meta_hypergraph"] = {
        "nodes": [node.node_id for node in trace.nodes],
        "hyperedges": trace.hyperedges,
        "recursion": "bounded fractal expansion",
        "mycelium_propagation": ["horizontal", "vertical", "diagonal"],
        "node_limit": cfg.node_limit,
        "max_depth": cfg.max_depth,
        "branching": cfg.branching,
    }
    write_json(meta_dir / "meta.json", meta_payload, trace, cfg)
    write_json(meta_dir / "meta.hypergraph", meta_payload["meta_hypergraph"], trace, cfg)
    write_text(meta_dir / "meta.graphml", graphml(trace), trace, cfg)
    write_text(
        meta_dir / "META_HYPERGRAPH.md",
        f"""# AIT-Universe Meta-Hypergraph

Generated by `scripts/ait_universe_folder_engine.py`.

- Nodes: {len(trace.nodes)}
- Hyperedges: {len(trace.hyperedges)}
- Max depth: {cfg.max_depth}
- Branching: {cfg.branching}
- Node limit: {cfg.node_limit}

## OAK boundary

This is a deterministic structural scaffold. It is not a proof system, not a truth oracle,
and not a scientific certification engine.
""",
        trace,
        cfg,
    )
    write_json(root / "ait_universe_trace.json", trace.to_jsonable(), trace, cfg)
    return trace


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a bounded AIT-Universe folder hypergraph.")
    parser.add_argument("--root", default="artifacts/AIT-Universe", help="Output root directory.")
    parser.add_argument("--domain-pack", default=None, help="Optional JSON seed/domain pack.")
    parser.add_argument("--max-depth", type=int, default=2, help="Maximum fractal depth.")
    parser.add_argument("--branching", type=int, default=3, help="Children per node.")
    parser.add_argument("--node-limit", type=int, default=128, help="Hard cap on generated nodes.")
    parser.add_argument("--seed", default="tristan-ait-universe", help="Deterministic seed.")
    parser.add_argument("--dry-run", action="store_true", help="Plan generation without writing files.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated files.")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.max_depth < 0:
        raise ValueError("--max-depth must be >= 0")
    if args.branching < 1:
        raise ValueError("--branching must be >= 1")
    if args.node_limit < 1:
        raise ValueError("--node-limit must be >= 1")

    cfg = EngineConfig(
        root=Path(args.root),
        max_depth=args.max_depth,
        branching=args.branching,
        node_limit=args.node_limit,
        seed=args.seed,
        dry_run=args.dry_run,
        force=args.force,
    )
    pack = load_domain_pack(args.domain_pack)
    trace = generate_universe(cfg, pack)
    print(json.dumps({
        "version": trace.version,
        "nodes": len(trace.nodes),
        "hyperedges": len(trace.hyperedges),
        "files": len(trace.files),
        "dry_run": cfg.dry_run,
        "root": str(ensure_safe_root(cfg.root)),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
