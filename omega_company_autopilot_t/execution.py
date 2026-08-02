"""Dry-run-first corporate execution adapters."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Protocol

from .approvals import action_hash, valid_approvals
from .models import ActionRequest, ExecutionReceipt, GateDecision, GateResult


class ExecutionAdapter(Protocol):
    name: str
    def execute(self, action: ActionRequest) -> str | None: ...


class DryRunAdapter:
    name = "dry_run"
    def execute(self, action: ActionRequest) -> str:
        return f"dryrun:{action.action_id}"


class ExecutionError(RuntimeError):
    pass


def execute_bounded(action: ActionRequest, gate: GateResult, approvals: list, *, adapter: ExecutionAdapter | None = None, execute_external: bool = False) -> ExecutionReceipt:
    if gate.decision in {GateDecision.BLOCK, GateDecision.PROFESSIONAL_REVIEW, GateDecision.PREPARE}:
        raise ExecutionError(f"gate_not_executable:{gate.decision.value}")
    valid = valid_approvals(action, approvals)
    if len(valid) < gate.required_approvals:
        raise ExecutionError("insufficient_valid_approvals")
    if execute_external:
        if os.environ.get("OMEGA_COMPANY_EXTERNAL_EXECUTION") != "I_ACKNOWLEDGE_ONE_ACTION":
            raise ExecutionError("external_execution_acknowledgement_missing")
        if os.environ.get("OMEGA_COMPANY_ALLOWED_ACTION_ID") != action.action_id:
            raise ExecutionError("action_allowlist_mismatch")
        if adapter is None or isinstance(adapter, DryRunAdapter):
            raise ExecutionError("real_adapter_required")
    else:
        adapter = adapter or DryRunAdapter()
    external_reference = adapter.execute(action)
    return ExecutionReceipt(
        action_id=action.action_id,
        provider=adapter.name,
        mode="external" if execute_external else "dry_run",
        accepted=True,
        executed_at=datetime.now(timezone.utc).isoformat(),
        external_reference=external_reference,
        action_hash=action_hash(action),
        notes=("provider_acceptance_is_not_legal_completion",),
    )
