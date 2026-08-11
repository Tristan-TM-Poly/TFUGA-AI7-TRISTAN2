from __future__ import annotations

from dataclasses import asdict

from .model import (
    BarrierClass,
    CertificateFamily,
    FrontierDecision,
    MomentTensorSpec,
    ResearchBundle,
    ResearchRoute,
    stable_cell_id,
)


def effective_rank_diagnostic(trace: float, frobenius_sq: float) -> float:
    """Return (tr A)^2 / ||A||_F^2 when the inputs are admissible.

    This quantity is a generic spectral concentration diagnostic. It becomes
    a rank lower bound only under the mathematical hypotheses of the relevant
    rank-trace inequality; this function does not assert those hypotheses for
    a zeta/Weil operator.
    """
    if frobenius_sq <= 0:
        raise ValueError("frobenius_sq must be positive")
    return (trace * trace) / frobenius_sq


def classify_frontier(
    family: CertificateFamily,
    target_bound: float,
    *,
    moment_spec: MomentTensorSpec | None = None,
) -> FrontierDecision:
    family.validate()
    if not (0.0 <= target_bound <= 1.0):
        raise ValueError("target_bound must be in [0, 1]")

    gap_current = max(0.0, target_bound - family.current_bound)
    beyond = max(0.0, target_bound - family.method_ceiling)
    if target_bound <= family.method_ceiling:
        return FrontierDecision(
            target_bound=target_bound,
            attainable_inside_declared_family=True,
            barrier=BarrierClass.WINDOW_OPTIMIZATION,
            gap_from_current=gap_current,
            gap_beyond_ceiling=0.0,
            required_support_radius_hint=family.fourier_support_radius,
            claim_boundary=(
                "Target is numerically below the declared family ceiling. "
                "This does not establish existence of a window attaining it."
            ),
        )

    support_hint = None
    if moment_spec is not None:
        support_hint = max(
            family.fourier_support_radius,
            moment_spec.conservative_support_radius,
        )
    return FrontierDecision(
        target_bound=target_bound,
        attainable_inside_declared_family=False,
        barrier=BarrierClass.NEW_ARITHMETIC_INFORMATION,
        gap_from_current=gap_current,
        gap_beyond_ceiling=beyond,
        required_support_radius_hint=support_hint,
        claim_boundary=(
            "Target exceeds the declared method ceiling. A larger search over "
            "the same bounded information class must not be advertised as a "
            "route around the barrier without a new theorem or new arithmetic input."
        ),
    )


def rank_routes(routes: list[ResearchRoute]) -> list[ResearchRoute]:
    for route in routes:
        route.validate()
    return sorted(routes, key=lambda route: (-route.voi_score, route.route_id))


def compile_problem_cells(bundle: ResearchBundle) -> list[dict]:
    """Compile a zeta research bundle into R0.10-compatible research cells."""
    bundle.family.validate()
    decision = classify_frontier(bundle.family, bundle.target_bound, moment_spec=bundle.moment_spec)
    cells: list[dict] = []

    decision_payload = {
        **asdict(decision),
        "barrier": decision.barrier.value,
        "family_id": bundle.family.family_id,
        "bundle_digest": bundle.digest,
        "proof_claimed": False,
        "rh_solved_claimed": False,
    }
    cells.append(
        {
            "cell_id": stable_cell_id((bundle.family.family_id, "frontier", f"{bundle.target_bound:.12g}")),
            "problem_id": "riemann-hypothesis",
            "target_id": "spectral-certificate-frontier",
            "front": "barrier",
            "method": "omega-zeta-cert-frontier",
            "priority": 1000,
            "source_ref": "omega_zeta_cert_t:frontier",
            "payload": decision_payload,
        }
    )

    if bundle.moment_spec is not None:
        spec = bundle.moment_spec
        spec.validate()
        cells.append(
            {
                "cell_id": stable_cell_id((bundle.family.family_id, "moments", str(spec.max_order), str(spec.window_count))),
                "problem_id": "riemann-hypothesis",
                "target_id": "spectral-moment-lift",
                "front": "representation",
                "method": "omega-zeta-cert-moment-tensor",
                "priority": 900,
                "source_ref": "omega_zeta_cert_t:moment_spec",
                "payload": {
                    "max_order": spec.max_order,
                    "window_count": spec.window_count,
                    "include_cross_moments": spec.include_cross_moments,
                    "observable_count": spec.observable_count,
                    "conservative_support_radius": spec.conservative_support_radius,
                    "support_semantics": "bookkeeping_upper_bound_not_zeta_theorem",
                    "proof_claimed": False,
                },
            }
        )

    for rank, route in enumerate(rank_routes(bundle.routes), start=1):
        cells.append(
            {
                "cell_id": stable_cell_id((bundle.family.family_id, "route", route.route_id)),
                "problem_id": "riemann-hypothesis",
                "target_id": route.route_id,
                "front": "research-route",
                "method": "bayes-tristan-voi",
                "priority": 800 - rank,
                "source_ref": "omega_zeta_cert_t:route",
                "payload": {
                    **asdict(route),
                    "barrier_target": route.barrier_target.value,
                    "voi_score": route.voi_score,
                    "score_semantics": "heuristic_routing_not_truth_probability",
                    "proof_claimed": False,
                },
            }
        )

    for item in bundle.mminus:
        cells.append(
            {
                "cell_id": stable_cell_id((bundle.family.family_id, "mminus", item.record_id)),
                "problem_id": "riemann-hypothesis",
                "target_id": item.record_id,
                "front": "m-minus",
                "method": "negative-memory",
                "priority": 950,
                "source_ref": "omega_zeta_cert_t:mminus",
                "payload": {
                    "record_id": item.record_id,
                    "barrier": item.barrier.value,
                    "summary": item.summary,
                    "falsifier": item.falsifier,
                    "source_refs": list(item.source_refs),
                    "negative_evidence_retained": True,
                    "proof_claimed": False,
                },
            }
        )

    return cells


def minimal_order_for_observable_budget(window_count: int, desired_observables: int) -> int:
    if window_count < 1 or desired_observables < 1:
        raise ValueError("window_count and desired_observables must be positive")
    order = 1
    while MomentTensorSpec(order, window_count, 1.0, True).observable_count < desired_observables:
        order += 1
        if order > 64:
            raise ValueError("observable budget exceeds bounded planner limit")
    return order
