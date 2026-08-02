"""Ω-MAIL-T: deterministic intercompany email simulation lab."""

from .cvcd_atlas import AtlasAudit, AtlasCell, CVCDAtlas
from .engine import ScenarioRunner, run_scenario
from .models import MailMessage, Mailbox
from .oak import OAKDecision, OAKMailGate
from .transport import InMemoryTransport

__all__ = [
    "AtlasAudit",
    "AtlasCell",
    "CVCDAtlas",
    "InMemoryTransport",
    "MailMessage",
    "Mailbox",
    "OAKDecision",
    "OAKMailGate",
    "ScenarioRunner",
    "run_scenario",
]

__version__ = "0.2.0"
