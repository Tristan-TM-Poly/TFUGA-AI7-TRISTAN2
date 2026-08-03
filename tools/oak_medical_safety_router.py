"""OAK medical safety router.

Purpose
-------
Small, conservative routing helper for medical-risk language.

Hard boundary
-------------
This module is not medical advice, not a diagnostic system, not a dosing tool,
and not a substitute for poison control, emergency services, physicians, or
pharmacists. It is designed to prevent unsafe automation by routing possible
medical-risk prompts toward qualified human care.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class SafetyRoute(str, Enum):
    """Conservative output routes for medical-risk prompts."""

    EMERGENCY = "emergency_services"
    POISON_CONTROL = "poison_control"
    CLINICIAN = "physician_or_pharmacist"
    EDUCATIONAL_ONLY = "educational_only_no_dosing_optimization"
    REFUSE_OPTIMIZATION = "refuse_optimization_and_redirect_to_safety"


@dataclass(frozen=True)
class SafetyDecision:
    """Safety routing decision."""

    route: SafetyRoute
    reason: str
    red_flags: tuple[str, ...]
    response_frame: str


RED_FLAGS = {
    "chest pain",
    "palpitations",
    "fainting",
    "shortness of breath",
    "seizure",
    "convulsion",
    "loss of consciousness",
    "confusion",
    "hallucination",
    "hallucinations",
    "uncontrollable agitation",
    "high fever",
    "hyperthermia",
    "rigid muscles",
    "severe headache",
    "mixed ingestion",
    "unknown ingestion",
    "overdose",
    "too much",
}

OVERDOSE_TERMS = {
    "overdose",
    "surdose",
    "took too much",
    "too much",
    "double dose",
    "wrong dose",
    "accidental dose",
    "mixed ingestion",
    "unknown ingestion",
}

OPTIMIZATION_TERMS = {
    "optimize",
    "max dose",
    "best dose",
    "how much can i take",
    "tolerance strategy",
    "potentiate",
    "stronger effect",
    "make it hit harder",
    "stack",
}


def _hits(text: str, vocabulary: Iterable[str]) -> tuple[str, ...]:
    normalized = text.lower()
    return tuple(term for term in vocabulary if term in normalized)


def route_medical_safety_prompt(text: str, *, already_taken: bool | None = None) -> SafetyDecision:
    """Route medical-risk text using conservative OAK-safe rules.

    Parameters
    ----------
    text:
        User-provided text.
    already_taken:
        Optional explicit context. ``True`` means a substance was already taken;
        ``False`` means no real exposure; ``None`` means unknown.

    Returns
    -------
    SafetyDecision
        Conservative route and response frame.
    """

    red_flags = _hits(text, RED_FLAGS)
    overdose_hits = _hits(text, OVERDOSE_TERMS)
    optimization_hits = _hits(text, OPTIMIZATION_TERMS)

    if red_flags:
        return SafetyDecision(
            route=SafetyRoute.EMERGENCY,
            reason="Emergency red-flag language detected.",
            red_flags=red_flags,
            response_frame=(
                "This could be a medical emergency. Contact emergency services or poison control now. "
                "Do not drive, do not take more substances, and stay with another person if possible."
            ),
        )

    if already_taken is True or overdose_hits:
        return SafetyDecision(
            route=SafetyRoute.POISON_CONTROL,
            reason="Possible real exposure, overdose, or medication error detected.",
            red_flags=red_flags,
            response_frame=(
                "Because this may involve a real medication exposure or overdose, contact poison control, "
                "a pharmacist, a prescriber, or emergency services. I can provide general mechanism and safety framing, "
                "but not individualized medical triage or dosing."
            ),
        )

    if optimization_hits:
        return SafetyDecision(
            route=SafetyRoute.REFUSE_OPTIMIZATION,
            reason="Dosing or effect-optimization language detected.",
            red_flags=red_flags,
            response_frame=(
                "I cannot help optimize dose, tolerance, stacking, or stronger effects. I can explain risks, mechanisms, "
                "and safer questions to ask a clinician or pharmacist."
            ),
        )

    return SafetyDecision(
        route=SafetyRoute.EDUCATIONAL_ONLY,
        reason="No emergency or optimization terms detected; keep answer educational and non-dosing.",
        red_flags=red_flags,
        response_frame=(
            "I can explain general mechanisms and safety concepts, but this is not medical advice or a dosing recommendation. "
            "For personal medication decisions, use a physician, pharmacist, or poison control."
        ),
    )


if __name__ == "__main__":
    examples = [
        "I took too much stimulant and have chest pain",
        "In theory, explain stimulant pharmacology",
        "How do I optimize the strongest effect?",
    ]
    for example in examples:
        print(example)
        print(route_medical_safety_prompt(example))
        print("-")
