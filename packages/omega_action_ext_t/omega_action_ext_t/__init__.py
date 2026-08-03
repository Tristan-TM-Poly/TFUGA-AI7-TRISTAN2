"""Ω-ACTION-EXT-T: OAK-safe external action automation kernel."""

from .approval_queue import ApprovalItem, ApprovalQueue
from .approval_state import ApprovalDecision, ApprovalState
from .automation_profile import AutomationMode, AutomationProfile, default_profiles
from .core import (
    ActionDNA,
    AutonomyLevel,
    Decision,
    DryRunReport,
    ProofOfExecution,
    RiskTensor,
)
from .draft_sweep import (
    DEFAULT_SIGNAL_WEIGHTS,
    DraftBlocker,
    DraftSignal,
    DraftSweepInput,
    DraftSweepPlan,
    infer_signals_from_files,
    plan_draft_sweep,
    render_draft_sweep_report,
)
from .green_builder import (
    BuildAction,
    GreenPlan,
    GreenStep,
    PRBlocker,
    PRGreenState,
    classify_blockers,
    plan_build_to_green,
    render_plan_markdown,
)
from .incident_codex import IncidentRule, incident_rules
from .leak_scan import LeakFinding, has_findings, scan_text
from .ledger import LedgerRecord, ProofLedger
from .manifest import ActionManifest
from .oakbench import OAKBenchScore, score_report
from .orchestrator import AutomationOrchestrator, AutomationResult
from .policy import OAKGate
from .pr_green_pipeline import (
    PRGreenPacket,
    action_for_plan,
    build_green_packet,
    build_green_packets,
    render_batch_report,
    risk_for_plan,
    summarize_packets,
)
from .rollback import RollbackRecipe, recipe_for, recipes
from .router import ConnectorRouter
from .validators import validate_payload
from .zero_manual_forge import (
    FailureMemory,
    ForgeDecision,
    RepairTactic,
    ZeroManualPlan,
    plan_zero_manual_forge,
    render_zero_manual_report,
)

__all__ = [
    "ActionDNA",
    "ActionManifest",
    "ApprovalDecision",
    "ApprovalItem",
    "ApprovalQueue",
    "ApprovalState",
    "AutomationMode",
    "AutomationOrchestrator",
    "AutomationProfile",
    "AutomationResult",
    "AutonomyLevel",
    "BuildAction",
    "ConnectorRouter",
    "DEFAULT_SIGNAL_WEIGHTS",
    "Decision",
    "DraftBlocker",
    "DraftSignal",
    "DraftSweepInput",
    "DraftSweepPlan",
    "DryRunReport",
    "FailureMemory",
    "ForgeDecision",
    "GreenPlan",
    "GreenStep",
    "IncidentRule",
    "LeakFinding",
    "LedgerRecord",
    "OAKBenchScore",
    "OAKGate",
    "PRBlocker",
    "PRGreenPacket",
    "PRGreenState",
    "ProofLedger",
    "ProofOfExecution",
    "RepairTactic",
    "RiskTensor",
    "RollbackRecipe",
    "ZeroManualPlan",
    "action_for_plan",
    "build_green_packet",
    "build_green_packets",
    "classify_blockers",
    "default_profiles",
    "has_findings",
    "incident_rules",
    "infer_signals_from_files",
    "plan_build_to_green",
    "plan_draft_sweep",
    "plan_zero_manual_forge",
    "recipe_for",
    "recipes",
    "render_batch_report",
    "render_draft_sweep_report",
    "render_plan_markdown",
    "render_zero_manual_report",
    "risk_for_plan",
    "scan_text",
    "score_report",
    "summarize_packets",
    "validate_payload",
]
