"""Typed R0.2 records for Ω-OPEN-PROBLEMS-ATLAS-T∞.

R0.2 separates source leads, mathematical problems, competitions, proof
obligations, methods, transfer hypotheses and evidence receipts.  No record is
promoted to an independently checked open problem by generation alone.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any


class LeadStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    SOURCE_REPORTED = "SOURCE_REPORTED"
    LICENSE_REVIEW_REQUIRED = "LICENSE_REVIEW_REQUIRED"
    STATUS_RECHECK_REQUIRED = "STATUS_RECHECK_REQUIRED"
    NORMALIZED = "NORMALIZED"
    LITERATURE_BASELINED = "LITERATURE_BASELINED"
    INDEPENDENTLY_CHECKED_OPEN = "INDEPENDENTLY_CHECKED_OPEN"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
    RESOLVED = "RESOLVED"
    DISPUTED = "DISPUTED"
    REJECTED = "REJECTED"


class EvidenceClass(str, Enum):
    SOURCE_SNAPSHOT = "SOURCE_SNAPSHOT"
    LITERATURE_CHECK = "LITERATURE_CHECK"
    STATEMENT_NORMALIZATION = "STATEMENT_NORMALIZATION"
    COMPUTATION = "COMPUTATION"
    FORMAL_CHECK = "FORMAL_CHECK"
    INDEPENDENT_REPRODUCTION = "INDEPENDENT_REPRODUCTION"
    PEER_REVIEW = "PEER_REVIEW"


class ObligationStatus(str, Enum):
    PROPOSED = "PROPOSED"
    READY = "READY"
    RUNNING = "RUNNING"
    PASSED_FINITE_FIXTURE = "PASSED_FINITE_FIXTURE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    FORMALLY_DISCHARGED = "FORMALLY_DISCHARGED"


class FormalStatus(str, Enum):
    NOT_FORMALIZED = "NOT_FORMALIZED"
    DEFINITIONS_ONLY = "DEFINITIONS_ONLY"
    PLACEHOLDERS_PRESENT = "PLACEHOLDERS_PRESENT"
    KERNEL_CHECKED_LOCAL = "KERNEL_CHECKED_LOCAL"
    INDEPENDENTLY_REBUILT = "INDEPENDENTLY_REBUILT"


@dataclass(frozen=True)
class SourceSnapshot:
    source_id: str
    canonical_url: str
    retrieved_at: str
    content_sha256: str
    license_class: str
    authority_class: str
    status_policy: str
    network_fetch_performed: bool = False
    notes: tuple[str, ...] = ()

    def canonical_hash(self) -> str:
        return _hash_payload(asdict(self))


@dataclass(frozen=True)
class ProblemLead:
    lead_id: str
    source_id: str
    source_locator: str
    title: str
    statement_summary: str
    domains: tuple[str, ...]
    kind: str
    lead_status: LeadStatus = LeadStatus.DISCOVERED
    source_snapshot_hash: str | None = None
    authors: tuple[str, ...] = ()
    citations: tuple[str, ...] = ()
    methods: tuple[str, ...] = ()
    related_ids: tuple[str, ...] = ()
    last_status_check: str | None = None
    license_reviewed: bool = False
    literature_search_required: bool = True
    independently_checked_open: bool = False
    finite_computation_is_not_proof: bool = True
    solution_claimed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def normalized_statement(self) -> str:
        return " ".join(self.statement_summary.casefold().split())

    def statement_hash(self) -> str:
        return sha256(self.normalized_statement().encode("utf-8")).hexdigest()

    def canonical_hash(self) -> str:
        payload = asdict(self)
        payload["lead_status"] = self.lead_status.value
        return _hash_payload(payload)


@dataclass(frozen=True)
class MethodCard:
    method_id: str
    name: str
    family: str
    domains: tuple[str, ...]
    prerequisites: tuple[str, ...] = ()
    known_failure_modes: tuple[str, ...] = ()
    implementation_refs: tuple[str, ...] = ()
    formalization_refs: tuple[str, ...] = ()
    status: str = "METHOD_HYPOTHESIS"

    def canonical_hash(self) -> str:
        return _hash_payload(asdict(self))


@dataclass(frozen=True)
class ProofObligation:
    obligation_id: str
    problem_id: str
    operator: str
    objective: str
    assumptions: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    falsifiers: tuple[str, ...] = ()
    expected_evidence: tuple[EvidenceClass, ...] = ()
    finite_budget_units: int = 1
    status: ObligationStatus = ObligationStatus.PROPOSED
    universal_claim: bool = False
    generated_from_template: bool = True

    def canonical_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["expected_evidence"] = [item.value for item in self.expected_evidence]
        return payload

    def canonical_hash(self) -> str:
        return _hash_payload(self.canonical_payload())


@dataclass(frozen=True)
class TransferEdge:
    edge_id: str
    source_problem_id: str
    target_problem_id: str
    method_id: str
    forward_hypothesis: str
    reverse_check: str
    shared_invariants: tuple[str, ...] = ()
    evidence_receipt_ids: tuple[str, ...] = ()
    round_trip_required: bool = True
    transfer_validated: bool = False

    def canonical_hash(self) -> str:
        return _hash_payload(asdict(self))


@dataclass(frozen=True)
class CompetitionPolicy:
    competition_id: str
    organizer: str
    canonical_url: str
    problem_class: str
    rules_snapshot_required: bool = True
    ai_use_review_required: bool = True
    identity_bound_submission: bool = True
    automated_submission_allowed: bool = False
    redistribution_allowed: bool = False
    deadline_recheck_required: bool = True
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceReceipt:
    receipt_id: str
    subject_id: str
    evidence_class: EvidenceClass
    artifact_sha256: str
    command: str
    environment: str
    observed_at: str
    result: str
    parent_receipt_hash: str | None = None
    claim_scope: str = "FINITE_DECLARED_FIXTURE"

    def canonical_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_class"] = self.evidence_class.value
        return payload

    def canonical_hash(self) -> str:
        return _hash_payload(self.canonical_payload())


@dataclass(frozen=True)
class CampaignAllocation:
    problem_id: str
    obligation_id: str
    priority_score: float
    finite_budget_units: int
    reasons: tuple[str, ...]
    status: str = "ALLOCATED_FINITE_BUDGET"


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()
