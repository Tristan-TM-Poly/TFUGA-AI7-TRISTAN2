from __future__ import annotations

from collections import defaultdict
import re
from typing import Iterable

from .graph import topological_order
from .models import (
    ArtifactSpec,
    CampaignPlan,
    CampaignState,
    IntentContract,
    PullRequestPlan,
    RouteDecisionRecord,
    sha256_digest,
)


def _branch_token(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return token[:48] or "campaign"


class PRCampaignPlanner:
    """Group routed artifacts into dependency-aware draft PR plans."""

    def plan(
        self,
        intent: IntentContract,
        artifacts: Iterable[ArtifactSpec],
        routes: Iterable[RouteDecisionRecord],
        *,
        default_branches: dict[str, str] | None = None,
    ) -> CampaignPlan:
        artifacts = tuple(artifacts)
        artifact_by_id = {artifact.artifact_id: artifact for artifact in artifacts}
        route_by_id = {route.artifact_id: route for route in routes}
        grouped: dict[str, list[ArtifactSpec]] = defaultdict(list)
        for artifact in artifacts:
            route = route_by_id.get(artifact.artifact_id)
            if route is not None and route.repository is not None:
                grouped[route.repository].append(artifact)

        repository_plan_ids: dict[str, str] = {}
        digest = sha256_digest({"intent": intent.to_dict(), "routes": [r.to_dict() for r in routes]})[:12]
        for index, repository in enumerate(sorted(grouped), start=1):
            repository_plan_ids[repository] = f"pr-plan.{digest}.{index:03d}"

        plans: list[PullRequestPlan] = []
        for repository in sorted(grouped):
            repository_artifacts = sorted(grouped[repository], key=lambda item: item.artifact_id)
            plan_dependencies: set[str] = set()
            repository_artifact_ids = {item.artifact_id for item in repository_artifacts}
            for artifact in repository_artifacts:
                for dependency in artifact.dependencies:
                    if dependency in repository_artifact_ids:
                        continue
                    dependency_route = route_by_id.get(dependency)
                    if dependency_route and dependency_route.repository in repository_plan_ids:
                        plan_dependencies.add(repository_plan_ids[dependency_route.repository])
            plan_id = repository_plan_ids[repository]
            branch = f"feat/mycelium/{_branch_token(intent.root_creation)}/{digest}-{plan_id.rsplit('.', 1)[-1]}"
            paths = tuple(sorted({artifact.suggested_path for artifact in repository_artifacts}))
            checks = ["python_compile", "focused_tests", "oak_campaign_audit"]
            if any(artifact.kind == "benchmark" for artifact in repository_artifacts):
                checks.append("baseline_benchmark")
            if any(artifact.kind == "ip_report" for artifact in repository_artifacts):
                checks.append("ip_gate")
            base_branch = (default_branches or {}).get(repository, "main")
            plans.append(
                PullRequestPlan(
                    plan_id=plan_id,
                    repository=repository,
                    base_branch=base_branch,
                    head_branch=branch,
                    role=f"Materialize {intent.root_creation} artifacts in {repository}",
                    artifact_ids=tuple(item.artifact_id for item in repository_artifacts),
                    depends_on=tuple(sorted(plan_dependencies)),
                    hypothesis=(
                        f"The routed artifacts improve the executable and evidentiary state of "
                        f"{intent.root_creation} without exceeding their declared OAK status."
                    ),
                    expected_checks=tuple(checks),
                    allowed_paths=paths,
                    draft=True,
                    human_gate_required=True,
                    remote_action_planned=False,
                )
            )

        dependency_map = {plan.plan_id: plan.depends_on for plan in plans}
        ordered_ids = topological_order((plan.plan_id for plan in plans), dependency_map)
        plan_by_id = {plan.plan_id: plan for plan in plans}
        ordered_plans = tuple(plan_by_id[plan_id] for plan_id in ordered_ids)
        campaign_id = f"campaign.{_branch_token(intent.root_creation)}.{digest}"
        return CampaignPlan(
            campaign_id=campaign_id,
            intent_id=intent.intent_id,
            creation_id=intent.root_creation.replace("-", "_"),
            objective=intent.objective,
            state=CampaignState.PLANNED,
            pull_requests=ordered_plans,
            rollback_required=True,
            remote_mutations_authorized=False,
            permanent_pr_cap=None,
            metadata={
                "backlog_artifact_ids": sorted(
                    artifact.artifact_id
                    for artifact in artifacts
                    if route_by_id.get(artifact.artifact_id) is None
                    or route_by_id[artifact.artifact_id].repository is None
                ),
                "generated_branches_are_plans_only": True,
                "automatic_merge_forbidden": True,
            },
        )


def plan_dependency_order(campaign: CampaignPlan) -> tuple[str, ...]:
    return topological_order(
        (plan.plan_id for plan in campaign.pull_requests),
        {plan.plan_id: plan.depends_on for plan in campaign.pull_requests},
    )
