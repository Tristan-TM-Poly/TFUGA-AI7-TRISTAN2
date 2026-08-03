"""Canon Mutation Engine for Tristan CanonOS.

Creates conservative mutation decisions for canon changes. It does not merge,
deploy, publish, delete, or execute external actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MutationType(StrEnum):
    ADD = "add"
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"
    DEPRECATE = "deprecate"
    SPLIT = "split"
    MERGE = "merge"
    QUARANTINE = "quarantine"
    LINK = "link"
    UNLINK = "unlink"
    ARTIFACT_COMPILE = "artifact_compile"


class MutationDecision(StrEnum):
    SANDBOX = "sandbox"
    DRAFT_PR = "draft_pr"
    REVIEW_REQUIRED = "review_required"
    QUARANTINE = "quarantine"
    REJECT = "reject"


@dataclass(frozen=True)
class CanonMutationPlan:
    mutation_type: MutationType
    target_nodes: tuple[str, ...]
    decision: MutationDecision
    required_gates: tuple[str, ...]
    safe_next_action: str


def plan_canon_mutation(
    mutation_type: MutationType,
    target_nodes: tuple[str, ...],
    *,
    high_stakes: bool = False,
    public_side_effect: bool = False,
    missing_tests: bool = False,
    privacy_or_ip_unclear: bool = False,
) -> CanonMutationPlan:
    gates: list[str] = ["oak"]

    if not target_nodes:
        return CanonMutationPlan(
            mutation_type,
            target_nodes,
            MutationDecision.REJECT,
            tuple(gates),
            "Reject: mutation has no target nodes.",
        )

    if high_stakes:
        gates.extend(["human_validation", "qualified_review"])
        return CanonMutationPlan(
            mutation_type,
            target_nodes,
            MutationDecision.QUARANTINE,
            tuple(gates),
            "Quarantine high-stakes mutation; analysis only until qualified review.",
        )

    if privacy_or_ip_unclear:
        gates.extend(["privacy", "ip"])
        return CanonMutationPlan(
            mutation_type,
            target_nodes,
            MutationDecision.REVIEW_REQUIRED,
            tuple(gates),
            "Run Privacy/IP gates before branch or PR.",
        )

    if public_side_effect:
        gates.append("explicit_validation")
        return CanonMutationPlan(
            mutation_type,
            target_nodes,
            MutationDecision.REVIEW_REQUIRED,
            tuple(gates),
            "Prepare draft only; public side effect requires explicit validation.",
        )

    if missing_tests and mutation_type in {MutationType.UPGRADE, MutationType.MERGE, MutationType.ARTIFACT_COMPILE}:
        gates.append("tests")
        return CanonMutationPlan(
            mutation_type,
            target_nodes,
            MutationDecision.SANDBOX,
            tuple(gates),
            "Add tests in sandbox before upgrade/merge/artifact compilation.",
        )

    return CanonMutationPlan(
        mutation_type,
        target_nodes,
        MutationDecision.DRAFT_PR,
        tuple(gates),
        "Create reversible branch or draft PR; do not auto-merge.",
    )
