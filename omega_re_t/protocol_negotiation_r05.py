"""Capability-bound protocol negotiation with downgrade evidence."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable


def _digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, order=True)
class ProtocolVersion:
    rank: int
    version: str
    capabilities: frozenset[str]
    deprecated: bool = False
    experimental: bool = False

    def __post_init__(self) -> None:
        if self.rank < 0 or not self.version.strip():
            raise ValueError("invalid version")
        if not self.capabilities:
            raise ValueError("capabilities cannot be empty")


@dataclass(frozen=True)
class NegotiationPolicy:
    minimum_rank: int = 0
    required_capabilities: frozenset[str] = frozenset()
    allow_deprecated: bool = False
    allow_experimental: bool = False
    prevent_downgrade_from_rank: int | None = None


@dataclass(frozen=True)
class NegotiationTranscript:
    selected_version: str | None
    selected_rank: int | None
    mutual_versions: tuple[str, ...]
    rejected: tuple[tuple[str, str], ...]
    downgrade_blocked: bool
    transcript_digest: str
    claim: str = "declared_protocol_compatibility_only"


def negotiate(
    client: Iterable[ProtocolVersion],
    server: Iterable[ProtocolVersion],
    *,
    policy: NegotiationPolicy = NegotiationPolicy(),
) -> NegotiationTranscript:
    client_map = {item.version: item for item in client}
    server_map = {item.version: item for item in server}
    mutual = sorted(set(client_map) & set(server_map), key=lambda version: client_map[version].rank, reverse=True)
    rejected: list[tuple[str, str]] = []
    selected: ProtocolVersion | None = None
    downgrade_blocked = False
    for version in mutual:
        left = client_map[version]
        right = server_map[version]
        rank = min(left.rank, right.rank)
        capabilities = left.capabilities & right.capabilities
        if rank < policy.minimum_rank:
            rejected.append((version, "below_minimum_rank"))
            continue
        if policy.prevent_downgrade_from_rank is not None and rank < policy.prevent_downgrade_from_rank:
            rejected.append((version, "downgrade_blocked"))
            downgrade_blocked = True
            continue
        if not policy.required_capabilities <= capabilities:
            rejected.append((version, "missing_required_capability"))
            continue
        if (left.deprecated or right.deprecated) and not policy.allow_deprecated:
            rejected.append((version, "deprecated"))
            continue
        if (left.experimental or right.experimental) and not policy.allow_experimental:
            rejected.append((version, "experimental"))
            continue
        selected = ProtocolVersion(
            rank=rank,
            version=version,
            capabilities=frozenset(capabilities),
            deprecated=left.deprecated or right.deprecated,
            experimental=left.experimental or right.experimental,
        )
        break
    payload = {
        "selected": (
            {
                "rank": selected.rank,
                "version": selected.version,
                "capabilities": sorted(selected.capabilities),
                "deprecated": selected.deprecated,
                "experimental": selected.experimental,
            }
            if selected
            else None
        ),
        "mutual": mutual,
        "rejected": sorted(rejected),
        "policy": {
            "minimum_rank": policy.minimum_rank,
            "required_capabilities": sorted(policy.required_capabilities),
            "allow_deprecated": policy.allow_deprecated,
            "allow_experimental": policy.allow_experimental,
            "prevent_downgrade_from_rank": policy.prevent_downgrade_from_rank,
        },
    }
    return NegotiationTranscript(
        selected_version=selected.version if selected else None,
        selected_rank=selected.rank if selected else None,
        mutual_versions=tuple(mutual),
        rejected=tuple(rejected),
        downgrade_blocked=downgrade_blocked,
        transcript_digest=_digest(payload),
    )
