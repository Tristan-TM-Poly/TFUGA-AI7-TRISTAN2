from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal

from .core import IPClass, OAKStatus, Signal
from .review_packets import ReviewPacket, build_review_packet

PriorityBand = Literal["blocked", "observe", "repair", "review", "build", "commercialize"]


@dataclass(frozen=True)
class OAKBenchWeights:
    """Weights for action-priority scoring.

    The default weights intentionally reward evidence, testability, revenue
    potential and safety while penalizing disclosure risk. This is an internal
    prioritization score, not a market forecast, patentability opinion or legal
    assessment.
    """

    evidence: float = 0.22
    testability: float = 0.18
    revenue: float = 0.18
    novelty: float = 0.12
    risk_control: float = 0.18
    readiness: float = 0.12

    def normalized(self) -> "OAKBenchWeights":
        total = sum(self.to_dict().values())
        if total <= 0:
            return OAKBenchWeights()
        return OAKBenchWeights(**{key: value / total for key, value in self.to_dict().items()})

    def to_dict(self) -> dict[str, float]:
        return {
            "evidence": float(self.evidence),
            "testability": float(self.testability),
            "revenue": float(self.revenue),
            "novelty": float(self.novelty),
            "risk_control": float(self.risk_control),
            "readiness": float(self.readiness),
        }


@dataclass(frozen=True)
class OAKBenchResult:
    signal: Signal
    review_packet: ReviewPacket
    action_score: float
    priority_band: PriorityBand
    build_now: bool
    commercialize_now: bool
    ip_review_required: bool
    public_action_allowed: bool
    github_actions: tuple[str, ...]
    m_minus: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal": {
                "title": self.signal.title,
                "domain": self.signal.domain,
                "evidence_level": self.signal.evidence_level.value,
                "novelty_score": self.signal.novelty_score,
                "testability_score": self.signal.testability_score,
                "revenue_score": self.signal.revenue_score,
                "disclosure_risk": self.signal.disclosure_risk,
                "tags": list(self.signal.tags),
            },
            "review_packet": self.review_packet.to_dict(),
            "action_score": self.action_score,
            "priority_band": self.priority_band,
            "build_now": self.build_now,
            "commercialize_now": self.commercialize_now,
            "ip_review_required": self.ip_review_required,
            "public_action_allowed": self.public_action_allowed,
            "github_actions": list(self.github_actions),
            "m_minus": list(self.m_minus),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n"


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _norm05(value: float) -> float:
    return _clamp01(float(value) / 5.0)


def _priority_band(packet: ReviewPacket, score: float) -> PriorityBand:
    if packet.handoff.oak_status == OAKStatus.BLOCKED:
        return "blocked"
    if packet.handoff.oak_status == OAKStatus.DRAFT_ONLY:
        return "repair"
    if packet.handoff.ip_class in {IPClass.PATENT_REVIEW, IPClass.TRADE_SECRET}:
        return "review"
    if score >= 0.78 and packet.handoff.ip_class == IPClass.SERVICE_REVENUE:
        return "commercialize"
    if score >= 0.62:
        return "build"
    return "observe"


def _github_actions(packet: ReviewPacket, band: PriorityBand) -> tuple[str, ...]:
    actions: list[str] = []

    if band == "blocked":
        actions.append("Create repair issue: missing title/summary or invalid metadata.")
    elif band == "repair":
        actions.append("Create source-repair issue with required citations and counter-hypotheses.")
    elif band == "review":
        actions.append("Create private IP-review checklist; public issue must use redacted handoff only.")
        actions.append("Generate prior-art query pack without implementation details.")
    elif band == "commercialize":
        actions.append("Create service-offer card issue gated by approval-before-outreach.")
        actions.append("Create pilot validation checklist with price, user, evidence and risk fields.")
    elif band == "build":
        actions.append("Create prototype issue with test, baseline, metric and OAK failure modes.")
    else:
        actions.append("Archive as observe/backlog; re-score when evidence or market signal improves.")

    actions.append("Attach ReviewPacket JSON as a safe artifact; never attach confidential details publicly.")
    return tuple(actions)


def run_oakbench(signal: Signal, *, weights: OAKBenchWeights | None = None, generated_at: str | None = None) -> OAKBenchResult:
    """Score one signal for OAK-safe action priority.

    The output tells AUTO²/GitHub what to do next while preserving OAK gates:
    public actions are disallowed for blocked, draft-only and sensitive IP routes.
    """

    normalized = signal.normalized()
    packet = build_review_packet(normalized, generated_at=generated_at)
    w = (weights or OAKBenchWeights()).normalized()
    score = (
        w.evidence * _norm05(packet.scores.evidence)
        + w.testability * normalized.testability_score
        + w.revenue * normalized.revenue_score
        + w.novelty * normalized.novelty_score
        + w.risk_control * (1.0 - normalized.disclosure_risk)
        + w.readiness * _norm05(packet.scores.readiness)
    )
    score = round(_clamp01(score), 4)
    band = _priority_band(packet, score)
    ip_review_required = packet.handoff.ip_class in {IPClass.PATENT_REVIEW, IPClass.TRADE_SECRET}
    public_action_allowed = packet.handoff.oak_status == OAKStatus.SAFE_TO_EXPLORE and not ip_review_required

    m_minus = list(packet.m_minus)
    if not public_action_allowed:
        m_minus.append("Public automation must stay disabled until OAK/IP gate is cleared.")
    if band == "commercialize":
        m_minus.append("Commercialization score is a triage signal, not proof of market demand or revenue.")

    return OAKBenchResult(
        signal=normalized,
        review_packet=packet,
        action_score=score,
        priority_band=band,
        build_now=band in {"build", "commercialize"},
        commercialize_now=band == "commercialize" and public_action_allowed,
        ip_review_required=ip_review_required,
        public_action_allowed=public_action_allowed,
        github_actions=_github_actions(packet, band),
        m_minus=tuple(dict.fromkeys(m_minus)),
    )


def rank_signals(signals: list[Signal], *, weights: OAKBenchWeights | None = None) -> list[OAKBenchResult]:
    """Return signals ranked by OAKBench action score, highest first."""

    return sorted((run_oakbench(signal, weights=weights) for signal in signals), key=lambda r: r.action_score, reverse=True)
