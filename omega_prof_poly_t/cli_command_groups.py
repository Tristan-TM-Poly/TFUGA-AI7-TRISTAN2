"""CLI command groups for Omega Absorb OS v2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class CLICommandGroup:
    name: str
    commands: Tuple[str, ...]
    purpose: str


@dataclass(frozen=True)
class CLICommandGroups:
    groups: Tuple[CLICommandGroup, ...]
    next_action: str


def build_cli_command_groups() -> CLICommandGroups:
    groups = (
        CLICommandGroup("source", ("route-source", "policy-check", "schema-check", "ingest-json", "ingest-json-v2"), "source ingestion"),
        CLICommandGroup("graph", ("claim-oak", "method-packets", "tensor", "tensor-weights", "department-matrix"), "graph and tensor operations"),
        CLICommandGroup("twin", ("twin-v2", "twin-answer", "next-actions", "bridge-opt"), "local strategy engines"),
        CLICommandGroup("oak", ("oak-manifest", "oak-manifest-plus", "oak-lineage", "oak-ledger", "evidence-risk"), "OAK evidence ledger"),
        CLICommandGroup("reports", ("reports", "write-reports", "release-intel", "changelog-plus", "ci-plan"), "report and release layer"),
        CLICommandGroup("github", ("github-packet", "github-bundle", "write-actions"), "local GitHub packet preparation"),
        CLICommandGroup("os", ("layout-v2", "report-contract", "workflow-seed", "command-groups", "absorb-os"), "Omega Absorb OS v2"),
    )
    return CLICommandGroups(groups, "render_cli_command_groups")


def render_cli_command_groups(groups: CLICommandGroups | None = None) -> str:
    groups = groups or build_cli_command_groups()
    lines = ["# Omega Absorb CLI Command Groups", "", "group | commands | purpose", "--- | --- | ---"]
    for group in groups.groups:
        lines.append(f"{group.name} | {', '.join(group.commands)} | {group.purpose}")
    return "\n".join(lines) + "\n"
