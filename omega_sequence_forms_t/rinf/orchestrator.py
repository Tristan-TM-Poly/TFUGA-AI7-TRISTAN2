"""Multi-family R∞ discovery orchestration and representation graph assembly."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
from typing import Any, Iterable, Sequence

from ..exact import NumberLike, normalize_terms
from .graph import (
    EdgeKind,
    NodeKind,
    RepresentationEdge,
    RepresentationHypergraph,
    RepresentationNode,
)
from .hankel import discover_rational_prony, hankel_rank_profile
from .hypergeometric import discover_hypergeometric
from .p_recursive import discover_p_recursive
from .quasipolynomial import discover_quasi_polynomials
from .rational_index import discover_rational_indices


@dataclass(frozen=True)
class DiscoveryLimits:
    max_period: int = 32
    max_degree: int = 8
    max_order: int = 8
    max_candidates_per_family: int = 16
    holdout: int | None = None

    def __post_init__(self) -> None:
        if min(self.max_period, self.max_degree + 1, self.max_order, self.max_candidates_per_family) <= 0:
            raise ValueError("discovery limits must be positive")


@dataclass
class RInfDiscoveryReport:
    terms: tuple[Fraction, ...]
    limits: DiscoveryLimits
    families: dict[str, list[dict[str, Any]]]
    diagnostics: dict[str, Any]
    graph: RepresentationHypergraph
    warnings: list[str]

    @property
    def candidate_count(self) -> int:
        return sum(len(items) for items in self.families.values())

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema": "omega-sequence-forms-rinf-discovery/2",
            "terms": [str(value) for value in self.terms],
            "limits": {
                "max_period": self.limits.max_period,
                "max_degree": self.limits.max_degree,
                "max_order": self.limits.max_order,
                "max_candidates_per_family": self.limits.max_candidates_per_family,
                "holdout": self.limits.holdout,
            },
            "families": self.families,
            "candidate_count": self.candidate_count,
            "diagnostics": self.diagnostics,
            "representation_graph": self.graph.to_dict(),
            "representation_graph_digest": self.graph.digest(),
            "warnings": self.warnings,
            "global_identity_proved": False,
            "formal_proof_completed": False,
        }
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        payload["report_digest"] = sha256(canonical.encode("utf-8")).hexdigest()
        return payload


def _candidate_node_id(family: str, index: int, candidate: dict[str, Any]) -> str:
    canonical = json.dumps(candidate, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"form.{family}.{index:03d}.{sha256(canonical.encode('utf-8')).hexdigest()[:12]}"


def discover_rinf(
    terms: Iterable[NumberLike],
    *,
    limits: DiscoveryLimits | None = None,
) -> RInfDiscoveryReport:
    values = normalize_terms(terms)
    limits = limits or DiscoveryLimits()
    families: dict[str, list[dict[str, Any]]] = {}

    quasi = discover_quasi_polynomials(
        values,
        max_period=limits.max_period,
        max_degree=limits.max_degree,
        holdout=limits.holdout,
    )[: limits.max_candidates_per_family]
    families["quasi_polynomial"] = [item.to_dict() for item in quasi]

    rational = discover_rational_indices(
        values,
        max_numerator_degree=limits.max_degree,
        max_denominator_degree=limits.max_degree,
        holdout=limits.holdout,
    )[: limits.max_candidates_per_family]
    families["rational_index"] = [item.to_dict() for item in rational]

    hyper = discover_hypergeometric(
        values,
        max_numerator_degree=limits.max_degree,
        max_denominator_degree=limits.max_degree,
        holdout=limits.holdout,
    )[: limits.max_candidates_per_family]
    families["hypergeometric"] = [item.to_dict() for item in hyper]

    prec = discover_p_recursive(
        values,
        max_order=limits.max_order,
        max_degree=limits.max_degree,
        holdout_equations=limits.holdout,
    )[: limits.max_candidates_per_family]
    families["p_recursive"] = [item.to_dict() for item in prec]

    prony = discover_rational_prony(
        values,
        max_order=limits.max_order,
        holdout=limits.holdout,
    )[: limits.max_candidates_per_family]
    families["rational_prony"] = [item.to_dict() for item in prony]

    graph = RepresentationHypergraph("sequence." + sha256(
        json.dumps([str(value) for value in values], separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16])
    sequence_id = "sequence.observed"
    graph.add_node(
        RepresentationNode(
            sequence_id,
            NodeKind.SEQUENCE,
            "Observed finite sequence",
            {"terms": [str(value) for value in values]},
            assumptions=("indices_start_at_zero",),
            risk_tags=("finite_prefix_nonuniqueness",),
            provenance="direct_input",
        )
    )
    for family, candidates in families.items():
        for index, candidate in enumerate(candidates):
            node_id = _candidate_node_id(family, index, candidate)
            kind = NodeKind.FORM
            if family == "p_recursive":
                kind = NodeKind.OPERATOR
            graph.add_node(
                RepresentationNode(
                    node_id,
                    kind,
                    family,
                    candidate,
                    assumptions=("finite_prefix",),
                    risk_tags=("global_identity_unproved",),
                    provenance="omega_sequence_forms_t.rinf",
                )
            )
            graph.add_edge(
                RepresentationEdge(
                    edge_id=f"infer.{family}.{index:03d}",
                    kind=EdgeKind.REPRESENTS,
                    sources=(sequence_id,),
                    targets=(node_id,),
                    transformation_id=f"discover.{family}",
                    exact=False,
                    invertible=False,
                    assumptions=("finite_input",),
                    proof_obligations=("prove_global_identity",),
                )
            )

    profile = hankel_rank_profile(values, max_size=min(16, (len(values) + 1) // 2))
    warnings = [
        "Finite-prefix agreement does not identify a unique infinite continuation.",
        "Every candidate remains unproved globally until a separate proof artifact is attached.",
    ]
    if not any(families.values()):
        warnings.append("No implemented R∞ family produced a non-vacuous candidate.")
    diagnostics = {
        "term_count": len(values),
        "hankel_rank_profile": profile.to_dict(),
        "families_attempted": sorted(families),
        "families_with_candidates": sorted(key for key, value in families.items() if value),
    }
    return RInfDiscoveryReport(values, limits, families, diagnostics, graph, warnings)
