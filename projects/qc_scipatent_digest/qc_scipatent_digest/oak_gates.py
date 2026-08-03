from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from .models import Opportunity


@dataclass
class GateResult:
    name: str
    status: str
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def assess_opportunity(opportunity: Opportunity) -> list[GateResult]:
    reasons = list(opportunity.cautions)
    source_status = "pass_with_caution" if opportunity.release_class == "internal_review" else "review_required"
    ip_status = "review_required" if opportunity.release_class in {"internal_review", "unknown"} else "blocked"
    science_status = "pass_with_caution" if opportunity.bridge_topics else "review_required"
    return [
        GateResult("OAK-Source", source_status, reasons or ["synthetic fixtures only"]),
        GateResult("OAK-IP", ip_status, ["no legal-status conclusion", "no freedom-to-operate conclusion"]),
        GateResult("OAK-Science", science_status, ["bridge is hypothesis only", "requires source verification"]),
    ]
