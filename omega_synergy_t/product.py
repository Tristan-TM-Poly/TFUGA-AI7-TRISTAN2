"""Conservative product-hypothesis compiler."""
from __future__ import annotations

from .models import ProductHypothesis, SynergyCandidate, stable_id


DOMAIN_USERS = {
    "software": "R&D and open-source engineering teams",
    "proof": "teams that need auditable technical claims",
    "knowledge": "researchers processing complex technical corpora",
    "business": "technical founders and innovation teams",
    "physics": "scientific and engineering laboratories",
    "materials": "materials and manufacturing R&D teams",
    "governance": "public-sector and regulated-technology teams",
}


def compile_product_hypothesis(candidate: SynergyCandidate, domains: list[str] | None = None) -> ProductHypothesis:
    domains = domains or []
    user = next((DOMAIN_USERS[domain] for domain in domains if domain in DOMAIN_USERS), "technical research teams")
    readiness = max(0.0, min(1.0, 0.3 * candidate.tensor.evidence + 0.25 * candidate.tensor.closure_gain + 0.2 * candidate.tensor.reuse + 0.15 * candidate.tensor.product_value - 0.2 * candidate.tensor.risk + 0.2))
    blockers: list[str] = []
    if candidate.tensor.evidence < 0.45:
        blockers.append("insufficient_measured_evidence")
    if candidate.tensor.causal_readiness < 0.45:
        blockers.append("causal_experiment_required")
    if candidate.tensor.risk > 0.45:
        blockers.append("risk_review_required")
    if not candidate.matched_needs:
        blockers.append("customer_problem_not_yet_grounded")
    return ProductHypothesis(
        id=stable_id("PRD", candidate.id, user),
        candidate_id=candidate.id,
        user=user,
        problem="Fragmented capabilities, evidence and workflows prevent research assets from closing a complete idea-to-proof-to-usage loop.",
        offer=f"A review-first integration and audit workflow for {' × '.join(candidate.systems)}.",
        proof_required=[
            "measured technical gain against the simplest baseline",
            "reduced human review time or error rate",
            "at least one real user workflow",
            "license, privacy and security review",
        ],
        monetization=["paid repository audit", "service-led pilot", "subscription workflow", "enterprise evidence integration"],
        readiness=round(readiness, 6),
        blockers=blockers,
    )
