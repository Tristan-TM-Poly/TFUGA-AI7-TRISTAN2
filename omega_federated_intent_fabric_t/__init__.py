"""Ω-FEDERATED-INTENT-FABRIC-T∞ R0.1.

Bounded cross-source intent normalization built to reuse the repository's existing
intent/capability stack. Source records never confer execution authority.
"""

from .bridge import to_capability_input, to_existing_intent, to_existing_intent_seed
from .compiler import FederatedIntentCompiler, FederatedIntentReceipt
from .model import (
    AuthorityLevel,
    IntentKind,
    RelationKind,
    SourceAvailability,
    SourceEnvelope,
    SourceKind,
    SourceVisibility,
    StructuredIntent,
)

__all__ = [
    "AuthorityLevel",
    "FederatedIntentCompiler",
    "FederatedIntentReceipt",
    "IntentKind",
    "RelationKind",
    "SourceAvailability",
    "SourceEnvelope",
    "SourceKind",
    "SourceVisibility",
    "StructuredIntent",
    "to_capability_input",
    "to_existing_intent",
    "to_existing_intent_seed",
]
