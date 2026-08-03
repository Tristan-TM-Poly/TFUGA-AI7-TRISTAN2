from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(value: Any) -> str:
    payload = value if isinstance(value, str) else canonical_json(value)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stable_id(prefix: str, value: Any, length: int = 24) -> str:
    return f"{prefix}-{sha256_hex(value)[:length]}"


class PlatformMode(str, Enum):
    DISCOVER = "discover"
    PRACTICE = "practice"
    SUBMIT = "submit"
    TRAIN = "train"


class Decision(str, Enum):
    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"


@dataclass(frozen=True)
class PlatformPolicy:
    platform_id: str
    display_name: str
    allow: tuple[PlatformMode, ...]
    review: tuple[PlatformMode, ...]
    block: tuple[PlatformMode, ...]
    discovery: tuple[str, ...]
    allowed_content: tuple[str, ...]
    blocked_content: tuple[str, ...]
    attribution_required: bool = True
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if set(self.allow) | set(self.review) | set(self.block) != set(PlatformMode):
            raise ValueError(f"incomplete mode policy: {self.platform_id}")

    def mode_decision(self, mode: PlatformMode) -> Decision:
        if mode in self.allow:
            return Decision.ALLOW
        if mode in self.review:
            return Decision.REVIEW
        return Decision.BLOCK

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform_id": self.platform_id,
            "display_name": self.display_name,
            "allow": [item.value for item in self.allow],
            "review": [item.value for item in self.review],
            "block": [item.value for item in self.block],
            "discovery": list(self.discovery),
            "allowed_content": list(self.allowed_content),
            "blocked_content": list(self.blocked_content),
            "attribution_required": self.attribution_required,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class AccessRequest:
    platform_id: str
    mode: PlatformMode
    content_class: str
    automated: bool = False
    commercial: bool = False
    public_export: bool = False
    explicit_permission: bool = False
    user_owned: bool = False
    license_id: str = "UNKNOWN"


@dataclass(frozen=True)
class Verdict:
    decision: Decision
    reasons: tuple[str, ...]
    controls: tuple[str, ...]
    policy_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reasons": list(self.reasons),
            "controls": list(self.controls),
            "policy_id": self.policy_id,
        }


@dataclass(frozen=True)
class ProblemRef:
    platform_id: str
    external_id: str
    title: str
    tags: tuple[str, ...]
    difficulty: float
    content_class: str = "problem_metadata"
    locator: str = ""
    solved: bool = False
    attempted: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedProblem:
    canonical_id: str
    platform_id: str
    external_id: str
    title_hash: str
    skills: tuple[str, ...]
    difficulty: float
    content_class: str
    locator: str
    solved: bool
    attempted: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "platform_id": self.platform_id,
            "external_id": self.external_id,
            "title_hash": self.title_hash,
            "skills": list(self.skills),
            "difficulty": self.difficulty,
            "content_class": self.content_class,
            "locator": self.locator,
            "solved": self.solved,
            "attempted": self.attempted,
            "statement_included": False,
            "solution_included": False,
            "hidden_tests_included": False,
        }


def _p(
    platform_id: str,
    display_name: str,
    *,
    allow: Iterable[PlatformMode],
    review: Iterable[PlatformMode],
    block: Iterable[PlatformMode],
    discovery: Iterable[str],
    allowed: Iterable[str],
    blocked: Iterable[str],
    notes: Iterable[str] = (),
) -> PlatformPolicy:
    return PlatformPolicy(
        platform_id, display_name, tuple(allow), tuple(review), tuple(block),
        tuple(discovery), tuple(allowed), tuple(blocked), True, tuple(notes)
    )


