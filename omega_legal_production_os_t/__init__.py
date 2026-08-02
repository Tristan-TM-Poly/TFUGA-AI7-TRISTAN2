"""Ω-LEGAL-PRODUCTION-OS-T∞ public API through R0.5."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .ledger import ActionLedger, LedgerEntry
from .models import (
    ActionState,
    ActionType,
    ApprovalRecord,
    AuthorityGrant,
    ExternalActionEnvelope,
    GateDecision,
    RiskLevel,
    detect_forbidden_payload_keys,
    hash_payload,
    iso_utc,
)
from .policy import LegalProductionPolicyGate, PolicyReport
from .real_execution import ExecutionReceipt, doctor, execute_action, reconcile_action
from .real_providers import (
    DropboxSignTestProvider,
    GmailSendProvider,
    GitHubDraftReleaseProvider,
    ProviderError,
    ProviderReceipt,
    StripeTestPaymentProvider,
)
from .release import (
    DryRunReleaseProvider,
    ReleaseArtifact,
    ReleaseCandidate,
    ReleaseDryRunReceipt,
    summarize_artifacts,
)


def generate_policy_atlas(root: str | Path) -> dict[str, Any]:
    from .atlas import generate

    return generate(root)


def audit_policy_atlas(root: str | Path) -> dict[str, Any]:
    from .atlas import audit

    return audit(root)


__all__ = [
    "ActionLedger",
    "ActionState",
    "ActionType",
    "ApprovalRecord",
    "AuthorityGrant",
    "DropboxSignTestProvider",
    "DryRunReleaseProvider",
    "ExecutionReceipt",
    "ExternalActionEnvelope",
    "GateDecision",
    "GmailSendProvider",
    "GitHubDraftReleaseProvider",
    "LedgerEntry",
    "LegalProductionPolicyGate",
    "PolicyReport",
    "ProviderError",
    "ProviderReceipt",
    "ReleaseArtifact",
    "ReleaseCandidate",
    "ReleaseDryRunReceipt",
    "RiskLevel",
    "StripeTestPaymentProvider",
    "audit_policy_atlas",
    "detect_forbidden_payload_keys",
    "doctor",
    "execute_action",
    "generate_policy_atlas",
    "hash_payload",
    "iso_utc",
    "reconcile_action",
    "summarize_artifacts",
]

__version__ = "0.5.0"
