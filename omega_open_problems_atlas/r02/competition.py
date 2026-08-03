"""Rules-first handling for competitions and computational challenges."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .models import CompetitionPolicy, ProblemLead


@dataclass(frozen=True)
class CompetitionDecision:
    competition_id: str
    allowed_actions: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    human_review_required: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_policy(policy: CompetitionPolicy) -> CompetitionDecision:
    allowed = ["store_public_metadata", "prepare_private_training_fixture"]
    blocked = ["automated_identity_bound_submission", "claim_official_participation"]
    reasons = ["competition rules and deadlines can change"]
    if not policy.redistribution_allowed:
        blocked.append("mirror_problem_or_dataset")
        reasons.append("redistribution permission is not recorded")
    if policy.ai_use_review_required:
        blocked.append("use_ai_without_rule_review")
        reasons.append("AI usage requires rule-specific review")
    if policy.deadline_recheck_required:
        blocked.append("rely_on_stale_deadline")
    if not policy.identity_bound_submission:
        allowed.append("prepare_non_identity_bound_public_benchmark")
    if policy.automated_submission_allowed:
        allowed.append("prepare_submission_payload_after_explicit_authorization")
    else:
        blocked.append("automated_submission")
    return CompetitionDecision(
        competition_id=policy.competition_id,
        allowed_actions=tuple(sorted(set(allowed))),
        blocked_actions=tuple(sorted(set(blocked))),
        human_review_required=True,
        reasons=tuple(sorted(set(reasons))),
    )


def research_open_count(leads: Iterable[ProblemLead]) -> int:
    """Count research-open records without mixing competition benchmarks."""
    count = 0
    for lead in leads:
        if lead.kind in {"COMPETITION_PROBLEM", "COMPUTATIONAL_CHALLENGE"}:
            continue
        if lead.independently_checked_open:
            count += 1
    return count


def competition_count(leads: Iterable[ProblemLead]) -> int:
    return sum(
        lead.kind in {"COMPETITION_PROBLEM", "COMPUTATIONAL_CHALLENGE"}
        for lead in leads
    )
