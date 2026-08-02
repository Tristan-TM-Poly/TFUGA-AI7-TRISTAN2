"""Ω-COMPANY-AUTOPILOT-T — bounded corporate operating system."""

from .approvals import action_hash, approve_action, valid_approvals
from .autopilot import AutopilotPlan, CompanyAutopilot, PlanItem
from .deadlines import DeadlineEngine
from .evidence import EvidenceLedger, LedgerEntry
from .governance import BoardPack, GovernanceEngine
from .models import *
from .policy import CorporatePolicy, OAKCorporateGate
from .registry import CompanyRegistry, RegistryError
from .spinout import SpinoutAssessment, SpinoutEngine
from .treasury import TreasuryEngine

__version__ = "0.1.0"
