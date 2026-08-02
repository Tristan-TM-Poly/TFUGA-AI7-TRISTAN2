"""Typed records for Ω-MAIL-GITHUB-LOOP-T.

The module models a bounded mail-to-GitHub development loop. It never treats
email text as authority to merge, release, publish, delete, or mutate protected
branches.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum, IntEnum
from hashlib import sha256
import json
from typing import Any


class LoopState(str, Enum):
    RECEIVED = "RECEIVED"
    AUTHENTICATED = "AUTHENTICATED"
    CLASSIFIED = "CLASSIFIED"
    CASE_CREATED = "CASE_CREATED"
    ISSUE_READY = "ISSUE_READY"
    PLAN_READY = "PLAN_READY"
    BRANCH_READY = "BRANCH_READY"
    IMPLEMENTING = "IMPLEMENTING"
    TESTING = "TESTING"
    OAK_REVIEW = "OAK_REVIEW"
    PR_DRAFTED = "PR_DRAFTED"
    REPLY_PREPARED = "REPLY_PREPARED"
    WAITING_FEEDBACK = "WAITING_FEEDBACK"
    REQUIRE_INFORMATION = "REQUIRE_INFORMATION"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    QUARANTINED = "QUARANTINED"
    M_MINUS_HOLD = "M_MINUS_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class LoopDecision(str, Enum):
    CONTINUE = "CONTINUE"
    STOP_ACCEPTED = "STOP_ACCEPTED"
    STOP_NO_GAIN = "STOP_NO_GAIN"
    STOP_REPEATED_FAILURE = "STOP_REPEATED_FAILURE"
    STOP_BUDGET = "STOP_BUDGET"
    REQUIRE_INFORMATION = "REQUIRE_INFORMATION"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    QUARANTINE = "QUARANTINE"
    BLOCK = "BLOCK"


class AuthorityLevel(IntEnum):
    READ_ONLY = 0
    ISSUE = 1
    BRANCH = 2
    COMMIT = 3
    DRAFT_PR = 4
    REVIEW_READY = 5


class GitAction(str, Enum):
    READ_REPOSITORY = "READ_REPOSITORY"
    CREATE_ISSUE = "CREATE_ISSUE"
    CREATE_BRANCH = "CREATE_BRANCH"
    UPDATE_FILES = "UPDATE_FILES"
    CREATE_COMMIT = "CREATE_COMMIT"
    OPEN_DRAFT_PR = "OPEN_DRAFT_PR"
    MARK_READY = "MARK_READY"
    MERGE = "MERGE"
    RELEASE = "RELEASE"
    DELETE_REPOSITORY = "DELETE_REPOSITORY"
    FORCE_PUSH = "FORCE_PUSH"


FORBIDDEN_AUTONOMOUS_ACTIONS = frozenset(
    {GitAction.MERGE, GitAction.RELEASE, GitAction.DELETE_REPOSITORY, GitAction.FORCE_PUSH}
)


@dataclass(frozen=True, slots=True)
class MailCommand:
    repository: str
    action: str
    target: str
    objective: str
    required: tuple[str, ...] = ()
    authority: dict[str, bool] = field(default_factory=dict)
    base_branch: str = "main"
    message_id: str | None = None
    thread_id: str | None = None
    sender: str | None = None
    raw_hash: str | None = None

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "action": self.action,
            "target": self.target,
            "objective": self.objective,
            "required": list(self.required),
            "authority": dict(sorted(self.authority.items())),
            "base_branch": self.base_branch,
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "sender": self.sender,
        }

    def content_hash(self) -> str:
        raw = json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":"))
        return sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class IterationMetrics:
    tests_added: int = 0
    tests_fixed: int = 0
    defects_removed: int = 0
    security_findings_removed: int = 0
    documentation_divergences_removed: int = 0
    coverage_delta: float = 0.0
    runtime_delta: float = 0.0
    false_positive_delta: float = 0.0
    risk_delta: float = 0.0
    complexity_delta: float = 0.0
    cost_units: float = 1.0


@dataclass(slots=True)
class LoopCase:
    case_id: str
    command: MailCommand
    state: LoopState = LoopState.RECEIVED
    issue_number: int | None = None
    branch_name: str | None = None
    pull_request_number: int | None = None
    iterations: int = 0
    unchanged_reply_count: int = 0
    repeated_failure_count: int = 0
    last_progress_score: float | None = None
    failure_signatures: list[str] = field(default_factory=list)
    artifact_hashes: dict[str, str] = field(default_factory=dict)
    evidence_head: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.value
        return payload


@dataclass(frozen=True, slots=True)
class LoopPolicy:
    authority_level: AuthorityLevel = AuthorityLevel.DRAFT_PR
    allow_issue: bool = True
    allow_branch: bool = True
    allow_commit: bool = True
    allow_draft_pr: bool = True
    allow_mark_ready: bool = False
    allow_merge: bool = False
    allow_release: bool = False
    allow_default_branch_write: bool = False
    maximum_consecutive_no_gain: int = 2
    maximum_repeated_failure: int = 2
    adaptive_cost_budget: float = 100.0
    minimum_progress_score: float = 0.01
    kill_switch: bool = False


@dataclass(frozen=True, slots=True)
class EvidenceEvent:
    event_id: str
    case_id: str
    kind: str
    payload_hash: str
    previous_hash: str | None
    event_hash: str
    created_at: str
