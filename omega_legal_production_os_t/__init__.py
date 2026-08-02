"""Ω-LEGAL-PRODUCTION-OS-T∞ public API through R0.6."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .filing_packets import (
    FilingDocument,
    GovernmentFilingPacket,
    build_packet,
    load_packet,
    record_official_receipt,
)
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
    "FilingDocument",
    "GateDecision",
    "GmailSendProvider",
    "GitHubDraftReleaseProvider",
    "GovernmentFilingPacket",
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
    "build_packet",
    "detect_forbidden_payload_keys",
    "doctor",
    "execute_action",
    "generate_policy_atlas",
    "hash_payload",
    "iso_utc",
    "load_packet",
    "reconcile_action",
    "record_official_receipt",
    "summarize_artifacts",
]

__version__ = "0.6.0"
