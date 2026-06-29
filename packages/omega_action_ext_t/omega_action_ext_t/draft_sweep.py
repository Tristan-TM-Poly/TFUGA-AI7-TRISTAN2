"""Draft PR sweep and readiness scoring.

Drafts are not merged and are never marked ready by this module. The goal is to
keep drafts moving autonomously by identifying missing guardrails, tests, docs,
and OAK boundaries until an explicit external ready decision exists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence

from .green_builder import PRGreenState
from .zero_manual_forge import FailureMemory


class DraftSignal(str, Enum):
    """Signals used to score whether a draft is getting safer."""

    HAS_TESTS = "has_tests"
    HAS_DOCS = "has_docs"
    HAS_OAK_GUARDRAILS = "has_oak_guardrails"
    HAS_DRY_RUN_DEFAULT = "has_dry_run_default"
    HAS_ROLLBACK_OR_COMPENSATION = "has_rollback_or_compensation"
    HAS_LEAK_SCAN = "has_leak_scan"
    HAS_APPROVAL_QUEUE = "has_approval_queue"
    HAS_PROOF_LEDGER = "has_proof_ledger"
    HAS_M_MINUS_MEMORY = "has_m_minus_memory"
    HAS_NO_LIVE_CONNECTORS = "has_no_live_connectors"
    HAS_GREEN_CHECKS = "has_green_checks"
    IS_MERGEABLE = "is_mergeable"


class DraftBlocker(str, Enum):
    """Why a draft should remain draft even if checks are green."""

    STILL_DRAFT = "still_draft"
    SAFETY_SENSITIVE = "safety_sensitive"
    MISSING_TESTS = "missing_tests"
    MISSING_DOCS = "missing_docs"
    MISSING_OAK_GUARDRAILS = "missing_oak_guardrails"
    MISSING_DRY_RUN_DEFAULT = "missing_dry_run_default"
    MISSING_ROLLBACK = "missing_rollback"
    MISSING_APPROVAL_QUEUE = "missing_approval_queue"
    MISSING_LEDGER = "missing_ledger"
    MISSING_M_MINUS = "missing_m_minus"
    LIVE_CONNECTOR_RISK = "live_connector_risk"
    CHECKS_NOT_GREEN = "checks_not_green"
    NOT_MERGEABLE = "not_mergeable"


@dataclass(frozen=True)
class DraftSweepInput:
    """Inputs for scoring one draft PR."""

    state: PRGreenState
    changed_files: tuple[str, ...] = ()
    signals: Mapping[DraftSignal, bool] = field(default_factory=dict)
    safety_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class DraftSweepPlan:
    """Zero-manual plan for a draft PR."""

    state: PRGreenState
    score: int
    max_score: int
    blockers: tuple[DraftBlocker, ...]
    next_autonomous_actions: tuple[str, ...]
    failure_memory: tuple[FailureMemory, ...]

    @property
    def readiness_ratio(self) -> float:
        return self.score / self.max_score if self.max_score else 0.0

    @property
    def is_ready_candidate(self) -> bool:
        """Draft can be considered by an external ready-decision process.

        This does not mark the PR ready. It only means no local readiness blockers
        remain in the sweep model.
        """
        blocking = set(self.blockers) - {DraftBlocker.STILL_DRAFT}
        return not blocking and self.readiness_ratio >= 0.9


DEFAULT_SIGNAL_WEIGHTS: Mapping[DraftSignal, int] = {
    DraftSignal.HAS_TESTS: 12,
    DraftSignal.HAS_DOCS: 8,
    DraftSignal.HAS_OAK_GUARDRAILS: 14,
    DraftSignal.HAS_DRY_RUN_DEFAULT: 14,
    DraftSignal.HAS_ROLLBACK_OR_COMPENSATION: 8,
    DraftSignal.HAS_LEAK_SCAN: 6,
    DraftSignal.HAS_APPROVAL_QUEUE: 8,
    DraftSignal.HAS_PROOF_LEDGER: 8,
    DraftSignal.HAS_M_MINUS_MEMORY: 8,
    DraftSignal.HAS_NO_LIVE_CONNECTORS: 8,
    DraftSignal.HAS_GREEN_CHECKS: 8,
    DraftSignal.IS_MERGEABLE: 6,
}


def infer_signals_from_files(state: PRGreenState, changed_files: Sequence[str]) -> dict[DraftSignal, bool]:
    """Infer readiness signals from changed paths and state."""
    files = tuple(changed_files)
    lowered = tuple(path.lower() for path in files)
    docs = any(path.endswith(".md") or "/docs/" in path or path.startswith("docs/") for path in lowered)
    tests = any("test" in path and path.endswith(".py") for path in lowered)
    oak = any("oak" in path or "guard" in path or "policy" in path for path in lowered)
    dry_run = any("dryrun" in path or "dry_run" in path or "connectors/" in path for path in lowered)
    rollback = any("rollback" in path or "compensation" in path for path in lowered)
    approval = any("approval" in path or "queue" in path for path in lowered)
    ledger = any("ledger" in path or "proof" in path or "manifest" in path for path in lowered)
    m_minus = any("incident" in path or "m_minus" in path or "m-" in path for path in lowered)
    leak_scan = any("leak" in path or "secret" in path for path in lowered)
    live_connector_risk = any("connectors/" in path for path in lowered) and not dry_run

    checks_green = state.checks_state.lower() in {"success", "clean", "passing", "green"}
    return {
        DraftSignal.HAS_TESTS: tests,
        DraftSignal.HAS_DOCS: docs,
        DraftSignal.HAS_OAK_GUARDRAILS: oak,
        DraftSignal.HAS_DRY_RUN_DEFAULT: dry_run,
        DraftSignal.HAS_ROLLBACK_OR_COMPENSATION: rollback,
        DraftSignal.HAS_LEAK_SCAN: leak_scan,
        DraftSignal.HAS_APPROVAL_QUEUE: approval,
        DraftSignal.HAS_PROOF_LEDGER: ledger,
        DraftSignal.HAS_M_MINUS_MEMORY: m_minus,
        DraftSignal.HAS_NO_LIVE_CONNECTORS: not live_connector_risk,
        DraftSignal.HAS_GREEN_CHECKS: checks_green,
        DraftSignal.IS_MERGEABLE: state.mergeable is True,
    }


def _blockers_for_signals(state: PRGreenState, signals: Mapping[DraftSignal, bool]) -> tuple[DraftBlocker, ...]:
    blockers: list[DraftBlocker] = []
    if state.draft:
        blockers.append(DraftBlocker.STILL_DRAFT)
    if state.safety_flags:
        blockers.append(DraftBlocker.SAFETY_SENSITIVE)
    if not signals.get(DraftSignal.HAS_TESTS, False):
        blockers.append(DraftBlocker.MISSING_TESTS)
    if not signals.get(DraftSignal.HAS_DOCS, False):
        blockers.append(DraftBlocker.MISSING_DOCS)
    if not signals.get(DraftSignal.HAS_OAK_GUARDRAILS, False):
        blockers.append(DraftBlocker.MISSING_OAK_GUARDRAILS)
    if not signals.get(DraftSignal.HAS_DRY_RUN_DEFAULT, False):
        blockers.append(DraftBlocker.MISSING_DRY_RUN_DEFAULT)
    if not signals.get(DraftSignal.HAS_ROLLBACK_OR_COMPENSATION, False):
        blockers.append(DraftBlocker.MISSING_ROLLBACK)
    if not signals.get(DraftSignal.HAS_APPROVAL_QUEUE, False):
        blockers.append(DraftBlocker.MISSING_APPROVAL_QUEUE)
    if not signals.get(DraftSignal.HAS_PROOF_LEDGER, False):
        blockers.append(DraftBlocker.MISSING_LEDGER)
    if not signals.get(DraftSignal.HAS_M_MINUS_MEMORY, False):
        blockers.append(DraftBlocker.MISSING_M_MINUS)
    if not signals.get(DraftSignal.HAS_NO_LIVE_CONNECTORS, False):
        blockers.append(DraftBlocker.LIVE_CONNECTOR_RISK)
    if not signals.get(DraftSignal.HAS_GREEN_CHECKS, False):
        blockers.append(DraftBlocker.CHECKS_NOT_GREEN)
    if not signals.get(DraftSignal.IS_MERGEABLE, False):
        blockers.append(DraftBlocker.NOT_MERGEABLE)
    return tuple(dict.fromkeys(blockers))


def _actions_for_blockers(blockers: Sequence[DraftBlocker]) -> tuple[str, ...]:
    actions: list[str] = []
    mapping = {
        DraftBlocker.MISSING_TESTS: "add tests for every approval, dry-run, blocking, rollback, and leak-scan path",
        DraftBlocker.MISSING_DOCS: "add operator docs and OAK runbooks",
        DraftBlocker.MISSING_OAK_GUARDRAILS: "add explicit OAK policy boundaries and forbidden-action tests",
        DraftBlocker.MISSING_DRY_RUN_DEFAULT: "make every connector dry-run-first by construction",
        DraftBlocker.MISSING_ROLLBACK: "add rollback or compensation recipes for reversible actions",
        DraftBlocker.MISSING_APPROVAL_QUEUE: "add or harden approval queue state transitions",
        DraftBlocker.MISSING_LEDGER: "add proof ledger or manifest hashing tests",
        DraftBlocker.MISSING_M_MINUS: "add M⁻ failure memory entries and anti-repetition rules",
        DraftBlocker.LIVE_CONNECTOR_RISK: "replace live connector effects with dry-run plans and proofs",
        DraftBlocker.CHECKS_NOT_GREEN: "read CI logs and repair red/pending/ambiguous checks without weakening gates",
        DraftBlocker.NOT_MERGEABLE: "preserve both sides of conflicts and restore mergeability without force-push",
        DraftBlocker.SAFETY_SENSITIVE: "increase guardrails because this draft touches sensitive external-action surfaces",
    }
    for blocker in blockers:
        if blocker in mapping and mapping[blocker] not in actions:
            actions.append(mapping[blocker])
    if not actions:
        actions.append("keep draft state and wait for explicit ready decision outside this module")
    return tuple(actions)


def plan_draft_sweep(input_data: DraftSweepInput) -> DraftSweepPlan:
    """Score a draft PR and produce next zero-manual enrichment actions."""
    signals = dict(infer_signals_from_files(input_data.state, input_data.changed_files))
    signals.update(input_data.signals)
    max_score = sum(DEFAULT_SIGNAL_WEIGHTS.values())
    score = sum(weight for signal, weight in DEFAULT_SIGNAL_WEIGHTS.items() if signals.get(signal, False))
    blockers = _blockers_for_signals(input_data.state, signals)
    actions = _actions_for_blockers(blockers)
    memories = tuple(
        FailureMemory(
            pr_number=input_data.state.number,
            failure_class="draft_readiness_gap",
            blocker=blocker.value,
            unsafe_shortcut="marking draft ready or merging before gates are complete",
            autonomous_next_action=action,
            anti_repetition_rule="drafts are enriched by artifacts, tests, and guardrails, never by pressure on the user",
        )
        for blocker, action in zip(blockers, actions + actions[-1:])
        if blocker != DraftBlocker.STILL_DRAFT
    )
    return DraftSweepPlan(
        state=input_data.state,
        score=score,
        max_score=max_score,
        blockers=blockers,
        next_autonomous_actions=actions,
        failure_memory=memories,
    )


def render_draft_sweep_report(plan: DraftSweepPlan) -> str:
    """Render a draft sweep report."""
    blockers = ", ".join(blocker.value for blocker in plan.blockers) or "none"
    lines = [
        f"# Draft Sweep report — PR #{plan.state.number}",
        "",
        f"Title: {plan.state.title}",
        f"Draft: `{plan.state.draft}`",
        f"Mergeable: `{plan.state.mergeable}`",
        f"Checks: `{plan.state.checks_state}`",
        f"Readiness score: `{plan.score}/{plan.max_score}` ({plan.readiness_ratio:.2%})",
        f"Ready candidate: `{plan.is_ready_candidate}`",
        f"Blockers: `{blockers}`",
        "",
        "## Next autonomous actions",
    ]
    lines.extend(f"- {action}" for action in plan.next_autonomous_actions)
    lines.append("")
    lines.append("## M⁻ failure memory")
    if plan.failure_memory:
        lines.extend(memory.to_markdown() for memory in plan.failure_memory)
    else:
        lines.append("- none")
    lines.append("")
    lines.append("OAK rule: draft enrichment is automatic; draft promotion is not automatic.")
    return "\n".join(lines)


__all__ = [
    "DEFAULT_SIGNAL_WEIGHTS",
    "DraftBlocker",
    "DraftSignal",
    "DraftSweepInput",
    "DraftSweepPlan",
    "infer_signals_from_files",
    "plan_draft_sweep",
    "render_draft_sweep_report",
]
