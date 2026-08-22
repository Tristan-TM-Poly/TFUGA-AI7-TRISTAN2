"""Ω-META-HMG-GENESIS-T∞ research kernel."""
from .book0 import BOOK0, INVARIANTS
from .models import (
    ArtifactGenome, Candidate, Certificate, GeneratorGenome,
    Residual, VerificationResult, VerificationStatus,
)
from .engine import MetaHMGEngine, FrozenBenchmark, DefaultVerifier
from .integration import hmg_representation_research_capability
from .meta import (
    AuthorityEnvelope, ForgetReceipt, MetaController, QuestionCandidate,
    RegenerationDepth, WorkflowGenome,
)

__all__ = [
    "BOOK0", "INVARIANTS", "ArtifactGenome", "Candidate", "Certificate",
    "GeneratorGenome", "Residual", "VerificationResult", "VerificationStatus",
    "MetaHMGEngine", "FrozenBenchmark", "DefaultVerifier",
    "AuthorityEnvelope", "ForgetReceipt", "MetaController", "QuestionCandidate",
    "RegenerationDepth", "WorkflowGenome", "hmg_representation_research_capability",
]
