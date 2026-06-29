"""OAK packet manifest plus for Omega absorb v1.8."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .evidence_risk_counter import EvidenceRiskCount
from .json_exports import packet_digest, to_deterministic_json
from .next_actions_engine import NextAction


@dataclass(frozen=True)
class OAKPacketPlusEntry:
    packet_id: str
    kind: str
    source_id: str
    adapter: str
    policy_status: str
    evidence_count: int
    risk_count: int
    digest: str
    parent_packet: str
    next_action: str


@dataclass(frozen=True)
class OAKPacketManifestPlus:
    version: str
    lineage: Tuple[str, ...]
    packets: Tuple[OAKPacketPlusEntry, ...]
    manifest_json: str
    next_action: str


def build_oak_packet_manifest_plus(
    actions: Iterable[NextAction],
    counts: EvidenceRiskCount,
    source_id: str = "combined",
    adapter: str = "demo_adapter",
    policy_status: str = "allow_with_warnings",
    version: str = "1.8.0",
) -> OAKPacketManifestPlus:
    entries = []
    lineage = ("source", "adapter", "policy", "atom", "action")
    for action in actions:
        payload = {
            "rank": action.rank,
            "action": action.action,
            "source_id": source_id,
            "adapter": adapter,
            "policy_status": policy_status,
            "packet_type": action.packet_type,
        }
        entries.append(
            OAKPacketPlusEntry(
                packet_id=f"oak-plus-{action.rank}-{action.packet_type}",
                kind=action.packet_type,
                source_id=source_id,
                adapter=adapter,
                policy_status=policy_status,
                evidence_count=counts.evidence_count,
                risk_count=counts.risk_count,
                digest=packet_digest(payload),
                parent_packet=f"oak-{action.rank}-{action.packet_type}",
                next_action="route_packet_to_lineage_ledger",
            )
        )
    manifest_json = to_deterministic_json({"version": version, "lineage": lineage, "packets": [entry.__dict__ for entry in entries]})
    return OAKPacketManifestPlus(version, lineage, tuple(entries), manifest_json, "store_oak_manifest_plus")
