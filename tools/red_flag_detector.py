"""Conservative medical red-flag detector for OAK safety routing.

This module is not a diagnostic tool and does not provide treatment advice. It
only detects language that should be routed toward poison control, emergency
services, physicians, pharmacists, or other qualified human care.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class RiskLevel(str, Enum):
    EDUCATIONAL = "educational_only"
    CLINICIAN = "clinician_or_pharmacist"
    POISON_CONTROL = "poison_control"
    EMERGENCY = "emergency_services"
    REFUSE_OPTIMIZATION = "refuse_optimization"


RED_FLAG_TERMS = {
    "chest pain",
    "severe palpitations",
    "fainting",
    "collapse",
    "difficulty breathing",
    "shortness of breath",
    "cannot breathe",
    "blue lips",
    "seizure",
    "convulsion",
    "loss of consciousness",
    "cannot be awakened",
    "can't be awakened",
    "severe confusion",
    "hallucination",
    "hallucinations",
    "high fever",
    "hyperthermia",
    "rigid muscles",
    "severe tremor",
    "uncontrollable agitation",
    "mixed ingestion",
    "unknown ingestion",
    "child exposure",
}

POISON_CONTROL_TERMS = {
    "overdose",
    "possible overdose",
    "surdose",
    "too much",
    "took too much",
    "wrong dose",
    "medication error",
    "double dose",
    "accidental dose",
}

OPTIMIZATION_TERMS = {
    "optimize",
    "best dose",
    "max dose",
    "maximum dose",
    "potentiate",
    "make it stronger",
    "make it hit harder",
    "tolerance strategy",
    "stack with",
    "combine with caffeine",
}


@dataclass(frozen=True)
class RedFlagResult:
    risk_level: RiskLevel
    hits: tuple[str, ...]
    reason: str
    safe_action: str


def find_terms(text: str, terms: Iterable[str]) -> tuple[str, ...]:
    normalized = " ".join(text.lower().split())
    return tuple(term for term in terms if term in normalized)


def detect_red_flags(text: str, *, real_exposure: bool | None = None) -> RedFlagResult:
    """Return a conservative OAK safety routing decision.

    Parameters
    ----------
    text:
        User text.
    real_exposure:
        Optional explicit context. ``True`` means a substance was actually taken;
        ``False`` means theoretical/no exposure; ``None`` means unknown.
    """

    red_hits = find_terms(text, RED_FLAG_TERMS)
    poison_hits = find_terms(text, POISON_CONTROL_TERMS)
    opt_hits = find_terms(text, OPTIMIZATION_TERMS)

    if red_hits:
        return RedFlagResult(
            risk_level=RiskLevel.EMERGENCY,
            hits=red_hits,
            reason="Emergency red-flag terms detected.",
            safe_action="Contact emergency services now. Do not drive. Do not take additional substances.",
        )

    if real_exposure is True or poison_hits:
        return RedFlagResult(
            risk_level=RiskLevel.POISON_CONTROL,
            hits=poison_hits,
            reason="Possible overdose, medication error, or real exposure detected.",
            safe_action="Contact poison control, a pharmacist, a prescriber, or emergency services depending on symptoms.",
        )

    if opt_hits:
        return RedFlagResult(
            risk_level=RiskLevel.REFUSE_OPTIMIZATION,
            hits=opt_hits,
            reason="Optimization or potentiation language detected.",
            safe_action="Refuse optimization and redirect to mechanism, risk, and qualified medical advice.",
        )

    return RedFlagResult(
        risk_level=RiskLevel.EDUCATIONAL,
        hits=(),
        reason="No red-flag or optimization terms detected.",
        safe_action="Provide education only; no individualized dosing or medical clearance.",
    )
