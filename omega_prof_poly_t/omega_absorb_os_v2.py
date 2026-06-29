"""Omega Absorb OS v2 core summary."""

from __future__ import annotations

from dataclasses import dataclass

from .cli_command_groups import CLICommandGroups, build_cli_command_groups
from .package_layout_v2 import PackageLayoutV2, build_package_layout_v2
from .report_bundle_contract import ReportBundleContract, build_report_bundle_contract
from .workflow_seed import WorkflowSeed, build_workflow_seed


@dataclass(frozen=True)
class OmegaAbsorbOSV2:
    version: str
    layout: PackageLayoutV2
    report_contract: ReportBundleContract
    workflow_seed: WorkflowSeed
    command_groups: CLICommandGroups
    next_action: str


def build_omega_absorb_os_v2() -> OmegaAbsorbOSV2:
    return OmegaAbsorbOSV2(
        version="2.0.0",
        layout=build_package_layout_v2(),
        report_contract=build_report_bundle_contract(),
        workflow_seed=build_workflow_seed(),
        command_groups=build_cli_command_groups(),
        next_action="route_os_v2_to_release_bundle",
    )


def render_omega_absorb_os_v2(os: OmegaAbsorbOSV2 | None = None) -> str:
    os = os or build_omega_absorb_os_v2()
    return (
        "# Omega Absorb OS v2\n\n"
        f"version: {os.version}\n"
        f"layout sections: {len(os.layout.sections)}\n"
        f"required reports: {len(os.report_contract.required_reports)}\n"
        f"workflow steps: {len(os.workflow_seed.steps)}\n"
        f"command groups: {len(os.command_groups.groups)}\n"
        f"next action: {os.next_action}\n"
    )
