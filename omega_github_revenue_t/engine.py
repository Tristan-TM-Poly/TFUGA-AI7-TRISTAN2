from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import asdict
from math import prod
from typing import Any

from .models import (
    Artifact,
    DisclosureClass,
    Experiment,
    ExperimentDecision,
    OAKStatus,
    Offer,
    RevenuePath,
    SponsorTier,
)


_PUBLIC_DISCLOSURES = {
    DisclosureClass.OPEN_PUBLIC,
    DisclosureClass.PUBLIC_AFTER_REVIEW,
}

_STATUS_WEIGHT = {
    OAKStatus.SPECULATIVE: 0.10,
    OAKStatus.EXPLORATORY: 0.25,
    OAKStatus.CRYSTALLIZABLE: 0.50,
    OAKStatus.DEMONSTRATED: 0.80,
    OAKStatus.CANONICAL: 1.00,
    OAKStatus.ARCHIVED: 0.05,
}


def _geometric_mean(values: Iterable[float]) -> float:
    items = tuple(max(0.0, min(1.0, value)) for value in values)
    if not items:
        return 0.0
    return prod(max(item, 1e-9) for item in items) ** (1.0 / len(items))


def evidence_score(artifact: Artifact) -> float:
    artifact.validate()
    evidence = artifact.evidence
    test_score = min(evidence.tests / 20.0, 1.0)
    binary = (
        float(evidence.reproducible_demo),
        float(evidence.benchmark),
        float(evidence.external_reproduction),
        float(evidence.paying_user),
        float(evidence.limitations_documented),
    )
    return min(1.0, 0.30 * test_score + 0.70 * (sum(binary) / len(binary)))


def disclosure_gate(artifact: Artifact, *, review_approved: bool = False) -> tuple[bool, str]:
    artifact.validate()
    if artifact.disclosure not in _PUBLIC_DISCLOSURES:
        return False, f"blocked by disclosure class {artifact.disclosure.value}"
    if artifact.disclosure is DisclosureClass.PUBLIC_AFTER_REVIEW and not review_approved:
        return False, "explicit IP/privacy/OAK review is required"
    if artifact.safety_privacy_risk >= 0.75:
        return False, "safety/privacy risk is above the public-release threshold"
    if artifact.ip_legal_risk >= 0.75:
        return False, "IP/legal risk is above the public-release threshold"
    return True, "public-release gate passed"


def evaluate_artifact(artifact: Artifact, *, review_approved: bool = False) -> dict[str, Any]:
    artifact.validate()
    proof = evidence_score(artifact)
    positive = _geometric_mean(
        (
            proof,
            artifact.utility,
            artifact.reuse,
            artifact.discoverability,
            artifact.trust,
            artifact.conversion_clarity,
            _STATUS_WEIGHT[artifact.oak_status],
        )
    )
    risk = sum(
        (
            artifact.noise,
            artifact.maintenance_burden,
            artifact.ip_legal_risk,
            artifact.safety_privacy_risk,
        )
    ) / 4.0
    score = max(0.0, min(1.0, positive * (1.0 - 0.75 * risk)))
    public_ready, gate_reason = disclosure_gate(artifact, review_approved=review_approved)
    demonstrated = artifact.oak_status in {OAKStatus.DEMONSTRATED, OAKStatus.CANONICAL}
    offer_ready = (
        demonstrated
        and artifact.evidence.reproducible_demo
        and artifact.evidence.limitations_documented
        and artifact.utility >= 0.6
        and artifact.conversion_clarity >= 0.5
        and artifact.maintenance_burden <= 0.7
    )
    return {
        "artifact_id": artifact.artifact_id,
        "score": round(score, 6),
        "evidence_score": round(proof, 6),
        "public_ready": public_ready,
        "public_gate_reason": gate_reason,
        "offer_ready": offer_ready,
        "observed_revenue": artifact.evidence.paying_user,
        "next_action": artifact.next_action,
    }


def compile_offer(artifact: Artifact) -> Offer:
    assessment = evaluate_artifact(artifact)
    preferred = artifact.revenue_paths[0]
    sustainable = bool(assessment["offer_ready"] and artifact.maintenance_burden <= 0.6)
    if sustainable:
        rationale = "demonstrated utility, bounded scope, reproducible evidence, and acceptable maintenance"
    else:
        rationale = "retain as an experiment until evidence, scope, or maintenance sustainability improves"
    return Offer(
        offer_id=f"offer-{artifact.artifact_id.lower()}",
        artifact_id=artifact.artifact_id,
        title=f"{artifact.title}: bounded delivery",
        scope=(
            f"Apply {artifact.title} to one explicitly authorized target",
            "Produce an evidence-bearing report and prioritized next actions",
        ),
        deliverables=(
            "machine-readable assessment",
            "human-readable OAK report",
            "limitations and residual risks",
        ),
        exclusions=(
            "no guaranteed business, scientific, security, or legal outcome",
            "no inaccessible system inspection",
            "no unlimited custom work",
        ),
        revenue_path=preferred,
        sustainable=sustainable,
        rationale=rationale,
    )


