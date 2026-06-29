"""Report atlas for Omega absorb v1.9."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ReportAtlasEntry:
    name: str
    path: str
    kind: str
    command: str
    next_action: str


@dataclass(frozen=True)
class ReportAtlas:
    entries: Tuple[ReportAtlasEntry, ...]
    next_action: str


def build_report_atlas() -> ReportAtlas:
    entries = (
        ReportAtlasEntry("status", "status.md", "markdown", "omega-absorb status", "write_report"),
        ReportAtlasEntry("health", "health.md", "markdown", "omega-absorb health", "write_report"),
        ReportAtlasEntry("changelog", "changelog.md", "markdown", "omega-absorb changelog-plus", "write_report"),
        ReportAtlasEntry("compact-table", "compact_table.md", "markdown", "omega-absorb table", "write_report"),
        ReportAtlasEntry("graphml", "graph.graphml", "graphml", "omega-absorb graphml", "write_report"),
        ReportAtlasEntry("oak-ledger", "oak_ledger.md", "markdown", "omega-absorb oak-ledger", "write_report"),
        ReportAtlasEntry("mminus", "mminus.md", "markdown", "omega-absorb mminus", "write_report"),
        ReportAtlasEntry("next-actions", "next_actions.md", "markdown", "omega-absorb next-actions", "write_report"),
    )
    return ReportAtlas(entries=entries, next_action="write_report_atlas")


def render_report_atlas(atlas: ReportAtlas | None = None) -> str:
    atlas = atlas or build_report_atlas()
    lines = ["# Omega Absorb Report Atlas", "", "name | kind | path | command", "--- | --- | --- | ---"]
    for entry in atlas.entries:
        lines.append(f"{entry.name} | {entry.kind} | {entry.path} | `{entry.command}`")
    return "\n".join(lines) + "\n"
