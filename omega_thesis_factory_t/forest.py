"""Fractal order-n thesis forest for Ω-THESIS-2N-GIT-T.

This module extends the existing thesis factory instead of introducing a second
thesis ontology.  It treats a thesis as a zoomable research node whose fractal
order is independent from its OAK maturity.

Design invariants:
- order n measures specialization depth, never epistemic quality;
- ZOOM is sparse and selected by the merged GO MAX / GO MIN metric;
- ZOOM never promotes OAK status;
- DEZOOM emits a review receipt and never mutates ancestors implicitly;
- logical depth may grow, while each runtime expansion remains bounded.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Literal, Mapping

from omega_generative_closure_t.core import MaxMinVector

from .core import OAK_STATUS_ORDER, OAKStatus, ThesisSeed

PropagationAction = Literal[
    "NO_CHANGE",
    "REVIEW",
    "UPDATE",
    "SUPPORT",
    "GENERALIZE",
    "REFUTE",
    "REOPEN",
]


def _segment(value: str) -> str:
    normalized = "_".join(value.strip().upper().replace("-", "_").split())
    if not normalized or not normalized.replace("_", "").isalnum():
        raise ValueError(f"invalid thesis address segment: {value!r}")
    return normalized


@dataclass(frozen=True)
class ThesisAddress:
    """Stable fractal address for a thesis node.

    The root is the canonical ThesisSeed id.  Each path component is one ZOOM
    specialization.  Therefore order == len(path).
    """

    root: str
    path: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", _segment(self.root))
        object.__setattr__(self, "path", tuple(_segment(x) for x in self.path))

    @property
    def order(self) -> int:
        return len(self.path)

    @property
    def uri(self) -> str:
        return "OMEGAT://" + "/".join((self.root, *self.path))

    def child(self, segment: str) -> "ThesisAddress":
        return ThesisAddress(self.root, self.path + (_segment(segment),))

    @property
    def parent(self) -> "ThesisAddress | None":
        if not self.path:
            return None
        return ThesisAddress(self.root, self.path[:-1])


@dataclass(frozen=True)
class ThesisNode:
    """One research node in the fractal thesis forest."""

    address: ThesisAddress
    title: str
    focus: str
    research_question: str
    status: OAKStatus
    parent_id: str | None = None
    local_claims: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    baselines: tuple[str, ...] = field(default_factory=tuple)
    falsifiers: tuple[str, ...] = field(default_factory=tuple)
    uncertainty: float = 1.0

    @property
    def id(self) -> str:
        return self.address.uri

    @property
    def order(self) -> int:
        return self.address.order

    def validate(self) -> None:
        if self.status not in OAK_STATUS_ORDER:
            raise ValueError(f"invalid OAK status: {self.status!r}")
        if not self.title.strip() or not self.focus.strip() or not self.research_question.strip():
            raise ValueError("title, focus, and research_question must not be empty")
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("uncertainty must be normalized to [0, 1]")
        expected_parent = self.address.parent.uri if self.address.parent else None
        if self.parent_id != expected_parent:
            raise ValueError(
                f"parent_id mismatch for {self.id}: expected {expected_parent!r}, got {self.parent_id!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "id": self.id,
            "order": self.order,
            "address": {"root": self.address.root, "path": list(self.address.path)},
            "title": self.title,
            "focus": self.focus,
            "research_question": self.research_question,
            "status": self.status,
            "parent_id": self.parent_id,
            "local_claims": list(self.local_claims),
            "evidence_refs": list(self.evidence_refs),
            "baselines": list(self.baselines),
            "falsifiers": list(self.falsifiers),
            "uncertainty": self.uncertainty,
        }


@dataclass(frozen=True)
class ZoomCandidate:
    """Candidate child thesis scored by the canonical GO MAX / GO MIN vector.

    Inputs are normalized to [0, 1] so power-density scores remain comparable
    inside one local ZOOM court.  The score is a planning proxy, not scientific
    evidence and not a claim of global optimality.
    """

    segment: str
    title: str
    focus: str
    research_question: str
    verified_value: float = 0.0
    evidence: float = 0.0
    reuse: float = 0.0
    reachability: float = 0.0
    regenerability: float = 0.0
    fertility: float = 0.0
    cost: float = 0.0
    structural_debt: float = 0.0
    proof_debt: float = 0.0
    semantic_debt: float = 0.0
    uncertainty: float = 0.0
    irreversibility: float = 0.0
    baselines: tuple[str, ...] = field(default_factory=tuple)
    falsifiers: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        _segment(self.segment)
        if not self.title.strip() or not self.focus.strip() or not self.research_question.strip():
            raise ValueError("candidate title, focus, and research_question must not be empty")
        for name in (
            "verified_value",
            "evidence",
            "reuse",
            "reachability",
            "regenerability",
            "fertility",
            "cost",
            "structural_debt",
            "proof_debt",
            "semantic_debt",
            "uncertainty",
            "irreversibility",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be normalized to [0, 1]")

    def vector(self) -> MaxMinVector:
        self.validate()
        return MaxMinVector(
            verified_value=self.verified_value,
            evidence=self.evidence,
            reuse=self.reuse,
            reachability=self.reachability,
            regenerability=self.regenerability,
            fertility=self.fertility,
            cost=self.cost,
            structural_debt=self.structural_debt,
            proof_debt=self.proof_debt,
            semantic_debt=self.semantic_debt,
            uncertainty=self.uncertainty,
            irreversibility=self.irreversibility,
        )

    @property
    def power_density(self) -> float:
        return self.vector().power_density()


@dataclass(frozen=True)
class ZoomPolicy:
    min_power_density: float = 0.45
    max_active_children: int = 4
    max_order: int | None = 16

    def validate(self) -> None:
        if self.min_power_density < 0.0:
            raise ValueError("min_power_density must be >= 0")
        if self.max_active_children <= 0:
            raise ValueError("max_active_children must be > 0")
        if self.max_order is not None and self.max_order < 0:
            raise ValueError("max_order must be >= 0 or None")


@dataclass(frozen=True)
class ZoomReceipt:
    parent_id: str
    parent_order: int
    candidate_count: int
    selected_ids: tuple[str, ...]
    rejected: tuple[tuple[str, str], ...]
    min_power_density: float
    max_active_children: int
    max_order: int | None
    oak_status_promoted: bool = False
    global_optimum_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "parent_id": self.parent_id,
            "parent_order": self.parent_order,
            "candidate_count": self.candidate_count,
            "selected_ids": list(self.selected_ids),
            "rejected": [{"segment": key, "reason": reason} for key, reason in self.rejected],
            "min_power_density": self.min_power_density,
            "max_active_children": self.max_active_children,
            "max_order": self.max_order,
            "oak_status_promoted": self.oak_status_promoted,
            "global_optimum_claimed": self.global_optimum_claimed,
        }


@dataclass
class ThesisForest:
    """Small canonical graph store for thesis nodes.

    Cross-links such as Venn/shared-evidence can live in higher graph layers;
    this class only enforces the ZOOM parent relation and deterministic ancestry.
    """

    nodes: dict[str, ThesisNode] = field(default_factory=dict)

    def add(self, node: ThesisNode) -> None:
        node.validate()
        if node.id in self.nodes:
            raise ValueError(f"duplicate thesis node: {node.id}")
        if node.parent_id is not None and node.parent_id not in self.nodes:
            raise ValueError(f"missing parent {node.parent_id!r} for {node.id}")
        self.nodes[node.id] = node

    def get(self, node_id: str) -> ThesisNode:
        return self.nodes[node_id]

    def children(self, node_id: str) -> tuple[ThesisNode, ...]:
        return tuple(sorted((n for n in self.nodes.values() if n.parent_id == node_id), key=lambda n: n.id))

    def ancestors(self, node_id: str) -> tuple[ThesisNode, ...]:
        out: list[ThesisNode] = []
        current = self.get(node_id)
        while current.parent_id is not None:
            current = self.get(current.parent_id)
            out.append(current)
        return tuple(out)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "omega-thesis-fractal/v0.1",
            "nodes": [self.nodes[key].to_dict() for key in sorted(self.nodes)],
        }


def root_thesis(seed: ThesisSeed) -> ThesisNode:
    """Compile a canonical ThesisSeed into the order-0 thesis node."""

    seed.validate()
    return ThesisNode(
        address=ThesisAddress(seed.id),
        title=seed.name,
        focus=seed.core_axiom,
        research_question="Which claims, tests, and residuals should this thesis resolve without exceeding its OAK status?",
        status=seed.status,
        parent_id=None,
        local_claims=(seed.core_axiom,),
        baselines=(),
        falsifiers=tuple(seed.oak_risks),
        uncertainty=1.0 if seed.status in {"A", "B"} else 0.75,
    )


def zoom_thesis(
    parent: ThesisNode,
    candidates: Iterable[ZoomCandidate],
    *,
    policy: ZoomPolicy = ZoomPolicy(),
) -> tuple[tuple[ThesisNode, ...], ZoomReceipt]:
    """Select a sparse order-(n+1) child set under GO MAX / GO MIN.

    Selection is local and deterministic.  It never upgrades the parent's OAK
    status and never claims a globally optimal thesis decomposition.
    """

    parent.validate()
    policy.validate()
    ordered = list(candidates)
    for candidate in ordered:
        candidate.validate()

    rejected: list[tuple[str, str]] = []
    selected: list[ThesisNode] = []
    seen_segments: set[str] = set()

    if policy.max_order is not None and parent.order >= policy.max_order:
        rejected.extend((_segment(c.segment), "max_order_reached") for c in ordered)
    else:
        ranked = sorted(ordered, key=lambda c: (-c.power_density, _segment(c.segment)))
        for candidate in ranked:
            segment = _segment(candidate.segment)
            if segment in seen_segments:
                rejected.append((segment, "duplicate_segment"))
                continue
            seen_segments.add(segment)
            if candidate.power_density < policy.min_power_density:
                rejected.append((segment, "below_min_power_density"))
                continue
            if len(selected) >= policy.max_active_children:
                rejected.append((segment, "active_child_budget_exhausted"))
                continue
            address = parent.address.child(segment)
            selected.append(
                ThesisNode(
                    address=address,
                    title=candidate.title,
                    focus=candidate.focus,
                    research_question=candidate.research_question,
                    status=parent.status,
                    parent_id=parent.id,
                    local_claims=(),
                    evidence_refs=(),
                    baselines=candidate.baselines,
                    falsifiers=candidate.falsifiers,
                    uncertainty=candidate.uncertainty,
                )
            )

    receipt = ZoomReceipt(
        parent_id=parent.id,
        parent_order=parent.order,
        candidate_count=len(ordered),
        selected_ids=tuple(node.id for node in selected),
        rejected=tuple(rejected),
        min_power_density=policy.min_power_density,
        max_active_children=policy.max_active_children,
        max_order=policy.max_order,
    )
    return tuple(selected), receipt


@dataclass(frozen=True)
class DezoomReceipt:
    """Review-only propagation proposal from a local result to ancestors."""

    source_id: str
    source_order: int
    result: str
    scope: str
    uncertainty: float
    propagation: tuple[tuple[str, PropagationAction], ...]
    ancestor_mutation_performed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_order": self.source_order,
            "result": self.result,
            "scope": self.scope,
            "uncertainty": self.uncertainty,
            "propagation": [
                {"ancestor_id": ancestor_id, "action": action}
                for ancestor_id, action in self.propagation
            ],
            "ancestor_mutation_performed": self.ancestor_mutation_performed,
        }


def dezoom_result(
    forest: ThesisForest,
    source_id: str,
    *,
    result: str,
    scope: str,
    uncertainty: float,
    actions: Mapping[str, PropagationAction] | None = None,
) -> DezoomReceipt:
    """Compile local evidence into a review-only ancestor propagation receipt."""

    if not result.strip() or not scope.strip():
        raise ValueError("result and scope must not be empty")
    if not 0.0 <= uncertainty <= 1.0:
        raise ValueError("uncertainty must be normalized to [0, 1]")
    source = forest.get(source_id)
    ancestors = forest.ancestors(source_id)
    allowed_ids = {node.id for node in ancestors}
    explicit = dict(actions or {})
    unknown = set(explicit).difference(allowed_ids)
    if unknown:
        raise ValueError(f"dezoom actions target non-ancestors: {sorted(unknown)!r}")
    propagation = tuple((node.id, explicit.get(node.id, "REVIEW")) for node in ancestors)
    return DezoomReceipt(
        source_id=source.id,
        source_order=source.order,
        result=result,
        scope=scope,
        uncertainty=uncertainty,
        propagation=propagation,
    )


def thesis_forest_oak_report(forest: ThesisForest) -> dict[str, Any]:
    """Check structural/OAK invariants without asserting scientific validity."""

    if not forest.nodes:
        raise ValueError("forest must not be empty")
    nodes = tuple(forest.nodes.values())
    roots = tuple(node for node in nodes if node.parent_id is None)
    order_errors: list[str] = []
    for node in nodes:
        node.validate()
        if node.parent_id is not None:
            parent = forest.get(node.parent_id)
            if node.order != parent.order + 1:
                order_errors.append(node.id)
    return {
        "schema_version": "omega-thesis-fractal/oak/v0.1",
        "node_count": len(nodes),
        "root_count": len(roots),
        "max_order": max(node.order for node in nodes),
        "order_parent_errors": sorted(order_errors),
        "order_is_epistemic_quality": False,
        "zoom_promotes_oak_status": False,
        "dezoom_auto_mutates_ancestors": False,
        "scientific_validity_certified": False,
        "status_counts": {
            status: sum(1 for node in nodes if node.status == status)
            for status in OAK_STATUS_ORDER
            if any(node.status == status for node in nodes)
        },
    }


def demo_zoom_candidates() -> tuple[ZoomCandidate, ...]:
    """Deterministic candidate fixture for docs/tests/demos."""

    return (
        ZoomCandidate(
            segment="HGFM",
            title="HGFM recursive thesis",
            focus="recursive multi-scale hypergraph structure",
            research_question="Which recursive HGFM operators survive explicit baseline comparison?",
            verified_value=0.6,
            evidence=0.5,
            reuse=0.9,
            reachability=0.8,
            regenerability=0.8,
            fertility=0.9,
            cost=0.4,
            structural_debt=0.2,
            proof_debt=0.5,
            semantic_debt=0.2,
            uncertainty=0.5,
            irreversibility=0.0,
            baselines=("typed_hypergraph", "property_graph"),
            falsifiers=("no measurable multi-scale advantage",),
        ),
        ZoomCandidate(
            segment="OAK",
            title="OAK falsification thesis",
            focus="claim/evidence/falsification governance",
            research_question="Does OAK reduce unsupported promotions against a simpler evidence ledger?",
            verified_value=0.7,
            evidence=0.7,
            reuse=0.9,
            reachability=0.7,
            regenerability=0.8,
            fertility=0.8,
            cost=0.3,
            structural_debt=0.1,
            proof_debt=0.2,
            semantic_debt=0.1,
            uncertainty=0.3,
            irreversibility=0.0,
            baselines=("plain_evidence_ledger",),
            falsifiers=("no reduction in unsupported claim promotion",),
        ),
        ZoomCandidate(
            segment="DECORATIVE_BRANCH",
            title="Decorative branch",
            focus="naming without a differential experiment",
            research_question="Can naming alone improve evidence?",
            verified_value=0.0,
            evidence=0.0,
            reuse=0.0,
            reachability=0.1,
            regenerability=0.0,
            fertility=0.1,
            cost=0.7,
            structural_debt=0.9,
            proof_debt=0.9,
            semantic_debt=0.8,
            uncertainty=0.9,
            irreversibility=0.0,
        ),
    )
