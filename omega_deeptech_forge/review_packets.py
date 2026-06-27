from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal

from .core import (
    REDACTED_SUMMARY,
    HandoffPacket,
    IPClass,
    OAKStatus,
    Signal,
    dry_run_report,
)

PacketKind = Literal[
    "blocked_repair",
    "draft_research_review",
    "ip_review_packet",
    "service_offer_card",
    "open_publication_note",
    "negative_memory_archive",
]


@dataclass(frozen=True)
class ValueAxisScores:
    """Company/Revenue/IP OS scoring axes.

    Scores are normalized from 0 to 5 and deliberately coarse. They are a
    review signal, not a revenue forecast or investment recommendation.
    """

    evidence: float
    market_clarity: float
    artifact_readiness: float
    risk_control: float
    privacy_safety: float
    readiness: float

    def to_dict(self) -> dict[str, float]:
        return {
            "evidence": _clamp05(self.evidence),
            "market_clarity": _clamp05(self.market_clarity),
            "artifact_readiness": _clamp05(self.artifact_readiness),
            "risk_control": _clamp05(self.risk_control),
            "privacy_safety": _clamp05(self.privacy_safety),
            "readiness": _clamp05(self.readiness),
        }

    @property
    def mean(self) -> float:
        scores = self.to_dict()
        return round(sum(scores.values()) / len(scores), 3)


@dataclass(frozen=True)
class ReviewPacket:
    """Public-safe packet connecting DeepTech Forge to Company/Revenue/IP OS."""

    packet_id: str
    kind: PacketKind
    title: str
    handoff: HandoffPacket
    scores: ValueAxisScores
    review_status: str
    gates: tuple[str, ...]
    next_actions: tuple[str, ...]
    offer_card: dict[str, Any] | None = None
    prior_art_query_pack: dict[str, Any] | None = None
    publication_note: dict[str, Any] | None = None
    ip_disclosure_draft: dict[str, Any] | None = None
    m_minus: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "kind": self.kind,
            "title": self.title,
            "handoff": self.handoff.to_dict(),
            "scores": self.scores.to_dict(),
            "mean_score": self.scores.mean,
            "review_status": self.review_status,
            "gates": list(self.gates),
            "next_actions": list(self.next_actions),
            "offer_card": self.offer_card,
            "prior_art_query_pack": self.prior_art_query_pack,
            "publication_note": self.publication_note,
            "ip_disclosure_draft": self.ip_disclosure_draft,
            "m_minus": list(self.m_minus),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n"


def _clamp05(value: float) -> float:
    return max(0.0, min(5.0, float(value)))


def _slug(text: str) -> str:
    keep = []
    for char in text.lower().strip():
        if char.isalnum():
            keep.append(char)
        elif char in {" ", "-", "_"}:
            keep.append("-")
    slug = "".join(keep).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug[:64] or "deeptech-signal"


def _evidence_score(handoff: HandoffPacket) -> float:
    return {
        "unsourced": 0.5,
        "single_source": 2.0,
        "multi_source": 3.5,
        "measured": 4.0,
        "reproduced": 5.0,
    }[handoff.evidence_level.value]


def _score_packet(signal: Signal, handoff: HandoffPacket) -> ValueAxisScores:
    if handoff.oak_status == OAKStatus.BLOCKED:
        readiness = 0.5
    elif handoff.oak_status == OAKStatus.DRAFT_ONLY:
        readiness = 1.5
    elif handoff.oak_status == OAKStatus.REVIEW_REQUIRED:
        readiness = 2.5
    else:
        readiness = 4.0

    risk_control = 4.5 if handoff.redacted else 3.5
    if handoff.oak_status in {OAKStatus.BLOCKED, OAKStatus.DRAFT_ONLY}:
        risk_control = 2.0

    privacy_safety = 5.0 if handoff.redacted else 4.0
    if handoff.oak_status == OAKStatus.DRAFT_ONLY:
        privacy_safety = 3.0

    market_clarity = 1.0 + 4.0 * signal.revenue_score
    artifact_readiness = 1.0 + 4.0 * signal.testability_score

    return ValueAxisScores(
        evidence=_evidence_score(handoff),
        market_clarity=market_clarity,
        artifact_readiness=artifact_readiness,
        risk_control=risk_control,
        privacy_safety=privacy_safety,
        readiness=readiness,
    )


def _packet_kind(handoff: HandoffPacket) -> PacketKind:
    if handoff.oak_status == OAKStatus.BLOCKED:
        return "blocked_repair"
    if handoff.oak_status == OAKStatus.DRAFT_ONLY:
        return "draft_research_review"
    if handoff.ip_class in {IPClass.PATENT_REVIEW, IPClass.TRADE_SECRET}:
        return "ip_review_packet"
    if handoff.ip_class == IPClass.SERVICE_REVENUE:
        return "service_offer_card"
    if handoff.ip_class == IPClass.OPEN_PUBLIC:
        return "open_publication_note"
    return "negative_memory_archive"


def _review_status(kind: PacketKind, scores: ValueAxisScores) -> str:
    if kind in {"blocked_repair", "draft_research_review"}:
        return "DRAFT_ONLY"
    if kind == "ip_review_packet":
        return "HUMAN_IP_REVIEW_REQUIRED"
    if kind == "negative_memory_archive":
        return "ARCHIVE_OR_OBSERVE"
    if scores.mean >= 4.0:
        return "REVIEW_READY"
    return "REWRITE_BEFORE_REVIEW"


