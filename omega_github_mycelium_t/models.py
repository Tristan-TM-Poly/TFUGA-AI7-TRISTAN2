from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
import re
from typing import Any, Iterable, Mapping


_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_digest(value: Any) -> str:
    raw = value if isinstance(value, str) else canonical_json(value)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _clean_tuple(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(v).strip() for v in values if str(v).strip()))


class RouteDecision(str, Enum):
    ADD_TO_EXISTING_REPO = "add_to_existing_repo"
    CREATE_SPECIALIZED_PACKAGE = "create_specialized_package"
    CREATE_NEW_REPO = "create_new_repo"
    KEEP_PRIVATE = "keep_private"
    KEEP_IN_BACKLOG = "keep_in_backlog"
    MERGE_WITH_EXISTING_SYSTEM = "merge_with_existing_system"
    ARCHIVE_AS_HISTORICAL = "archive_as_historical"


class CampaignState(str, Enum):
    PLANNED = "planned"
    SCAFFOLDED = "scaffolded"
    CODE_GENERATED = "code_generated"
    LOCALLY_TESTED = "locally_tested"
    PRS_OPEN = "prs_open"
    CI_RUNNING = "ci_running"
    PARTIALLY_BLOCKED = "partially_blocked"
    OAK_REVIEW = "oak_review"
    READY = "ready"
    MERGED = "merged"
    ROLLED_BACK = "rolled_back"
    CANONIZED = "canonized"


class FindingSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"


@dataclass(frozen=True, slots=True)
class RepositorySnapshot:
    full_name: str
    visibility: str
    default_branch: str = "main"
    archived: bool = False
    size_kb: int = 0
    permissions: tuple[str, ...] = ()
    packages: tuple[str, ...] = ()
    workflows: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    docs: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    head_sha: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not _REPO_RE.fullmatch(self.full_name):
            raise ValueError(f"invalid repository full name: {self.full_name!r}")
        if self.visibility not in {"public", "private", "internal", "unknown"}:
            raise ValueError(f"unsupported visibility: {self.visibility}")
        if self.size_kb < 0:
            raise ValueError("size_kb cannot be negative")
        if self.head_sha is not None and not _SHA_RE.fullmatch(self.head_sha):
            raise ValueError("head_sha must be a lowercase 40-character SHA")
        object.__setattr__(self, "permissions", _clean_tuple(self.permissions))
        object.__setattr__(self, "packages", _clean_tuple(self.packages))
        object.__setattr__(self, "workflows", _clean_tuple(self.workflows))
        object.__setattr__(self, "tests", _clean_tuple(self.tests))
        object.__setattr__(self, "docs", _clean_tuple(self.docs))
        object.__setattr__(self, "topics", _clean_tuple(self.topics))

    @property
    def owner(self) -> str:
        return self.full_name.split("/", 1)[0]

    @property
    def name(self) -> str:
        return self.full_name.split("/", 1)[1]

    @property
    def writable(self) -> bool:
        return bool({"admin", "maintain", "push"}.intersection(self.permissions))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RepositorySnapshot":
        return cls(
            full_name=str(value["full_name"]),
            visibility=str(value.get("visibility", "unknown")),
            default_branch=str(value.get("default_branch", "main")),
            archived=bool(value.get("archived", False)),
            size_kb=int(value.get("size_kb", 0)),
            permissions=tuple(value.get("permissions", ())),
            packages=tuple(value.get("packages", ())),
            workflows=tuple(value.get("workflows", ())),
            tests=tuple(value.get("tests", ())),
            docs=tuple(value.get("docs", ())),
            topics=tuple(value.get("topics", ())),
            head_sha=value.get("head_sha"),
            metadata=dict(value.get("metadata", {})),
        )


