"""Package status report for Omega absorb v1.4."""

from __future__ import annotations

from dataclasses import dataclass

from .documentation_index import build_documentation_index
from .source_selection import available_demo_sources
from .version_manifest import build_version_manifest


@dataclass(frozen=True)
class PackageStatusReport:
    version: str
    version_count: int
    document_count: int
    source_count: int
    cli_commands: tuple[str, ...]
    markdown: str
    next_action: str


def build_package_status_report() -> PackageStatusReport:
    manifest = build_version_manifest()
    docs = build_documentation_index()
    commands = (
        "version", "demo", "roadmap", "summary-json", "validation-json", "graph-json", "graphml", "docs-index", "status", "sources", "write-bundle", "ingest-json", "table", "export-bundle", "health", "changelog", "schema-check", "claim-oak", "method-packets", "mminus", "github-packet",
    )
    lines = [
        "# Omega Absorb Package Status",
        "",
        "Version: 1.4.0",
        f"Manifest entries: {len(manifest.entries)}",
        f"Documentation entries: {len(docs.entries)}",
        f"Demo sources: {', '.join(available_demo_sources())}",
        "",
        "## CLI commands",
    ]
    lines.extend(f"- {command}" for command in commands)
    return PackageStatusReport(
        version="1.4.0",
        version_count=len(manifest.entries),
        document_count=len(docs.entries),
        source_count=len(available_demo_sources()),
        cli_commands=commands,
        markdown="\n".join(lines).strip() + "\n",
        next_action="store_package_status_report",
    )
