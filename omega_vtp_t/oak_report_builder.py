"""Unified OAK report builder for Ω-VTP-T++ productization.

This module turns scattered technical, invariant, residual, and financial
signals into a reusable decision report. It is intentionally small and JSON-like
so it can be consumed by docs, demos, dashboards, and future APIs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence, Tuple


@dataclass(frozen=True)
class OAKDecision:
    status: str
    reason: str
    confidence: float


@dataclass(frozen=True)
class OAKUnifiedReport:
    name: str
    model: Mapping[str, Any]
    residuals: Mapping[str, Any] = field(default_factory=dict)
    invariants: Mapping[str, Any] = field(default_factory=dict)
    performance: Mapping[str, Any] = field(default_factory=dict)
    finance: Mapping[str, Any] = field(default_factory=dict)
    mminus: Tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    decision: OAKDecision = field(default_factory=lambda: OAKDecision("research_only", "no decision data", 0.0))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _status_score(status: str) -> float:
    s = status.lower()
    if any(word in s for word in ("certified", "deploy")):
        return 1.0
    if any(word in s for word in ("checked", "pilot")):
        return 0.75
    if any(word in s for word in ("experimental", "research")):
        return 0.45
    if any(word in s for word in ("high", "fail", "violation", "m_minus", "no_go")):
        return 0.05
    return 0.35


def build_oak_decision(
    *,
    residual_status: str = "unknown",
    invariant_status: str = "unknown",
    finance_decision: str = "research_only",
    mminus_count: int = 0,
) -> OAKDecision:
    """Build a conservative OAK decision from status strings."""

    residual_score = _status_score(residual_status)
    invariant_score = _status_score(invariant_status)
    finance_score = _status_score(finance_decision)
    penalty = min(0.5, 0.1 * mminus_count)
    confidence = max(0.0, min(1.0, (residual_score + invariant_score + finance_score) / 3.0 - penalty))

    if mminus_count > 0 and confidence < 0.4:
        status = "no_go_m_minus"
        reason = "M-minus risk dominates the report"
    elif finance_decision == "deploy" and confidence >= 0.75:
        status = "deploy_candidate"
        reason = "technical and financial checks support deployment"
    elif finance_decision in {"deploy", "pilot"} and confidence >= 0.5:
        status = "pilot_candidate"
        reason = "checks support a controlled pilot"
    elif confidence >= 0.35:
        status = "research_only"
        reason = "evidence is promising but not ready for deployment"
    else:
        status = "no_go_m_minus"
        reason = "insufficient evidence or high risk"

    return OAKDecision(status=status, reason=reason, confidence=float(confidence))


def build_unified_oak_report(
    *,
    name: str,
    model: Mapping[str, Any],
    residuals: Mapping[str, Any] | None = None,
    invariants: Mapping[str, Any] | None = None,
    performance: Mapping[str, Any] | None = None,
    finance: Mapping[str, Any] | None = None,
    mminus: Sequence[Mapping[str, Any]] = (),
) -> OAKUnifiedReport:
    residual_map = dict(residuals or {})
    invariant_map = dict(invariants or {})
    finance_map = dict(finance or {})
    decision = build_oak_decision(
        residual_status=str(residual_map.get("oak_status", "unknown")),
        invariant_status=str(invariant_map.get("oak_status", "unknown")),
        finance_decision=str(finance_map.get("decision", "research_only")),
        mminus_count=len(tuple(mminus)),
    )
    return OAKUnifiedReport(
        name=name,
        model=dict(model),
        residuals=residual_map,
        invariants=invariant_map,
        performance=dict(performance or {}),
        finance=finance_map,
        mminus=tuple(dict(item) for item in mminus),
        decision=decision,
    )
