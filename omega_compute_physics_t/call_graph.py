"""Static call/dependency graph over Complexity-IR for R0.6.

Resolution is intentionally conservative and name-based. It can reveal likely
internal dependencies and recursive strongly connected components, but dynamic
dispatch, monkey patching, imports, decorators and runtime reflection can make
the actual call graph different.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .complexity_ir import FunctionIR


@dataclass(frozen=True)
class CallEdge:
    caller: str
    callee: str
    resolution: str


@dataclass(frozen=True)
class CallGraphReport:
    nodes: tuple[str, ...]
    edges: tuple[CallEdge, ...]
    unresolved_calls: Mapping[str, tuple[str, ...]]
    strongly_connected_components: tuple[tuple[str, ...], ...]
    recursive_components: tuple[tuple[str, ...], ...]
    fan_in: Mapping[str, int]
    fan_out: Mapping[str, int]
    status: str = "static-call-graph-candidate"
    oak_warning: str = (
        "This graph uses static name resolution. It is a dependency hypothesis, "
        "not a complete runtime call trace."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "edges": [asdict(edge) for edge in self.edges],
            "unresolved_calls": {k: list(v) for k, v in self.unresolved_calls.items()},
            "strongly_connected_components": [list(v) for v in self.strongly_connected_components],
            "recursive_components": [list(v) for v in self.recursive_components],
            "fan_in": dict(self.fan_in),
            "fan_out": dict(self.fan_out),
        }


def _tarjan(nodes: Sequence[str], adjacency: Mapping[str, set[str]]) -> tuple[tuple[str, ...], ...]:
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    components: list[tuple[str, ...]] = []

    def strongconnect(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlink[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for nxt in sorted(adjacency.get(node, set())):
            if nxt not in indices:
                strongconnect(nxt)
                lowlink[node] = min(lowlink[node], lowlink[nxt])
            elif nxt in on_stack:
                lowlink[node] = min(lowlink[node], indices[nxt])
        if lowlink[node] == indices[node]:
            members: list[str] = []
            while True:
                item = stack.pop()
                on_stack.remove(item)
                members.append(item)
                if item == node:
                    break
            components.append(tuple(sorted(members)))

    for node in sorted(nodes):
        if node not in indices:
            strongconnect(node)
    return tuple(sorted(components, key=lambda c: (c[0], len(c))))


def build_call_graph(functions: Sequence[FunctionIR]) -> CallGraphReport:
    nodes = tuple(sorted({f"{row.module}:{row.qualified_name}" for row in functions}))
    by_simple: dict[str, list[str]] = {}
    by_module_simple: dict[tuple[str, str], list[str]] = {}
    function_by_id = {f"{row.module}:{row.qualified_name}": row for row in functions}
    for node_id, row in function_by_id.items():
        simple = row.qualified_name.split(".")[-1]
        by_simple.setdefault(simple, []).append(node_id)
        by_module_simple.setdefault((row.module, simple), []).append(node_id)

    edges: list[CallEdge] = []
    unresolved: dict[str, tuple[str, ...]] = {}
    adjacency: dict[str, set[str]] = {node: set() for node in nodes}
    for caller, row in sorted(function_by_id.items()):
        missed: list[str] = []
        for target in row.call_targets:
            local = by_module_simple.get((row.module, target), [])
            global_matches = by_simple.get(target, [])
            matches = local if len(local) == 1 else global_matches if len(global_matches) == 1 else []
            if matches:
                callee = matches[0]
                resolution = "same-module-simple-name" if local else "fleet-unique-simple-name"
                edges.append(CallEdge(caller, callee, resolution))
                adjacency[caller].add(callee)
            else:
                missed.append(target)
        if missed:
            unresolved[caller] = tuple(sorted(set(missed)))

    components = _tarjan(nodes, adjacency)
    edge_pairs = {(edge.caller, edge.callee) for edge in edges}
    recursive = tuple(
        component
        for component in components
        if len(component) > 1 or (len(component) == 1 and (component[0], component[0]) in edge_pairs)
    )
    fan_in = {node: 0 for node in nodes}
    fan_out = {node: 0 for node in nodes}
    for caller, callee in edge_pairs:
        fan_out[caller] += 1
        fan_in[callee] += 1
    return CallGraphReport(
        nodes=nodes,
        edges=tuple(sorted(edges, key=lambda e: (e.caller, e.callee, e.resolution))),
        unresolved_calls=unresolved,
        strongly_connected_components=components,
        recursive_components=recursive,
        fan_in=fan_in,
        fan_out=fan_out,
    )
