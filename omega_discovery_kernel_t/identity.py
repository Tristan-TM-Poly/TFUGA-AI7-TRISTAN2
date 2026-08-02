"""Universal content-addressed identities for cross-module discovery objects.

The identity layer connects repository theory nodes, knowledge cells, claims,
MorphIR objects, experiments, results, datasets, commits, products, and IP
records without pretending that aliases imply semantic equivalence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
import re
from typing import Any, Iterable, Mapping, Sequence


_KIND_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")
_VERSION_PATTERN = re.compile(r"^[0-9]+(?:\.[0-9]+){0,3}(?:[-+][A-Za-z0-9._-]+)?$")


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def content_digest(value: object) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def normalize_kind(kind: str) -> str:
    normalized = re.sub(r"[^a-z0-9_-]+", "-", kind.strip().casefold()).strip("-")
    if not _KIND_PATTERN.match(normalized):
        raise ValueError(f"Invalid identity kind: {kind!r}")
    return normalized


def normalize_version(version: str) -> str:
    normalized = version.strip()
    if not _VERSION_PATTERN.match(normalized):
        raise ValueError(f"Invalid semantic-ish version: {version!r}")
    return normalized


@dataclass(frozen=True, slots=True)
class AliasRecord:
    value: str
    relation: str = "probable_alias"
    source: str | None = None
    confidence: float | None = None

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.value.strip():
            issues.append("alias value is required")
        if self.relation not in {
            "exact_alias",
            "probable_alias",
            "historical_name",
            "abbreviation",
            "translation",
            "overlap",
            "specialization",
            "generalization",
            "not_equivalent",
        }:
            issues.append(f"unsupported alias relation: {self.relation}")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            issues.append("alias confidence must be in [0, 1]")
        return issues

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class UniversalIdentity:
    universal_id: str
    kind: str
    namespace: str
    local_id: str
    version: str
    content_hash: str
    parent_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    supersedes: tuple[str, ...] = ()
    aliases: tuple[AliasRecord, ...] = ()
    repository_commit: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    oak_status: str = "IDEA"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        kind: str,
        namespace: str,
        local_id: str,
        version: str,
        content: object,
        parent_ids: Sequence[str] = (),
        source_ids: Sequence[str] = (),
        supersedes: Sequence[str] = (),
        aliases: Sequence[AliasRecord] = (),
        repository_commit: str | None = None,
        valid_from: str | None = None,
        valid_until: str | None = None,
        oak_status: str = "IDEA",
        metadata: Mapping[str, Any] | None = None,
    ) -> "UniversalIdentity":
        normalized_kind = normalize_kind(kind)
        normalized_namespace = namespace.strip().casefold()
        normalized_local_id = local_id.strip()
        normalized_version = normalize_version(version)
        if not normalized_namespace:
            raise ValueError("namespace is required")
        if not normalized_local_id:
            raise ValueError("local_id is required")
        digest = content_digest(content)
        raw_identity = {
            "kind": normalized_kind,
            "namespace": normalized_namespace,
            "local_id": normalized_local_id,
            "version": normalized_version,
            "content_hash": digest,
        }
        short = content_digest(raw_identity)[:28]
        universal_id = f"urn:omega:{normalized_namespace}:{normalized_kind}:{normalized_local_id}:{normalized_version}:{short}"
        identity = cls(
            universal_id=universal_id,
            kind=normalized_kind,
            namespace=normalized_namespace,
            local_id=normalized_local_id,
            version=normalized_version,
            content_hash=digest,
            parent_ids=tuple(parent_ids),
            source_ids=tuple(source_ids),
            supersedes=tuple(supersedes),
            aliases=tuple(aliases),
            repository_commit=repository_commit,
            valid_from=valid_from,
            valid_until=valid_until,
            oak_status=oak_status,
            metadata=dict(metadata or {}),
        )
        issues = identity.validate()
        if issues:
            raise ValueError("; ".join(issues))
        return identity

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "UniversalIdentity":
        aliases = tuple(AliasRecord(**item) for item in value.get("aliases", ()))
        return cls(
            universal_id=str(value["universal_id"]),
            kind=str(value["kind"]),
            namespace=str(value["namespace"]),
            local_id=str(value["local_id"]),
            version=str(value["version"]),
            content_hash=str(value["content_hash"]),
            parent_ids=tuple(value.get("parent_ids", ())),
            source_ids=tuple(value.get("source_ids", ())),
            supersedes=tuple(value.get("supersedes", ())),
            aliases=aliases,
            repository_commit=value.get("repository_commit"),
            valid_from=value.get("valid_from"),
            valid_until=value.get("valid_until"),
            oak_status=str(value.get("oak_status", "IDEA")),
            metadata=dict(value.get("metadata", {})),
        )

    def validate(self) -> list[str]:
        issues: list[str] = []
        try:
            normalized_kind = normalize_kind(self.kind)
        except ValueError as exc:
            issues.append(str(exc))
            normalized_kind = self.kind
        try:
            normalized_version = normalize_version(self.version)
        except ValueError as exc:
            issues.append(str(exc))
            normalized_version = self.version
        if len(self.content_hash) != 64 or any(char not in "0123456789abcdef" for char in self.content_hash):
            issues.append("content_hash must be a lowercase SHA-256 hex digest")
        if not self.namespace.strip():
            issues.append("namespace is required")
        if not self.local_id.strip():
            issues.append("local_id is required")
        expected_prefix = (
            f"urn:omega:{self.namespace.strip().casefold()}:{normalized_kind}:"
            f"{self.local_id.strip()}:{normalized_version}:"
        )
        if not self.universal_id.startswith(expected_prefix):
            issues.append("universal_id prefix does not match identity fields")
        if len(set(self.parent_ids)) != len(self.parent_ids):
            issues.append("parent_ids contain duplicates")
        if len(set(self.source_ids)) != len(self.source_ids):
            issues.append("source_ids contain duplicates")
        if self.universal_id in self.parent_ids or self.universal_id in self.supersedes:
            issues.append("identity cannot parent or supersede itself")
        for alias in self.aliases:
            issues.extend(alias.validate())
        return issues

    def verify_content(self, content: object) -> bool:
        return content_digest(content) == self.content_hash

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["aliases"] = [alias.to_dict() for alias in self.aliases]
        return value

    def with_revision(
        self,
        *,
        version: str,
        content: object,
        repository_commit: str | None = None,
        oak_status: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "UniversalIdentity":
        return UniversalIdentity.create(
            kind=self.kind,
            namespace=self.namespace,
            local_id=self.local_id,
            version=version,
            content=content,
            parent_ids=(self.universal_id,),
            source_ids=self.source_ids,
            supersedes=(self.universal_id,),
            aliases=self.aliases,
            repository_commit=repository_commit,
            valid_from=self.valid_until,
            oak_status=oak_status or self.oak_status,
            metadata={**dict(self.metadata), **dict(metadata or {})},
        )


class IdentityRegistry:
    """In-memory identity registry used by compilers and tests.

    Persistent frontiers use the SQLite-backed registry in ``streaming.py``.
    """

    def __init__(self) -> None:
        self._by_id: dict[str, UniversalIdentity] = {}
        self._by_local: dict[tuple[str, str, str], list[str]] = {}
        self._by_hash: dict[str, list[str]] = {}

    def add(self, identity: UniversalIdentity) -> UniversalIdentity:
        issues = identity.validate()
        if issues:
            raise ValueError("; ".join(issues))
        if identity.universal_id in self._by_id:
            raise ValueError(f"duplicate universal_id: {identity.universal_id}")
        key = (identity.namespace, identity.kind, identity.local_id)
        self._by_id[identity.universal_id] = identity
        self._by_local.setdefault(key, []).append(identity.universal_id)
        self._by_hash.setdefault(identity.content_hash, []).append(identity.universal_id)
        return identity

    def get(self, universal_id: str) -> UniversalIdentity:
        try:
            return self._by_id[universal_id]
        except KeyError as exc:
            raise KeyError(f"unknown universal identity: {universal_id}") from exc

    def revisions(self, namespace: str, kind: str, local_id: str) -> tuple[UniversalIdentity, ...]:
        key = (namespace.strip().casefold(), normalize_kind(kind), local_id.strip())
        return tuple(self._by_id[item] for item in self._by_local.get(key, ()))

    def by_content_hash(self, digest: str) -> tuple[UniversalIdentity, ...]:
        return tuple(self._by_id[item] for item in self._by_hash.get(digest, ()))

    def validate_links(self) -> list[str]:
        issues: list[str] = []
        known = set(self._by_id)
        for identity in self._by_id.values():
            for relation, targets in (
                ("parent", identity.parent_ids),
                ("source", identity.source_ids),
                ("supersedes", identity.supersedes),
            ):
                for target in targets:
                    if target not in known:
                        issues.append(f"{identity.universal_id}: unknown {relation} identity {target}")
        return sorted(issues)

    def manifest(self) -> dict[str, object]:
        return {
            "schema": "omega_discovery_kernel.identity_registry.v0.2",
            "identity_count": len(self._by_id),
            "unique_content_hashes": len(self._by_hash),
            "revision_families": len(self._by_local),
            "link_findings": self.validate_links(),
            "identities": [self._by_id[key].to_dict() for key in sorted(self._by_id)],
            "oak_boundary": "Identity equality is not semantic equivalence or scientific validation.",
        }
