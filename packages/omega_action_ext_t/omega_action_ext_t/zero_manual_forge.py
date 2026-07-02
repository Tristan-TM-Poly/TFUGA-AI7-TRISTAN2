"""Zero-Manual PR Forge kernel.

This module converts blocked pull-request states into autonomous-safe repair
plans. It encodes Tristan's rule: never send routine CI/conflict work back to the
human; instead preserve content, synthesize safely, repair additively, and merge
only after GitHub is clean/green.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence

from .green_builder import BuildAction, GreenStep, PRBlocker, PRGreenState, classify_blockers


class ForgeDecision(str, Enum):
    """Zero-manual decision classes."""

    MERGE_WHEN_CLEAN = "merge_when_clean"
    AUTONOMOUS_REPAIR = "autonomous_repair"
    PRESERVE_AND_SYNTHESIZE = "preserve_and_synthesize"
    WAIT_FOR_CHECKS = "wait_for_checks"
    HARD_OAK_LOCK = "hard_oak_lock"
    SKIP_DRAFT = "skip_draft"


class RepairTactic(str, Enum):
    """Allowed non-destructive repair tactics."""

    REPO_ROOT_IMPORT_BOOTSTRAP = "repo_root_import_bootstrap"
    ADD_REGRESSION_TEST = "add_regression_test"
    ADD_VALIDATOR = "add_validator"
    ADD_GUARDRAIL = "add_guardrail"
    PRESERVE_BRANCH_VERSION = "preserve_branch_version"
    REALIGN_CANONICAL_PATH = "realign_canonical_path"
    SYNTHESIZE_CANON_ARTIFACT = "synthesize_canon_artifact"
    UPDATE_MACHINE_REPORT = "update_machine_report"
    RERUN_OR_WAIT_CHECKS = "rerun_or_wait_checks"
    MERGE_WITH_EXPECTED_SHA = "merge_with_expected_sha"


@dataclass(frozen=True)
class FailureMemory:
    """M⁻ entry for a repeated PR blocker."""

    pr_number: int
    failure_class: str
    blocker: str
    unsafe_shortcut: str
    autonomous_next_action: str
    anti_repetition_rule: str

    def to_markdown(self) -> str:
        return (
            f"- PR #{self.pr_number} `{self.failure_class}`: {self.blocker}. "
            f"Unsafe shortcut: {self.unsafe_shortcut}. "
            f"Next autonomous action: {self.autonomous_next_action}. "
            f"M⁻ rule: {self.anti_repetition_rule}"
        )


@dataclass(frozen=True)
class ZeroManualPlan:
    """Autonomous-safe repair plan for one PR."""

    state: PRGreenState
    decision: ForgeDecision
    blockers: tuple[PRBlocker, ...]
    tactics: tuple[RepairTactic, ...]
    steps: tuple[GreenStep, ...]
    failure_memory: tuple[FailureMemory, ...] = field(default_factory=tuple)

    @property
    def can_merge_now(self) -> bool:
        return self.decision == ForgeDecision.MERGE_WHEN_CLEAN

    @property
    def needs_future_iteration(self) -> bool:
        return self.decision in {
            ForgeDecision.AUTONOMOUS_REPAIR,
            ForgeDecision.PRESERVE_AND_SYNTHESIZE,
            ForgeDecision.WAIT_FOR_CHECKS,
            ForgeDecision.HARD_OAK_LOCK,
        }


def _checks_state(state: PRGreenState) -> str:
    return state.checks_state.lower().strip()


def _is_clean(state: PRGreenState) -> bool:
    return _checks_state(state) in {"success", "clean", "passing", "green"}


def _memory_for_blockers(state: PRGreenState, blockers: Sequence[PRBlocker]) -> tuple[FailureMemory, ...]:
    memories: list[FailureMemory] = []
    if PRBlocker.CONFLICT in blockers:
        memories.append(
            FailureMemory(
                pr_number=state.number,
                failure_class="merge_conflict",
                blocker="branch is not mergeable against the current base",
                unsafe_shortcut="force-push, blind overwrite, or deleting one side of a canon artifact",
                autonomous_next_action="preserve both sides, synthesize or realign the canonical path, then re-check mergeability",
                anti_repetition_rule="conflict resolution must be preservation-first and auditable",
            )
        )
    if PRBlocker.FAILING_CHECK in blockers:
        memories.append(
            FailureMemory(
                pr_number=state.number,
                failure_class="failing_check",
                blocker=f"checks_state={state.checks_state}",
                unsafe_shortcut="weakening, skipping, or removing the failing check",
                autonomous_next_action="read failing job/step logs, add an additive fix or regression test, then wait for green checks",
                anti_repetition_rule="a red check becomes a repair target, not a lowered gate",
            )
        )
    if PRBlocker.AMBIGUOUS_STATUS in blockers or PRBlocker.MISSING_CHECK in blockers:
        memories.append(
            FailureMemory(
                pr_number=state.number,
                failure_class="ambiguous_status",
                blocker=f"checks_state={state.checks_state}",
                unsafe_shortcut="treating missing checks as proof of safety",
                autonomous_next_action="add status guardrails or wait for GitHub clean status before merge",
                anti_repetition_rule="absence of evidence is not green evidence",
            )
        )
    if PRBlocker.SAFETY_AMBIGUITY in blockers:
        memories.append(
            FailureMemory(
                pr_number=state.number,
                failure_class="safety_ambiguity",
                blocker=", ".join(state.safety_flags),
                unsafe_shortcut="executing sensitive public/legal/financial/health/destructive action without approval gates",
                autonomous_next_action="add OAK guardrails, manifests, dry-run mode, rollback, and proof ledger before execution",
                anti_repetition_rule="higher-impact actions require stronger gates, not more autonomy",
            )
        )
    return tuple(memories)


def plan_zero_manual_forge(state: PRGreenState) -> ZeroManualPlan:
    """Plan the next zero-manual action for a PR state."""
    blockers = classify_blockers(state)
    memories = _memory_for_blockers(state, blockers)
    steps: list[GreenStep] = [
        GreenStep(BuildAction.INSPECT, "Inspect PR state, changed files, checks, conflicts, and OAK risk flags.")
    ]
    tactics: list[RepairTactic] = []

    if state.draft:
        steps.append(
            GreenStep(
                BuildAction.ADD_REPAIR_REPORT,
                "Draft PRs may be enriched but are never marked ready automatically.",
                target="docs/repair_reports/",
            )
        )
        return ZeroManualPlan(
            state=state,
            decision=ForgeDecision.SKIP_DRAFT,
            blockers=blockers,
            tactics=(RepairTactic.UPDATE_MACHINE_REPORT,),
            steps=tuple(steps),
            failure_memory=memories,
        )

    if not blockers and state.mergeable is True and _is_clean(state):
        steps.append(GreenStep(BuildAction.MERGE_WHEN_CLEAN, "Merge using expected head SHA after green checks."))
        return ZeroManualPlan(state, ForgeDecision.MERGE_WHEN_CLEAN, blockers, (RepairTactic.MERGE_WITH_EXPECTED_SHA,), tuple(steps), memories)

    if PRBlocker.PENDING_CHECK in blockers:
        steps.append(GreenStep(BuildAction.SKIP, "Checks are still pending; wait for GitHub verdict before mutation or merge."))
        return ZeroManualPlan(state, ForgeDecision.WAIT_FOR_CHECKS, blockers, (RepairTactic.RERUN_OR_WAIT_CHECKS,), tuple(steps), memories)

    if PRBlocker.CONFLICT in blockers:
        tactics.extend(
            [
                RepairTactic.PRESERVE_BRANCH_VERSION,
                RepairTactic.REALIGN_CANONICAL_PATH,
                RepairTactic.SYNTHESIZE_CANON_ARTIFACT,
                RepairTactic.UPDATE_MACHINE_REPORT,
            ]
        )
        steps.extend(
            [
                GreenStep(BuildAction.ADD_REPAIR_REPORT, "Record the conflict and preservation strategy.", target="docs/repair_reports/"),
                GreenStep(BuildAction.ADD_GUARDRAIL, "Preserve branch-only content in a named artifact before canonical realignment."),
                GreenStep(BuildAction.ADD_VALIDATOR, "Run or wait for checks after mergeability changes."),
            ]
        )
        return ZeroManualPlan(state, ForgeDecision.PRESERVE_AND_SYNTHESIZE, blockers, tuple(tactics), tuple(steps), memories)

    if PRBlocker.FAILING_CHECK in blockers:
        tactics.extend([RepairTactic.REPO_ROOT_IMPORT_BOOTSTRAP, RepairTactic.ADD_REGRESSION_TEST, RepairTactic.ADD_VALIDATOR])
        steps.extend(
            [
                GreenStep(BuildAction.ADD_TEST, "Add a regression test or smoke path for the failing CI step."),
                GreenStep(BuildAction.ADD_VALIDATOR, "Repair root cause without weakening CI."),
            ]
        )
        return ZeroManualPlan(state, ForgeDecision.AUTONOMOUS_REPAIR, blockers, tuple(tactics), tuple(steps), memories)

    if PRBlocker.SAFETY_AMBIGUITY in blockers:
        tactics.extend([RepairTactic.ADD_GUARDRAIL, RepairTactic.UPDATE_MACHINE_REPORT])
        steps.append(GreenStep(BuildAction.ADD_GUARDRAIL, "Add stronger OAK gates before any execution or publication."))
        return ZeroManualPlan(state, ForgeDecision.HARD_OAK_LOCK, blockers, tuple(tactics), tuple(steps), memories)

    tactics.append(RepairTactic.UPDATE_MACHINE_REPORT)
    steps.append(GreenStep(BuildAction.ADD_REPAIR_REPORT, "Record current blocker and continue future autonomous repair attempts."))
    return ZeroManualPlan(state, ForgeDecision.AUTONOMOUS_REPAIR, blockers, tuple(tactics), tuple(steps), memories)


def render_zero_manual_report(plan: ZeroManualPlan) -> str:
    """Render a machine-readable-ish Markdown report."""
    blockers = ", ".join(blocker.value for blocker in plan.blockers) or "none"
    tactics = ", ".join(tactic.value for tactic in plan.tactics) or "none"
    lines = [
        f"# Zero-Manual PR Forge report — PR #{plan.state.number}",
        "",
        f"Decision: `{plan.decision.value}`",
        f"Draft: `{plan.state.draft}`",
        f"Mergeable: `{plan.state.mergeable}`",
        f"Checks: `{plan.state.checks_state}`",
        f"Blockers: `{blockers}`",
        f"Tactics: `{tactics}`",
        "",
        "## Steps",
    ]
    for index, step in enumerate(plan.steps, start=1):
        target = f" Target: `{step.target}`." if step.target else ""
        lines.append(f"{index}. `{step.action.value}` — {step.reason}{target}")
    lines.append("")
    lines.append("## M⁻ failure memory")
    if plan.failure_memory:
        lines.extend(memory.to_markdown() for memory in plan.failure_memory)
    else:
        lines.append("- none")
    lines.append("")
    lines.append("OAK rule: zero manual means autonomous preservation, tests, reports, and green-only merge; never unsafe automation.")
    return "\n".join(lines)


__all__ = [
    "FailureMemory",
    "ForgeDecision",
    "RepairTactic",
    "ZeroManualPlan",
    "plan_zero_manual_forge",
    "render_zero_manual_report",
]
