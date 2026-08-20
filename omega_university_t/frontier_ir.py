from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class FrontierItem:
    frontier_id: str
    required_capabilities: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.frontier_id, str) or not self.frontier_id.strip():
            raise ValueError("frontier_id must be a non-empty string")
        if not self.required_capabilities:
            raise ValueError("frontier item must require at least one capability")
        if any(not isinstance(x, str) or not x.strip() for x in self.required_capabilities):
            raise ValueError("required capabilities must be non-empty strings")


@dataclass(frozen=True)
class FrontierReachability:
    frontier_id: str
    required_capabilities: tuple[str, ...]
    missing_capabilities: tuple[str, ...]
    reachable_under_declared_capabilities: bool
    distance: int
    authority: str = "NAVIGATION_ONLY"
    research_success_claimed: bool = False
    scientific_novelty_claimed: bool = False
    external_action_authorized: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def map_frontier(
    items: Iterable[FrontierItem],
    evidence_qualified_capabilities: Iterable[str],
) -> tuple[FrontierReachability, ...]:
    """Map structural distance from declared capabilities to frontier items.

    Reachability means only that declared prerequisites are present. It is not a
    claim that the research question is genuinely open, novel, safe, valuable, or
    solvable by the learner.
    """

    qualified = {str(x).strip() for x in evidence_qualified_capabilities if str(x).strip()}
    rows: list[FrontierReachability] = []
    seen: set[str] = set()

    for item in items:
        frontier_id = item.frontier_id.strip()
        if frontier_id in seen:
            raise ValueError(f"duplicate frontier_id: {frontier_id!r}")
        seen.add(frontier_id)
        required = tuple(sorted(set(item.required_capabilities)))
        missing = tuple(sorted(set(required).difference(qualified)))
        rows.append(
            FrontierReachability(
                frontier_id=frontier_id,
                required_capabilities=required,
                missing_capabilities=missing,
                reachable_under_declared_capabilities=not missing,
                distance=len(missing),
            )
        )

    return tuple(sorted(rows, key=lambda row: (row.distance, row.frontier_id)))
