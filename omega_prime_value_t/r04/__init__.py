"""Ω-PRIME-VALUE-T∞ R0.4: recursive proof DAGs and governed publication evidence."""

from .budget import BudgetLedger, ComputeBudgetPolicy
from .proof_dag import ProofGraph, build_proof_graph, verify_proof_graph
from .residue import ResidueProgram, compile_proth_residue_program
from .transparency import TransparencyLog

__all__ = [
    "BudgetLedger",
    "ComputeBudgetPolicy",
    "ProofGraph",
    "ResidueProgram",
    "TransparencyLog",
    "build_proof_graph",
    "compile_proth_residue_program",
    "verify_proof_graph",
]

__version__ = "0.4.0"
