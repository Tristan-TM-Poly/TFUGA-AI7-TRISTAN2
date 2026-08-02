"""Ω-MAIL-T: deterministic intercompany and officialization mail laboratory."""

from .cvcd_atlas import AtlasAudit, AtlasCell, CVCDAtlas
from .engine import ScenarioRunner, run_scenario
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
from .production import DeliveryReceipt, DryRunProvider, SMTPConfig, SMTPProvider, deliver_one
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
    "SMTPConfig",
    "SMTPProvider",
    "ScenarioRunner",
    "deliver_one",
    "run_scenario",
]

__version__ = "0.3.0"
