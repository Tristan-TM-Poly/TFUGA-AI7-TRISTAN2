"""512-unit research-monograph planner built on Ω-THESIS-2N-GIT-T.

The key reuse invariant is 512 = 2**9: the existing LOG/EXP PageTree already
provides an exact 512-node frontier at depth 9. This module maps that frontier
into an evidence-first monograph budget without treating page count as proof or
scientific quality.

A second structural invariant is equally useful: the depth-9 frontier is formed
by 256 sibling LOG/EXP dyads. Each dyad can be used as a research unit:

LOG -> compress definitions, assumptions, invariants, evidence and limits.
EXP -> expand counterexamples, experiments, applications and implications.

These are planning units. The compiled PDF remains the only source of truth for
actual page count.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .core import PageNode, ThesisSeed, build_page_tree, oak_report

TARGET_PAGES = 512
PAGE_TREE_DEPTH = 9
TARGET_DYADS = TARGET_PAGES // 2


@dataclass(frozen=True)
class SectionBudget:
    id: str
    title: str
    pages: int
    evidence_class: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchDyad:
    """One sibling LOG/EXP pair at the depth-9 planning frontier."""

    id: str
    parent_id: str
    log_node_id: str
    exp_node_id: str
    log_role: str = "definitions+assumptions+invariants+evidence+limits"
    exp_role: str = "counterexamples+experiments+applications+implications"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_BUDGET: tuple[SectionBudget, ...] = (
    SectionBudget("front", "Front matter", 24, "navigation"),
    SectionBudget("p1", "Problem, prior art, foundations", 48, "literature+definitions"),
    SectionBudget("p2", "Formal mycelial systems calculus", 84, "formal"),
    SectionBudget("p3", "Architecture and compilers", 84, "implementation+formal"),
    SectionBudget("p4", "Evidence, trust, OAK and UNC2", 72, "evidence+governance"),
    SectionBudget("p5", "Learning, evolution and self-hosting", 60, "algorithmic+empirical"),
    SectionBudget("p6", "Experiments and case studies", 80, "empirical"),
    SectionBudget("p7", "Synthesis and conclusion", 24, "synthesis"),
    SectionBudget("bib", "Bibliography", 24, "literature"),
    SectionBudget("app", "Appendices", 12, "reproducibility"),
)


def validate_budget(budget: Iterable[SectionBudget] = DEFAULT_BUDGET) -> None:
    items = tuple(budget)
    if not items:
        raise ValueError("budget must not be empty")
    if any(item.pages <= 0 for item in items):
        raise ValueError("all section budgets must be positive")
    total = sum(item.pages for item in items)
    if total != TARGET_PAGES:
        raise ValueError(f"budget must sum to {TARGET_PAGES}, got {total}")
    ids = [item.id for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("section budget ids must be unique")


def frontier_512(seed: ThesisSeed) -> tuple[PageNode, ...]:
    """Return the exact 512-node LOG/EXP frontier from the existing engine."""
    nodes = build_page_tree(seed, PAGE_TREE_DEPTH)
    frontier = tuple(node for node in nodes if node.depth == PAGE_TREE_DEPTH)
    if len(frontier) != TARGET_PAGES:
        raise AssertionError(f"expected {TARGET_PAGES} frontier nodes, got {len(frontier)}")
    return frontier


def frontier_dyads_256(seed: ThesisSeed) -> tuple[ResearchDyad, ...]:
    """Pair the 512 frontier nodes into 256 sibling LOG/EXP research dyads."""
    grouped: dict[str, dict[str, PageNode]] = {}
    for node in frontier_512(seed):
        if node.parent_id is None:
            raise AssertionError("frontier node unexpectedly has no parent")
        grouped.setdefault(node.parent_id, {})[node.kind] = node

    dyads: list[ResearchDyad] = []
    for index, parent_id in enumerate(sorted(grouped), start=1):
        pair = grouped[parent_id]
        if set(pair) != {"LOG", "EXP"}:
            raise AssertionError(f"parent {parent_id!r} is not a complete LOG/EXP dyad")
        dyads.append(
            ResearchDyad(
                id=f"DYAD-{index:03d}",
                parent_id=parent_id,
                log_node_id=pair["LOG"].id,
                exp_node_id=pair["EXP"].id,
            )
        )

    if len(dyads) != TARGET_DYADS:
        raise AssertionError(f"expected {TARGET_DYADS} dyads, got {len(dyads)}")
    return tuple(dyads)


def allocate_frontier(seed: ThesisSeed, budget: Iterable[SectionBudget] = DEFAULT_BUDGET) -> list[dict[str, Any]]:
    """Assign each frontier node to exactly one page-budget region.

    This is a planning allocation only. The actual compiled PDF remains the
    source of truth for page count.
    """
    items = tuple(budget)
    validate_budget(items)
    frontier = frontier_512(seed)
    rows: list[dict[str, Any]] = []
    offset = 0
    for section in items:
        for local_page, node in enumerate(frontier[offset : offset + section.pages], start=1):
            rows.append(
                {
                    "planned_page": offset + local_page,
                    "section_id": section.id,
                    "section_title": section.title,
                    "evidence_class": section.evidence_class,
                    "page_node_id": node.id,
                    "page_node_kind": node.kind,
                    "claim_seed": list(node.claims),
                    "oak_tests": list(node.oak_tests),
                    "status": node.status,
                }
            )
        offset += section.pages
    if len(rows) != TARGET_PAGES:
        raise AssertionError("frontier allocation is not bijective")
    return rows


def build_monograph_plan(seed: ThesisSeed) -> dict[str, Any]:
    """Build a deterministic 512-unit planning receipt.

    OAK note: this proves only structural allocation consistency. It does not
    prove that a later LaTeX build has 512 pages, nor that any scientific claim
    is true or novel.
    """
    validate_budget()
    nodes = build_page_tree(seed, PAGE_TREE_DEPTH)
    report = oak_report(seed, nodes)
    allocation = allocate_frontier(seed)
    dyads = frontier_dyads_256(seed)
    return {
        "target_pages": TARGET_PAGES,
        "page_tree_depth": PAGE_TREE_DEPTH,
        "identity": "512 == 2**9",
        "dyad_identity": "512 frontier nodes == 256 LOG/EXP sibling dyads",
        "dyad_count": len(dyads),
        "compiled_page_count_is_source_of_truth": True,
        "structural_plan_status": "PASS",
        "scientific_validation_status": "NOT_IMPLIED",
        "budget": [item.to_dict() for item in DEFAULT_BUDGET],
        "page_tree": report,
        "dyads": [dyad.to_dict() for dyad in dyads],
        "allocation": allocation,
        "oak_invariants": [
            "page allocation is not scientific evidence",
            "512 planning nodes are not 512 compiled PDF pages",
            "LOG/EXP dyads are research-planning structure, not proof",
            "compiled PDF page count must be measured separately",
            "test passed is not scientific proof",
            "GitHub provenance is not peer review",
            "unsupported claims remain HOLD",
        ],
    }
