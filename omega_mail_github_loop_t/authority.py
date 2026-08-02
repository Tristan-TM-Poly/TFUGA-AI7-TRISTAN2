"""Authority checks for mail-originated GitHub actions."""
from __future__ import annotations

from dataclasses import dataclass

from .models import AuthorityLevel, FORBIDDEN_AUTONOMOUS_ACTIONS, GitAction, LoopPolicy, MailCommand


@dataclass(frozen=True, slots=True)
class AuthorityResult:
    allowed: bool
    reasons: tuple[str, ...]


def required_level(action: GitAction) -> AuthorityLevel:
    return {
        GitAction.READ_REPOSITORY: AuthorityLevel.READ_ONLY,
        GitAction.CREATE_ISSUE: AuthorityLevel.ISSUE,
        GitAction.CREATE_BRANCH: AuthorityLevel.BRANCH,
        GitAction.UPDATE_FILES: AuthorityLevel.COMMIT,
        GitAction.CREATE_COMMIT: AuthorityLevel.COMMIT,
        GitAction.OPEN_DRAFT_PR: AuthorityLevel.DRAFT_PR,
        GitAction.MARK_READY: AuthorityLevel.REVIEW_READY,
        GitAction.MERGE: AuthorityLevel.REVIEW_READY,
        GitAction.RELEASE: AuthorityLevel.REVIEW_READY,
        GitAction.DELETE_REPOSITORY: AuthorityLevel.REVIEW_READY,
        GitAction.FORCE_PUSH: AuthorityLevel.REVIEW_READY,
    }[action]


def evaluate_action(command: MailCommand, policy: LoopPolicy, action: GitAction) -> AuthorityResult:
    reasons: list[str] = []
    if policy.kill_switch:
        reasons.append("kill_switch")
    if action in FORBIDDEN_AUTONOMOUS_ACTIONS:
        reasons.append(f"forbidden_autonomous_action:{action.value}")
    if policy.authority_level < required_level(action):
        reasons.append("insufficient_policy_authority")
    if action is GitAction.CREATE_ISSUE and not policy.allow_issue:
        reasons.append("issue_disabled")
    if action is GitAction.CREATE_BRANCH and not policy.allow_branch:
        reasons.append("branch_disabled")
    if action in {GitAction.UPDATE_FILES, GitAction.CREATE_COMMIT} and not policy.allow_commit:
        reasons.append("commit_disabled")
    if action is GitAction.OPEN_DRAFT_PR and not policy.allow_draft_pr:
        reasons.append("draft_pr_disabled")
    if action is GitAction.MARK_READY and not policy.allow_mark_ready:
        reasons.append("mark_ready_disabled")
    if action is GitAction.MERGE and not policy.allow_merge:
        reasons.append("merge_disabled")
    if action is GitAction.RELEASE and not policy.allow_release:
        reasons.append("release_disabled")
    if command.base_branch in {"main", "master"} and action in {GitAction.UPDATE_FILES, GitAction.CREATE_COMMIT}:
        if not policy.allow_default_branch_write:
            reasons.append("default_branch_write_forbidden")
    if command.authority.get(action.value.lower()) is False:
        reasons.append("mail_explicitly_denied")
    return AuthorityResult(not reasons, tuple(reasons) or ("allowed_by_bounded_policy",))