@dataclass(frozen=True, slots=True)
class PullRequestSnapshot:
    repo_full_name: str
    number: int
    title: str
    state: str = "open"
    draft: bool = True
    mergeable: bool | None = None
    base_branch: str = "main"
    head_branch: str = "unknown"
    head_sha: str | None = None
    url: str = ""
    labels: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    body_digest: str | None = None
    changed_files: int | None = None
    additions: int | None = None
    deletions: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not _REPO_RE.fullmatch(self.repo_full_name):
            raise ValueError(f"invalid repository full name: {self.repo_full_name!r}")
        if self.number <= 0:
            raise ValueError("pull request number must be positive")
        if not self.title.strip():
            raise ValueError("pull request title cannot be empty")
        if self.state not in {"open", "closed", "merged", "unknown"}:
            raise ValueError(f"unsupported PR state: {self.state}")
        if self.head_sha is not None and not _SHA_RE.fullmatch(self.head_sha):
            raise ValueError("head_sha must be a lowercase 40-character SHA")
        object.__setattr__(self, "labels", _clean_tuple(self.labels))
        object.__setattr__(self, "depends_on", _clean_tuple(self.depends_on))

    @property
    def pr_id(self) -> str:
        return f"{self.repo_full_name}#{self.number}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PullRequestSnapshot":
        return cls(
            repo_full_name=str(value["repo_full_name"]),
            number=int(value["number"]),
            title=str(value["title"]),
            state=str(value.get("state", "open")),
            draft=bool(value.get("draft", True)),
            mergeable=value.get("mergeable"),
            base_branch=str(value.get("base_branch", "main")),
            head_branch=str(value.get("head_branch", "unknown")),
            head_sha=value.get("head_sha"),
            url=str(value.get("url", "")),
            labels=tuple(value.get("labels", ())),
            depends_on=tuple(value.get("depends_on", ())),
            body_digest=value.get("body_digest"),
            changed_files=value.get("changed_files"),
            additions=value.get("additions"),
            deletions=value.get("deletions"),
            metadata=dict(value.get("metadata", {})),
        )


@dataclass(frozen=True, slots=True)
class IntentContract:
    intent_id: str
    objective: str
    root_creation: str
    expected_outputs: tuple[str, ...]
    candidate_repositories: tuple[str, ...]
    constraints: tuple[str, ...]
    success_conditions: tuple[str, ...]
    requested_depth_mode: str = "adaptive"
    observed_depth_target: int | None = None
    author: str = "Tristan"
    remote_mutations_authorized: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.intent_id.strip() or not self.objective.strip() or not self.root_creation.strip():
            raise ValueError("intent_id, objective and root_creation are required")
        if self.requested_depth_mode not in {"adaptive", "fixed", "root_only"}:
            raise ValueError("unsupported requested_depth_mode")
        if self.observed_depth_target is not None and self.observed_depth_target < 0:
            raise ValueError("observed_depth_target cannot be negative")
        object.__setattr__(self, "expected_outputs", _clean_tuple(self.expected_outputs))
        object.__setattr__(self, "candidate_repositories", _clean_tuple(self.candidate_repositories))
        object.__setattr__(self, "constraints", _clean_tuple(self.constraints))
        object.__setattr__(self, "success_conditions", _clean_tuple(self.success_conditions))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CreationRecord:
    creation_id: str
    name: str
    category: str
    canonical_repository: str
    canonical_path: str
    aliases: tuple[str, ...] = ()
    implementations: tuple[str, ...] = ()
    related_prs: tuple[str, ...] = ()
    parents: tuple[str, ...] = ()
    children: tuple[str, ...] = ()
    truth_status: str = "fertile"
    code_status: str = "absent"
    test_status: str = "planned"
    product_status: str = "hypothesis"
    ip_status: str = "review_required"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.creation_id.strip() or not self.name.strip():
            raise ValueError("creation_id and name are required")
        if not _REPO_RE.fullmatch(self.canonical_repository):
            raise ValueError("canonical_repository must use owner/name")
        object.__setattr__(self, "aliases", _clean_tuple(self.aliases))
        object.__setattr__(self, "implementations", _clean_tuple(self.implementations))
        object.__setattr__(self, "related_prs", _clean_tuple(self.related_prs))
        object.__setattr__(self, "parents", _clean_tuple(self.parents))
        object.__setattr__(self, "children", _clean_tuple(self.children))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ArtifactSpec:
    artifact_id: str
    creation_id: str
    kind: str
    suggested_path: str
    description: str
    dependencies: tuple[str, ...] = ()
    required_visibility: str = "public_safe"
    risk_level: str = "low"
    generated_status: str = "planned"
    content_digest: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not all((self.artifact_id.strip(), self.creation_id.strip(), self.kind.strip())):
            raise ValueError("artifact_id, creation_id and kind are required")
        if self.required_visibility not in {"public_safe", "private_required", "review_required"}:
            raise ValueError("unsupported required_visibility")
        object.__setattr__(self, "dependencies", _clean_tuple(self.dependencies))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RouteDecisionRecord:
    artifact_id: str
    decision: RouteDecision
    repository: str | None
    score: float
    reasons: tuple[str, ...]
    alternatives: tuple[str, ...] = ()
    human_review_required: bool = True

    def __post_init__(self) -> None:
        if self.repository is not None and not _REPO_RE.fullmatch(self.repository):
            raise ValueError("repository must use owner/name")
        object.__setattr__(self, "reasons", _clean_tuple(self.reasons))
        object.__setattr__(self, "alternatives", _clean_tuple(self.alternatives))

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["decision"] = self.decision.value
        return value


