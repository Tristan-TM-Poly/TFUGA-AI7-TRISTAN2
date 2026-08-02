"""Ω-LEGAL-PRODUCTION-OS-T∞ R0.1/R0.2 public API."""
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
    "DryRunReleaseProvider",
    "ExternalActionEnvelope",
    "GateDecision",
    "LedgerEntry",
    "LegalProductionPolicyGate",
    "PolicyReport",
    "ReleaseArtifact",
    "ReleaseCandidate",
    "ReleaseDryRunReceipt",
    "RiskLevel",
    "audit_policy_atlas",
    "detect_forbidden_payload_keys",
    "generate_policy_atlas",
    "hash_payload",
    "iso_utc",
    "summarize_artifacts",
]

__version__ = "0.2.0"
