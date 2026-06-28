"""M⁻-CHATGPT-OAK gate.

This module encodes the negative memory learned from ChatGPT workflow failures:
not merging green PRs, stale CI summaries, repeated checks, over-rich connector
messages, oversized patches, missing exports/tests, and confusing intermediate
states with completion.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Iterable


class GitHubWorkflowState(str, Enum):
    START = "START"
    BRANCH_READY = "BRANCH_READY"
    FILES_CHANGED = "FILES_CHANGED"
    TESTS_ADDED = "TESTS_ADDED"
    PR_OPENED = "PR_OPENED"
    CI_RUNNING = "CI_RUNNING"
    CI_FAILED = "CI_FAILED"
    FIXING = "FIXING"
    CI_GREEN = "CI_GREEN"
    MERGEABLE = "MERGEABLE"
    MERGED = "MERGED"
    BLOCKED_REAL = "BLOCKED_REAL"


@dataclass(slots=True)
class ChatGPTFailureRule:
    code: str
    failure: str
    cause: str
    anti_rule: str
    severity: str = "medium"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class GitHubRunContext:
    requested_go_github: bool = False
    pr_open: bool = False
    ci_green: bool = False
    mergeable: bool = False
    merged: bool = False
    human_approval_required: bool = False
    real_blocker: str | None = None
    checks_per_head_sha: int = 0
    used_fresh_head_sha: bool = False
    summary_after_merge: bool = False


@dataclass(slots=True)
class ChatGPTOAKDecision:
    action: str
    passed: bool
    failed_rules: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


DEFAULT_FAILURE_RULES: tuple[ChatGPTFailureRule, ...] = (
    ChatGPTFailureRule(
        code="MCHATGPT001",
        failure="Stopped at PR open or CI green instead of merging.",
        cause="Over-cautious human validation assumption.",
        anti_rule="If Tristan requested Go GitHub, CI is green, and PR is mergeable, merge automatically.",
        severity="critical",
        tags=["github", "zero-touch", "merge"],
    ),
    ChatGPTFailureRule(
        code="MCHATGPT002",
        failure="Reported stale CI status.",
        cause="Final summary used an old queued/running state.",
        anti_rule="Before final summary, refresh PR head sha and workflow result.",
        severity="high",
        tags=["github", "ci", "freshness"],
    ),
    ChatGPTFailureRule(
        code="MCHATGPT003",
        failure="Repeated identical CI checks too many times.",
        cause="Safety loop without state compression.",
        anti_rule="Use at most two checks per head sha unless there is a failure or ambiguity.",
        severity="medium",
        tags=["ci", "least-compute", "cvcd"],
    ),
    ChatGPTFailureRule(
        code="MCHATGPT004",
        failure="Connector blocked a rich merge message.",
        cause="Over-decorated commit message with long or special content.",
        anti_rule="Use short ASCII-safe commit titles/messages for merge operations.",
        severity="medium",
        tags=["github", "connector", "merge"],
    ),
    ChatGPTFailureRule(
        code="MCHATGPT005",
        failure="Large README patch blocked.",
        cause="Patch was too long or ambiguous for connector safety filter.",
        anti_rule="Split large documentation into short docs/topic.md files and atomic commits.",
        severity="medium",
        tags=["docs", "connector", "patch"],
    ),
    ChatGPTFailureRule(
        code="MCHATGPT006",
        failure="Added modules without complete public exports/tests.",
        cause="Implementation was not followed by package API stabilization.",
        anti_rule="For each public module, update exports and add import/function tests.",
        severity="high",
        tags=["python", "tests", "exports"],
    ),
    ChatGPTFailureRule(
        code="MCHATGPT007",
        failure="Summarized before the workflow reached the final state.",
        cause="Confused pushed/open/green/mergeable with merged.",
        anti_rule="Use MERGED as the default final state for Tristan Go GitHub workflows.",
        severity="critical",
        tags=["github", "summary", "state-machine"],
    ),
)


class ChatGPTOAKGate:
    """Supervisor for Tristan-style zero-touch GitHub workflows."""

    def __init__(self, rules: Iterable[ChatGPTFailureRule] = DEFAULT_FAILURE_RULES) -> None:
        self.rules = tuple(rules)

    def evaluate_github_context(self, context: GitHubRunContext) -> ChatGPTOAKDecision:
        failed: list[str] = []
        warnings: list[str] = []
        next_steps: list[str] = []

        if context.real_blocker:
            return ChatGPTOAKDecision(
                action="REPORT_BLOCKED_REAL",
                passed=False,
                failed_rules=[],
                warnings=[context.real_blocker],
                next_steps=["Explain blocker and smallest required user-side action."],
            )

        if context.requested_go_github and context.ci_green and context.mergeable and not context.merged:
            failed.append("MCHATGPT001")
            next_steps.append("Merge the PR automatically with a short safe merge message.")

        if context.requested_go_github and context.pr_open and not context.used_fresh_head_sha:
            failed.append("MCHATGPT002")
            next_steps.append("Refresh PR head sha and workflow status before final summary.")

        if context.checks_per_head_sha > 2:
            failed.append("MCHATGPT003")
            warnings.append("Repeated CI checks detected; compress state and act.")

        if context.requested_go_github and context.human_approval_required and not context.real_blocker:
            failed.append("MCHATGPT001")
            next_steps.append("Remove unnecessary human validation step for green mergeable PR.")

        if context.requested_go_github and context.merged and not context.summary_after_merge:
            failed.append("MCHATGPT007")
            next_steps.append("Only produce final summary after confirming merge.")

        if not failed and context.merged:
            return ChatGPTOAKDecision(action="POST_MERGE_SUMMARY", passed=True)
        if not failed and context.ci_green and context.mergeable:
            return ChatGPTOAKDecision(action="MERGE", passed=True, next_steps=["Merge automatically."])
        if not failed and context.pr_open:
            return ChatGPTOAKDecision(action="WAIT_OR_CHECK_CI", passed=True, next_steps=["Check CI once for current head sha."])
        return ChatGPTOAKDecision(action="FIX_WORKFLOW", passed=False, failed_rules=failed, warnings=warnings, next_steps=next_steps)

    def rules_as_markdown(self) -> str:
        lines = ["# M-CHATGPT-OAK Rules", ""]
        for rule in self.rules:
            lines.extend(
                [
                    f"## {rule.code}",
                    "",
                    f"- Failure: {rule.failure}",
                    f"- Cause: {rule.cause}",
                    f"- Anti-rule: {rule.anti_rule}",
                    f"- Severity: {rule.severity}",
                    f"- Tags: {', '.join(rule.tags)}",
                    "",
                ]
            )
        return "\n".join(lines)
