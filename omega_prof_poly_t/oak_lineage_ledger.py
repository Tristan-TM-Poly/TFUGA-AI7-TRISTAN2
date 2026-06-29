"""OAK lineage ledger for Omega absorb v1.8."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .oak_packet_manifest_plus import OAKPacketManifestPlus


@dataclass(frozen=True)
class OAKLineageEntry:
    packet_id: str
    lineage: Tuple[str, ...]
    digest: str
    next_action: str


@dataclass(frozen=True)
class OAKLineageLedger:
    entries: Tuple[OAKLineageEntry, ...]
    next_action: str


def build_oak_lineage_ledger(manifest: OAKPacketManifestPlus) -> OAKLineageLedger:
    entries = tuple(
        OAKLineageEntry(
            packet_id=packet.packet_id,
            lineage=manifest.lineage,
            digest=packet.digest,
            next_action="inspect_or_store_lineage_entry",
        )
        for packet in manifest.packets
    )
    return OAKLineageLedger(entries, "render_or_write_lineage_ledger")


def render_oak_lineage_ledger(ledger: OAKLineageLedger) -> str:
    lines = ["packet_id | lineage | digest", "--- | --- | ---"]
    for entry in ledger.entries:
        lines.append(f"{entry.packet_id} | {' -> '.join(entry.lineage)} | {entry.digest}")
    return "\n".join(lines) + "\n"
