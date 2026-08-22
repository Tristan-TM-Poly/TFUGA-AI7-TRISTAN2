"""DAG resource composition for Omega Compute Physics R0.5.

This is a transparent planning model. Durations, peak bytes and transfer costs
must come from measurements or explicitly labelled estimates; the composition
itself does not turn estimates into observed truth.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class DAGNode:
    node_id: str
    duration_s: float
    peak_bytes: float = 0.0
    output_bytes: float = 0.0

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("node_id cannot be empty")
        if self.duration_s < 0 or self.peak_bytes < 0 or self.output_bytes < 0:
            raise ValueError("resource estimates must be nonnegative")


@dataclass(frozen=True)
class DAGEdge:
    source: str
    target: str
    transfer_s: float = 0.0
    buffer_bytes: float = 0.0

    def __post_init__(self) -> None:
        if self.transfer_s < 0 or self.buffer_bytes < 0:
            raise ValueError("edge resource estimates must be nonnegative")


@dataclass(frozen=True)
class DAGResourceReport:
    topological_order: tuple[str, ...]
    critical_path: tuple[str, ...]
    critical_path_s: float
    serial_sum_s: float
    max_single_node_peak_bytes: float
    conservative_live_bytes: float
    status: str = "composed-resource-estimate"
    oak_warning: str = (
        "DAG composition is exact only relative to supplied node/edge cost semantics. "
        "Contention, allocator behaviour, overlap and hardware effects require measurement."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _topological(nodes: Mapping[str, DAGNode], edges: Sequence[DAGEdge]) -> tuple[str, ...]:
    incoming = {node: 0 for node in nodes}
    outgoing: dict[str, list[str]] = {node: [] for node in nodes}
    for edge in edges:
        if edge.source not in nodes or edge.target not in nodes:
            raise KeyError(f"edge references unknown node: {edge.source}->{edge.target}")
        incoming[edge.target] += 1
        outgoing[edge.source].append(edge.target)
    ready = sorted(node for node, count in incoming.items() if count == 0)
    order: list[str] = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for target in sorted(outgoing[current]):
            incoming[target] -= 1
            if incoming[target] == 0:
                ready.append(target)
                ready.sort()
    if len(order) != len(nodes):
        raise ValueError("pipeline graph contains a cycle")
    return tuple(order)


def compose_dag(nodes: Sequence[DAGNode], edges: Sequence[DAGEdge]) -> DAGResourceReport:
    node_map = {node.node_id: node for node in nodes}
    if len(node_map) != len(nodes):
        raise ValueError("node ids must be unique")
    if not node_map:
        raise ValueError("DAG needs at least one node")
    order = _topological(node_map, edges)
    incoming_edges: dict[str, list[DAGEdge]] = {node: [] for node in node_map}
    outgoing_edges: dict[str, list[DAGEdge]] = {node: [] for node in node_map}
    for edge in edges:
        incoming_edges[edge.target].append(edge)
        outgoing_edges[edge.source].append(edge)

    finish: dict[str, float] = {}
    predecessor: dict[str, str | None] = {}
    for node_id in order:
        best_start = 0.0
        best_parent: str | None = None
        for edge in incoming_edges[node_id]:
            candidate = finish[edge.source] + edge.transfer_s
            if candidate > best_start:
                best_start = candidate
                best_parent = edge.source
        finish[node_id] = best_start + node_map[node_id].duration_s
        predecessor[node_id] = best_parent

    end = max(order, key=lambda node_id: finish[node_id])
    path: list[str] = []
    cursor: str | None = end
    while cursor is not None:
        path.append(cursor)
        cursor = predecessor[cursor]
    path.reverse()

    # Conservative liveness proxy: all outputs whose consumers may still run,
    # plus the largest active node peak and explicit edge buffers. This is not
    # an allocator-accurate temporal simulation.
    output_live = sum(node.output_bytes for node in nodes if outgoing_edges[node.node_id])
    edge_buffers = sum(edge.buffer_bytes for edge in edges)
    max_peak = max(node.peak_bytes for node in nodes)
    conservative_live = output_live + edge_buffers + max_peak

    return DAGResourceReport(
        topological_order=order,
        critical_path=tuple(path),
        critical_path_s=finish[end],
        serial_sum_s=sum(node.duration_s for node in nodes) + sum(edge.transfer_s for edge in edges),
        max_single_node_peak_bytes=max_peak,
        conservative_live_bytes=conservative_live,
    )
