"""Package status report for Omega absorb v1.8."""

from __future__ import annotations

from dataclasses import dataclass

from .documentation_index import build_documentation_index
from .source_selection import available_demo_sources
from .version_manifest import build_version_manifest


COMMANDS = (
    "version", "demo", "roadmap", "summary-json", "validation-json", "graph-json", "graphml", "docs-index", "status", "sources", "write-bundle", "ingest-json", "table", "export-bundle", "health", "changelog", "schema-check", "claim-oak", "method-packets", "mminus", "github-packet", "tensor", "twin-v2", "bridge-opt", "next-actions", "oak-manifest", "route-source", "policy-check", "ingest-json-v2", "write-actions", "github-bundle", "tensor-weights", "twin-answer", "department-matrix", "route-dashboard", "evidence-risk", "oak-manifest-plus", "oak-lineage", "mminus-apply", "oak-ledger",
)


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
    lines = ["# Omega Absorb Package Status", "", "Version: 1.8.0", f"Manifest entries: {len(manifest.entries)}", f"Documentation entries: {len(docs.entries)}", f"Demo sources: {', '.join(available_demo_sources())}", "", "## CLI commands"]
    lines.extend(f"- {command}" for command in COMMANDS)
    return PackageStatusReport("1.8.0", len(manifest.entries), len(docs.entries), len(available_demo_sources()), COMMANDS, "\n".join(lines).strip() + "\n", "store_package_status_report")
