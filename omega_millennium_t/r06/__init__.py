"""Ω-PROBLEM-ATLAS-T∞ R0.6 claim-evidence-barrier hypergraph.

R0.6 attaches claims, assumptions, evidence, barriers, counterexamples,
computation receipts, formal artifacts and independent reviews to stable R0.5
problem identities. It never infers a general proof from numerical evidence.
"""

from . import audit as _audit_module
from . import compiler as _compiler_module
from .hardening import assess_claims_hardened

_compiler_module.assess_claims = assess_claims_hardened
_audit_module.assess_claims = assess_claims_hardened

from .evidence_graph import (
    BUNDLE_SCHEMA,
    NODE_TYPES,
    RELATIONS,
    audit_evidence_graph,
    compile_evidence_graph,
)

__all__ = [
    "BUNDLE_SCHEMA",
    "NODE_TYPES",
    "RELATIONS",
    "audit_evidence_graph",
    "compile_evidence_graph",
]

__version__ = "0.6.1"
