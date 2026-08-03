"""Autonomy Downgrade Loop for Ω-AIT-NO-HUMAN-BOTTLENECK-T.

Never stop: downgrade the mode and produce the next safe artifact. This module
plans only; it does not execute external actions or bypass review.
"""

from __future__ import annotations

from dataclasses import dataclass

from tools.continuation_mode_router import ContinuationDecision, route_continuation


@dataclass(frozen=True)
class DowngradePacket:
    intent: str
    decision: ContinuationDecision
    missing_evidence: tuple[str, ...]
    tests_to_add: tuple[str, ...]
    gates: tuple[str, ...]
    next_safe_action: str


def build_downgrade_packet(
    *,
    intent: str,
    reversible: bool = True,
    private: bool = True,
    testable: bool = True,
    review_domain: bool = False,
    public_effect: bool = False,
    irreversible: bool = False,
) -> DowngradePacket:
    decision = route_continuation(
        reversible=reversible,
        private=private,
        testable=testable,
        review_domain=review_domain,
        public_effect=public_effect,
        irreversible=irreversible,
    )

    missing: list[str] = []
    tests: list[str] = []
    gates: list[str] = ["oak"]

    if not reversible:
        missing.append("rollback_or_compensation")
        gates.append("rollback")
    if not private:
        gates.append("privacy_or_release_review")
    if not testable:
        missing.append("test_plan")
        tests.append("minimal_safety_or_regression_test")
    if review_domain:
        gates.append("qualified_review")
    if public_effect:
        gates.append("explicit_validation")
    if irreversible:
        gates.append("hold_direct_action")

    return DowngradePacket(
        intent=intent,
        decision=decision,
        missing_evidence=tuple(missing),
        tests_to_add=tuple(tests),
        gates=tuple(dict.fromkeys(gates)),
        next_safe_action=decision.next_safe_action,
    )
