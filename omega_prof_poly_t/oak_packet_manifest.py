"""OAK packet manifest for Omega absorb v1.5."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .json_exports import packet_digest, to_deterministic_json
from .next_actions_engine import NextAction


@dataclass(frozen=True)
class OAKPacketEntry:
    packet_id: str
    kind: str
    source: str
    score: float
    digest: str
    next_action: str


@dataclass(frozen=True)
class OAKPacketManifest:
    version: str
    entries: Tuple[OAKPacketEntry, ...]
    manifest_json: str
    next_action: str


def build_oak_packet_manifest(actions: Iterable[NextAction], version: str = "1.5.0") -> OAKPacketManifest:
    entries = []
    for action in actions:
        payload = {
            "rank": action.rank,
            "action": action.action,
            "source": action.source,
            "score": action.score,
            "packet_type": action.packet_type,
        }
        entries.append(
            OAKPacketEntry(
                packet_id=f"oak-{action.rank}-{action.packet_type}",
                kind=action.packet_type,
                source=action.source,
                score=action.score,
                digest=packet_digest(payload),
                next_action="route_packet_to_local_artifact",
            )
        )
    manifest_json = to_deterministic_json({"version": version, "entries": [entry.__dict__ for entry in entries]})
    return OAKPacketManifest(
        version=version,
        entries=tuple(entries),
        manifest_json=manifest_json,
        next_action="store_oak_packet_manifest",
    )
