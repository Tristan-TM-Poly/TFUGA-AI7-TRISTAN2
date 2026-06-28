"""Version manifest for Omega absorb v1.3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class VersionEntry:
    version: str
    title: str
    modules: Tuple[str, ...]
    status: str


@dataclass(frozen=True)
class VersionManifest:
    release: str
    entries: Tuple[VersionEntry, ...]
    next_action: str


def build_version_manifest() -> VersionManifest:
    return VersionManifest(
        release="1.3.0",
        entries=(
            VersionEntry("0.3", "public research atoms", ("research_atom", "professor_genome", "poly_research_twin"), "merged"),
            VersionEntry("0.4", "claim and method graph compiler", ("claim_graph", "method_graph", "research_opportunity_compiler"), "merged"),
            VersionEntry("0.5", "opportunity ranking and reports", ("opportunity_ranker", "professor_backlog_report"), "merged"),
            VersionEntry("0.6", "artifact and graph exports", ("generated_report_artifacts", "graph_exports", "portfolio_optimizer"), "merged"),
            VersionEntry("0.7", "generated fixtures and graph upgrades", ("artifact_summaries", "enriched_graph_exports"), "merged"),
            VersionEntry("0.8", "source registry and bridge scoring", ("public_source_registry", "department_bridge_scoring"), "merged"),
            VersionEntry("0.9", "validation and roadmap pipeline", ("source_record_validation", "roadmap_compiler", "e2e_pipeline_v09"), "merged"),
            VersionEntry("1.0", "stable local CLI and release bundle", ("cli", "version_manifest", "release_bundle"), "merged"),
            VersionEntry("1.1", "CLI exports and documentation index", ("export_commands", "documentation_index", "release_bundle_writer"), "merged"),
            VersionEntry("1.2", "source selection and GraphML exports", ("source_selection", "package_status", "export_commands"), "merged"),
            VersionEntry("1.3", "local JSON input, compact tables, bundles, health and changelog", ("local_json_loader", "compact_table_report", "export_bundle", "package_health", "changelog_generator"), "current"),
        ),
        next_action="publish_release_notes_packet",
    )
