"""Global automation orchestrator.

The orchestrator automates the full safe preparation pipeline:
validate payload -> ActionDNA -> ActionManifest -> connector dry-run plan ->
approval queue -> proof ledger. It does not execute external side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .approval_queue import ApprovalQueue
from .automation_profile import AutomationProfile, PROFILE_DEFAULT
from .cli import action_from_dict
from .ledger import ProofLedger
from .manifest import ActionManifest
from .oakbench import score_report
from .router import ConnectorRouter


@dataclass(frozen=True)
class AutomationResult:
    manifest: ActionManifest
    connector_plan: dict[str, object]
    approval_item: dict[str, object] | None
    ledger_hash: str | None
    oakbench_score: dict[str, int]
    profile: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "manifest": self.manifest.to_dict(),
            "connector_plan": self.connector_plan,
            "approval_item": self.approval_item,
            "ledger_hash": self.ledger_hash,
            "oakbench_score": self.oakbench_score,
            "profile": self.profile,
        }


class AutomationOrchestrator:
    """Prepare every safe artifact for an action without final execution."""

    def __init__(
        self,
        profile: AutomationProfile = PROFILE_DEFAULT,
        queue_path: str | Path | None = None,
        ledger_path: str | Path | None = None,
    ) -> None:
        self.profile = profile
        self.queue = ApprovalQueue(queue_path or ".omega_action/approval_queue.json")
        self.ledger = ProofLedger(ledger_path or ".omega_action/proof_ledger.jsonl")
        self.router = ConnectorRouter()

    def prepare(self, payload: dict[str, Any]) -> AutomationResult:
        action = action_from_dict(payload)
        manifest = ActionManifest.compile(action)
        plan = self.router.plan(manifest).to_dict()
        score = score_report(manifest.dry_run).to_dict()

        approval_item = None
        if manifest.dry_run.required_approvals or manifest.dry_run.decision.value in {"needs_approval", "require_expert", "block"}:
            approval_item = self.queue.add_manifest(manifest).to_dict()

        ledger_record = self.ledger.append(
            "automation_prepare",
            {
                "manifest_hash": manifest.to_dict()["manifest_hash"],
                "decision": manifest.dry_run.decision.value,
                "connector_plan": plan,
                "score": score,
                "profile": self.profile.to_dict(),
            },
        )

        return AutomationResult(
            manifest=manifest,
            connector_plan=plan,
            approval_item=approval_item,
            ledger_hash=ledger_record.record_hash,
            oakbench_score=score,
            profile=self.profile.to_dict(),
        )
