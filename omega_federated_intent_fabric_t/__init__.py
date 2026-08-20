"""Ω-FEDERATED-INTENT-FABRIC-T∞ R0.1.

Bounded cross-source intent normalization built to reuse the repository's existing
intent/capability stack. Source records never confer execution authority.
"""

from .model import (
    AuthorityLevel,
    IntentKind,
    RelationKind,
    SourceEnvelope,
    SourceKind,
    SourceVisibility,
    StructuredIntent,
)
from .compiler import FederatedIntentCompiler, FederatedIntentReceipt

__all__ = [
    "AuthorityLevel",
    "FederatedIntentCompiler",
    "FederatedIntentReceipt",
    "IntentKind",
    "RelationKind",
    "SourceEnvelope",
    "SourceKind",
    "SourceVisibility",
    "StructuredIntent",
]
