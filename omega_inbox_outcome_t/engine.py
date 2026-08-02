"""Inbox-to-outcome orchestration engine."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .deliverables import build_deliverable
from .followup import schedule_followups
from .intent import analyze_request
from .models import AutonomousDeliveryContract, CaseRecord, IntakeEvent, IntakeStatus, ResolvedIdentity
from .planner import build_plan
from .policy import gate_case
from .reply import compose_reply
from .routing import DryRunDispatcher, choose_route
from .validation import validate_deliverable


@dataclass(slots=True)
class OutcomeResult:
    case: CaseRecord
    gate: object
    plan: object
    manifest: object
    validation: object
    route: object
    receipt: object
    reply: object
    followups: list[object]

    def to_dict(self) -> dict:
        return {
            "case": self.case.to_dict(),
            "gate": {
                "case_id": self.gate.case_id,
                "decision": self.gate.decision.value,
                "reasons": list(self.gate.reasons),
                "required_approvals": self.gate.required_approvals,
                "allowed_channels": [item.value for item in self.gate.allowed_channels],
                "allowed_deliverables": list(self.gate.allowed_deliverables),
            },
            "plan": self.plan.to_dict(),
            "manifest": self.manifest.to_dict(),
            "validation": {
                "deliverable_id": self.validation.deliverable_id,
                "status": self.validation.status.value,
                "checks": self.validation.checks,
                "reasons": list(self.validation.reasons),
                "warnings": list(self.validation.warnings),
            },
            "route": {
                "primary_channel": self.route.primary_channel.value,
                "notification_channel": self.route.notification_channel.value if self.route.notification_channel else None,
                "destination": self.route.destination,
                "reasons": list(self.route.reasons),
            },
            "receipt": self.receipt.to_dict(),
            "reply": self.reply.to_dict(),
            "followups": [item.to_dict() for item in self.followups],
        }


class InboxOutcomeEngine:
    def __init__(self, workspace: Path, dispatcher: DryRunDispatcher | None = None) -> None:
        self.workspace = workspace
        self.dispatcher = dispatcher or DryRunDispatcher()

    def process(
        self,
        event: IntakeEvent,
        *,
        identity: ResolvedIdentity,
        contract: AutonomousDeliveryContract,
        company_id: str,
        division_id: str,
    ) -> OutcomeResult:
        analysis = analyze_request(event)
        case = CaseRecord(
            case_id=f"CASE-{event.event_id}",
            event_id=event.event_id,
            company_id=company_id,
            division_id=division_id,
            identity=identity,
            analysis=analysis,
        )
        gate = gate_case(case, contract)
        plan = build_plan(case)
        case.task_ids = [task.task_id for task in plan.tasks]
        case.status = IntakeStatus.PLANNED

        manifest = build_deliverable(case, self.workspace)
        case.deliverable_ids.append(manifest.deliverable_id)
        validation = validate_deliverable(case, manifest)
        route = choose_route(manifest, identity, event.sender_address)
        receipt = self.dispatcher.dispatch(case.case_id, manifest, route)
        reply = compose_reply(case, manifest, validation, gate, route, event.sender_address)
        followups = schedule_followups(case, receipt)
        case.status = IntakeStatus.READY_TO_DISPATCH
        return OutcomeResult(case, gate, plan, manifest, validation, route, receipt, reply, followups)
