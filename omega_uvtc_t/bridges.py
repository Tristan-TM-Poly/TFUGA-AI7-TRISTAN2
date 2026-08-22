"""Adapters that keep existing merged kernels as the system of record."""
from __future__ import annotations
from typing import Any, Iterable
from .knowledge import KnowledgeNode

def to_scientific_build_graph(nodes: Iterable[KnowledgeNode]) -> Any:
    from omega_meta_science_t.operating_system import BuildNode, ScientificBuildGraph
    return ScientificBuildGraph(tuple(BuildNode(n.node_id, n.kind, n.dependencies, n.content_hash) for n in nodes))

def capability_registry_to_search_records(registry: Iterable[Any]) -> tuple[dict[str, Any], ...]:
    return tuple({"capability_id": cap.capability_id, "authority": cap.authority, "utility": cap.utility()} for cap in registry)

def cognitive_opcode_to_transform(opcode: Any) -> dict[str, str]:
    value = getattr(opcode, "value", str(opcode))
    return {"primitive": "TRANSFORM", "backend": "omega_cognitive_computer_t", "opcode": str(value)}
