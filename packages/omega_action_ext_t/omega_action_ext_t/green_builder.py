"""OAK-safe PR build-to-green planner.

This module does not call GitHub or mutate repositories. It converts a PR
state snapshot into a bounded repair/enrichment plan that another approved
connector can execute in dry-run or reviewed mode.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence


class PRBlocker(str, Enum):
    """Known reasons why a pull request is not green yet."""

    DRAFT = "draft"
    CONFLICT = "conflict"
    FAILING_CHECK = "failing_check"
    PENDING_CHECK = "pending_check"
    MISSING_CHECK = "missing_check"
    AMBIGUOUS_STATUS = "ambiguous_status"
    SAFETY_AMBIGUITY = "safety_ambiguity"
    NEEDS_MANUAL_JUDGMENT = "needs_manual_judgment"


class BuildAction(str, Enum):
    """Safe action categories for moving a PR toward green."""

    INSPECT = "inspect"
    ADD_TEST = "add_test"
    ADD_DOC = "add_doc"
    ADD_VALIDATOR = "add_validator"
    ADD_GUARDRAIL = "add_guardrail"
    ADD_REPAIR_REPORT = "add_repair_report"
    REQUEST_MANUAL_RESOLUTION = "request_manual_resolution"
    MERGE_WHEN_CLEAN = "merge_when_clean"
    SKIP = "skip"


@dataclass(frozen=True)
class PRGreenState:
    """Minimal PR state required by the build-to-green planner."""

    number: int
    title: str
    draft: bool
    mergeable: bool | None
    checks_state: str = "unknown"
    has_conflicts: bool = False
    changed_files: tuple[str, ...] = ()
    safety_flags: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class GreenStep:
    """One bounded action in a PR build-to-green plan."""

    action: BuildAction
    reason: str
    target: str = ""
    requires_human: bool = False


@dataclass(frozen=True)
class GreenPlan:
    """Plan for safe PR enrichment and eventual merge."""

    pr_number: int
    decision: str
    blockers: tuple[PRBlocker, ...]
    steps: tuple[GreenStep, ...]

    @property
    def can_auto_enrich(self) -> bool:
        return self.decision == "auto_enrich"

    @property
    def can_merge_now(self) -> bool:
        return self.decision == "merge_now"


def classify_blockers(state: PRGreenState) -> tuple[PRBlocker, ...]:
    blockers: list[PRBlocker] = []
    if state.draft:
        blockers.append(PRBlocker.DRAFT)
    if state.has_conflicts or state.mergeable is False:
        blockers.append(PRBlocker.CONFLICT)

    checks = state.checks_state.lower().strip()
    if checks in {"failure", "failed", "red"}:
        blockers.append(PRBlocker.FAILING_CHECK)
    elif checks in {"pending", "queued", "in_progress"}:
        blockers.append(PRBlocker.PENDING_CHECK)
    elif checks in {"missing", "none"}:
        blockers.append(PRBlocker.MISSING_CHECK)
    elif checks in {"unknown", "ambiguous", "stale"}:
        blockers.append(PRBlocker.AMBIGUOUS_STATUS)

    if state.safety_flags:
        blockers.append(PRBlocker.SAFETY_AMBIGUITY)
    return tuple(dict.fromkeys(blockers))


def infer_enrichment_steps(state: PRGreenState, blockers: Sequence[PRBlocker]) -> tuple[GreenStep, ...]:
    steps: list[GreenStep] = [
        GreenStep(BuildAction.INSPECT, "Read PR metadata, changed files, check results, and OAK risk flags.")
    ]

    if PRBlocker.DRAFT in blockers:
        steps.append(
            GreenStep(
                BuildAction.SKIP,
                "Draft PRs are not auto-promoted or marked ready by the builder.",
                requires_human=True,
            )
        )
        return tuple(steps)

    if PRBlocker.CONFLICT in blockers:
        steps.append(
            GreenStep(
                BuildAction.REQUEST_MANUAL_RESOLUTION,
                "Merge conflicts require semantic judgment; do not auto-resolve or force-push.",
                requires_human=True,
            )
        )
        steps.append(
            GreenStep(
                BuildAction.ADD_REPAIR_REPORT,
                "Write a conflict report with files, preferred safe strategy, and validation commands.",
                target="docs/repair_reports/",
            )
        )
        return tuple(steps)

    if PRBlocker.FAILING_CHECK in blockers:
        test_target = "tests/"
        if any(path.endswith(".md") for path in state.changed_files):
            steps.append(GreenStep(BuildAction.ADD_DOC, "Add missing runbook or OAK clarification for documentation-only failures."))
        steps.append(GreenStep(BuildAction.ADD_TEST, "Add or repair minimal regression tests for the failing behavior.", target=test_target))
        steps.append(GreenStep(BuildAction.ADD_VALIDATOR, "Add validation that prevents the same failure from returning."))

    if PRBlocker.MISSING_CHECK in blockers or PRBlocker.AMBIGUOUS_STATUS in blockers:
        steps.append(
            GreenStep(
                BuildAction.ADD_GUARDRAIL,
                "Add explicit local validation commands and CI expectations instead of treating silence as proof.",
                target="docs/ or .github/workflows/",
            )
        )

    if PRBlocker.SAFETY_AMBIGUITY in blockers:
        steps.append(
            GreenStep(
                BuildAction.ADD_GUARDRAIL,
                "Add OAK safety boundaries for secrets, permissions, public actions, IP, money, health, and destructive effects.",
                requires_human=True,
            )
        )

    if not blockers:
        steps.append(GreenStep(BuildAction.MERGE_WHEN_CLEAN, "PR is clean/green; merge with expected head SHA."))

    return tuple(steps)


def plan_build_to_green(state: PRGreenState) -> GreenPlan:
    """Return a conservative plan for bringing a PR to green."""
    blockers = classify_blockers(state)
    steps = infer_enrichment_steps(state, blockers)

    if not blockers and state.mergeable is True and state.checks_state.lower() in {"success", "clean", "passing", "green"}:
        decision = "merge_now"
    elif PRBlocker.DRAFT in blockers or PRBlocker.CONFLICT in blockers or PRBlocker.NEEDS_MANUAL_JUDGMENT in blockers:
        decision = "manual_required"
    elif PRBlocker.PENDING_CHECK in blockers:
        decision = "wait"
    elif PRBlocker.FAILING_CHECK in blockers or PRBlocker.MISSING_CHECK in blockers or PRBlocker.AMBIGUOUS_STATUS in blockers:
        decision = "auto_enrich"
    elif PRBlocker.SAFETY_AMBIGUITY in blockers:
        decision = "manual_required"
    else:
        decision = "skip"

    return GreenPlan(state.number, decision, blockers, steps)


def render_plan_markdown(plan: GreenPlan) -> str:
    """Render a reviewable build-to-green plan."""
    blocker_text = ", ".join(blocker.value for blocker in plan.blockers) or "none"
    lines = [f"# PR #{plan.pr_number} build-to-green plan", "", f"Decision: `{plan.decision}`", f"Blockers: `{blocker_text}`", "", "## Steps"]
    for index, step in enumerate(plan.steps, start=1):
        human = " yes" if step.requires_human else " no"
        target = f" Target: `{step.target}`." if step.target else ""
        lines.append(f"{index}. `{step.action.value}` — {step.reason}{target} Human review:{human}.")
    lines.append("")
    lines.append("OAK rule: enrich by adding tests, documentation, validators, reports, or guardrails; never weaken checks or force conflicts.")
    return "\n".join(lines)
