"""Dry-run CI admission analysis for the Omega repository."""

from .resilient import audit_route_config, build_admission_report, scan_workflows

__all__ = ["audit_route_config", "build_admission_report", "scan_workflows"]

__version__ = "0.2.0"
