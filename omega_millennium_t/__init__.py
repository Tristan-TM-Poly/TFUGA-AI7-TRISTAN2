"""Ω-MILLENNIUM-T∞ R0.1.

A research-program compiler for proof graphs, adversarial testing, formal
skeletons and OAK evidence gates.  The package claims no solution to any open
millennium problem.
"""
from .adversary import adversarial_report, boundary_cases, cartesian_cases, search_counterexamples
from .benchmark import poincare_dependency_fixture, run_benchmark
from .campaign import compile_campaign, default_strategies
from .equivalence import DirectionalImplication, EquivalenceAudit, audit_equivalence
from .formal_bridge import export_lean_skeleton
from .graph import ProofGraph
from .models import (
    CampaignAllocation,
    Claim,
    ClaimKind,
    CounterexampleRecord,
    EdgeKind,
    Evidence,
    EvidenceKind,
    FormalSkeleton,
    OAKDecision,
    OAKLevel,
    ProblemId,
    ProblemSpec,
    ProblemStatus,
    ProofEdge,
    StrategyScore,
    ValidationReport,
)
from .oak import evaluate_claim, maximum_evidence_level, required_evidence_for
from .receipts import GENESIS, ResearchReceipt, create_receipt, verify_chain
from .registry import all_problems, get_problem, validate_registry
from .strategy import allocate_finite_budget, rank_strategies, update_strategy

__all__ = [
    "CampaignAllocation", "Claim", "ClaimKind", "CounterexampleRecord", "DirectionalImplication",
    "EdgeKind", "EquivalenceAudit", "Evidence", "EvidenceKind", "FormalSkeleton", "GENESIS",
    "OAKDecision", "OAKLevel", "ProblemId", "ProblemSpec", "ProblemStatus", "ProofEdge",
    "ProofGraph", "ResearchReceipt", "StrategyScore", "ValidationReport", "adversarial_report",
    "allocate_finite_budget", "all_problems", "audit_equivalence", "boundary_cases",
    "cartesian_cases", "compile_campaign", "create_receipt", "default_strategies",
    "evaluate_claim", "export_lean_skeleton", "get_problem", "maximum_evidence_level",
    "poincare_dependency_fixture", "rank_strategies", "required_evidence_for", "run_benchmark",
    "search_counterexamples", "update_strategy", "validate_registry", "verify_chain",
]

__version__ = "0.1.0"
