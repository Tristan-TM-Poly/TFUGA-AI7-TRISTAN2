"""Core engine for Ω-THESIS-2N-GIT-T.

The MVP is intentionally deterministic and dependency-light:
- ThesisSeed captures a theory as a reusable seed.
- build_page_tree expands the seed into a binary LOG/EXP tree.
- oak_report keeps claims at the right maturity level instead of promoting names as proof.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

OAKStatus = Literal["A", "B", "C", "D", "E", "F", "G"]
PageKind = Literal["ROOT", "LOG", "EXP"]

OAK_STATUS_ORDER: tuple[str, ...] = ("A", "B", "C", "D", "E", "F", "G")


@dataclass(frozen=True)
class ThesisSeed:
    """Canonical seed for one Tristan theory/system."""

    id: str
    name: str
    status: OAKStatus
    domain: tuple[str, ...]
    core_axiom: str
    cvcd_invariants: tuple[str, ...]
    oak_risks: tuple[str, ...]
    code_targets: tuple[str, ...]
    git_targets: tuple[str, ...]
    venture_targets: tuple[str, ...]
    m_minus: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""

    def validate(self) -> None:
        if self.status not in OAK_STATUS_ORDER:
            raise ValueError(f"Invalid OAK status: {self.status!r}")
        if not self.id or not self.id.replace("_", "").isalnum() or self.id != self.id.upper():
            raise ValueError("ThesisSeed.id must be uppercase alphanumeric with underscores")
        required_sequences = {
            "domain": self.domain,
            "cvcd_invariants": self.cvcd_invariants,
            "oak_risks": self.oak_risks,
            "code_targets": self.code_targets,
            "git_targets": self.git_targets,
            "venture_targets": self.venture_targets,
        }
        for name, value in required_sequences.items():
            if not value:
                raise ValueError(f"ThesisSeed.{name} must not be empty")
        if len(self.core_axiom.strip()) < 10:
            raise ValueError("ThesisSeed.core_axiom is too short to be useful")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        data = asdict(self)
        for key, value in list(data.items()):
            if isinstance(value, tuple):
                data[key] = list(value)
        return data


@dataclass(frozen=True)
class PageNode:
    """One node in the 2^n thesis expansion tree."""

    id: str
    title: str
    depth: int
    kind: PageKind
    parent_id: str | None
    claims: tuple[str, ...]
    code_targets: tuple[str, ...]
    oak_tests: tuple[str, ...]
    status: OAKStatus

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key, value in list(data.items()):
            if isinstance(value, tuple):
                data[key] = list(value)
        return data


def build_page_tree(seed: ThesisSeed, depth: int) -> list[PageNode]:
    """Expand a theory into a deterministic binary LOG/EXP PageTree.

    Args:
        seed: canonical theory seed.
        depth: expansion depth. depth=0 returns only the root. depth=n returns
            2^(n+1)-1 total nodes, with 2^n frontier pages.
    """

    seed.validate()
    if depth < 0:
        raise ValueError("depth must be >= 0")
    if depth > 16:
        raise ValueError("depth is capped at 16 in the MVP to avoid runaway expansion")

    root = PageNode(
        id=f"{seed.id}:ROOT",
        title=f"{seed.name} — compressed thesis root",
        depth=0,
        kind="ROOT",
        parent_id=None,
        claims=(seed.core_axiom,),
        code_targets=seed.code_targets,
        oak_tests=("validate seed", "classify claims", "record uncertainty"),
        status=seed.status,
    )
    nodes: list[PageNode] = [root]
    frontier: list[PageNode] = [root]

    for level in range(1, depth + 1):
        next_frontier: list[PageNode] = []
        for parent in frontier:
            log_node = PageNode(
                id=f"{parent.id}/LOG{level}",
                title=f"LOG compression of {parent.title}",
                depth=level,
                kind="LOG",
                parent_id=parent.id,
                claims=tuple(seed.cvcd_invariants),
                code_targets=("canon_manifest", "invariant_extractor"),
                oak_tests=("definition check", "invariant survival check", "overclaim scan"),
                status=seed.status,
            )
            exp_node = PageNode(
                id=f"{parent.id}/EXP{level}",
                title=f"EXP fertile expansion of {parent.title}",
                depth=level,
                kind="EXP",
                parent_id=parent.id,
                claims=tuple(seed.venture_targets),
                code_targets=tuple(seed.code_targets),
                oak_tests=("prototype path check", "baseline requirement", "M- failure-mode capture"),
                status=seed.status,
            )
            nodes.extend([log_node, exp_node])
            next_frontier.extend([log_node, exp_node])
        frontier = next_frontier

    return nodes


def oak_report(seed: ThesisSeed, nodes: list[PageNode]) -> dict[str, Any]:
    """Return a compact OAK report for the current thesis expansion."""

    seed.validate()
    if not nodes:
        raise ValueError("nodes must not be empty")
    frontier_depth = max(node.depth for node in nodes)
    frontier_count = sum(1 for node in nodes if node.depth == frontier_depth)
    kind_counts: dict[str, int] = {}
    for node in nodes:
        kind_counts[node.kind] = kind_counts.get(node.kind, 0) + 1

    blocked_promotions = []
    if seed.status in {"A", "B", "C"}:
        blocked_promotions.append(
            "Do not claim proof, industrial validation, revenue certainty, or scientific novelty beyond current OAK evidence."
        )
    if seed.oak_risks:
        blocked_promotions.append("Risk register must remain attached to every export.")

    return {
        "seed_id": seed.id,
        "seed_name": seed.name,
        "status": seed.status,
        "total_nodes": len(nodes),
        "frontier_depth": frontier_depth,
        "frontier_pages": frontier_count,
        "kind_counts": kind_counts,
        "expected_total_nodes": (2 ** (frontier_depth + 1)) - 1,
        "expected_frontier_pages": 2**frontier_depth,
        "oak_risks": list(seed.oak_risks),
        "blocked_promotions": blocked_promotions,
        "git_targets": list(seed.git_targets),
        "next_actions": [
            "write thesis_seed.yaml/json",
            "generate PageTree JSON",
            "create code skeleton",
            "attach tests and baselines",
            "open PR instead of pushing directly to protected branches",
        ],
    }


def example_seed() -> ThesisSeed:
    """Seed used by tests and demo scripts."""

    return ThesisSeed(
        id="OMEGA_THESIS_2N_GIT_T",
        name="Ω-THESIS-2N-GIT-T",
        status="C",
        domain=("research-architecture", "software", "git", "venture"),
        core_axiom=(
            "A Tristan theory is a compressed seed that expands into theses, code, OAKBench, Git artifacts, IP, and venture paths."
        ),
        cvcd_invariants=(
            "theory-to-artifact traceability",
            "LOG/EXP reversible compression discipline",
            "OAK status must cap claim strength",
            "M- captures every failure mode",
        ),
        oak_risks=(
            "overclaiming unvalidated theories",
            "runaway text expansion without tests",
            "mixing metaphor with proof",
            "unsafe autonomous Git actions",
        ),
        code_targets=("python_package", "cli", "tests", "oak_report"),
        git_targets=("branch", "pull_request", "docs", "schemas", "ci_candidate"),
        venture_targets=("thesis_factory", "research_os", "ip_brief_generator", "company_compiler"),
        m_minus=("2^n pages without OAK creates entropy, not knowledge",),
    )
