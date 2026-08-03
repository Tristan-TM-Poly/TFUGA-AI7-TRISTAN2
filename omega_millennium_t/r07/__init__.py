"""Ω-PROBLEM-ATLAS-T∞ R0.7 certified offline job runners.

R0.7 executes a small allowlisted family of deterministic, offline research
jobs without arbitrary subprocesses or network access. Every result is emitted
with an independently checked receipt, replay contract and M− failure memory.
"""

from .job_system import (
    BUNDLE_SCHEMA,
    RUNNER_KINDS,
    audit_job_campaign,
    compile_job_campaign,
)

__all__ = [
    "BUNDLE_SCHEMA",
    "RUNNER_KINDS",
    "audit_job_campaign",
    "compile_job_campaign",
]

__version__ = "0.7.0"
