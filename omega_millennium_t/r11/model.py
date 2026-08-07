from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

BUNDLE_SCHEMA = "omega-competition-ledger-bundle/11"
REPORT_SCHEMA = "omega-competition-ledger-report/11"

CYCLE_STATES = {"announced", "active", "judging", "closed", "archived"}
PLAN_TYPES = {"eligibility", "submission"}
PLAN_STATUSES = {"draft", "reviewed", "authorized", "withdrawn"}
RESULT_STATUSES = {"submitted", "accepted", "rejected", "scored", "winner", "not_selected"}
SOURCE_KINDS = {
    "official_rules",
    "official_announcement",
    "official_task",
    "official_results",
    "official_faq",
}

FORBIDDEN_FIELDS = {
    "open_problem",
    "open_problem_status",
    "proof_claimed",
    "solution_claimed",
    "mathematical_truth_probability",
    "auto_register",
    "auto_submit",
    "submit_now",
    "register_now",
    "registration_performed",
    "submission_performed",
    "payment_guaranteed",
    "winner_guaranteed",
}

DEADLINE_KEYS = (
    "announced_at",
    "registration_open",
    "registration_close",
    "task_release",
    "submission_open",
    "submission_close",
    "judging_end",
    "archive_at",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def require_nonempty(value: Any, field_name: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{field_name} must be non-empty")
    return result


def require_sha256(value: Any, field_name: str) -> str:
    result = require_nonempty(value, field_name).lower()
    if len(result) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    try:
        int(result, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be hexadecimal") from exc
    return result


def parse_datetime(value: Any, field_name: str) -> datetime:
    text = require_nonempty(value, field_name)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include an explicit timezone")
    return parsed


def validate_zone(value: Any, field_name: str = "timezone") -> str:
    zone = require_nonempty(value, field_name)
    try:
        ZoneInfo(zone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown IANA timezone: {zone}") from exc
    return zone


def require_string_list(
    value: Any,
    field_name: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    result = tuple(require_nonempty(item, field_name) for item in value)
    if not allow_empty and not result:
        raise ValueError(f"{field_name} cannot be empty")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} cannot contain duplicates")
    return result


def reject_forbidden_fields(value: Any, path: str = "bundle") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).strip().lower()
            if normalized in FORBIDDEN_FIELDS:
                raise ValueError(f"forbidden competition-ledger field at {path}.{key}")
            reject_forbidden_fields(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_forbidden_fields(item, f"{path}[{index}]")


@dataclass(frozen=True)
class SourceReceipt:
    source_id: str
    source_kind: str
    official_url: str
    source_digest: str
    observed_at: str
    location: str
    organizer_domain: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "SourceReceipt":
        allowed = {
            "source_id",
            "source_kind",
            "official_url",
            "source_digest",
            "observed_at",
            "location",
            "organizer_domain",
            "metadata",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown source fields: {sorted(unknown)}")
        source_kind = require_nonempty(row.get("source_kind"), "source_kind")
        if source_kind not in SOURCE_KINDS:
            raise ValueError(f"unsupported source_kind: {source_kind}")
        observed_at = require_nonempty(row.get("observed_at"), "observed_at")
        parse_datetime(observed_at, "observed_at")
        metadata = row.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise ValueError("source metadata must be an object")
        return cls(
            source_id=require_nonempty(row.get("source_id"), "source_id"),
            source_kind=source_kind,
            official_url=require_nonempty(row.get("official_url"), "official_url"),
            source_digest=require_sha256(row.get("source_digest"), "source_digest"),
            observed_at=observed_at,
            location=require_nonempty(row.get("location"), "location"),
            organizer_domain=require_nonempty(row.get("organizer_domain"), "organizer_domain"),
            metadata=dict(metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_kind": self.source_kind,
            "official_url": self.official_url,
            "source_digest": self.source_digest,
            "observed_at": self.observed_at,
            "location": self.location,
            "organizer_domain": self.organizer_domain,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class EligibilityRules:
    registration_required: bool
    participation_mode: str
    team_min_size: int
    team_max_size: int
    minimum_age: int | None
    maximum_age: int | None
    allowed_residencies: tuple[str, ...]
    excluded_residencies: tuple[str, ...]
    affiliation_requirements: tuple[str, ...]
    identity_verification_required: bool
    terms_reference_ids: tuple[str, ...]

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "EligibilityRules":
        allowed = {
            "registration_required",
            "participation_mode",
            "team_min_size",
            "team_max_size",
            "minimum_age",
            "maximum_age",
            "allowed_residencies",
            "excluded_residencies",
            "affiliation_requirements",
            "identity_verification_required",
            "terms_reference_ids",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown eligibility fields: {sorted(unknown)}")
        mode = require_nonempty(row.get("participation_mode"), "participation_mode")
        if mode not in {"individual", "team", "individual_or_team"}:
            raise ValueError(f"unsupported participation_mode: {mode}")
        team_min = row.get("team_min_size")
        team_max = row.get("team_max_size")
        if not isinstance(team_min, int) or isinstance(team_min, bool) or team_min < 1:
            raise ValueError("team_min_size must be a positive integer")
        if not isinstance(team_max, int) or isinstance(team_max, bool) or team_max < team_min:
            raise ValueError("team_max_size must be >= team_min_size")
        minimum_age = row.get("minimum_age")
        maximum_age = row.get("maximum_age")
        for name, value in (("minimum_age", minimum_age), ("maximum_age", maximum_age)):
            if value is not None and (
                not isinstance(value, int) or isinstance(value, bool) or value < 0
            ):
                raise ValueError(f"{name} must be a nonnegative integer or null")
        if minimum_age is not None and maximum_age is not None and minimum_age > maximum_age:
            raise ValueError("minimum_age cannot exceed maximum_age")
        registration_required = row.get("registration_required")
        identity_required = row.get("identity_verification_required")
        if not isinstance(registration_required, bool) or not isinstance(identity_required, bool):
            raise ValueError("registration and identity flags must be boolean")
        return cls(
            registration_required=registration_required,
            participation_mode=mode,
            team_min_size=team_min,
            team_max_size=team_max,
            minimum_age=minimum_age,
            maximum_age=maximum_age,
            allowed_residencies=require_string_list(
                row.get("allowed_residencies", []),
                "allowed_residencies",
                allow_empty=True,
            ),
            excluded_residencies=require_string_list(
                row.get("excluded_residencies", []),
                "excluded_residencies",
                allow_empty=True,
            ),
            affiliation_requirements=require_string_list(
                row.get("affiliation_requirements", []),
                "affiliation_requirements",
                allow_empty=True,
            ),
            identity_verification_required=identity_required,
            terms_reference_ids=require_string_list(
                row.get("terms_reference_ids", []),
                "terms_reference_ids",
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "registration_required": self.registration_required,
            "participation_mode": self.participation_mode,
            "team_min_size": self.team_min_size,
            "team_max_size": self.team_max_size,
            "minimum_age": self.minimum_age,
            "maximum_age": self.maximum_age,
            "allowed_residencies": list(self.allowed_residencies),
            "excluded_residencies": list(self.excluded_residencies),
            "affiliation_requirements": list(self.affiliation_requirements),
            "identity_verification_required": self.identity_verification_required,
            "terms_reference_ids": list(self.terms_reference_ids),
        }


@dataclass(frozen=True)
class LicenseRules:
    data_license: str
    code_license: str
    model_license: str
    external_data_policy: str
    open_source_obligation: str
    disclosure_obligation: str
    publication_obligation: str
    license_reference_ids: tuple[str, ...]

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "LicenseRules":
        allowed = {
            "data_license",
            "code_license",
            "model_license",
            "external_data_policy",
            "open_source_obligation",
            "disclosure_obligation",
            "publication_obligation",
            "license_reference_ids",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown license fields: {sorted(unknown)}")
        return cls(
            data_license=require_nonempty(row.get("data_license"), "data_license"),
            code_license=require_nonempty(row.get("code_license"), "code_license"),
            model_license=require_nonempty(row.get("model_license"), "model_license"),
            external_data_policy=require_nonempty(
                row.get("external_data_policy"), "external_data_policy"
            ),
            open_source_obligation=require_nonempty(
                row.get("open_source_obligation"), "open_source_obligation"
            ),
            disclosure_obligation=require_nonempty(
                row.get("disclosure_obligation"), "disclosure_obligation"
            ),
            publication_obligation=require_nonempty(
                row.get("publication_obligation"), "publication_obligation"
            ),
            license_reference_ids=require_string_list(
                row.get("license_reference_ids", []), "license_reference_ids"
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "data_license": self.data_license,
            "code_license": self.code_license,
            "model_license": self.model_license,
            "external_data_policy": self.external_data_policy,
            "open_source_obligation": self.open_source_obligation,
            "disclosure_obligation": self.disclosure_obligation,
            "publication_obligation": self.publication_obligation,
            "license_reference_ids": list(self.license_reference_ids),
        }


@dataclass(frozen=True)
class PrizeRules:
    amount_minor_units: int
    currency: str
    payment_conditions: tuple[str, ...]
    tax_note: str
    prize_reference_ids: tuple[str, ...]

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "PrizeRules":
        allowed = {
            "amount_minor_units",
            "currency",
            "payment_conditions",
            "tax_note",
            "prize_reference_ids",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown prize fields: {sorted(unknown)}")
        amount = row.get("amount_minor_units")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
            raise ValueError("amount_minor_units must be a nonnegative integer")
        currency = require_nonempty(row.get("currency"), "currency").upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("currency must be a three-letter alphabetic code")
        return cls(
            amount_minor_units=amount,
            currency=currency,
            payment_conditions=require_string_list(
                row.get("payment_conditions", []), "payment_conditions", allow_empty=True
            ),
            tax_note=require_nonempty(row.get("tax_note"), "tax_note"),
            prize_reference_ids=require_string_list(
                row.get("prize_reference_ids", []), "prize_reference_ids"
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "amount_minor_units": self.amount_minor_units,
            "currency": self.currency,
            "payment_conditions": list(self.payment_conditions),
            "tax_note": self.tax_note,
            "prize_reference_ids": list(self.prize_reference_ids),
        }


@dataclass(frozen=True)
class JudgingRules:
    metric: str
    direction: str
    public_leaderboard: bool
    private_leaderboard: bool
    leaderboard_leakage_risk: str
    reproducibility_requirements: tuple[str, ...]
    judging_reference_ids: tuple[str, ...]

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "JudgingRules":
        allowed = {
            "metric",
            "direction",
            "public_leaderboard",
            "private_leaderboard",
            "leaderboard_leakage_risk",
            "reproducibility_requirements",
            "judging_reference_ids",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown judging fields: {sorted(unknown)}")
        direction = require_nonempty(row.get("direction"), "direction")
        if direction not in {"maximize", "minimize", "ranked", "judged"}:
            raise ValueError(f"unsupported metric direction: {direction}")
        public = row.get("public_leaderboard")
        private = row.get("private_leaderboard")
        if not isinstance(public, bool) or not isinstance(private, bool):
            raise ValueError("leaderboard flags must be boolean")
        return cls(
            metric=require_nonempty(row.get("metric"), "metric"),
            direction=direction,
            public_leaderboard=public,
            private_leaderboard=private,
            leaderboard_leakage_risk=require_nonempty(
                row.get("leaderboard_leakage_risk"), "leaderboard_leakage_risk"
            ),
            reproducibility_requirements=require_string_list(
                row.get("reproducibility_requirements", []),
                "reproducibility_requirements",
                allow_empty=True,
            ),
            judging_reference_ids=require_string_list(
                row.get("judging_reference_ids", []), "judging_reference_ids"
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "direction": self.direction,
            "public_leaderboard": self.public_leaderboard,
            "private_leaderboard": self.private_leaderboard,
            "leaderboard_leakage_risk": self.leaderboard_leakage_risk,
            "reproducibility_requirements": list(self.reproducibility_requirements),
            "judging_reference_ids": list(self.judging_reference_ids),
        }


@dataclass(frozen=True)
class TaskRules:
    task_id: str
    title: str
    task_type: str
    artifact_digest: str | None
    archive_license: str
    task_reference_ids: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "TaskRules":
        allowed = {
            "task_id",
            "title",
            "task_type",
            "artifact_digest",
            "archive_license",
            "task_reference_ids",
            "metadata",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown task fields: {sorted(unknown)}")
        artifact_digest = row.get("artifact_digest")
        if artifact_digest is not None:
            artifact_digest = require_sha256(artifact_digest, "artifact_digest")
        metadata = row.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise ValueError("task metadata must be an object")
        return cls(
            task_id=require_nonempty(row.get("task_id"), "task_id"),
            title=require_nonempty(row.get("title"), "task title"),
            task_type=require_nonempty(row.get("task_type"), "task_type"),
            artifact_digest=artifact_digest,
            archive_license=require_nonempty(row.get("archive_license"), "archive_license"),
            task_reference_ids=require_string_list(
                row.get("task_reference_ids", []), "task_reference_ids"
            ),
            metadata=dict(metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "task_type": self.task_type,
            "artifact_digest": self.artifact_digest,
            "archive_license": self.archive_license,
            "task_reference_ids": list(self.task_reference_ids),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CompetitionCycle:
    competition_id: str
    cycle_id: str
    title: str
    organizer: str
    organizer_domain: str
    official_rule_url: str
    cycle_version: str
    timezone_name: str
    deadlines: Mapping[str, str | None]
    eligibility: EligibilityRules
    licenses: LicenseRules
    prize: PrizeRules
    judging: JudgingRules
    tasks: tuple[TaskRules, ...]
    source_reference_ids: tuple[str, ...]
    predecessor_cycle_id: str | None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "CompetitionCycle":
        allowed = {
            "competition_id",
            "cycle_id",
            "title",
            "organizer",
            "organizer_domain",
            "official_rule_url",
            "cycle_version",
            "timezone",
            "deadlines",
            "eligibility",
            "licenses",
            "prize",
            "judging",
            "tasks",
            "source_reference_ids",
            "predecessor_cycle_id",
            "metadata",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown cycle fields: {sorted(unknown)}")
        timezone_name = validate_zone(row.get("timezone"))
        deadlines_raw = row.get("deadlines")
        if not isinstance(deadlines_raw, Mapping):
            raise ValueError("deadlines must be an object")
        unknown_deadlines = set(deadlines_raw) - set(DEADLINE_KEYS)
        if unknown_deadlines:
            raise ValueError(f"unknown deadline fields: {sorted(unknown_deadlines)}")
        deadlines: dict[str, str | None] = {}
        for key in DEADLINE_KEYS:
            value = deadlines_raw.get(key)
            if value is None:
                deadlines[key] = None
            else:
                text = require_nonempty(value, key)
                parse_datetime(text, key)
                deadlines[key] = text
        if deadlines["announced_at"] is None or deadlines["submission_close"] is None:
            raise ValueError("announced_at and submission_close are required")
        task_rows = row.get("tasks", [])
        if not isinstance(task_rows, list) or not task_rows:
            raise ValueError("tasks must be a non-empty list")
        tasks = tuple(TaskRules.from_dict(item) for item in task_rows)
        if len({task.task_id for task in tasks}) != len(tasks):
            raise ValueError("task IDs must be unique within a cycle")
        predecessor = row.get("predecessor_cycle_id")
        if predecessor is not None:
            predecessor = require_nonempty(predecessor, "predecessor_cycle_id")
        metadata = row.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise ValueError("cycle metadata must be an object")
        return cls(
            competition_id=require_nonempty(row.get("competition_id"), "competition_id"),
            cycle_id=require_nonempty(row.get("cycle_id"), "cycle_id"),
            title=require_nonempty(row.get("title"), "title"),
            organizer=require_nonempty(row.get("organizer"), "organizer"),
            organizer_domain=require_nonempty(row.get("organizer_domain"), "organizer_domain"),
            official_rule_url=require_nonempty(row.get("official_rule_url"), "official_rule_url"),
            cycle_version=require_nonempty(row.get("cycle_version"), "cycle_version"),
            timezone_name=timezone_name,
            deadlines=deadlines,
            eligibility=EligibilityRules.from_dict(row.get("eligibility", {})),
            licenses=LicenseRules.from_dict(row.get("licenses", {})),
            prize=PrizeRules.from_dict(row.get("prize", {})),
            judging=JudgingRules.from_dict(row.get("judging", {})),
            tasks=tasks,
            source_reference_ids=require_string_list(
                row.get("source_reference_ids", []), "source_reference_ids"
            ),
            predecessor_cycle_id=predecessor,
            metadata=dict(metadata),
        )

    def rules_payload(self) -> dict[str, Any]:
        return {
            "competition_id": self.competition_id,
            "cycle_id": self.cycle_id,
            "organizer": self.organizer,
            "organizer_domain": self.organizer_domain,
            "official_rule_url": self.official_rule_url,
            "cycle_version": self.cycle_version,
            "timezone": self.timezone_name,
            "deadlines": dict(self.deadlines),
            "eligibility": self.eligibility.to_dict(),
            "licenses": self.licenses.to_dict(),
            "prize": self.prize.to_dict(),
            "judging": self.judging.to_dict(),
            "tasks": [task.to_dict() for task in self.tasks],
            "source_reference_ids": list(self.source_reference_ids),
            "predecessor_cycle_id": self.predecessor_cycle_id,
        }

    @property
    def rule_digest(self) -> str:
        return stable_digest(self.rules_payload())

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.rules_payload(),
            "title": self.title,
            "metadata": dict(self.metadata),
            "rule_digest": self.rule_digest,
        }


@dataclass(frozen=True)
class LocalPlan:
    plan_id: str
    competition_id: str
    cycle_id: str
    plan_type: str
    created_at: str
    rule_digest: str
    status: str
    participant_age: int | None
    participant_residency: str | None
    team_size: int | None
    assumptions: tuple[str, ...]
    authorization_reference: str | None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "LocalPlan":
        allowed = {
            "plan_id",
            "competition_id",
            "cycle_id",
            "plan_type",
            "created_at",
            "rule_digest",
            "status",
            "participant_age",
            "participant_residency",
            "team_size",
            "assumptions",
            "authorization_reference",
            "metadata",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown plan fields: {sorted(unknown)}")
        plan_type = require_nonempty(row.get("plan_type"), "plan_type")
        status = require_nonempty(row.get("status"), "plan status")
        if plan_type not in PLAN_TYPES:
            raise ValueError(f"unsupported plan_type: {plan_type}")
        if status not in PLAN_STATUSES:
            raise ValueError(f"unsupported plan status: {status}")
        created_at = require_nonempty(row.get("created_at"), "created_at")
        parse_datetime(created_at, "created_at")
        age = row.get("participant_age")
        team_size = row.get("team_size")
        if age is not None and (not isinstance(age, int) or isinstance(age, bool) or age < 0):
            raise ValueError("participant_age must be nonnegative or null")
        if team_size is not None and (
            not isinstance(team_size, int) or isinstance(team_size, bool) or team_size < 1
        ):
            raise ValueError("team_size must be positive or null")
        residency = row.get("participant_residency")
        if residency is not None:
            residency = require_nonempty(residency, "participant_residency")
        authorization = row.get("authorization_reference")
        if authorization is not None:
            authorization = require_nonempty(authorization, "authorization_reference")
        metadata = row.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise ValueError("plan metadata must be an object")
        return cls(
            plan_id=require_nonempty(row.get("plan_id"), "plan_id"),
            competition_id=require_nonempty(row.get("competition_id"), "competition_id"),
            cycle_id=require_nonempty(row.get("cycle_id"), "cycle_id"),
            plan_type=plan_type,
            created_at=created_at,
            rule_digest=require_sha256(row.get("rule_digest"), "plan rule_digest"),
            status=status,
            participant_age=age,
            participant_residency=residency,
            team_size=team_size,
            assumptions=require_string_list(
                row.get("assumptions", []), "plan assumptions", allow_empty=True
            ),
            authorization_reference=authorization,
            metadata=dict(metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "competition_id": self.competition_id,
            "cycle_id": self.cycle_id,
            "plan_type": self.plan_type,
            "created_at": self.created_at,
            "rule_digest": self.rule_digest,
            "status": self.status,
            "participant_age": self.participant_age,
            "participant_residency": self.participant_residency,
            "team_size": self.team_size,
            "assumptions": list(self.assumptions),
            "authorization_reference": self.authorization_reference,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class SubmissionReceipt:
    receipt_id: str
    competition_id: str
    cycle_id: str
    submitted_at: str
    artifact_digest: str
    external_receipt_reference: str
    rule_digest: str
    result_status: str
    result_reference_ids: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "SubmissionReceipt":
        allowed = {
            "receipt_id",
            "competition_id",
            "cycle_id",
            "submitted_at",
            "artifact_digest",
            "external_receipt_reference",
            "rule_digest",
            "result_status",
            "result_reference_ids",
            "metadata",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown submission-receipt fields: {sorted(unknown)}")
        result_status = require_nonempty(row.get("result_status"), "result_status")
        if result_status not in RESULT_STATUSES:
            raise ValueError(f"unsupported result_status: {result_status}")
        submitted_at = require_nonempty(row.get("submitted_at"), "submitted_at")
        parse_datetime(submitted_at, "submitted_at")
        metadata = row.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise ValueError("submission metadata must be an object")
        return cls(
            receipt_id=require_nonempty(row.get("receipt_id"), "receipt_id"),
            competition_id=require_nonempty(row.get("competition_id"), "competition_id"),
            cycle_id=require_nonempty(row.get("cycle_id"), "cycle_id"),
            submitted_at=submitted_at,
            artifact_digest=require_sha256(row.get("artifact_digest"), "artifact_digest"),
            external_receipt_reference=require_nonempty(
                row.get("external_receipt_reference"), "external_receipt_reference"
            ),
            rule_digest=require_sha256(row.get("rule_digest"), "submission rule_digest"),
            result_status=result_status,
            result_reference_ids=require_string_list(
                row.get("result_reference_ids", []),
                "result_reference_ids",
                allow_empty=True,
            ),
            metadata=dict(metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "competition_id": self.competition_id,
            "cycle_id": self.cycle_id,
            "submitted_at": self.submitted_at,
            "artifact_digest": self.artifact_digest,
            "external_receipt_reference": self.external_receipt_reference,
            "rule_digest": self.rule_digest,
            "result_status": self.result_status,
            "result_reference_ids": list(self.result_reference_ids),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class LedgerBundle:
    as_of: str
    freshness_seconds: int
    recommendation_timezone: str
    sources: tuple[SourceReceipt, ...]
    cycles: tuple[CompetitionCycle, ...]
    plans: tuple[LocalPlan, ...]
    submission_receipts: tuple[SubmissionReceipt, ...]

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "LedgerBundle":
        reject_forbidden_fields(row)
        allowed = {
            "schema",
            "as_of",
            "freshness_seconds",
            "recommendation_timezone",
            "sources",
            "cycles",
            "plans",
            "submission_receipts",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown ledger fields: {sorted(unknown)}")
        if row.get("schema") != BUNDLE_SCHEMA:
            raise ValueError(f"schema must equal {BUNDLE_SCHEMA}")
        as_of = require_nonempty(row.get("as_of"), "as_of")
        parse_datetime(as_of, "as_of")
        freshness = row.get("freshness_seconds")
        if not isinstance(freshness, int) or isinstance(freshness, bool) or freshness < 1:
            raise ValueError("freshness_seconds must be a positive integer")
        recommendation_timezone = validate_zone(
            row.get("recommendation_timezone"), "recommendation_timezone"
        )
        source_rows = row.get("sources", [])
        cycle_rows = row.get("cycles", [])
        plan_rows = row.get("plans", [])
        receipt_rows = row.get("submission_receipts", [])
        if not all(isinstance(value, list) for value in (source_rows, cycle_rows, plan_rows, receipt_rows)):
            raise ValueError("sources, cycles, plans and submission_receipts must be lists")
        sources = tuple(SourceReceipt.from_dict(item) for item in source_rows)
        cycles = tuple(CompetitionCycle.from_dict(item) for item in cycle_rows)
        plans = tuple(LocalPlan.from_dict(item) for item in plan_rows)
        receipts = tuple(SubmissionReceipt.from_dict(item) for item in receipt_rows)
        for label, values, key in (
            ("source", sources, lambda item: item.source_id),
            ("cycle", cycles, lambda item: (item.competition_id, item.cycle_id)),
            ("plan", plans, lambda item: item.plan_id),
            ("submission receipt", receipts, lambda item: item.receipt_id),
        ):
            keys = [key(item) for item in values]
            if len(keys) != len(set(keys)):
                raise ValueError(f"duplicate {label} identity")
        return cls(
            as_of=as_of,
            freshness_seconds=freshness,
            recommendation_timezone=recommendation_timezone,
            sources=sources,
            cycles=cycles,
            plans=plans,
            submission_receipts=receipts,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": BUNDLE_SCHEMA,
            "as_of": self.as_of,
            "freshness_seconds": self.freshness_seconds,
            "recommendation_timezone": self.recommendation_timezone,
            "sources": [item.to_dict() for item in self.sources],
            "cycles": [item.to_dict() for item in self.cycles],
            "plans": [item.to_dict() for item in self.plans],
            "submission_receipts": [item.to_dict() for item in self.submission_receipts],
        }


def load_bundle(path: str | Path) -> LedgerBundle:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError("ledger bundle root must be an object")
    return LedgerBundle.from_dict(value)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.write_text("".join(canonical_json(dict(row)) + "\n" for row in rows), encoding="utf-8")


def convert_datetime(value: str, zone_name: str) -> dict[str, str]:
    parsed = parse_datetime(value, "datetime")
    local = parsed.astimezone(ZoneInfo(zone_name))
    utc = parsed.astimezone(timezone.utc)
    montreal = parsed.astimezone(ZoneInfo("America/Montreal"))
    return {
        "source": parsed.isoformat(),
        "utc": utc.isoformat(),
        "america_montreal": montreal.isoformat(),
        "recommendation_timezone": local.isoformat(),
    }