def assess_sponsor_tier(
    tier: SponsorTier,
    *, hourly_cost_minor: int = 6000,
    delivery_fraction_limit: float = 0.50,
) -> dict[str, Any]:
    tier.validate()
    if hourly_cost_minor <= 0:
        raise ValueError("hourly_cost_minor must be positive")
    if not 0 < delivery_fraction_limit <= 1:
        raise ValueError("delivery_fraction_limit must be in (0, 1]")
    delivery_cost = round(tier.monthly_delivery_minutes * hourly_cost_minor / 60)
    sustainable = (
        not tier.unlimited_custom_work
        and delivery_cost <= round(tier.monthly_minor * delivery_fraction_limit)
    )
    reasons: list[str] = []
    if tier.unlimited_custom_work:
        reasons.append("unlimited custom work is forbidden")
    if delivery_cost > round(tier.monthly_minor * delivery_fraction_limit):
        reasons.append("estimated delivery cost exceeds the permitted revenue fraction")
    if not reasons:
        reasons.append("bounded benefits fit the configured maintenance budget")
    return {
        "name": tier.name,
        "sustainable": sustainable,
        "estimated_delivery_cost_minor": delivery_cost,
        "monthly_minor": tier.monthly_minor,
        "reasons": reasons,
    }


def decide_experiment(experiment: Experiment) -> ExperimentDecision:
    experiment.validate()
    if experiment.hard_failure:
        return ExperimentDecision.STOP
    if experiment.observed_sample < experiment.minimum_sample:
        return ExperimentDecision.CONTINUE
    if experiment.target_value == 0:
        return ExperimentDecision.SCALE if experiment.observed_value > 0 else ExperimentDecision.REVISE
    ratio = experiment.observed_value / experiment.target_value
    if ratio >= 1.25:
        return ExperimentDecision.SCALE
    if ratio >= 0.60:
        return ExperimentDecision.REVISE
    return ExperimentDecision.STOP


def allocate_capital(
    candidates: Iterable[tuple[Artifact, int]],
    *, available_minor: int,
) -> list[dict[str, Any]]:
    if available_minor < 0:
        raise ValueError("available_minor must be non-negative")
    ranked: list[tuple[float, Artifact, int]] = []
    for artifact, requested_minor in candidates:
        if requested_minor <= 0:
            raise ValueError("requested amounts must be positive")
        assessment = evaluate_artifact(artifact)
        leverage = assessment["score"] / requested_minor
        ranked.append((leverage, artifact, requested_minor))
    ranked.sort(key=lambda item: (item[0], item[1].artifact_id), reverse=True)

    remaining = available_minor
    allocations: list[dict[str, Any]] = []
    for leverage, artifact, requested_minor in ranked:
        granted = min(remaining, requested_minor)
        if granted <= 0:
            break
        allocations.append(
            {
                "artifact_id": artifact.artifact_id,
                "requested_minor": requested_minor,
                "granted_minor": granted,
                "evidence_weighted_leverage": round(leverage, 12),
            }
        )
        remaining -= granted
    return allocations


def artifact_from_mapping(payload: Mapping[str, Any]) -> Artifact:
    from .models import Evidence

    evidence_payload = payload.get("evidence", {})
    evidence = Evidence(**evidence_payload)
    return Artifact(
        artifact_id=str(payload["artifact_id"]),
        title=str(payload["title"]),
        problem=str(payload["problem"]),
        actor=str(payload["actor"]),
        oak_status=OAKStatus(payload["oak_status"]),
        disclosure=DisclosureClass(payload["disclosure"]),
        revenue_paths=tuple(RevenuePath(item) for item in payload["revenue_paths"]),
        evidence=evidence,
        utility=float(payload.get("utility", 0.0)),
        reuse=float(payload.get("reuse", 0.0)),
        discoverability=float(payload.get("discoverability", 0.0)),
        trust=float(payload.get("trust", 0.0)),
        conversion_clarity=float(payload.get("conversion_clarity", 0.0)),
        noise=float(payload.get("noise", 0.0)),
        maintenance_burden=float(payload.get("maintenance_burden", 0.0)),
        ip_legal_risk=float(payload.get("ip_legal_risk", 0.0)),
        safety_privacy_risk=float(payload.get("safety_privacy_risk", 0.0)),
        risks=tuple(str(item) for item in payload.get("risks", ())),
        next_action=str(payload.get("next_action", "")),
    )


def stream_frontier(
    records: Iterable[Mapping[str, Any]],
    *,
    minimum_score: float = 0.0,
    review_approved: bool = False,
) -> Iterator[dict[str, Any]]:
    """Evaluate a finite stream lazily, with no permanent item-count ceiling."""
    if not 0.0 <= minimum_score <= 1.0:
        raise ValueError("minimum_score must be between 0 and 1")
    for index, record in enumerate(records):
        artifact = artifact_from_mapping(record)
        assessment = evaluate_artifact(artifact, review_approved=review_approved)
        if assessment["score"] >= minimum_score:
            yield {
                "index": index,
                "artifact": artifact.to_dict(),
                "assessment": assessment,
                "offer": asdict(compile_offer(artifact)),
            }
