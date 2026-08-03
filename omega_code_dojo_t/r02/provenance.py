from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import LicenseDecision, ProvenanceRecord


@dataclass(frozen=True)
class IPGateResult:
    decision: LicenseDecision
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {"decision": self.decision.value, "reasons": list(self.reasons)}


class IPGate:
    """Conservative policy gate for training and redistribution decisions."""

    blocked_source_types = frozenset(
        {
            "scraped_restricted_service",
            "hidden_test_extraction",
            "unknown_proprietary_dump",
            "credentialed_private_source_without_consent",
        }
    )
    review_licenses = frozenset({"UNKNOWN", "CUSTOM", "NOASSERTION"})

    def evaluate(self, record: ProvenanceRecord, purpose: str) -> IPGateResult:
        reasons: list[str] = []
        if record.source_type in self.blocked_source_types:
            reasons.append(f"blocked source type: {record.source_type}")
            return IPGateResult(LicenseDecision.BLOCK, tuple(reasons))

        if purpose == "train" and not record.training_allowed:
            reasons.append("training is not allowed by the provenance record")
        if purpose == "redistribute" and not record.redistribution_allowed:
            reasons.append("redistribution is not allowed by the provenance record")
        if purpose == "commercial" and not record.commercial_use_allowed:
            reasons.append("commercial use is not allowed by the provenance record")
        if reasons:
            return IPGateResult(LicenseDecision.BLOCK, tuple(reasons))

        if record.license_id.upper() in self.review_licenses:
            reasons.append(f"license requires review: {record.license_id}")
        if not record.content_hash or len(record.content_hash) < 16:
            reasons.append("content hash is missing or too short")
        if not record.author:
            reasons.append("author or source owner is not identified")
        if record.attribution_required and not record.notes:
            reasons.append("attribution is required but no attribution note is stored")

        if reasons:
            return IPGateResult(LicenseDecision.REVIEW, tuple(reasons))
        return IPGateResult(LicenseDecision.ALLOW, ("policy requirements satisfied",))

    def batch_evaluate(
        self, records: Iterable[ProvenanceRecord], purpose: str
    ) -> dict[str, IPGateResult]:
        return {record.source_id: self.evaluate(record, purpose) for record in records}
