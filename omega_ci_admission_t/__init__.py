"""Dry-run CI admission analysis for the Omega repository."""

from .core import audit_route_config, build_admission_report, scan_workflows

__all__ = ["audit_route_config", "build_admission_report", "scan_workflows"]

__version__ = "0.1.0"