PLATFORMS: tuple[PlatformPolicy, ...] = (
    _p("codewars", "Codewars", allow=(PlatformMode.DISCOVER, PlatformMode.PRACTICE), review=(PlatformMode.SUBMIT, PlatformMode.TRAIN), block=(), discovery=("official_public_api_metadata",), allowed=("profile_metadata", "completion_metadata", "problem_metadata", "user_owned_solution"), blocked=("hidden_tests", "community_solution", "scraped_statement")),
    _p("exercism", "Exercism", allow=(PlatformMode.DISCOVER, PlatformMode.PRACTICE), review=(PlatformMode.SUBMIT, PlatformMode.TRAIN), block=(), discovery=("open_source_track_repository", "official_cli"), allowed=("exercise_definition", "problem_metadata", "user_owned_solution"), blocked=("third_party_solution", "mentor_private_content")),
    _p("codeforces", "Codeforces", allow=(PlatformMode.DISCOVER, PlatformMode.PRACTICE), review=(PlatformMode.SUBMIT, PlatformMode.TRAIN), block=(), discovery=("official_api_metadata",), allowed=("problem_metadata", "contest_metadata", "profile_metadata", "user_owned_solution"), blocked=("scraped_statement", "community_solution", "hidden_tests")),
    _p("cses", "CSES", allow=(PlatformMode.DISCOVER, PlatformMode.PRACTICE), review=(PlatformMode.SUBMIT,), block=(PlatformMode.TRAIN,), discovery=("manual_reference", "licensed_problem_index"), allowed=("problem_metadata", "user_owned_solution"), blocked=("bulk_statement_corpus", "hidden_tests", "community_solution")),
    _p("kattis", "Kattis", allow=(PlatformMode.PRACTICE,), review=(PlatformMode.DISCOVER, PlatformMode.SUBMIT), block=(PlatformMode.TRAIN,), discovery=("manual_reference", "policy_reviewed_metadata"), allowed=("problem_metadata", "user_owned_solution"), blocked=("bulk_statement_corpus", "hidden_tests", "machine_account_submission")),
    _p("project_euler", "Project Euler", allow=(PlatformMode.DISCOVER, PlatformMode.PRACTICE), review=(PlatformMode.SUBMIT, PlatformMode.TRAIN), block=(), discovery=("problem_id_reference", "manual_reference"), allowed=("problem_metadata", "problem_id_reference", "user_owned_solution"), blocked=("bulk_statement_corpus", "published_answer")),
    _p("atcoder", "AtCoder", allow=(PlatformMode.PRACTICE,), review=(PlatformMode.DISCOVER, PlatformMode.SUBMIT), block=(PlatformMode.TRAIN,), discovery=("manual_reference", "user_progress_export"), allowed=("problem_metadata", "user_owned_solution"), blocked=("bulk_statement_corpus", "hidden_tests", "community_solution")),
    _p("dmoj", "DMOJ", allow=(PlatformMode.DISCOVER, PlatformMode.PRACTICE), review=(PlatformMode.SUBMIT,), block=(PlatformMode.TRAIN,), discovery=("public_api_metadata", "manual_reference"), allowed=("problem_metadata", "profile_metadata", "user_owned_solution"), blocked=("judge_training", "automated_submission", "third_party_statement_corpus")),
    _p("advent_of_code", "Advent of Code", allow=(PlatformMode.DISCOVER, PlatformMode.PRACTICE), review=(PlatformMode.SUBMIT,), block=(PlatformMode.TRAIN,), discovery=("event_metadata", "manual_reference"), allowed=("event_metadata", "private_input", "user_owned_solution"), blocked=("bulk_statement_corpus", "public_input_redistribution", "published_answer")),
)
PLATFORM_BY_ID = {item.platform_id: item for item in PLATFORMS}


