"""Action packet writer for Omega absorb v1.6."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

from .next_actions_engine import NextAction
from .oak_packet_manifest import build_oak_packet_manifest


@dataclass(frozen=True)
class WrittenActionPacket:
    path: str
    packet_type: str
    rank: int


@dataclass(frozen=True)
class ActionPacketWriteResult:
    files: Tuple[WrittenActionPacket, ...]
    manifest_path: str
    next_action: str


def render_action_packet(action: NextAction) -> str:
    return (
        f"# Action {action.rank}: {action.action}\n\n"
        f"- source: {action.source}\n"
        f"- score: {action.score:.4f}\n"
        f"- packet type: {action.packet_type}\n"
        "- why: selected by the local top-actions engine\n"
        "- evidence: public/demo metadata route\n"
        "- risks: verify assumptions and missing evidence fields\n"
        "- next local command: omega-absorb oak-manifest --source combined\n"
    )


def write_action_packets(actions: Iterable[NextAction], output_dir: str | Path = "generated/omega_absorb_poly_prof_v16/actions") -> ActionPacketWriteResult:
    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)
    actions_tuple = tuple(actions)
    files = []
    for action in actions_tuple:
        safe_type = action.packet_type.replace("/", "_").replace(" ", "_")
        path = base / f"action_{action.rank:03d}_{safe_type}.md"
        path.write_text(render_action_packet(action), encoding="utf-8")
        files.append(WrittenActionPacket(str(path), action.packet_type, action.rank))
    manifest = build_oak_packet_manifest(actions_tuple, version="1.6.0")
    manifest_path = base / "oak_packet_manifest.json"
    manifest_path.write_text(manifest.manifest_json, encoding="utf-8")
    return ActionPacketWriteResult(tuple(files), str(manifest_path), "action_packets_written")
