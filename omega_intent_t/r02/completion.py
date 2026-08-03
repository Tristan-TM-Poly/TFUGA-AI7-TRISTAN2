from __future__ import annotations

from .models import CompletionContract, CompletionDecision


def evaluate_completion(contract: CompletionContract) -> CompletionDecision:
    blockers: list[str] = []
    actions: list[str] = []

    unresolved_requirements = (
        contract.requirements_total
        - contract.requirements_verified
        - contract.requirements_blocked
        - contract.requirements_rejected
    )
    if unresolved_requirements:
        blockers.append(f"{unresolved_requirements} requirements unresolved")
        actions.append("resolve_or_explicitly_classify_remaining_requirements")
    if contract.requirements_blocked:
        blockers.append(f"{contract.requirements_blocked} requirements blocked")
        actions.append("clear_or_accept_declared_requirement_blockers")
    if contract.critical_risks_open:
        blockers.append(f"{contract.critical_risks_open} critical risks open")
        actions.append("close_critical_risks_through_human_gate")
    if not contract.build_passed:
        blockers.append("build not passed")
        actions.append("repair_build_and_capture_evidence")
    if not contract.tests_passed:
        blockers.append("tests not passed")
        actions.append("repair_tests_or_reject_invalid_requirements")
    if not contract.documentation_synced:
        blockers.append("documentation not synchronized")
        actions.append("regenerate_and_diff_documentation")
    if contract.unresolved_claims:
        blockers.append(f"{contract.unresolved_claims} claims unresolved")
        actions.append("attach_evidence_or_downgrade_claim_status")
    if contract.claims_evidence_backed < contract.claims_total:
        missing = contract.claims_total - contract.claims_evidence_backed
        blockers.append(f"{missing} claims lack evidence")
        actions.append("execute_claim_evidence_plan")
    if contract.benchmark_regressions:
        blockers.append(f"{contract.benchmark_regressions} benchmark regressions")
        actions.append("explain_accept_or_repair_benchmark_regressions")
    if not contract.residuals_declared:
        blockers.append("residuals not declared")
        actions.append("write_m_minus_and_unresolved_residual_report")

    complete = not blockers
    if complete:
        status = "completed_with_evidence"
        actions.append("freeze_receipt_and_open_next_optional_intent")
    elif contract.critical_risks_open or contract.requirements_blocked:
        status = "blocked_with_declared_residuals"
    elif contract.requirement_closure_ratio == 1.0:
        status = "closed_but_not_validated"
    else:
        status = "in_progress"

    return CompletionDecision(
        complete=complete,
        status=status,
        closure_ratio=contract.requirement_closure_ratio,
        verification_ratio=contract.verification_ratio,
        claim_evidence_ratio=contract.claim_evidence_ratio,
        blockers=tuple(blockers),
        next_actions=tuple(dict.fromkeys(actions)),
    )
