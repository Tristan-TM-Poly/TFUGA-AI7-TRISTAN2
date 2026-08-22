"""TSP adapter for the invariant-first operator synthesizer.

The adapter names only graph invariants.  Classic local-search labels are used
only by post-hoc recognition helpers after synthesis has produced witnesses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from .core import NamedInvariant, OperatorWitness, SynthesisReceipt, synthesize_minimal_operator

Edge = tuple[int, int]


def edge(a: int, b: int) -> Edge:
    if a == b:
        raise ValueError("self-loops are not valid TSP edges")
    return (a, b) if a < b else (b, a)


def complete_graph_edges(nodes: Sequence[int]) -> frozenset[Edge]:
    unique = tuple(dict.fromkeys(int(node) for node in nodes))
    if len(unique) != len(nodes):
        raise ValueError("nodes must be unique")
    return frozenset(edge(a, b) for index, a in enumerate(unique) for b in unique[index + 1 :])


def cycle_edges(nodes: Sequence[int]) -> frozenset[Edge]:
    unique = tuple(dict.fromkeys(int(node) for node in nodes))
    if len(unique) != len(nodes):
        raise ValueError("nodes must be unique")
    if len(unique) < 3:
        raise ValueError("a TSP cycle needs at least three nodes")
    return frozenset(edge(unique[index], unique[(index + 1) % len(unique)]) for index in range(len(unique)))


def _degree(state: frozenset[Edge], node: int) -> int:
    return sum(1 for a, b in state if a == node or b == node)


def _connected(state: frozenset[Edge], nodes: tuple[int, ...]) -> bool:
    if not nodes:
        return False
    adjacency = {node: set() for node in nodes}
    for a, b in state:
        if a not in adjacency or b not in adjacency:
            return False
        adjacency[a].add(b)
        adjacency[b].add(a)
    seen = {nodes[0]}
    stack = [nodes[0]]
    while stack:
        current = stack.pop()
        for nxt in adjacency[current] - seen:
            seen.add(nxt)
            stack.append(nxt)
    return seen == set(nodes)


def tsp_invariants(nodes: Sequence[int]) -> tuple[NamedInvariant[Edge], ...]:
    ordered = tuple(dict.fromkeys(int(node) for node in nodes))
    if len(ordered) != len(nodes):
        raise ValueError("nodes must be unique")
    node_set = set(ordered)
    n = len(ordered)
    if n < 3:
        raise ValueError("TSP needs at least three nodes")

    return (
        NamedInvariant(
            "edge_count_n",
            lambda state: len(state) == n,
            "a Hamiltonian cycle on n vertices carries exactly n undirected edges",
        ),
        NamedInvariant(
            "endpoints_in_domain",
            lambda state: all(a in node_set and b in node_set for a, b in state),
            "every edge endpoint belongs to the declared node set",
        ),
        NamedInvariant(
            "degree_two",
            lambda state: all(_degree(state, node) == 2 for node in ordered),
            "every node has degree two",
        ),
        NamedInvariant(
            "single_connected_component",
            lambda state: _connected(state, ordered),
            "the degree-two graph is one connected component rather than subtours",
        ),
    )


def synthesize_tsp_exchange(
    nodes: Sequence[int],
    source: Iterable[Edge] | None = None,
    *,
    max_candidates: int = 100_000,
    max_witnesses: int = 64,
) -> SynthesisReceipt[Edge]:
    ordered = tuple(int(node) for node in nodes)
    source_state = cycle_edges(ordered) if source is None else frozenset(edge(a, b) for a, b in source)
    return synthesize_minimal_operator(
        source_state,
        complete_graph_edges(ordered),
        tsp_invariants(ordered),
        max_candidates=max_candidates,
        max_witnesses=max_witnesses,
    )


def posthoc_exchange_name(witness: OperatorWitness[Edge]) -> str:
    """Recognize a classic family *after* synthesis; never used by the search."""

    signature = witness.exchange_signature
    if signature == (2, 2):
        return "2-edge-exchange (2-opt family)"
    if signature == (3, 3):
        return "3-edge-exchange (3-opt family)"
    return f"{signature[0]}-remove/{signature[1]}-add exchange"


def tour_weight(state: Iterable[Edge], weights: Mapping[Edge, float]) -> float:
    total = 0.0
    for a, b in state:
        key = edge(a, b)
        if key not in weights:
            raise KeyError(f"missing weight for edge {key}")
        total += float(weights[key])
    return total


@dataclass(frozen=True, slots=True)
class WeightedWitness:
    witness: OperatorWitness[Edge]
    source_weight: float
    target_weight: float

    @property
    def improvement(self) -> float:
        return self.source_weight - self.target_weight


def rank_weighted_witnesses(
    receipt: SynthesisReceipt[Edge],
    weights: Mapping[Edge, float],
) -> tuple[WeightedWitness, ...]:
    source_weight = tour_weight(receipt.source, weights)
    ranked = [
        WeightedWitness(witness, source_weight, tour_weight(witness.target, weights))
        for witness in receipt.witnesses
    ]
    return tuple(sorted(ranked, key=lambda item: (-item.improvement, repr(item.witness.target))))
