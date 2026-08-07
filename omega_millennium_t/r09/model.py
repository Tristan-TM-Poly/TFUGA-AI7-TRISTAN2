from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

BUNDLE_SCHEMA = "omega-problem-promotion-bundle/9"
REPORT_SCHEMA = "omega-problem-promotion-report/9"

PROMOTION_STATUSES = {
    "experiment",
    "restricted_theorem",
    "manuscript",
    "formal_artifact",
    "independently_reviewed_result",
}

DESTINATIONS = {
    "internal_archive",
    "public_preprint",
    "journal_submission",
    "competition_submission",
    "prize_claim",
    "patent_filing",
    "open_source_release",
    "public_talk",
}

IP_DECISIONS = {"publish", "patent", "secret", "open_source", "abandon"}

CHECK_KINDS = {
    "statement_scope",
    "literature_search",
    "prior_art_search",
    "novelty_review",
    "independent_reconstruction",
    "reproducibility_snapshot",
    "dependency_audit",
    "hidden_assumption_audit",
    "formal_verification",
    "negative_results",
    "authorship",
    "license_copyright",
    "dataset_terms",
    "competition_rules",
    "prize_recognition",
    "ip_decision",
    "limitations",
    "citations",
}

REVIEW_REQUIRED_CHECKS = {
    "novelty_review",
    "independent_reconstruction",
    "dependency_audit",
    "hidden_assumption_audit",
}

SELF_APPROVAL_FORBIDDEN_FIELDS = {
    "approved",
    "gate_passed",
    "novel",
    "correct",
    "proof_verified",
    "publication_authorized",
    "submission_authorized",
    "prize_eligible",
    "prize_winner",
    "clay_recognized",
    "truth_probability",
    "confidence_probability",
}

MANDATORY_BY_STATUS: dict[str, set[str]] = {
    "experiment": {
        "statement_scope",
        "reproducibility_snapshot",
        "negative_results",
        "authorship",
        "license_copyright",
        "limitations",
        "citations",
        "ip_decision",
    },
    "restricted_theorem": {
        "statement_scope",
        "literature_search",
        "novelty_review",
        "independent_reconstruction",
        "dependency_audit",
        "hidden_assumption_audit",
        "negative_results",
        "authorship",
        "license_copyright",
        "limitations",
        "citations",
        "ip_decision",
    },
    "manuscript": {
        "statement_scope",
        "literature_search",
        "prior_art_search",
        "novelty_review",
        "independent_reconstruction",
        "reproducibility_snapshot",
        "dependency_audit",
        "hidden_assumption_audit",
        "negative_results",
        "authorship",
        "license_copyright",
        "dataset_terms",
        "limitations",
        "citations",
        "ip_decision",
    },
    "formal_artifact": {
        "statement_scope",
        "literature_search",
        "novelty_review",
        "independent_reconstruction",
        "reproducibility_snapshot",
        "dependency_audit",
        "hidden_assumption_audit",
        "formal_verification",
        "negative_results",
        "authorship",
        "license_copyright",
        "limitations",
        "citations",
        "ip_decision",
    },
    "independently_reviewed_result": set(CHECK_KINDS)
    - {"competition_rules", "prize_recognition"},
}

