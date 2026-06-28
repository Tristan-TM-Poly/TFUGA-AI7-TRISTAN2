"""IP-OAK Gate for publication, patent, license, and open-source routing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple

from .zero_touch_oak import OAKCompileResult, compile_oak


class IPStatus(str, Enum):
    PUBLISH = "publish"
    PATENT_CANDIDATE = "patent_candidate"
    OPEN_SOURCE = "open_source"
    TRADE_SECRET = "trade_secret"
    LICENSE_CANDIDATE = "license_candidate"
    HOLD_FOR_EVIDENCE = "hold_for_evidence"


@dataclass(frozen=True)
class IPInput:
    result_name: str
    novelty_score: float
    utility_score: float
    market_score: float
    feasibility_score: float
    disclosure_risk: float
    cost_score: float = 0.3
    time_score: float = 0.3
    reproducibility_score: float = 0.5


@dataclass(frozen=True)
class IPGatePacket:
    result_name: str
    ip_status: IPStatus
    value_score: float
    disclosure_risk: float
    commercial_value: float
    rationale: Tuple[str, ...]
    oak: OAKCompileResult
    next_action: str


def classify_ip(ip: IPInput, evidence_count: int = 1) -> IPGatePacket:
    value = (
        ip.novelty_score
        + ip.utility_score
        + ip.market_score
        + ip.feasibility_score
        - ip.cost_score
        - ip.disclosure_risk
        - ip.time_score
    ) / 4.0
    value_score = round(max(0.0, min(1.0, value)), 4)
    commercial_value = round((ip.utility_score + ip.market_score + ip.feasibility_score) / 3.0, 4)
    rationale = []

    if ip.disclosure_risk >= 0.70 and ip.novelty_score >= 0.60:
        status = IPStatus.TRADE_SECRET
        rationale.append("high_disclosure_risk_and_novelty")
    elif ip.novelty_score >= 0.72 and commercial_value >= 0.62:
        status = IPStatus.PATENT_CANDIDATE
        rationale.append("high_novelty_and_commercial_value")
    elif commercial_value >= 0.70 and ip.disclosure_risk < 0.55:
        status = IPStatus.LICENSE_CANDIDATE
        rationale.append("partner_or_license_route")
    elif ip.reproducibility_score >= 0.70 and ip.market_score < 0.45:
        status = IPStatus.OPEN_SOURCE
        rationale.append("high_reproducibility_lower_market_pressure")
    elif evidence_count == 0:
        status = IPStatus.HOLD_FOR_EVIDENCE
        rationale.append("evidence_missing")
    else:
        status = IPStatus.PUBLISH
        rationale.append("publish_route_with_oak_limits")

    benefits: Dict[str, float] = {
        "novelty": ip.novelty_score,
        "utility": ip.utility_score,
        "market": ip.market_score,
        "feasibility": ip.feasibility_score,
        "reproducibility": ip.reproducibility_score,
    }
    risks: Dict[str, float] = {
        "confidentiality": ip.disclosure_risk,
        "cost": ip.cost_score,
        "complexity": ip.time_score,
        "overclaim": max(0.0, 0.60 - ip.reproducibility_score),
    }
    oak = compile_oak(
        ip.result_name,
        benefits,
        risks,
        evidence_count=evidence_count,
        external_action=status in {IPStatus.PATENT_CANDIDATE, IPStatus.LICENSE_CANDIDATE, IPStatus.TRADE_SECRET},
    )
    return IPGatePacket(
        result_name=ip.result_name,
        ip_status=status,
        value_score=value_score,
        disclosure_risk=round(max(0.0, min(1.0, ip.disclosure_risk)), 4),
        commercial_value=commercial_value,
        rationale=tuple(rationale),
        oak=oak,
        next_action="generate_ip_summary_and_prior_art_search_plan",
    )
