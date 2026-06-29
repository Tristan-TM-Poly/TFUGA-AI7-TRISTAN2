from __future__ import annotations

import argparse
import json
from collections import Counter
from typing import Any

from sage_tristan.prime_tensors import build_prime_nodes, finite_prime_tensor_packet


def _node_id(index: int) -> str:
    return f"p:{index}"


def _edge_id(kind: str, signature: list[int], ordinal: int) -> str:
    suffix = ".".join(str(x) for x in signature) if signature else "empty"
    return f"e:{kind}:{suffix}:{ordinal}"


def build_hgfm_prime_graph(count: int = 16, max_jump: int = 2, prefix: int = 3) -> dict[str, Any]:
    """Build a finite HGFM graph packet from prime tensor signatures.

    The graph is intentionally finite and observational. It is useful for
    visualizations, test fixtures, and OAK-gated motif exploration.
    """
    if count < 2:
        raise ValueError("count must be at least 2")
    if max_jump < 1:
        raise ValueError("max_jump must be at least 1")
    if prefix < 1:
        raise ValueError("prefix must be at least 1")

    packet = finite_prime_tensor_packet(count=count, max_jump=max_jump)
    prime_nodes = build_prime_nodes(count=count, max_jump=max_jump)

    nodes: list[dict[str, Any]] = []
    for node in prime_nodes:
        nodes.append(
            {
                "id": _node_id(node.index),
                "kind": "prime",
                "index": node.index,
                "prime": node.prime,
                "oak_status": node.oak_status,
                "fertility": node.fertility,
                "signature": {
                    "primorial_prefix": node.primorial_digits[:prefix],
                    "residue_prefix": node.residues[:prefix],
                    "gap1_modular_prefix": node.modular_gaps.get(1, [])[:prefix],
                },
            }
        )

    edges: list[dict[str, Any]] = []
    for ordinal, edge in enumerate(packet["hyperedges"], start=1):
        connected = [_node_id(index) for index in edge["node_indices"]]
        edges.append(
            {
                "id": _edge_id(edge["kind"], edge["signature"], ordinal),
                "kind": edge["kind"],
                "signature": edge["signature"],
                "connects": connected,
                "arity": len(connected),
                "oak_status": edge["oak_status"],
            }
        )

    degrees = Counter()
    for edge in edges:
        for node_id in edge["connects"]:
            degrees[node_id] += 1

    for node in nodes:
        node["degree"] = degrees[node["id"]]

    return {
        "name": "hgfm_prime_graph",
        "oak_status": "prototype",
        "parameters": {"count": count, "max_jump": max_jump, "prefix": prefix},
        "nodes": nodes,
        "hyperedges": edges,
        "metrics": {
            "node_count": len(nodes),
            "hyperedge_count": len(edges),
            "nonisolated_node_count": sum(1 for node in nodes if node["degree"] > 0),
            "max_degree": max((node["degree"] for node in nodes), default=0),
            "checks_passed": all(packet["checks"].values()),
        },
        "limits": [
            "finite prefix only",
            "hyperedges are observed signature collisions, not global laws",
            "prototype graph packet, not a proof of prime distribution claims",
        ],
    }


def summarize_graph(graph: dict[str, Any]) -> str:
    metrics = graph["metrics"]
    return (
        f"{graph['name']} OAK={graph['oak_status']} "
        f"nodes={metrics['node_count']} "
        f"hyperedges={metrics['hyperedge_count']} "
        f"nonisolated={metrics['nonisolated_node_count']} "
        f"max_degree={metrics['max_degree']} "
        f"checks_passed={metrics['checks_passed']}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate finite HGFM prime graph JSON.")
    parser.add_argument("--count", type=int, default=16)
    parser.add_argument("--max-jump", type=int, default=2)
    parser.add_argument("--prefix", type=int, default=3)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    graph = build_hgfm_prime_graph(args.count, args.max_jump, args.prefix)
    if args.summary:
        print(summarize_graph(graph))
    else:
        print(json.dumps(graph, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
