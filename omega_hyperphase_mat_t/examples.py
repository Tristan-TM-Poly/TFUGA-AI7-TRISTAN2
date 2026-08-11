from __future__ import annotations

from .model import ExactHypergraphEnsemble, Hyperedge, HypergraphState


def four_site_topology_ensemble(*, structural_penalty: float = 0.8) -> ExactHypergraphEnsemble:
    """A tiny model with pair interactions plus an optional collective 4-body edge."""

    pair_edges = tuple(
        Hyperedge(pair, 1.0, label=f"pair-{pair[0]}-{pair[1]}")
        for pair in ((0, 1), (1, 2), (2, 3), (3, 0))
    )
    pair_only = HypergraphState("pair-only", pair_edges)
    collective = HypergraphState(
        "pair-plus-collective",
        pair_edges + (Hyperedge((0, 1, 2, 3), 0.65, label="collective-4"),),
        structural_energy=structural_penalty,
    )
    return ExactHypergraphEnsemble(4, (pair_only, collective))
