"""Ω-MAIL-T: deterministic intercompany and officialization mail laboratory."""

from .cvcd_atlas import AtlasAudit, AtlasCell, CVCDAtlas
from .engine import ScenarioRunner, run_scenario
from .hardening import (
    LedgerEntry,
    LedgerReservation,
    OneMessageLedger,
    recipient_hash,
    validate_approval_for_execution,
    validate_delivery_draft,
)
from .models import MailMessage, Mailbox
from .oak import OAKDecision, OAKMailGate
from .officialization import (
    ApprovalRecord,
    CompanyIdentity,
    CompanyState,
    ComplianceContext,
    MailAuthority,
    MessageClass,
    OfficialDecision,
    OfficialGateReport,
    OfficialMessageDraft,
    OfficializationGate,
)
from .production import (
    DeliveryReceipt,
    DryRunProvider,
    SMTPConfig,
    SMTPProvider,
    deliver_one,
    render_message,
)
from .transport import InMemoryTransport

__all__ = [
    "ApprovalRecord",
    "AtlasAudit",
    "AtlasCell",
    "CVCDAtlas",
    "CompanyIdentity",
    "CompanyState",
    "ComplianceContext",
    "DeliveryReceipt",
    "DryRunProvider",
    "InMemoryTransport",
    "LedgerEntry",
    "LedgerReservation",
    "MailAuthority",
    "MailMessage",
    "Mailbox",
    "MessageClass",
    "OAKDecision",
    "OAKMailGate",
    "OfficialDecision",
    "OfficialGateReport",
    "OfficialMessageDraft",
    "OfficializationGate",
    "OneMessageLedger",
    "SMTPConfig",
    "SMTPProvider",
    "ScenarioRunner",
    "deliver_one",
    "recipient_hash",
    "render_message",
    "run_scenario",
    "validate_approval_for_execution",
    "validate_delivery_draft",
]

__version__ = "0.4.0"
