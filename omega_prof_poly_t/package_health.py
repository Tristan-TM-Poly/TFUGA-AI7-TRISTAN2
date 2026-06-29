"""Package health score for Omega absorb v1.9."""

from __future__ import annotations

from dataclasses import dataclass

from .documentation_index import build_documentation_index
from .package_status import build_package_status_report
from .source_selection import available_demo_sources
from .version_manifest import build_version_manifest


@dataclass(frozen=True)
class PackageHealthReport:
    version: str
    score: float
    version_count: int
    doc_count: int
    cli_command_count: int
    source_count: int
    missing_items: tuple[str, ...]
    markdown: str
    next_action: str


def build_package_health_report() -> PackageHealthReport:
    manifest = build_version_manifest()
    docs = build_documentation_index()
    status = build_package_status_report()
    missing = []
    if len(available_demo_sources()) < 3:
        missing.append("demo_sources")
    if len(status.cli_commands) < 40:
        missing.append("cli_surface")
    if len(docs.entries) < 17:
        missing.append("doc_lineage")
    score = round(min(1.0, 0.25 + 0.018 * len(status.cli_commands) + 0.02 * len(docs.entries) + 0.02 * len(manifest.entries) - 0.05 * len(missing)), 4)
    lines = ["# Omega Absorb Health", "", f"score: {score:.4f}", f"versions: {len(manifest.entries)}", f"docs: {len(docs.entries)}", f"cli commands: {len(status.cli_commands)}", f"sources: {len(available_demo_sources())}", "", "## Missing"]
    lines.extend(f"- {item}" for item in (missing or ["none"]))
    return PackageHealthReport("1.9.0", score, len(manifest.entries), len(docs.entries), len(status.cli_commands), len(available_demo_sources()), tuple(missing), "\n".join(lines).strip() + "\n", "use_health_report_to_prioritize_next_release")