def _common_m_minus(handoff: HandoffPacket) -> tuple[str, ...]:
    notes = list(handoff.negative_memory)
    if handoff.redacted:
        notes.append("Sensitive IP route: do not expose full technical details in public GitHub artifacts.")
    if handoff.oak_status in {OAKStatus.BLOCKED, OAKStatus.DRAFT_ONLY}:
        notes.append("Do not convert into offer, publication, or outreach before source repair.")
    notes.append("No external sending, filing, or publication is authorized by this packet.")
    return tuple(dict.fromkeys(notes))


def build_offer_card(signal: Signal, handoff: HandoffPacket) -> dict[str, Any]:
    """Build a public-safe service/revenue offer card."""

    return {
        "offer_id": f"offer-{_slug(signal.title)}",
        "status": "HYPOTHESIS_READY",
        "ip_protection_mode": "PUBLIC_SAFE_SERVICE_DESCRIPTION" if not handoff.redacted else "BLACK_BOX_SERVICE",
        "audience_hypothesis": signal.domain,
        "value_hypothesis": handoff.safe_summary,
        "proof_level": handoff.evidence_level.value,
        "risk_check": handoff.risk_notes,
        "pricing_hypothesis": "TBD after non-confidential pilot validation.",
        "validation_threshold": "At least one reviewer or pilot user confirms the problem and accepts a benchmark/review packet.",
        "forbidden_actions": [
            "external_outreach_without_approval",
            "public_claim_beyond_evidence",
            "ip_disclosure_without_review",
            "revenue_guarantee",
        ],
    }


def build_prior_art_query_pack(signal: Signal, handoff: HandoffPacket) -> dict[str, Any]:
    """Build a public-safe prior-art query pack without exposing implementation details."""

    return {
        "query_pack_id": f"prior-art-{_slug(signal.title)}",
        "status": "PRIVATE_REVIEW_REQUIRED",
        "search_domains": ["patents", "papers", "open_source", "standards", "commercial_products"],
        "safe_query_terms": sorted({signal.domain, *signal.tags, "deeptech", "benchmark", "system"}),
        "redaction_notice": REDACTED_SUMMARY if handoff.redacted else "No automatic redaction applied.",
        "review_questions": [
            "What public work already solves the same problem?",
            "Which claims are novel only as an implementation detail?",
            "Which parts should remain trade secret instead of being published?",
            "What evidence is needed before any patentability discussion?",
        ],
        "forbidden_actions": ["do_not_file_patent_from_this_packet", "do_not_publish_claims_from_this_packet"],
    }


def build_publication_note(signal: Signal, handoff: HandoffPacket) -> dict[str, Any]:
    return {
        "note_id": f"pub-note-{_slug(signal.title)}",
        "status": "PUBLIC_SAFE_DRAFT",
        "title": signal.title,
        "claim_status": "evidence_bounded",
        "summary": handoff.safe_summary,
        "sources": list(handoff.source_urls),
        "limits": [
            "This note is not a scientific certification.",
            "Claims must remain within the listed evidence level.",
            "No confidential or patent-review details may be added without review.",
        ],
        "next_artifact": "DCT-Ω publication card or benchmark report.",
    }


def build_ip_disclosure_draft(signal: Signal, handoff: HandoffPacket) -> dict[str, Any]:
    return {
        "draft_id": f"ip-draft-{_slug(signal.title)}",
        "status": "PRIVATE_REVIEW_REQUIRED",
        "title": signal.title,
        "public_safe_summary": handoff.safe_summary,
        "evidence_level": handoff.evidence_level.value,
        "owner_notes": "To be completed in a private review channel.",
        "novelty_hypothesis": "REDACTED_OR_TBD_PRIVATE_REVIEW",
        "prior_art_search_needed": True,
        "professional_review_needed": True,
        "public_disclosure_risk": "high" if handoff.redacted else "medium",
    }


def build_review_packet(signal: Signal, *, generated_at: str | None = None) -> ReviewPacket:
    """Create a public-safe review packet from one deeptech signal.

    This is the bridge from DeepTech Forge to Company/Revenue/IP OS. It prepares
    review artifacts only. It never sends emails, files IP, publishes, or claims
    legal/revenue certainty.
    """

    normalized = signal.normalized()
    handoff = dry_run_report(normalized, generated_at=generated_at)
    kind = _packet_kind(handoff)
    scores = _score_packet(normalized, handoff)
    gates: list[str] = []
    next_actions = list(handoff.next_actions)

    offer_card = None
    prior_art_query_pack = None
    publication_note = None
    ip_disclosure_draft = None

    if kind == "ip_review_packet":
        gates.extend(["human_ip_review_required", "public_details_redacted"])
        prior_art_query_pack = build_prior_art_query_pack(normalized, handoff)
        ip_disclosure_draft = build_ip_disclosure_draft(normalized, handoff)
    elif kind == "service_offer_card":
        gates.append("approval_required_before_outreach")
        offer_card = build_offer_card(normalized, handoff)
    elif kind == "open_publication_note":
        gates.append("claim_audit_required_before_publication")
        publication_note = build_publication_note(normalized, handoff)
    elif kind == "draft_research_review":
        gates.append("source_repair_required")
    elif kind == "blocked_repair":
        gates.append("metadata_repair_required")
    else:
        gates.append("archive_or_observe")

    next_actions.append("Record approval or rejection before any external action.")

    return ReviewPacket(
        packet_id=f"packet-{_slug(normalized.title)}",
        kind=kind,
        title=normalized.title,
        handoff=handoff,
        scores=scores,
        review_status=_review_status(kind, scores),
        gates=tuple(gates),
        next_actions=tuple(dict.fromkeys(next_actions)),
        offer_card=offer_card,
        prior_art_query_pack=prior_art_query_pack,
        publication_note=publication_note,
        ip_disclosure_draft=ip_disclosure_draft,
        m_minus=_common_m_minus(handoff),
    )
