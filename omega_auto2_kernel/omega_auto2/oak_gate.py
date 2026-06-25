from __future__ import annotations

from .models import OAKReport, SENSITIVE_ACTIONS, Workflow


HIGH_RISK_KEYWORDS = {
    "delete",
    "publish",
    "email",
    "send",
    "spend",
    "payment",
    "contract",
    "legal",
    "medical",
    "patent",
    "secret",
    "permission",
}


def _score_from_blockers(blockers: list[str], warnings: list[str]) -> float:
    score = 1.0 - 0.18 * len(blockers) - 0.05 * len(warnings)
    return round(max(0.0, min(1.0, score)), 4)


def _status(final_score: float, blockers: list[str]) -> str:
    if blockers or final_score < 0.50:
        return "blocked"
    if final_score < 0.70:
        return "draft_only"
    if final_score < 0.85:
        return "dry_run_allowed"
    if final_score < 0.95:
        return "controlled_deployment"
    return "trusted_limited"


def evaluate_workflow(workflow: Workflow) -> OAKReport:
    blockers: list[str] = []
    warnings: list[str] = []

    if not workflow.purpose or len(workflow.purpose.strip()) < 12:
        blockers.append("purpose_too_weak")

    if not workflow.steps:
        blockers.append("missing_steps")

    if not workflow.outputs:
        blockers.append("missing_outputs")

    if not workflow.oak.get("required", False):
        blockers.append("oak_not_required")

    if not workflow.rollback.get("possible", False):
        blockers.append("missing_rollback")

    sensitive_writes = workflow.sensitive_writes()
    if sensitive_writes:
        blockers.append(f"sensitive_write_permissions_not_allowed: {sorted(sensitive_writes)}")

    forbidden = workflow.forbidden_actions()
    missing_forbidden = SENSITIVE_ACTIONS.difference(forbidden).difference({"medical_decision", "legal_commitment"})
    if missing_forbidden:
        warnings.append(f"consider_forbidding_sensitive_actions: {sorted(missing_forbidden)}")

    joined = " ".join(workflow.steps + workflow.outputs + [workflow.purpose]).lower()
    keyword_hits = sorted(word for word in HIGH_RISK_KEYWORDS if word in joined)
    if keyword_hits:
        warnings.append(f"high_risk_keywords_present: {keyword_hits}")

    clarity = 0.95 if workflow.purpose and workflow.steps and workflow.outputs else 0.55
    safety = 0.95 if not sensitive_writes else 0.35
    reversibility = 0.90 if workflow.rollback.get("possible", False) else 0.20
    usefulness = 0.85 if len(workflow.steps) >= 4 else 0.65
    cost_control = 0.80
    legal_ip = 0.85 if "ip_disclosure" in forbidden else 0.60

    final_score = round(
        min(
            _score_from_blockers(blockers, warnings),
            (clarity + safety + reversibility + usefulness + cost_control + legal_ip) / 6,
        ),
        4,
    )

    approval_required = sorted(SENSITIVE_ACTIONS.intersection(forbidden).union(sensitive_writes))

    return OAKReport(
        clarity=round(clarity, 4),
        safety=round(safety, 4),
        reversibility=round(reversibility, 4),
        usefulness=round(usefulness, 4),
        cost_control=round(cost_control, 4),
        legal_ip=round(legal_ip, 4),
        final_score=final_score,
        status=_status(final_score, blockers),
        blockers=blockers,
        warnings=warnings,
        human_approval_required_for=approval_required,
    )
