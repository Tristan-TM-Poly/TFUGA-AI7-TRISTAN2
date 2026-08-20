"""Ω-FEDERATED-INTENT-FABRIC-T∞ R0.2.

Bounded cross-source intent normalization, exact duplicate compression and closure
selection built to reuse the repository's existing intent/capability stack. Source
records and generated closure plans never confer execution authority.
"""

from .bridge import to_capability_input, to_existing_intent, to_existing_intent_seed
from .closure import (
    ClosureObligation,
    EigenIntent,
    IntentClosureCompiler,
    IntentClosureReceipt,
    MinimalUnlockSet,
)
from .compiler import FederatedIntentCompiler, FederatedIntentReceipt
from .model import (
    AuthorityLevel,
    IntentKind,
    RelationHint,
    RelationKind,
    SourceAvailability,
    SourceEnvelope,
    SourceKind,
    SourceVisibility,
    StructuredIntent,
)

__all__ = [
    "AuthorityLevel",
    "ClosureObligation",
    "EigenIntent",
    "FederatedIntentCompiler",
    "FederatedIntentReceipt",
    "IntentClosureCompiler",
    "IntentClosureReceipt",
    "IntentKind",
    "MinimalUnlockSet",
    "RelationHint",
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
