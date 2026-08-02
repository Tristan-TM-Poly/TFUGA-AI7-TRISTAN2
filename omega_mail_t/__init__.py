"""Ω-MAIL-T: deterministic intercompany email simulation lab."""

from .engine import ScenarioRunner, run_scenario
from .models import MailMessage, Mailbox
from .oak import OAKDecision, OAKMailGate
from .transport import InMemoryTransport

__all__ = [
    "InMemoryTransport",
    "MailMessage",
    "Mailbox",
    "OAKDecision",
    "OAKMailGate",
    "ScenarioRunner",
    "run_scenario",
]

__version__ = "0.1.0"
