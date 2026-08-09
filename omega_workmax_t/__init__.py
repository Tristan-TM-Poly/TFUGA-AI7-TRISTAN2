"""Ω-WORKMAX-GIT-T∞ — OAK-safe repository work optimization primitives."""

from .capability import CapabilityMatch, route_capabilities
from .crystallizer import CrystallizationDecision, CrystallizationGovernor
from .engine import build_report
from .graph import CriticalPath, WorkHypergraph
from .models import ProofGates, WorkMetrics, WorkPacket, WorkState
from .planner import DeduplicationResult, PlannedWave, deduplicate_packets, pareto_front, plan_waves, priority_score
from .promotion import PromotionDecision, decide_promotion
from .telemetry import WorkTelemetryInput, compute_metrics
from .twin import TwinResult, adaptive_worker_sweep, simulate

__all__ = [
    "CapabilityMatch",
    "CriticalPath",
    "CrystallizationDecision",
    "CrystallizationGovernor",
    "DeduplicationResult",
    "PlannedWave",
    "ProofGates",
    "PromotionDecision",
    "TwinResult",
    "WorkHypergraph",
    "WorkMetrics",
    "WorkPacket",
    "WorkState",
    "WorkTelemetryInput",
    "adaptive_worker_sweep",
    "build_report",
    "compute_metrics",
    "decide_promotion",
    "deduplicate_packets",
    "pareto_front",
    "plan_waves",
    "priority_score",
    "route_capabilities",
    "simulate",
]
