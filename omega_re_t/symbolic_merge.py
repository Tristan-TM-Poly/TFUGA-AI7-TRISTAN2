"""Conservative symbolic state merging for finite authorized traces."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Hashable, Iterable, Sequence

Symbol = Hashable
Output = Hashable


@dataclass
class PrefixNode:
    node_id: int
    depth: int
    transitions: dict[Symbol, tuple[Output, int]] = field(default_factory=dict)
    terminal_count: int = 0


@dataclass(frozen=True)
class TraceConflict:
    node_id: int
    symbol: Symbol
    existing_output: Output
    observed_output: Output


@dataclass(frozen=True)
class SymbolicMergeReport:
    node_count: int
    class_count: int
    classes: tuple[tuple[int, ...], ...]
    conflicts: tuple[TraceConflict, ...]
    signature_depth: int
    claim: str = "bounded_symbolic_equivalence_only"


class PrefixTreeTransducer:
    def __init__(self) -> None:
        self.nodes: dict[int, PrefixNode] = {0: PrefixNode(node_id=0, depth=0)}
        self._next_id = 1
        self.conflicts: list[TraceConflict] = []

    def add_trace(self, inputs: Sequence[Symbol], outputs: Sequence[Output]) -> None:
        if len(inputs) != len(outputs):
            raise ValueError("inputs and outputs must have equal length")
        node_id = 0
        for symbol, output in zip(inputs, outputs, strict=True):
            node = self.nodes[node_id]
            existing = node.transitions.get(symbol)
            if existing is not None:
                existing_output, child_id = existing
                if existing_output != output:
                    self.conflicts.append(
                        TraceConflict(node_id, symbol, existing_output, output)
                    )
                    return
                node_id = child_id
                continue
            child_id = self._next_id
            self._next_id += 1
            self.nodes[child_id] = PrefixNode(node_id=child_id, depth=node.depth + 1)
            node.transitions[symbol] = (output, child_id)
            node_id = child_id
        self.nodes[node_id].terminal_count += 1

    @classmethod
    def from_traces(
        cls,
        traces: Iterable[tuple[Sequence[Symbol], Sequence[Output]]],
    ) -> "PrefixTreeTransducer":
        tree = cls()
        for inputs, outputs in traces:
            tree.add_trace(inputs, outputs)
        return tree

    def _signature(self, node_id: int, depth: int, memo: dict[tuple[int, int], tuple]) -> tuple:
        key = (node_id, depth)
        if key in memo:
            return memo[key]
        node = self.nodes[node_id]
        if depth == 0:
            signature = (
                bool(node.terminal_count),
                tuple(sorted((repr(k), repr(v[0])) for k, v in node.transitions.items())),
            )
        else:
            signature = (
                bool(node.terminal_count),
                tuple(
                    sorted(
                        (
                            repr(symbol),
                            repr(output),
                            self._signature(child_id, depth - 1, memo),
                        )
                        for symbol, (output, child_id) in node.transitions.items()
                    )
                ),
            )
        memo[key] = signature
        return signature

    def merge_report(self, *, signature_depth: int = 2) -> SymbolicMergeReport:
        if signature_depth < 0:
            raise ValueError("signature_depth must be non-negative")
        memo: dict[tuple[int, int], tuple] = {}
        buckets: dict[tuple, list[int]] = {}
        for node_id in sorted(self.nodes):
            signature = self._signature(node_id, signature_depth, memo)
            buckets.setdefault(signature, []).append(node_id)
        classes = tuple(sorted((tuple(ids) for ids in buckets.values()), key=lambda ids: ids[0]))
        return SymbolicMergeReport(
            node_count=len(self.nodes),
            class_count=len(classes),
            classes=classes,
            conflicts=tuple(self.conflicts),
            signature_depth=signature_depth,
        )

    def replay(self, inputs: Sequence[Symbol]) -> tuple[Output, ...] | None:
        node_id = 0
        outputs: list[Output] = []
        for symbol in inputs:
            transition = self.nodes[node_id].transitions.get(symbol)
            if transition is None:
                return None
            output, node_id = transition
            outputs.append(output)
        return tuple(outputs)
