"""Ω-META-GTNT-T∞²: reflexive, falsifiable strategy compiler.

The package operationalizes selected engineering ideas around Gödel/Turing/
von-Neumann/Tristan without claiming to extend classical incompleteness or
computability theorems.
"""

from .engine import MetaGTNTEngine
from .ledger import EpistemicLedger, NegativeMemory, NoGoRule
from .models import (
    ClaimRecord,
    CostVector,
    Diagnosis,
    FailureKind,
    FrontierKind,
    RepresentationCandidate,
    StrategyPath,
    TruthLevel,
)

__all__ = [
    "ClaimRecord",
    "CostVector",
    "Diagnosis",
    "EpistemicLedger",
    "FailureKind",
    "FrontierKind",
    "MetaGTNTEngine",
    "NegativeMemory",
    "NoGoRule",
    "RepresentationCandidate",
    "StrategyPath",
    "TruthLevel",
]

__version__ = "0.1.0"