class PolicyGate:
    def evaluate(self, request: AccessRequest) -> Verdict:
        policy = PLATFORM_BY_ID[request.platform_id]
        decision = Decision.ALLOW if request.explicit_permission else policy.mode_decision(request.mode)
        reasons = [f"mode_default:{decision.value}"]
        controls = ["retain_provenance", "no_hidden_tests", "no_statement_mirror"]

        if request.content_class in policy.blocked_content:
            decision = Decision.BLOCK
            reasons.append("blocked_content_class")
        elif request.content_class not in policy.allowed_content:
            decision = max_decision(decision, Decision.REVIEW)
            reasons.append("unknown_content_class")

        if request.automated and request.mode is PlatformMode.SUBMIT:
            decision = max_decision(decision, Decision.REVIEW)
            reasons.append("automated_submission")
            controls.append("human_submission_required")

        if request.mode is PlatformMode.TRAIN and not (
            request.explicit_permission
            or request.user_owned
            or request.license_id in {"MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "CC0-1.0"}
        ):
            decision = max_decision(decision, Decision.REVIEW)
            reasons.append("training_license_unverified")
            controls.append("license_review_required")

        if request.platform_id == "dmoj" and request.mode is PlatformMode.TRAIN and not request.explicit_permission:
            decision = Decision.BLOCK
            reasons.append("administrator_permission_required")

        if request.public_export and policy.attribution_required:
            controls.append("attribution_manifest_required")
        return Verdict(decision, tuple(dict.fromkeys(reasons)), tuple(dict.fromkeys(controls)), f"omega-r05:{policy.platform_id}")


def max_decision(left: Decision, right: Decision) -> Decision:
    rank = {Decision.ALLOW: 0, Decision.REVIEW: 1, Decision.BLOCK: 2}
    return left if rank[left] >= rank[right] else right


class ContaminationError(ValueError):
    pass


_FORBIDDEN = {"statement", "full_statement", "solution", "editorial", "community_solution", "hidden_tests", "private_tests", "answer"}
_ALIASES = {"graphs": "graph", "bfs": "graph_traversal", "dfs": "graph_traversal", "dp": "dynamic_programming", "number-theory": "number_theory", "binary-search": "binary_search", "two-pointers": "two_pointers"}


class Normalizer:
    def normalize(self, items: Iterable[ProblemRef | Mapping[str, Any]]) -> tuple[NormalizedProblem, ...]:
        output: dict[str, NormalizedProblem] = {}
        for raw in items:
            if isinstance(raw, Mapping):
                forbidden = _FORBIDDEN.intersection(raw) | _FORBIDDEN.intersection(raw.get("metadata", {}))
                if forbidden:
                    raise ContaminationError("forbidden fields: " + ", ".join(sorted(forbidden)))
                raw = ProblemRef(
                    platform_id=str(raw["platform_id"]),
                    external_id=str(raw["external_id"]),
                    title=str(raw.get("title", raw["external_id"])),
                    tags=tuple(map(str, raw.get("tags", ()))),
                    difficulty=float(raw.get("difficulty", 0.5)),
                    content_class=str(raw.get("content_class", "problem_metadata")),
                    locator=str(raw.get("locator", "")),
                    solved=bool(raw.get("solved", False)),
                    attempted=bool(raw.get("attempted", False)),
                    metadata=dict(raw.get("metadata", {})),
                )
            skills = tuple(sorted({_tag(tag) for tag in raw.tags if tag.strip()})) or ("general_problem_solving",)
            canonical_id = stable_id("external-problem", [raw.platform_id, raw.external_id])
            problem = NormalizedProblem(canonical_id, raw.platform_id, raw.external_id, sha256_hex(raw.title), skills, raw.difficulty, raw.content_class, raw.locator, raw.solved, raw.attempted)
            previous = output.get(canonical_id)
            if previous:
                problem = NormalizedProblem(
                    canonical_id, raw.platform_id, raw.external_id, previous.title_hash,
                    tuple(sorted(set(previous.skills) | set(problem.skills))),
                    max(previous.difficulty, problem.difficulty), previous.content_class,
                    previous.locator or problem.locator, previous.solved or problem.solved,
                    previous.attempted or problem.attempted,
                )
            output[canonical_id] = problem
        return tuple(output[key] for key in sorted(output))


def _tag(value: str) -> str:
    key = value.strip().lower().replace("_", "-")
    return _ALIASES.get(key, key.replace("-", "_").replace(" ", "_"))
