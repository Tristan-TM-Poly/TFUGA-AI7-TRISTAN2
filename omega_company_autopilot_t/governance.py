"""Board/owner review packets for a founder-controlled company."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Iterable

from .deadlines import DeadlineEngine
from .models import ActionRequest, CompanyRecord, GateResult, Obligation
from .spinout import SpinoutEngine


@dataclass(frozen=True, slots=True)
class BoardPack:
    company_id: str
    as_of: str
    legal_state: str
    autonomy_level: int
    division_count: int
    enabled_divisions: int
    upcoming_obligations: tuple[dict, ...]
    pending_actions: tuple[dict, ...]
    spinout_assessments: tuple[dict, ...]
    risks: tuple[str, ...]
    decisions_required: tuple[str, ...]


class GovernanceEngine:
    def build_board_pack(self, company: CompanyRecord, *, obligations: Iterable[Obligation] = (), actions: Iterable[tuple[ActionRequest, GateResult]] = (), as_of: date | None = None) -> BoardPack:
        as_of = as_of or date.today()
        upcoming = DeadlineEngine().upcoming(obligations, today=as_of)
        spinouts = [SpinoutEngine().assess(item) for item in company.divisions if item.enabled]
        risks: list[str] = []
        decisions: list[str] = []
        if not company.legal_identity_verified: risks.append("legal_identity_unverified")
        if not company.privacy_officer: risks.append("privacy_officer_missing")
        if company.production_enabled and company.state.value != "PRODUCTION_AUTHORIZED": risks.append("production_flag_without_authorized_state")
        if not company.directors: risks.append("director_registry_empty")
        action_rows: list[dict] = []
        for action, gate in actions:
            action_rows.append({
                "action_id": action.action_id,
                "kind": action.kind.value,
                "title": action.title,
                "decision": gate.decision.value,
                "required_approvals": gate.required_approvals,
                "professional_review": list(gate.professional_review),
            })
            if gate.required_approvals or gate.professional_review:
                decisions.append(action.action_id)
        return BoardPack(
            company_id=company.company_id,
            as_of=as_of.isoformat(),
            legal_state=company.state.value,
            autonomy_level=int(company.autonomy_level),
            division_count=len(company.divisions),
            enabled_divisions=sum(1 for item in company.divisions if item.enabled),
            upcoming_obligations=tuple({
                "obligation_id": obligation.obligation_id,
                "title": obligation.title,
                "due_date": obligation.due_date.isoformat(),
                "days_remaining": days,
                "professional_review_required": obligation.professional_review_required,
            } for obligation, days in upcoming),
            pending_actions=tuple(action_rows),
            spinout_assessments=tuple(asdict(item) for item in spinouts),
            risks=tuple(sorted(set(risks))),
            decisions_required=tuple(sorted(set(decisions))),
        )
