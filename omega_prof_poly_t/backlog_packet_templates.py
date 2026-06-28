"""Local backlog packet templates for Omega absorb v0.6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .portfolio_optimizer import PortfolioSelection


@dataclass(frozen=True)
class BacklogPacket:
    title: str
    body: str
    labels: Tuple[str, ...]
    next_action: str


def render_backlog_packet(selection: PortfolioSelection) -> BacklogPacket:
    lines = [
        "# Omega Absorb Portfolio Backlog",
        "",
        f"Objective: {selection.objective}",
        "",
        "## Selected items",
    ]
    for item in selection.selected:
        lines.append(f"- #{item.rank} {item.atom_id} score={item.score:.4f} path={item.recommended_path}")
    lines.extend(["", "## Skipped items"])
    for item in selection.skipped[:20]:
        lines.append(f"- #{item.rank} {item.atom_id} score={item.score:.4f} path={item.recommended_path}")
    lines.extend(["", "## Next action", selection.next_action])
    return BacklogPacket(
        title="Omega Absorb Portfolio Backlog",
        body="\n".join(lines).strip() + "\n",
        labels=("omega-absorb", "portfolio", "zero-touch"),
        next_action="store_backlog_packet",
    )
