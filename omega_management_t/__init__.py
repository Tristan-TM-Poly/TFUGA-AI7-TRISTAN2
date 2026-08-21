"""Ω-MANAGEMENT-T∞ — evidence-oriented management primitives.

Software outputs from this package are decision support only. They do not establish
employee performance, leadership quality, legal compliance, or authority to act.
"""

from .core import (
    InterventionCandidate,
    ManagementReceipt,
    ManagementSignal,
    ManagementState,
    absence_resilience,
    leadership_value,
    prioritize_interventions,
    proxy_gap,
)

__all__ = [
    "InterventionCandidate",
    "ManagementReceipt",
    "ManagementSignal",
    "ManagementState",
    "absence_resilience",
    "leadership_value",
    "prioritize_interventions",
    "proxy_gap",
]
