"""Non-compensatory OAK gates and conservative certification."""
from __future__ import annotations
from .models import Authority, Certification, GateDecision, InteractionEstimate, stable_id

REQUIRED=("typed_interfaces","declared_losses","provenance","baseline","simplest_baseline","metric","falsifier","uncertainty","rollback","budget","owner","logging")


def hard_gate(candidate: dict) -> GateDecision:
    passed=[]; failed=[]; warnings=[]
    for item in REQUIRED:
        if candidate.get(item): passed.append(item)
        else: failed.append(item)
    if candidate.get("sensitive") and not candidate.get("human_gate"): failed.append("sensitive_human_gate")
    if candidate.get("recursive"):
        for item in ("finite_budget","stop_gate","recursive_governor"):
            if candidate.get(item): passed.append(item)
            else: failed.append(item)
    if candidate.get("heuristic_only",True): warnings.append("Heuristic score cannot certify an interaction.")
    status="BLOCKED" if failed else "ELIGIBLE_FOR_EXPERIMENT"
    return GateDecision(candidate.get("id",stable_id("CAND",candidate)),status,tuple(sorted(set(passed))),tuple(sorted(set(failed))),tuple(warnings))


def classify(estimate: InteractionEstimate, *, threshold: float=0.0, causal: bool=False, replicated: bool=False, external: bool=False) -> Certification:
    if estimate.interval_high<=threshold: return Certification.N4_GROSS
    if estimate.interval_low<=threshold: return Certification.N4_GROSS
    level=Certification.N5_PROPER
    if causal: level=Certification.N6_CAUSAL
    if causal and replicated: level=Certification.N7_ROBUST
    if causal and replicated and external: level=Certification.N9_EXTERNAL
    return level


def promotion_flags(certification: Certification) -> dict:
    return {"certification":certification.value,"maximum_authority":Authority.REVIEW_ONLY.value,
            "human_review_required":True,"automatic_merge_allowed":False,"automatic_publication_allowed":False,
            "scientific_proof_claimed":False,"product_market_fit_claimed":False}
