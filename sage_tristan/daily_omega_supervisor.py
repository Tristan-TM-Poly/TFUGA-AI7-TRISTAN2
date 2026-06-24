"""Reusable supervisor for Daily Omega issue specifications.

The module stays side-effect free: it prepares a decision and an issue spec,
but does not call GitHub. This keeps the workflow reusable across repos while
preserving OAK review before publication or action.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sage_tristan.daily_omega_briefing import BriefingItem
from sage_tristan.daily_omega_router import IssueSpec, make_issue_spec, route_item

REVIEW_ONLY_POSTURES = {"confidential_ip_review", "trade_secret_candidate"}


@dataclass(frozen=True)
class SupervisionDecision:
    """Review result for one issue specification."""

    allowed: bool
    mode: str
    reasons: tuple[str, ...]
    issue_spec: IssueSpec

    def render_markdown(self) -> str:
        status = "ALLOW" if self.allowed else "REVIEW"
        lines = [
            f"# Daily Omega Decision: {status}",
            "",
            f"Mode: `{self.mode}`",
            "",
            "## Reasons",
        ]
        lines.extend(f"- {reason}" for reason in self.reasons)
        lines.extend(
            [
                "",
                "## Issue spec",
                f"Title: {self.issue_spec.title}",
                f"Labels: {', '.join(self.issue_spec.labels)}",
            ]
        )
        return "\n".join(lines).strip() + "\n"


def _has_source_quality(item: BriefingItem, minimum_quality: int) -> bool:
    return any(source.source_quality >= minimum_quality for source in item.sources)


def _has_action(item: BriefingItem) -> bool:
    return bool(item.next_action.strip() and item.actionable_opportunity.strip())


def _has_oak(item: BriefingItem) -> bool:
    return bool(item.oak_check.risk.strip() and item.oak_check.falsification_route.strip())


def supervise_issue_spec(
    item: BriefingItem,
    *,
    dry_run: bool = True,
    minimum_source_quality: int = 3,
    allow_review_only: bool = False,
) -> SupervisionDecision:
    """Return a reusable gate decision for one Daily Omega item."""

    route = route_item(item)
    issue_spec = make_issue_spec(item)
    reasons: list[str] = []

    if dry_run:
        reasons.append("dry-run mode: keep as reviewable spec")
    if not _has_source_quality(item, minimum_source_quality):
        reasons.append("needs review: source quality threshold not met")
    if not _has_action(item):
        reasons.append("needs review: missing concrete action")
    if not _has_oak(item):
        reasons.append("needs review: missing OAK risk or falsification route")
    if route.ip_classification in REVIEW_ONLY_POSTURES and not allow_review_only:
        reasons.append(f"needs review: posture is {route.ip_classification}")
    if item.final_score < 12:
        reasons.append("needs review: score below creation threshold")

    needs_review = any(reason.startswith("needs review") for reason in reasons)
    allowed = (not dry_run) and (not needs_review)
    mode = "create_issue" if allowed else "review_spec"

    if allowed:
        reasons.append("allowed: source, action, OAK, posture, and score gates passed")
    elif not reasons:
        reasons.append("review default: explicit approval still required")

    return SupervisionDecision(
        allowed=allowed,
        mode=mode,
        reasons=tuple(reasons),
        issue_spec=issue_spec,
    )


def supervise_many(
    items: Iterable[BriefingItem],
    *,
    dry_run: bool = True,
    minimum_source_quality: int = 3,
    allow_review_only: bool = False,
) -> list[SupervisionDecision]:
    """Return gate decisions for many Daily Omega items."""

    return [
        supervise_issue_spec(
            item,
            dry_run=dry_run,
            minimum_source_quality=minimum_source_quality,
            allow_review_only=allow_review_only,
        )
        for item in items
    ]


__all__ = [
    "REVIEW_ONLY_POSTURES",
    "SupervisionDecision",
    "supervise_issue_spec",
    "supervise_many",
]