@dataclass(frozen=True, slots=True)
class PullRequestPlan:
    plan_id: str
    repository: str
    base_branch: str
    head_branch: str
    role: str
    artifact_ids: tuple[str, ...]
    depends_on: tuple[str, ...] = ()
    hypothesis: str = ""
    expected_checks: tuple[str, ...] = ()
    allowed_paths: tuple[str, ...] = ()
    draft: bool = True
    human_gate_required: bool = True
    remote_action_planned: bool = False

    def __post_init__(self) -> None:
        if not _REPO_RE.fullmatch(self.repository):
            raise ValueError("repository must use owner/name")
        if not self.plan_id.strip() or not self.head_branch.strip():
            raise ValueError("plan_id and head_branch are required")
        object.__setattr__(self, "artifact_ids", _clean_tuple(self.artifact_ids))
        object.__setattr__(self, "depends_on", _clean_tuple(self.depends_on))
        object.__setattr__(self, "expected_checks", _clean_tuple(self.expected_checks))
        object.__setattr__(self, "allowed_paths", _clean_tuple(self.allowed_paths))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CampaignPlan:
    campaign_id: str
    intent_id: str
    creation_id: str
    objective: str
    state: CampaignState
    pull_requests: tuple[PullRequestPlan, ...]
    rollback_required: bool = True
    remote_mutations_authorized: bool = False
    permanent_pr_cap: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.campaign_id.strip() or not self.objective.strip():
            raise ValueError("campaign_id and objective are required")
        ids = [plan.plan_id for plan in self.pull_requests]
        if len(ids) != len(set(ids)):
            raise ValueError("pull request plan identifiers must be unique")

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "intent_id": self.intent_id,
            "creation_id": self.creation_id,
            "objective": self.objective,
            "state": self.state.value,
            "pull_requests": [plan.to_dict() for plan in self.pull_requests],
            "rollback_required": self.rollback_required,
            "remote_mutations_authorized": self.remote_mutations_authorized,
            "permanent_pr_cap": self.permanent_pr_cap,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    evidence_id: str
    intent_id: str
    campaign_id: str
    source_snapshot_digest: str
    artifact_digests: Mapping[str, str]
    claims: tuple[str, ...]
    limitations: tuple[str, ...]
    residuals: tuple[str, ...]
    status: str = "planned_evidence"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class OAKFinding:
    code: str
    severity: FindingSeverity
    message: str
    subject: str
    remediation: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["severity"] = self.severity.value
        return value
