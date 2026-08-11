"""Machine-readable proof obligations for Ω-RH-PROOF-OS-T∞.

This exporter does not prove obligations. It makes missing mathematical work
explicit and suitable for OAK/HGFM/formal-proof handoff.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, Any


@dataclass(frozen=True)
class ProofObligation:
    obligation_id: str
    statement: str
    status: str
    dependencies: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()
    failure_condition: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def obligations_from_proof_graph(graph: Mapping[str, Any]) -> list[ProofObligation]:
    """Extract unresolved/research obligations from an HGFM proof graph."""

    nodes = graph.get("nodes", [])
    edges = graph.get("hyperedges", [])
    incoming: dict[str, list[Mapping[str, Any]]] = {}
    for edge in edges:
        target = edge.get("target")
        if isinstance(target, str):
            incoming.setdefault(target, []).append(edge)

    obligations: list[ProofObligation] = []
    for node in nodes:
        node_id = node.get("id")
        status = node.get("status")
        if not isinstance(node_id, str):
            continue
        if status not in {"OPEN", "CONJECTURE", "SYMBOLICALLY_DERIVED", "NUMERICALLY_VERIFIED"}:
            continue
        deps: set[str] = set()
        relations: list[str] = []
        for edge in incoming.get(node_id, []):
            deps.update(str(x) for x in edge.get("sources", []))
            relation = edge.get("relation")
            if relation:
                relations.append(str(relation))
        obligations.append(
            ProofObligation(
                obligation_id=f"obl.{node_id}",
                statement=f"Discharge proof/research obligation for node '{node_id}'.",
                status=str(status),
                dependencies=tuple(sorted(deps)),
                required_evidence=(
                    "proof-grade derivation or explicit refutation",
                    "all quantifiers/domains preserved",
                    "no forbidden epistemic promotion",
                ),
                failure_condition="a counterexample, circular dependency, or non-proof-grade leaf remains",
                notes=("incoming relations: " + ", ".join(sorted(set(relations)))) if relations else "root/open obligation",
            )
        )
    return obligations


def lean_stub(obligation: ProofObligation) -> str:
    """Emit a Lean-compatible *commented* stub, deliberately not fake Lean code."""

    deps = ", ".join(obligation.dependencies) or "none"
    return (
        f"/- OAK PROOF OBLIGATION: {obligation.obligation_id}\n"
        f"Statement: {obligation.statement}\n"
        f"Current status: {obligation.status}\n"
        f"Dependencies: {deps}\n"
        "This block is documentation only. Replace it with a formally typed theorem\n"
        "whose assumptions and conclusion are independently verified.\n"
        "-/\n"
    )


def export_obligation_bundle(obligations: Iterable[ProofObligation]) -> dict[str, Any]:
    values = tuple(obligations)
    return {
        "schema": "omega-rh-proof-obligations/1",
        "solution_claimed": False,
        "obligation_count": len(values),
        "obligations": [item.to_dict() for item in values],
        "lean_comment_stubs": [lean_stub(item) for item in values],
        "oak": {
            "formal_stub_is_not_proof": True,
            "promotion_requires_formally_or_independently_verified_theorem": True,
        },
    }