MANDATORY_BY_DESTINATION: dict[str, set[str]] = {
    "internal_archive": {"statement_scope", "authorship", "limitations", "ip_decision"},
    "public_preprint": {
        "literature_search",
        "novelty_review",
        "license_copyright",
        "dataset_terms",
        "limitations",
        "citations",
        "ip_decision",
    },
    "journal_submission": {
        "literature_search",
        "novelty_review",
        "independent_reconstruction",
        "reproducibility_snapshot",
        "dependency_audit",
        "hidden_assumption_audit",
        "authorship",
        "license_copyright",
        "dataset_terms",
        "limitations",
        "citations",
        "ip_decision",
    },
    "competition_submission": {
        "competition_rules",
        "authorship",
        "license_copyright",
        "ip_decision",
    },
    "prize_claim": {
        "prize_recognition",
        "competition_rules",
        "authorship",
        "citations",
        "ip_decision",
    },
    "patent_filing": {
        "prior_art_search",
        "novelty_review",
        "authorship",
        "ip_decision",
    },
    "open_source_release": {
        "authorship",
        "license_copyright",
        "dataset_terms",
        "limitations",
        "ip_decision",
    },
    "public_talk": {
        "statement_scope",
        "limitations",
        "citations",
        "authorship",
        "ip_decision",
    },
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def parse_zoned_datetime(value: str, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty ISO-8601 datetime")
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO-8601: {value}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return parsed


def require_sha256(value: str, field_name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field_name} must be a 64-character SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be hexadecimal") from exc
    return value.lower()


def reject_self_approval_fields(value: Any, path: str = "bundle") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).strip().lower()
            if normalized in SELF_APPROVAL_FORBIDDEN_FIELDS:
                raise ValueError(f"self-approval field is forbidden at {path}.{key}")
            reject_self_approval_fields(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_self_approval_fields(item, f"{path}[{index}]")


def require_string_list(value: Any, field_name: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    result = tuple(str(item).strip() for item in value)
    if any(not item for item in result):
        raise ValueError(f"{field_name} cannot contain empty values")
    if not allow_empty and not result:
        raise ValueError(f"{field_name} cannot be empty")
    if len(set(result)) != len(result):
        raise ValueError(f"{field_name} cannot contain duplicates")
    return result


@dataclass(frozen=True)
class EvidenceReference:
    reference_id: str
    source_uri: str
    source_digest: str
    observed_at: str
    location: str
    license_note: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "EvidenceReference":
        allowed = {
            "reference_id",
            "source_uri",
            "source_digest",
            "observed_at",
            "location",
            "license_note",
            "metadata",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown evidence-reference fields: {sorted(unknown)}")
        reference_id = str(row.get("reference_id", "")).strip()
        source_uri = str(row.get("source_uri", "")).strip()
        location = str(row.get("location", "")).strip()
        license_note = str(row.get("license_note", "")).strip()
        if not all((reference_id, source_uri, location, license_note)):
            raise ValueError("evidence reference requires id, URI, location and license note")
        digest = require_sha256(str(row.get("source_digest", "")), "source_digest")
        observed_at = str(row.get("observed_at", ""))
        parse_zoned_datetime(observed_at, "observed_at")
        metadata = row.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise ValueError("evidence metadata must be an object")
        return cls(reference_id, source_uri, digest, observed_at, location, license_note, dict(metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "source_uri": self.source_uri,
            "source_digest": self.source_digest,
            "observed_at": self.observed_at,
            "location": self.location,
            "license_note": self.license_note,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CheckAttestation:
    check_id: str
    check_kind: str
    outcome: str
    scope: str
    reviewer_id: str
    reviewer_role: str
    reviewed_at: str
    evidence_reference_ids: tuple[str, ...]
    limitations: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "CheckAttestation":
        allowed = {
            "check_id",
            "check_kind",
            "outcome",
            "scope",
            "reviewer_id",
            "reviewer_role",
            "reviewed_at",
            "evidence_reference_ids",
            "limitations",
            "metadata",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown check fields: {sorted(unknown)}")
        check_id = str(row.get("check_id", "")).strip()
        check_kind = str(row.get("check_kind", "")).strip()
        outcome = str(row.get("outcome", "")).strip()
        scope = str(row.get("scope", "")).strip()
        reviewer_id = str(row.get("reviewer_id", "")).strip()
        reviewer_role = str(row.get("reviewer_role", "")).strip()
        reviewed_at = str(row.get("reviewed_at", "")).strip()
        if not all((check_id, check_kind, outcome, scope, reviewer_id, reviewer_role, reviewed_at)):
            raise ValueError("check attestation contains missing required strings")
        if check_kind not in CHECK_KINDS:
            raise ValueError(f"unsupported check_kind: {check_kind}")
        if outcome not in {"pass", "fail", "not_applicable"}:
            raise ValueError(f"unsupported check outcome: {outcome}")
        parse_zoned_datetime(reviewed_at, "reviewed_at")
        evidence_ids = require_string_list(row.get("evidence_reference_ids", []), "evidence_reference_ids")
        limitations = require_string_list(row.get("limitations", []), "limitations", allow_empty=True)
        metadata = row.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise ValueError("check metadata must be an object")
        return cls(
            check_id,
            check_kind,
            outcome,
            scope,
            reviewer_id,
            reviewer_role,
            reviewed_at,
            evidence_ids,
            limitations,
            dict(metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "check_kind": self.check_kind,
            "outcome": self.outcome,
            "scope": self.scope,
            "reviewer_id": self.reviewer_id,
            "reviewer_role": self.reviewer_role,
            "reviewed_at": self.reviewed_at,
            "evidence_reference_ids": list(self.evidence_reference_ids),
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class SignatureAttestation:
    signature_id: str
    signer_id: str
    signer_role: str
    signed_at: str
    method: str
    signature_ref: str
    payload_digest: str

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "SignatureAttestation":
        allowed = {
            "signature_id",
            "signer_id",
            "signer_role",
            "signed_at",
            "method",
            "signature_ref",
            "payload_digest",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown signature fields: {sorted(unknown)}")
        values = {key: str(row.get(key, "")).strip() for key in allowed}
        if not all(values.values()):
            raise ValueError("signature attestation contains missing required strings")
        if values["method"] not in {"sha256_detached", "pgp", "sigstore"}:
            raise ValueError(f"unsupported signature method: {values['method']}")
        parse_zoned_datetime(values["signed_at"], "signed_at")
        require_sha256(values["payload_digest"], "payload_digest")
        return cls(**values)

    def to_dict(self) -> dict[str, Any]:
        return {
            "signature_id": self.signature_id,
            "signer_id": self.signer_id,
            "signer_role": self.signer_role,
            "signed_at": self.signed_at,
            "method": self.method,
            "signature_ref": self.signature_ref,
            "payload_digest": self.payload_digest,
        }


@dataclass(frozen=True)
class PromotionRequest:
    request_id: str
    canonical_problem_id: str
    artifact_id: str
    title: str
    exact_statement: str
    assumptions: tuple[str, ...]
    status: str
    destination: str
    author_ids: tuple[str, ...]
    ip_decision: str
    requested_at: str
    evidence: tuple[EvidenceReference, ...]
    checks: tuple[CheckAttestation, ...]
    signatures: tuple[SignatureAttestation, ...]
    m_minus_records: tuple[Mapping[str, Any], ...]
    metadata: Mapping[str, Any]

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "PromotionRequest":
        reject_self_approval_fields(row)
        allowed = {
            "schema",
            "request_id",
            "canonical_problem_id",
            "artifact_id",
            "title",
            "exact_statement",
            "assumptions",
            "status",
            "destination",
            "author_ids",
            "ip_decision",
            "requested_at",
            "evidence",
            "checks",
            "signatures",
            "m_minus_records",
            "metadata",
        }
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"unknown promotion-bundle fields: {sorted(unknown)}")
        if row.get("schema") != BUNDLE_SCHEMA:
            raise ValueError(f"schema must equal {BUNDLE_SCHEMA}")
        string_fields = [
            "request_id",
            "canonical_problem_id",
            "artifact_id",
            "title",
            "exact_statement",
            "status",
            "destination",
            "ip_decision",
            "requested_at",
        ]
        values = {field_name: str(row.get(field_name, "")).strip() for field_name in string_fields}
        if not all(values.values()):
            raise ValueError("promotion bundle contains missing required strings")
        if values["status"] not in PROMOTION_STATUSES:
            raise ValueError(f"unsupported promotion status: {values['status']}")
        if values["destination"] not in DESTINATIONS:
            raise ValueError(f"unsupported destination: {values['destination']}")
        if values["ip_decision"] not in IP_DECISIONS:
            raise ValueError(f"unsupported IP decision: {values['ip_decision']}")
        parse_zoned_datetime(values["requested_at"], "requested_at")
        assumptions = require_string_list(row.get("assumptions", []), "assumptions", allow_empty=True)
        author_ids = require_string_list(row.get("author_ids", []), "author_ids")
        evidence_rows = row.get("evidence", [])
        check_rows = row.get("checks", [])
        signature_rows = row.get("signatures", [])
        m_minus_records = row.get("m_minus_records", [])
        metadata = row.get("metadata", {})
        if not isinstance(evidence_rows, list) or not isinstance(check_rows, list):
            raise ValueError("evidence and checks must be lists")
        if not isinstance(signature_rows, list) or not isinstance(m_minus_records, list):
            raise ValueError("signatures and m_minus_records must be lists")
        if not isinstance(metadata, Mapping):
            raise ValueError("metadata must be an object")
        evidence = tuple(EvidenceReference.from_dict(item) for item in evidence_rows)
        checks = tuple(CheckAttestation.from_dict(item) for item in check_rows)
        signatures = tuple(SignatureAttestation.from_dict(item) for item in signature_rows)
        if len({item.reference_id for item in evidence}) != len(evidence):
            raise ValueError("evidence reference IDs must be unique")
        if len({item.check_id for item in checks}) != len(checks):
            raise ValueError("check IDs must be unique")
        if len({item.signature_id for item in signatures}) != len(signatures):
            raise ValueError("signature IDs must be unique")
        if any(not isinstance(item, Mapping) for item in m_minus_records):
            raise ValueError("M-minus records must be objects")
        return cls(
            request_id=values["request_id"],
            canonical_problem_id=values["canonical_problem_id"],
            artifact_id=values["artifact_id"],
            title=values["title"],
            exact_statement=values["exact_statement"],
            assumptions=assumptions,
            status=values["status"],
            destination=values["destination"],
            author_ids=author_ids,
            ip_decision=values["ip_decision"],
            requested_at=values["requested_at"],
            evidence=evidence,
            checks=checks,
            signatures=signatures,
            m_minus_records=tuple(dict(item) for item in m_minus_records),
            metadata=dict(metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": BUNDLE_SCHEMA,
            "request_id": self.request_id,
            "canonical_problem_id": self.canonical_problem_id,
            "artifact_id": self.artifact_id,
            "title": self.title,
            "exact_statement": self.exact_statement,
            "assumptions": list(self.assumptions),
            "status": self.status,
            "destination": self.destination,
            "author_ids": list(self.author_ids),
            "ip_decision": self.ip_decision,
            "requested_at": self.requested_at,
            "evidence": [item.to_dict() for item in self.evidence],
            "checks": [item.to_dict() for item in self.checks],
            "signatures": [item.to_dict() for item in self.signatures],
            "m_minus_records": [dict(item) for item in self.m_minus_records],
            "metadata": dict(self.metadata),
        }


def load_request(path: str | Path) -> PromotionRequest:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError("promotion bundle root must be an object")
    return PromotionRequest.from_dict(raw)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.write_text("".join(canonical_json(dict(row)) + "\n" for row in rows), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number} must contain an object")
        rows.append(value)
    return rows
