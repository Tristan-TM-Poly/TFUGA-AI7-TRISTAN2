"""Packaged documentation index for Omega absorb v1.6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class DocumentationEntry:
    title: str
    path: str
    version: str


@dataclass(frozen=True)
class DocumentationIndex:
    entries: Tuple[DocumentationEntry, ...]
    next_action: str


def build_documentation_index() -> DocumentationIndex:
    entries = tuple(
        DocumentationEntry(
            title=f"Omega absorb v{version}",
            path=f"docs/omega-prof-poly/ABSORB_POLY_PROF_V{version.replace('.', '_')}.md",
            version=version,
        )
        for version in ("0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6")
    )
    return DocumentationIndex(entries=entries, next_action="render_documentation_index")


def render_documentation_index() -> str:
    index = build_documentation_index()
    lines = ["# Omega Absorb Documentation Index", "", "| Version | Title | Path |", "|---|---|---|"]
    for entry in index.entries:
        lines.append(f"| {entry.version} | {entry.title} | `{entry.path}` |")
    return "\n".join(lines) + "\n"
