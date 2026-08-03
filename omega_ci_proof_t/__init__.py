"""Ω-CI-PROOF-AUTONOMY-T∞ A1-A3 proof-producing CI kernel."""
from .adversarial import audit_source, evidence_quality
from .autonomy import AutonomyGate
from .claims import ClaimRegistry
from .diagnosis import diagnose_pytest_log
from .evidence import EvidenceBundleBuilder, EvidenceVerifier, hash_file
from .generators import MMinusRegressionGenerator
from .ledger import ProofLedger
from .models import (
    ArtifactEvidence,
    AutonomyDecision,
    Claim,
    EvidenceBundle,
    EvidenceDecision,
    FailureDiagnostic,
    Finding,
    MMinusRule,
    ProofPlan,
    TestResult,
    TestSpec,
)
from .oak import run_oakbench
from .planner import ProofPlanner

__all__ = [
    "ArtifactEvidence", "AutonomyDecision", "AutonomyGate", "Claim", "ClaimRegistry",
    "EvidenceBundle", "EvidenceBundleBuilder", "EvidenceDecision", "EvidenceVerifier",
    "FailureDiagnostic", "Finding", "MMinusRegressionGenerator", "MMinusRule", "ProofLedger",
    "ProofPlan", "ProofPlanner", "TestResult", "TestSpec", "audit_source", "diagnose_pytest_log",
    "evidence_quality", "hash_file", "run_oakbench",
]
