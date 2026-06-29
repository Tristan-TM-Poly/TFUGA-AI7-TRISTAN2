"""Method reproduction packets for Omega absorb v1.4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .method_graph import MethodGraph, MethodNode


@dataclass(frozen=True)
class MethodReproductionPacket:
    method_id: str
    method: str
    inputs: Tuple[str, ...]
    outputs: Tuple[str, ...]
    assumptions: Tuple[str, ...]
    failure_modes: Tuple[str, ...]
    tests: Tuple[str, ...]
    score: float
    next_action: str


@dataclass(frozen=True)
class MethodReproductionSet:
    packets: Tuple[MethodReproductionPacket, ...]
    next_action: str


def build_method_reproduction_packet(node: MethodNode) -> MethodReproductionPacket:
    failure_modes = (
        "input_domain_mismatch",
        "missing_reproducibility_evidence",
        "parameter_or_unit_ambiguity",
    )
    tests = (
        f"known_case_for_{node.method_id}",
        "noise_or_perturbation_robustness",
        "document_inputs_outputs_assumptions",
    )
    return MethodReproductionPacket(
        method_id=node.method_id,
        method=node.method,
        inputs=tuple(node.inputs),
        outputs=tuple(node.outputs),
        assumptions=tuple(node.assumptions),
        failure_modes=failure_modes,
        tests=tests,
        score=node.reproducibility_score,
        next_action="generate_minimal_reproduction_stub",
    )


def build_method_reproduction_set(graph: MethodGraph | Iterable[MethodNode]) -> MethodReproductionSet:
    nodes = graph.methods if isinstance(graph, MethodGraph) else tuple(graph)
    return MethodReproductionSet(
        packets=tuple(build_method_reproduction_packet(node) for node in nodes),
        next_action="rank_methods_by_reproducibility_and_value",
    )
