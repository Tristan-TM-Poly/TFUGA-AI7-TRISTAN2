from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from typing import Iterable, Mapping, Tuple


class SourceKind(str, Enum):
    GITHUB = "github"
    GOOGLE_DRIVE = "google_drive"
    DROPBOX = "dropbox"
    OPENAI_TOOL = "openai_tool"
    OTHER = "other"


class SourceVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


class SourceAvailability(str, Enum):
    PRESENT = "present"
    EMPTY = "empty"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class AuthorityLevel(str, Enum):
    EVIDENCE_ONLY = "evidence_only"
    READ = "read"
    DRAFT = "draft"
    WRITE = "write"
    IRREVERSIBLE = "irreversible"


class IntentKind(str, Enum):
    EXPLICIT = "explicit"
    DERIVED = "derived"
    VERIFICATION = "verification"
    RESIDUAL = "residual"
    COUNTER = "counter"
    NEGATIVE = "negative"
    REGENERATIVE = "regenerative"


class RelationKind(str, Enum):
    AGREE = "agree"
    CONFLICT = "conflict"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    DUPLICATE = "duplicate"
    IMPLEMENTATION_GAP = "implementation_gap"
    DOCUMENTATION_GAP = "documentation_gap"
    EVIDENCE_GAP = "evidence_gap"
    REALITY_GAP = "reality_gap"
    HARVEST_GAP = "harvest_gap"


def _canon_text(value: str) -> str:
    return " ".join(value.strip().split())


def _canon_many(values: Iterable[str]) -> Tuple[str, ...]:
    return tuple(_canon_text(v) for v in values if _canon_text(v))


def _canon_metadata(metadata: Mapping[str, str] | None) -> Tuple[Tuple[str, str], ...]:
    if not metadata:
        return ()
    return tuple(sorted((str(k), _canon_text(str(v))) for k, v in metadata.items()))


@dataclass(frozen=True)
class SourceEnvelope:
    source_kind: SourceKind
    source_id: str
    fingerprint: str
    observed_at: str
    visibility: SourceVisibility = SourceVisibility.UNKNOWN
    availability: SourceAvailability = SourceAvailability.PRESENT
    authority: AuthorityLevel = AuthorityLevel.EVIDENCE_ONLY
    provenance: Tuple[str, ...] = field(default_factory=tuple)
    claims: Tuple[str, ...] = field(default_factory=tuple)
    explicit_intents: Tuple[str, ...] = field(default_factory=tuple)
    residuals: Tuple[str, ...] = field(default_factory=tuple)
    prohibitions: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        source_id = _canon_text(self.source_id)
        fingerprint = _canon_text(self.fingerprint)
        observed_at = _canon_text(self.observed_at)
        if not source_id:
            raise ValueError("source_id must be non-empty")
        if not fingerprint:
            raise ValueError("fingerprint must be non-empty")
        if not observed_at:
            raise ValueError("observed_at must be non-empty")
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "fingerprint", fingerprint)
        object.__setattr__(self, "observed_at", observed_at)
        object.__setattr__(self, "provenance", _canon_many(self.provenance))
        object.__setattr__(self, "claims", _canon_many(self.claims))
        object.__setattr__(self, "explicit_intents", _canon_many(self.explicit_intents))
        object.__setattr__(self, "residuals", _canon_many(self.residuals))
        object.__setattr__(self, "prohibitions", _canon_many(self.prohibitions))
        object.__setattr__(self, "metadata", tuple(sorted(self.metadata)))

    @classmethod
    def build(
        cls,
        *,
        source_kind: SourceKind,
        source_id: str,
        fingerprint: str,
        observed_at: str,
        visibility: SourceVisibility = SourceVisibility.UNKNOWN,
        availability: SourceAvailability = SourceAvailability.PRESENT,
        authority: AuthorityLevel = AuthorityLevel.EVIDENCE_ONLY,
        provenance: Iterable[str] = (),
        claims: Iterable[str] = (),
        explicit_intents: Iterable[str] = (),
        residuals: Iterable[str] = (),
        prohibitions: Iterable[str] = (),
        metadata: Mapping[str, str] | None = None,
    ) -> "SourceEnvelope":
        return cls(
            source_kind=source_kind,
            source_id=source_id,
            fingerprint=fingerprint,
            observed_at=observed_at,
            visibility=visibility,
            availability=availability,
            authority=authority,
            provenance=_canon_many(provenance),
            claims=_canon_many(claims),
            explicit_intents=_canon_many(explicit_intents),
            residuals=_canon_many(residuals),
            prohibitions=_canon_many(prohibitions),
            metadata=_canon_metadata(metadata),
        )

    @property
    def envelope_id(self) -> str:
        payload = "|".join(
            (
                self.source_kind.value,
                self.source_id,
                self.fingerprint,
                self.observed_at,
                self.visibility.value,
                self.availability.value,
            )
        )
        return "src_" + sha256(payload.encode("utf-8")).hexdigest()[:20]


@dataclass(frozen=True)
class StructuredIntent:
    intent_id: str
    kind: IntentKind
    text: str
    source_envelope_ids: Tuple[str, ...]
    evidence_refs: Tuple[str, ...]
    status: str = "PROPOSED"
    action_authorized: bool = False

    def __post_init__(self) -> None:
        if self.action_authorized:
            raise ValueError("R0.1 generated intents cannot authorize actions")
        if self.status != "PROPOSED":
            raise ValueError("R0.1 generated intents must remain PROPOSED")


@dataclass(frozen=True)
class IntentRelation:
    relation_id: str
    kind: RelationKind
    intent_ids: Tuple[str, ...]
    evidence_refs: Tuple[str, ...]
    inferred: bool

    def __post_init__(self) -> None:
        if len(self.intent_ids) < 2:
            raise ValueError("intent relation needs at least two intents")


@dataclass(frozen=True)
class RelationHint:
    kind: RelationKind
    intent_ids: Tuple[str, ...]
    evidence_refs: Tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def build(
        cls,
        *,
        kind: RelationKind,
        intent_ids: Iterable[str],
        evidence_refs: Iterable[str] = (),
    ) -> "RelationHint":
        return cls(kind=kind, intent_ids=tuple(intent_ids), evidence_refs=_canon_many(evidence_refs))
