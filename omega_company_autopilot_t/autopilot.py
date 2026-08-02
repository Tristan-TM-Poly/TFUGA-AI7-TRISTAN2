"""Observe → plan → gate → approve → execute → learn orchestrator."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .approvals import action_hash
from .evidence import EvidenceLedger
from .execution import execute_bounded
from .models import ActionRequest, ApprovalRecord, CompanyRecord, ExecutionReceipt, GateResult
from .policy import OAKCorporateGate


@dataclass(frozen=True, slots=True)
class PlanItem:
    action: ActionRequest
    gate: GateResult


@dataclass(frozen=True, slots=True)
class AutopilotPlan:
    company_id: str
    items: tuple[PlanItem, ...]
    blocked: int
    approval_required: int
    professional_review: int
    preparation_only: int
    auto_ready: int


class CompanyAutopilot:
    def __init__(self, *, gate: OAKCorporateGate | None = None, ledger: EvidenceLedger | None = None) -> None:
        self.gate = gate or OAKCorporateGate()
        self.ledger = ledger or EvidenceLedger()

    def plan(self, company: CompanyRecord, actions: Iterable[ActionRequest]) -> AutopilotPlan:
        items: list[PlanItem] = []
        counters = {"blocked": 0, "approval_required": 0, "professional_review": 0, "preparation_only": 0, "auto_ready": 0}
        for action in actions:
            action.content_hash = action_hash(action)
            gate = self.gate.evaluate(company, action)
            items.append(PlanItem(action, gate))
            if gate.decision.value == "BLOCK": counters["blocked"] += 1
            elif gate.decision.value == "PROFESSIONAL_REVIEW": counters["professional_review"] += 1
            elif gate.required_approvals: counters["approval_required"] += 1
            elif gate.decision.value == "AUTO": counters["auto_ready"] += 1
            else: counters["preparation_only"] += 1
            self.ledger.append(
                entry_id=f"gate:{action.action_id}",
                event_type="ACTION_GATED",
                subject_id=action.action_id,
                payload={"action": asdict(action), "gate": asdict(gate)},
            )
        return AutopilotPlan(company.company_id, tuple(items), **counters)

    def execute(self, item: PlanItem, approvals: list[ApprovalRecord], *, adapter=None, execute_external: bool = False) -> ExecutionReceipt:
        receipt = execute_bounded(item.action, item.gate, approvals, adapter=adapter, execute_external=execute_external)
        self.ledger.append(
            entry_id=f"receipt:{item.action.action_id}",
            event_type="ACTION_EXECUTION_RECEIPT",
            subject_id=item.action.action_id,
            payload=asdict(receipt),
        )
        return receipt
