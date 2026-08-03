"""Dry-run CI admission analysis for the Omega repository."""

from .router import audit_route_config, build_admission_report, scan_repository_workflows

__all__ = [
    "audit_route_config",
    "build_admission_report",
    "scan_repository_workflows",
]

__version__ = "0.1.0"
