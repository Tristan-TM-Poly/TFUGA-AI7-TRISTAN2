from __future__ import annotations

from typing import Iterable

from .campaign import plan_dependency_order
from .models import (
    ArtifactSpec,
    CampaignPlan,
    FindingSeverity,
    OAKFinding,
    RouteDecisionRecord,
)
from .snapshot import SnapshotBundle


_COMPLETE_SNAPSHOT = "all_owned_repositories_and_open_pull_requests_returned_by_paginated_api"


class CampaignOAKAuditor:
    """Non-compensatory campaign gates.

    A high score cannot compensate for a forbidden merge, missing rollback,
    public routing of private material, or cyclic dependency graph.
    """

    def audit(
        self,
        snapshot: SnapshotBundle,
        artifacts: Iterable[ArtifactSpec],
        routes: Iterable[RouteDecisionRecord],
        campaign: CampaignPlan,
    ) -> tuple[OAKFinding, ...]:
        artifacts = tuple(artifacts)
        routes = tuple(routes)
        repositories = {repository.full_name: repository for repository in snapshot.repositories}
        artifact_by_id = {artifact.artifact_id: artifact for artifact in artifacts}
        route_by_id = {route.artifact_id: route for route in routes}
        findings: list[OAKFinding] = []

        if not campaign.rollback_required:
            findings.append(
                OAKFinding(
                    code="ROLLBACK_REQUIRED",
                    severity=FindingSeverity.BLOCKER,
                    message="The campaign has no rollback contract.",
                    subject=campaign.campaign_id,
                    remediation="Require rollback before any branch or PR mutation.",
                )
            )
        if campaign.remote_mutations_authorized:
            findings.append(
                OAKFinding(
                    code="REMOTE_AUTHORITY_OUT_OF_SCOPE",
                    severity=FindingSeverity.BLOCKER,
                    message="R0.1 plans campaigns but must not carry remote mutation authority.",
                    subject=campaign.campaign_id,
                    remediation="Set remote_mutations_authorized=false.",
                )
            )
        try:
            plan_dependency_order(campaign)
        except ValueError as error:
            findings.append(
                OAKFinding(
                    code="PR_DEPENDENCY_GRAPH_INVALID",
                    severity=FindingSeverity.BLOCKER,
                    message=str(error),
                    subject=campaign.campaign_id,
                    remediation="Remove cycles and unresolved PR-plan dependencies.",
                )
            )

        branch_keys: set[tuple[str, str]] = set()
        for plan in campaign.pull_requests:
            branch_key = (plan.repository, plan.head_branch)
            if branch_key in branch_keys:
                findings.append(
                    OAKFinding(
                        code="DUPLICATE_HEAD_BRANCH",
                        severity=FindingSeverity.BLOCKER,
                        message="Two PR plans target the same repository and head branch.",
                        subject=plan.plan_id,
                        remediation="Assign a unique campaign branch.",
                    )
                )
            branch_keys.add(branch_key)
            if not plan.draft or not plan.human_gate_required or plan.remote_action_planned:
                findings.append(
                    OAKFinding(
                        code="HUMAN_GATE_VIOLATION",
                        severity=FindingSeverity.BLOCKER,
                        message="Every generated PR must remain draft, review-gated and non-executed.",
                        subject=plan.plan_id,
                        remediation="Restore draft=true, human_gate_required=true and remote_action_planned=false.",
                    )
                )
            if plan.repository not in repositories:
                findings.append(
                    OAKFinding(
                        code="UNKNOWN_ROUTE_REPOSITORY",
                        severity=FindingSeverity.BLOCKER,
                        message="A PR plan targets a repository absent from the source snapshot.",
                        subject=plan.plan_id,
                        remediation="Refresh the snapshot or reroute the plan.",
                    )
                )

        for artifact in artifacts:
            route = route_by_id.get(artifact.artifact_id)
            if route is None or route.repository is None:
                findings.append(
                    OAKFinding(
                        code="ARTIFACT_IN_BACKLOG",
                        severity=FindingSeverity.WARNING,
                        message="Artifact has no executable repository route and remains in backlog.",
                        subject=artifact.artifact_id,
                        remediation="Select an authorized repository or retain the backlog decision.",
                    )
                )
                continue
            repository = repositories.get(route.repository)
            if repository is None:
                continue
            if artifact.required_visibility == "private_required" and repository.visibility != "private":
                findings.append(
                    OAKFinding(
                        code="PRIVATE_ARTIFACT_PUBLIC_ROUTE",
                        severity=FindingSeverity.BLOCKER,
                        message="A private-required artifact is routed to a non-private repository.",
                        subject=artifact.artifact_id,
                        remediation="Route to a private repository or redact through IPGate.",
                    )
                )
            if not repository.writable:
                findings.append(
                    OAKFinding(
                        code="ROUTE_WITHOUT_WRITE_PERMISSION",
                        severity=FindingSeverity.BLOCKER,
                        message="The observed snapshot does not include write permission for the route.",
                        subject=artifact.artifact_id,
                        remediation="Request permission or route elsewhere.",
                    )
                )
            unresolved = [dependency for dependency in artifact.dependencies if dependency not in artifact_by_id]
            if unresolved:
                findings.append(
                    OAKFinding(
                        code="UNRESOLVED_ARTIFACT_DEPENDENCY",
                        severity=FindingSeverity.BLOCKER,
                        message=f"Unknown artifact dependencies: {unresolved}",
                        subject=artifact.artifact_id,
                        remediation="Add or remove the missing artifact contracts.",
                    )
                )

        if snapshot.completeness != _COMPLETE_SNAPSHOT:
            findings.append(
                OAKFinding(
                    code="SNAPSHOT_COMPLETENESS_DECLARATIVE",
                    severity=FindingSeverity.WARNING,
                    message="Snapshot does not certify a complete paginated owner/open-PR scan.",
                    subject=snapshot.digest,
                    remediation="Run the read-only live scanner before organization-wide routing.",
                )
            )
        if not findings:
            findings.append(
                OAKFinding(
                    code="CAMPAIGN_STRUCTURALLY_READY",
                    severity=FindingSeverity.INFO,
                    message="The supplied dry-run campaign satisfies the structural R0.1 gates.",
                    subject=campaign.campaign_id,
                    remediation="Human review, implementation, tests and exact-head CI are still required.",
                )
            )
        return tuple(findings)


def oak_report(findings: Iterable[OAKFinding]) -> dict[str, object]:
    findings = tuple(findings)
    blockers = sum(item.severity is FindingSeverity.BLOCKER for item in findings)
    warnings = sum(item.severity is FindingSeverity.WARNING for item in findings)
    return {
        "status": "blocked" if blockers else ("review_required" if warnings else "structurally_ready"),
        "blocker_count": blockers,
        "warning_count": warnings,
        "finding_count": len(findings),
        "findings": [item.to_dict() for item in findings],
        "claims": {
            "remote_mutation_performed": False,
            "merge_authorized": False,
            "scientific_validation_claimed": False,
            "product_market_fit_claimed": False,
        },
    }
