from __future__ import annotations

from dataclasses import dataclass

from .models import RecoveryPlan


@dataclass(frozen=True, slots=True)
class OAKReport:
    status: str
    scientific_status: str
    physical_execution_authorized: bool
    warnings: tuple[str, ...]
    next_experiment: str


def audit_plan(plan: RecoveryPlan) -> OAKReport:
    warnings: list[str] = []
    if plan.dry_run_only:
        warnings.append("plan_contains_routes_requiring_certified_or_professional_handling")
    if not plan.evaluations:
        warnings.append("empty_plan_has_no_demonstrated_utility")
    return OAKReport(status="D-MVP" if plan.evaluations else "E", scientific_status="decision_support_model_not_physical_law_or_lca_certification", physical_execution_authorized=False, warnings=tuple(warnings), next_experiment="benchmark coupled capacity, transport and uncertainty constraints against a transparent baseline dataset")
