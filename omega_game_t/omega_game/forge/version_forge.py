"""VersionForge-T for Ω-GAME-T+++.

Convert FeedbackLoopResult objects into internal OAK-safe version plans.
This module does not create Git tags, releases, commits, or external actions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .feedback_loop import FeedbackLoopResult


@dataclass(slots=True)
class VersionChange:
    category: str
    description: str
    source_memory: str
    priority: str = "p1"

    def __post_init__(self) -> None:
        if self.category not in {"add", "change", "fix", "measure", "oak"}:
            raise ValueError("VersionChange.category must be add/change/fix/measure/oak.")
        if self.priority not in {"p0", "p1", "p2"}:
            raise ValueError("VersionChange.priority must be p0, p1 or p2.")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class ReleaseCriteria:
    tests: list[str]
    oak_gates: list[str]
    memory_checks: list[str]
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class VersionPlan:
    product_name: str
    target_engine: str
    version: str
    release_type: str
    confidence_score: float
    changes: list[VersionChange]
    release_criteria: ReleaseCriteria
    changelog: list[str]
    next_actions: list[str]

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("VersionPlan.version must be non-empty.")
        if self.release_type != "internal_iteration":
            raise ValueError("VersionPlan.release_type must remain internal_iteration.")
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("VersionPlan.confidence_score must be in [0, 1].")
        if not self.changes:
            raise ValueError("VersionPlan.changes must be non-empty.")

    def to_dict(self) -> dict[str, object]:
        return {
            "product_name": self.product_name,
            "target_engine": self.target_engine,
            "version": self.version,
            "release_type": self.release_type,
            "confidence_score": self.confidence_score,
            "changes": [change.to_dict() for change in self.changes],
            "release_criteria": self.release_criteria.to_dict(),
            "changelog": list(self.changelog),
            "next_actions": list(self.next_actions),
        }

    def to_markdown(self) -> str:
        changes = "\n".join(
            f"- [{change.priority.upper()}] {change.category}: {change.description}"
            for change in self.changes
        )
        criteria_tests = "\n".join(f"- [ ] {item}" for item in self.release_criteria.tests)
        criteria_oak = "\n".join(f"- [ ] {item}" for item in self.release_criteria.oak_gates)
        memory = "\n".join(f"- [ ] {item}" for item in self.release_criteria.memory_checks)
        blockers = "\n".join(f"- {item}" for item in self.release_criteria.blockers)
        changelog = "\n".join(f"- {item}" for item in self.changelog)
        actions = "\n".join(f"- [ ] {item}" for item in self.next_actions)
        return (
            f"# {self.product_name} {self.version}\n\n"
            f"Release type: `{self.release_type}`\n\n"
            f"Engine: `{self.target_engine}`\n\n"
            f"Confidence: `{self.confidence_score:.3f}`\n\n"
            f"## Planned changes\n\n{changes}\n\n"
            f"## Release criteria — tests\n\n{criteria_tests}\n\n"
            f"## Release criteria — OAK\n\n{criteria_oak}\n\n"
            f"## Memory checks\n\n{memory}\n\n"
            f"## Blockers\n\n{blockers}\n\n"
            f"## Changelog draft\n\n{changelog}\n\n"
            f"## Next actions\n\n{actions}\n"
        )


class VersionForge:
    """Generate version plans from feedback loop results."""

    def forge(self, feedback: FeedbackLoopResult) -> VersionPlan:
        changes = self._changes(feedback)
        criteria = self._criteria(feedback)
        return VersionPlan(
            product_name=feedback.product_name,
            target_engine=feedback.target_engine,
            version=feedback.decision.next_version,
            release_type="internal_iteration",
            confidence_score=feedback.confidence_score,
            changes=changes,
            release_criteria=criteria,
            changelog=self._changelog(feedback, changes),
            next_actions=self._next_actions(feedback),
        )

    def forge_many(self, feedback_results: list[FeedbackLoopResult]) -> list[VersionPlan]:
        return [self.forge(result) for result in feedback_results]

    def _changes(self, feedback: FeedbackLoopResult) -> list[VersionChange]:
        changes: list[VersionChange] = []
        for pattern in feedback.m_plus:
            changes.append(
                VersionChange(
                    category="add",
                    description=f"Amplify positive pattern `{pattern}` in the next version.",
                    source_memory=pattern,
                    priority="p1",
                )
            )
        for pattern in feedback.m_minus:
            changes.append(
                VersionChange(
                    category="fix",
                    description=f"Reduce negative pattern `{pattern}` before release review.",
                    source_memory=pattern,
                    priority="p0" if "ip" in pattern or "pricing" in pattern else "p1",
                )
            )
        changes.append(
            VersionChange(
                category="measure",
                description="Re-run ProductBench and FeedbackLoop after changes.",
                source_memory="feedback_loop_result",
                priority="p0",
            )
        )
        changes.append(
            VersionChange(
                category="oak",
                description="Keep version internal until OAK criteria are checked.",
                source_memory="oak_controls",
                priority="p0",
            )
        )
        return changes

    def _criteria(self, feedback: FeedbackLoopResult) -> ReleaseCriteria:
        blockers = []
        if any("ip" in item for item in feedback.m_minus):
            blockers.append("ip_review_required")
        if any("pricing" in item for item in feedback.m_minus):
            blockers.append("pricing_signal_missing_or_unreviewed")
        if feedback.confidence_score < 0.55:
            blockers.append("confidence_below_targeted_demo_threshold")
        return ReleaseCriteria(
            tests=[
                "unit_tests_pass",
                "version_plan_serializes_to_dict",
                "markdown_preview_generated",
            ],
            oak_gates=list(dict.fromkeys(feedback.oak_controls + ["no_public_release_from_version_plan"])),
            memory_checks=[
                "m_plus_patterns_have_follow_up_changes",
                "m_minus_patterns_have_mitigation_changes",
                "next_version_matches_feedback_decision",
            ],
            blockers=blockers,
        )

    def _changelog(self, feedback: FeedbackLoopResult, changes: list[VersionChange]) -> list[str]:
        return [
            f"Planned `{feedback.decision.next_version}` as an internal iteration.",
            f"Decision: {feedback.decision.decision}.",
            f"Confidence score: {feedback.confidence_score:.3f}.",
            f"Changes planned: {len(changes)}.",
        ]

    @staticmethod
    def _next_actions(feedback: FeedbackLoopResult) -> list[str]:
        return [
            "create_version_notes",
            "map_p0_changes_to_issues",
            "apply_changes_in_small_sprint",
            "rerun_product_bench",
            "rerun_feedback_loop",
            "review_oak_blockers_before_release",
        ]


def default_version_forge() -> VersionForge:
    return VersionForge()


__all__ = [
    "ReleaseCriteria",
    "VersionChange",
    "VersionForge",
    "VersionPlan",
    "default_version_forge",
]
