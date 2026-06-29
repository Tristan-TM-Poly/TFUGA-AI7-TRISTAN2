"""Release intelligence for Omega absorb v1.9."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .package_status import build_package_status_report
from .version_manifest import build_version_manifest


@dataclass(frozen=True)
class ReleaseIntelligence:
    release: str
    command_count: int
    version_count: int
    strengths: Tuple[str, ...]
    risks: Tuple[str, ...]
    next_targets: Tuple[str, ...]
    next_action: str


def build_release_intelligence() -> ReleaseIntelligence:
    status = build_package_status_report()
    manifest = build_version_manifest()
    strengths = ("local_cli_surface", "oak_ledgers", "report_generation", "version_lineage")
    risks = ("tests_not_executed_in_connector", "demo_metadata_scope", "needs_ci_workflow")
    targets = ("v2_package_layout", "ci_execution", "artifact_bundle_contract", "source_policy_expansion")
    return ReleaseIntelligence(manifest.release, len(status.cli_commands), len(manifest.entries), strengths, risks, targets, "route_release_intelligence_to_ci_plan")


def render_release_intelligence(report: ReleaseIntelligence | None = None) -> str:
    report = report or build_release_intelligence()
    lines = ["# Omega Absorb Release Intelligence", "", f"release: {report.release}", f"commands: {report.command_count}", f"versions: {report.version_count}", "", "## Strengths"]
    lines.extend(f"- {item}" for item in report.strengths)
    lines.extend(["", "## Risks"])
    lines.extend(f"- {item}" for item in report.risks)
    lines.extend(["", "## Next targets"])
    lines.extend(f"- {item}" for item in report.next_targets)
    return "\n".join(lines) + "\n"
