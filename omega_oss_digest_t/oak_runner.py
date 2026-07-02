from __future__ import annotations

from dataclasses import dataclass

from .license_gate import LicenseDecision, classify_license
from .scorer import DigestScore, score_band


@dataclass(frozen=True)
class OakDecision:
    status: str
    score: float
    license_status: str
    required_actions: tuple[str, ...]


def oak_decision(license_id: str | None, score: DigestScore | None = None) -> OakDecision:
    license_decision: LicenseDecision = classify_license(license_id)
    score = score or DigestScore()
    value = score.value()
    band = score_band(value)
    actions: list[str] = []

    if license_decision.oak_status.startswith("OAK_RED"):
        return OakDecision(
            "OAK_RED_BLOCKED",
            value,
            license_decision.oak_status,
            (
                "Do not integrate direct code.",
                "Extract high-level idea only or obtain explicit permission.",
                "Record M⁻ license risk.",
            ),
        )

    if "YELLOW" in license_decision.oak_status or "RED_OR" in license_decision.oak_status:
        actions.append("Manual legal/architecture review before direct integration.")
    if score.security < 0.7:
        actions.append("Run dependency/SBOM/vulnerability scan before use.")
    if score.tests < 0.6:
        actions.append("Add OAKBench tests before canonization.")
    if score.risk > 0.5:
        actions.append("Create M⁻ risk entry and prefer sandbox/rewrite.")

    status = band
    if actions and status.startswith("OAK_GREEN"):
        status = "OAK_YELLOW_CONDITIONAL"

    return OakDecision(
        status,
        value,
        license_decision.oak_status,
        tuple(actions or ["Preserve provenance, attribution, tests, and license notices."]),
    )
