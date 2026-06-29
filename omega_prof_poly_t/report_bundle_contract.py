"""Report bundle contract for Omega Absorb OS v2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .json_exports import to_deterministic_json
from .report_atlas import build_report_atlas


@dataclass(frozen=True)
class ReportBundleContract:
    version: str
    required_reports: Tuple[str, ...]
    optional_reports: Tuple[str, ...]
    manifest_json: str
    next_action: str


def build_report_bundle_contract(version: str = "2.0.0") -> ReportBundleContract:
    atlas = build_report_atlas()
    required = tuple(entry.name for entry in atlas.entries if entry.name in {"status", "health", "changelog", "oak-ledger"})
    optional = tuple(entry.name for entry in atlas.entries if entry.name not in required)
    manifest_json = to_deterministic_json(
        {
            "version": version,
            "required_reports": required,
            "optional_reports": optional,
            "contract": "local_report_bundle",
        }
    )
    return ReportBundleContract(version, required, optional, manifest_json, "validate_report_bundle_contract")


def render_report_bundle_contract(contract: ReportBundleContract | None = None) -> str:
    contract = contract or build_report_bundle_contract()
    lines = ["# Report Bundle Contract", "", f"version: {contract.version}", "", "## Required"]
    lines.extend(f"- {item}" for item in contract.required_reports)
    lines.extend(["", "## Optional"])
    lines.extend(f"- {item}" for item in contract.optional_reports)
    return "\n".join(lines) + "\n"
