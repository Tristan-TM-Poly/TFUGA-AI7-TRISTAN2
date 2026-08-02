"""Outcome and task-graph planning."""
from __future__ import annotations

from .models import CaseRecord, Intent, OutcomePlan, TaskSpec


BASE = (
    ("collect_context", (), ("case_graph",), ("required sources resolved",)),
    ("verify_identity_authority", ("collect_context",), ("identity_registry",), ("sender and recipient permissions checked",)),
    ("extract_requirements", ("collect_context",), ("intent_engine",), ("explicit and implicit requirements recorded",)),
)

INTENT_TASKS: dict[Intent, tuple[tuple[str, tuple[str, ...]], ...]] = {
    Intent.TECHNICAL_REPORT: (
        ("collect_project_data", ("extract_requirements",)),
        ("validate_data_provenance", ("collect_project_data",)),
        ("run_benchmarks", ("validate_data_provenance",)),
        ("generate_technical_report", ("run_benchmarks",)),
    ),
    Intent.BUG_REPORT: (
        ("reproduce_bug", ("extract_requirements",)),
        ("create_failing_test", ("reproduce_bug",)),
        ("prepare_patch", ("create_failing_test",)),
        ("run_tests", ("prepare_patch",)),
        ("prepare_github_delivery", ("run_tests",)),
    ),
    Intent.DOCUMENT_REQUEST: (("resolve_document", ("extract_requirements",)), ("prepare_document_package", ("resolve_document",))),
    Intent.SUPPORT_QUESTION: (("resolve_verified_answer", ("extract_requirements",)),),
    Intent.STATUS_REQUEST: (("collect_verified_status", ("extract_requirements",)),),
    Intent.PROPOSAL_REQUEST: (
        ("qualify_need", ("extract_requirements",)),
        ("estimate_scope_cost_risk", ("qualify_need",)),
        ("generate_proposal", ("estimate_scope_cost_risk",)),
    ),
    Intent.QUOTE_REQUEST: (("estimate_scope_cost_risk", ("extract_requirements",)), ("generate_quote", ("estimate_scope_cost_risk",))),
    Intent.INVOICE_REQUEST: (("verify_contract_milestone", ("extract_requirements",)), ("generate_invoice_draft", ("verify_contract_milestone",))),
    Intent.PRIVACY_REQUEST: (("verify_requester_identity", ("verify_identity_authority",)), ("prepare_privacy_request_packet", ("verify_requester_identity",))),
    Intent.SECURITY_INCIDENT: (("contain_and_triage", ("collect_context",)), ("prepare_incident_packet", ("contain_and_triage",))),
}


def build_plan(case: CaseRecord) -> OutcomePlan:
    tasks: list[TaskSpec] = []
    for action, deps, tools, criteria in BASE:
        tasks.append(TaskSpec(f"{case.case_id}:{action}", case.case_id, action, deps, tools, criteria))

    specific = INTENT_TASKS.get(case.analysis.primary_intent, (("prepare_clarification", ("extract_requirements",)),))
    for action, deps in specific:
        tasks.append(
            TaskSpec(
                f"{case.case_id}:{action}",
                case.case_id,
                action,
                deps,
                ("deliverable_factory",),
                (f"{action} completed with evidence",),
                external_effect=False,
            )
        )

    tail_dep = (tasks[-1].action,) if tasks else ()
    tasks.extend(
        (
            TaskSpec(f"{case.case_id}:oak_validate", case.case_id, "oak_validate", tail_dep, ("oak_deliverable",), ("all mandatory gates pass",)),
            TaskSpec(f"{case.case_id}:route", case.case_id, "route", ("oak_validate",), ("channel_router",), ("destination and channel authorized",)),
            TaskSpec(f"{case.case_id}:prepare_reply", case.case_id, "prepare_reply", ("route",), ("reply_factory",), ("reply references exact deliverable version",)),
        )
    )
    return OutcomePlan(
        plan_id=f"PLAN-{case.case_id}",
        case_id=case.case_id,
        objective=f"resolve_{case.analysis.primary_intent.value.lower()}",
        tasks=tasks,
    )
