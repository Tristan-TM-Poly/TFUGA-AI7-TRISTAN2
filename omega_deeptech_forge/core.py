from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Literal


class EvidenceLevel(str, Enum):
    UNSOURCED = "unsourced"
    SINGLE_SOURCE = "single_source"
    MULTI_SOURCE = "multi_source"
    MEASURED = "measured"
    REPRODUCED = "reproduced"


class IPClass(str, Enum):
    OPEN_PUBLIC = "open_public"
    PATENT_REVIEW = "patent_review"
    TRADE_SECRET = "trade_secret"
    SERVICE_REVENUE = "service_revenue"
    DISCARD = "discard"


class OAKStatus(str, Enum):
    BLOCKED = "blocked"
    DRAFT_ONLY = "draft_only"
    REVIEW_REQUIRED = "review_required"
    SAFE_TO_EXPLORE = "safe_to_explore"


@dataclass(frozen=True)
class Signal:
    title: str
    summary: str
    source_urls: tuple[str, ...] = ()
    domain: str = "deeptech"
    novelty_score: float = 0.0
    testability_score: float = 0.0
    revenue_score: float = 0.0
    disclosure_risk: float = 0.0
    evidence_level: EvidenceLevel = EvidenceLevel.UNSOURCED
    tags: tuple[str, ...] = ()

    def normalized(self) -> "Signal":
        return Signal(
            title=self.title.strip(),
            summary=self.summary.strip(),
            source_urls=tuple(u.strip() for u in self.source_urls if u.strip()),
            domain=self.domain.strip().lower() or "deeptech",
            novelty_score=_clamp01(self.novelty_score),
            testability_score=_clamp01(self.testability_score),
            revenue_score=_clamp01(self.revenue_score),
            disclosure_risk=_clamp01(self.disclosure_risk),
            evidence_level=self.evidence_level,
            tags=tuple(t.strip().lower() for t in self.tags if t.strip()),
        )


@dataclass(frozen=True)
class ForgeDecision:
    signal: Signal
    oak_status: OAKStatus
    ip_class: IPClass
    reasons: tuple[str, ...]
    next_actions: tuple[str, ...]
    negative_memory: tuple[str, ...] = field(default_factory=tuple)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _has_any(tags: Iterable[str], keywords: Iterable[str]) -> bool:
    tagset = {t.lower() for t in tags}
    return any(k.lower() in tagset for k in keywords)


def classify_ip(signal: Signal) -> IPClass:
    """Classify a signal into an OAK-safe IP/revenue route.

    This is heuristic triage, not legal advice and not a patentability opinion.
    """
    s = signal.normalized()

    if not s.title or not s.summary:
        return IPClass.DISCARD

    if _has_any(s.tags, {"secret", "confidential", "undisclosed", "invention"}):
        return IPClass.PATENT_REVIEW if s.novelty_score >= 0.55 else IPClass.TRADE_SECRET

    if s.disclosure_risk >= 0.70 and s.novelty_score >= 0.50:
        return IPClass.PATENT_REVIEW

    if s.revenue_score >= 0.65 and s.testability_score >= 0.45:
        return IPClass.SERVICE_REVENUE

    if s.evidence_level in {EvidenceLevel.UNSOURCED, EvidenceLevel.SINGLE_SOURCE} and s.novelty_score < 0.35:
        return IPClass.DISCARD

    return IPClass.OPEN_PUBLIC


def oak_gate(signal: Signal) -> tuple[OAKStatus, tuple[str, ...], tuple[str, ...]]:
    """Return OAK status, reasons, and negative-memory warnings."""
    s = signal.normalized()
    reasons: list[str] = []
    m_minus: list[str] = []

    if not s.title:
        reasons.append("missing title")
    if not s.summary:
        reasons.append("missing summary")
    if not s.source_urls:
        reasons.append("missing sources")
        m_minus.append("Do not promote unsourced intelligence signals.")
    if s.evidence_level == EvidenceLevel.UNSOURCED:
        reasons.append("unsourced evidence level")
        m_minus.append("Unsourced claims must stay draft-only until verified.")
    if s.disclosure_risk >= 0.70:
        reasons.append("high disclosure risk")
        m_minus.append("Do not publish potentially patentable/confidential content before IP review.")

    if not s.title or not s.summary:
        return OAKStatus.BLOCKED, tuple(reasons), tuple(m_minus)
    if s.evidence_level == EvidenceLevel.UNSOURCED or not s.source_urls:
        return OAKStatus.DRAFT_ONLY, tuple(reasons), tuple(m_minus)
    if s.disclosure_risk >= 0.70:
        return OAKStatus.REVIEW_REQUIRED, tuple(reasons), tuple(m_minus)
    return OAKStatus.SAFE_TO_EXPLORE, tuple(reasons or ["basic OAK checks passed"]), tuple(m_minus)


def forge_decision(signal: Signal) -> ForgeDecision:
    s = signal.normalized()
    ip_class = classify_ip(s)
    oak_status, reasons, m_minus = oak_gate(s)
    next_actions: list[str] = []

    if oak_status == OAKStatus.BLOCKED:
        next_actions.append("Repair missing title/summary before further processing.")
    elif oak_status == OAKStatus.DRAFT_ONLY:
        next_actions.append("Add primary sources and citations before external use.")
    elif oak_status == OAKStatus.REVIEW_REQUIRED:
        next_actions.append("Route to IP/legal review before publication or outreach.")
    else:
        next_actions.append("Create a GitHub issue with OAK reasons, prototype task, and revenue hypothesis.")

    if ip_class == IPClass.PATENT_REVIEW:
        next_actions.append("Prepare prior-art query pack and provisional-claim sketch, private only.")
    elif ip_class == IPClass.SERVICE_REVENUE:
        next_actions.append("Convert into a client-facing service/report offer and validate price willingness.")
    elif ip_class == IPClass.OPEN_PUBLIC:
        next_actions.append("Publish as open research note only after source and claim audit.")
    elif ip_class == IPClass.TRADE_SECRET:
        next_actions.append("Keep implementation private; document secret-boundary and access rules.")
    elif ip_class == IPClass.DISCARD:
        next_actions.append("Archive as negative memory unless new evidence appears.")

    return ForgeDecision(
        signal=s,
        oak_status=oak_status,
        ip_class=ip_class,
        reasons=tuple(reasons),
        next_actions=tuple(next_actions),
        negative_memory=tuple(m_minus),
    )
