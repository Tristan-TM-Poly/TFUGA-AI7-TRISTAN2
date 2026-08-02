"""Audit synthetic worker submissions against lease and provenance evidence."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ExpectedLease:
    item_id: str
    lease_id: str
    worker_id: str
    payload_digest: str
    expires_at: int


@dataclass(frozen=True)
class WorkerSubmission:
    item_id: str
    lease_id: str
    worker_id: str
    payload_digest: str
    result_digest: str
    submitted_at: int


@dataclass(frozen=True)
class SubmissionVerdict:
    submission: WorkerSubmission
    accepted: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class WorkerAuditReport:
    verdicts: tuple[SubmissionVerdict, ...]
    accepted_items: tuple[str, ...]
    rejected_count: int
    equivocation_workers: tuple[str, ...]
    claim: str = "synthetic_worker_evidence_audit_only"


def audit_submissions(
    leases: Iterable[ExpectedLease],
    submissions: Iterable[WorkerSubmission],
    *,
    revoked_workers: Iterable[str] = (),
) -> WorkerAuditReport:
    lease_map = {lease.lease_id: lease for lease in leases}
    revoked = set(revoked_workers)
    accepted_items: set[str] = set()
    result_by_worker_item: dict[tuple[str, str], str] = {}
    equivocation: set[str] = set()
    verdicts: list[SubmissionVerdict] = []
    for submission in submissions:
        reasons: list[str] = []
        lease = lease_map.get(submission.lease_id)
        if lease is None:
            reasons.append("unknown_lease")
        else:
            if submission.item_id != lease.item_id:
                reasons.append("item_mismatch")
            if submission.worker_id != lease.worker_id:
                reasons.append("worker_mismatch")
            if submission.payload_digest != lease.payload_digest:
                reasons.append("payload_digest_mismatch")
            if submission.submitted_at >= lease.expires_at:
                reasons.append("stale_lease")
        if submission.worker_id in revoked:
            reasons.append("revoked_worker")
        if submission.item_id in accepted_items:
            reasons.append("duplicate_item_commit")
        key = (submission.worker_id, submission.item_id)
        previous = result_by_worker_item.get(key)
        if previous is not None and previous != submission.result_digest:
            reasons.append("equivocation")
            equivocation.add(submission.worker_id)
        result_by_worker_item[key] = submission.result_digest
        accepted = not reasons
        if accepted:
            accepted_items.add(submission.item_id)
        verdicts.append(SubmissionVerdict(submission, accepted, tuple(reasons)))
    return WorkerAuditReport(
        verdicts=tuple(verdicts),
        accepted_items=tuple(sorted(accepted_items)),
        rejected_count=sum(not item.accepted for item in verdicts),
        equivocation_workers=tuple(sorted(equivocation)),
    )
