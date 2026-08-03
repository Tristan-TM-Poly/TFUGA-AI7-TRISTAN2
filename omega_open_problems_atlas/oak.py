"""Fail-closed OAK evaluation for problem records."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from .models import EpistemicStatus, OpenStatus, ProblemGenome


class OAKDecision(str, Enum):
    BLOCK = "BLOCK"
    DISCOVERY_ONLY = "DISCOVERY_ONLY"
    RESEARCH_READY = "RESEARCH_READY"
    RESULT_REVIEW_REQUIRED = "RESULT_REVIEW_REQUIRED"
    CANON_REVIEW_REQUIRED = "CANON_REVIEW_REQUIRED"


@dataclass(frozen=True)
class OAKReport:
    problem_id: str
    decision: OAKDecision
    findings: tuple[str, ...]
    allowed_actions: tuple[str, ...]
    blocked_claims: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["decision"] = self.decision.value
        return data


def evaluate_problem(problem: ProblemGenome) -> OAKReport:
    findings: list[str] = []
    blocked_claims = [
        "solution_announced_without_independent_verification",
        "finite_computation_promoted_to_universal_proof",
        "source_report_promoted_to_current_open_status",
        "generated_volume_promoted_to_mathematical_progress",
    ]

    if not problem.problem_id.strip() or not problem.title.strip():
        findings.append("missing_identity")
    if not problem.statement.strip():
        findings.append("missing_statement")
    if not problem.source_id.strip() or not problem.source_locator.strip():
        findings.append("missing_provenance")
    if problem.solution_claimed:
        findings.append("solution_claim_requires_external_review")
    if not problem.finite_computation_is_not_proof:
        findings.append("finite_computation_boundary_removed")
    if problem.open_status is OpenStatus.INDEPENDENTLY_CHECKED_OPEN and not problem.last_status_check:
        findings.append("checked_open_without_check_date")
    if not problem.human_review_required:
        findings.append("human_review_boundary_removed")

    hard = {
        "missing_identity",
        "missing_statement",
        "missing_provenance",
        "finite_computation_boundary_removed",
        "human_review_boundary_removed",
    }
    if hard.intersection(findings):
        return OAKReport(
            problem.problem_id,
            OAKDecision.BLOCK,
            tuple(findings),
            (),
            tuple(blocked_claims),
        )

    if problem.open_status in {
        OpenStatus.DISCOVERED_UNVERIFIED,
        OpenStatus.SOURCE_REPORTED_OPEN,
        OpenStatus.STALE_SOURCE,
        OpenStatus.STATUS_DISPUTED,
    }:
        return OAKReport(
            problem.problem_id,
            OAKDecision.DISCOVERY_ONLY,
            tuple(findings or ["independent_status_check_required"]),
            ("verify_source", "search_literature", "normalize_statement"),
            tuple(blocked_claims),
        )

    if problem.epistemic_status in {
        EpistemicStatus.PARTIAL_PROGRESS,
        EpistemicStatus.INDEPENDENTLY_REPRODUCED,
    } or problem.solution_claimed:
        return OAKReport(
            problem.problem_id,
            OAKDecision.RESULT_REVIEW_REQUIRED,
            tuple(findings or ["independent_mathematical_review_required"]),
            ("reproduce", "formalize", "seek_expert_review"),
            tuple(blocked_claims),
        )

    if problem.epistemic_status in {
        EpistemicStatus.FORMALIZED_OR_PEER_REVIEWED,
        EpistemicStatus.CANON_CANDIDATE,
    }:
        return OAKReport(
            problem.problem_id,
            OAKDecision.CANON_REVIEW_REQUIRED,
            tuple(findings or ["canon_promotion_is_human_governed"]),
            ("audit_provenance", "audit_proof", "review_public_claims"),
            tuple(blocked_claims),
        )

    return OAKReport(
        problem.problem_id,
        OAKDecision.RESEARCH_READY,
        tuple(findings),
        (
            "decompose",
            "construct_finite_surrogates",
            "search_counterexamples",
            "run_reproducible_experiments",
            "record_m_minus",
        ),
        tuple(blocked_claims),
    )
