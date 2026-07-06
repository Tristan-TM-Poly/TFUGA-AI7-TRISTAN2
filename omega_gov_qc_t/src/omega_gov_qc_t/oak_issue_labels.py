"""Label manifest for local Ω-GOV-QC-T OAK issue drafts.

This module defines suggested labels only. It does not create remote labels.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from typing import Dict, Tuple


@dataclass(frozen=True)
class OAKIssueLabel:
    """Suggested project label."""

    name: str
    color: str
    description: str


LABELS: Tuple[OAKIssueLabel, ...] = (
    OAKIssueLabel(
        name="omega-gov-qc",
        color="5319e7",
        description="Ω-GOV-QC-T governance graph and OAK workflow",
    ),
    OAKIssueLabel(
        name="oak-review",
        color="fbca04",
        description="Requires accountable OAK review before advancement",
    ),
    OAKIssueLabel(
        name="source-governance",
        color="1d76db",
        description="Source authorization, provenance, locator and permission review",
    ),
    OAKIssueLabel(
        name="dataset-health",
        color="0e8a16",
        description="Dataset quality and readiness review signal",
    ),
    OAKIssueLabel(
        name="human-review",
        color="d93f0b",
        description="Human-review gate for higher-impact contexts",
    ),
    OAKIssueLabel(
        name="graph",
        color="0052cc",
        description="GovGraph, EvidenceGraph or GraphML semantics",
    ),
    OAKIssueLabel(
        name="semantic-review",
        color="bfdadc",
        description="Review vocabulary, relation meaning, confidence and limitations",
    ),
    OAKIssueLabel(
        name="bundle-review",
        color="c2e0c6",
        description="Generated from a local export bundle",
    ),
)


def label_manifest() -> Tuple[OAKIssueLabel, ...]:
    """Return the suggested label manifest."""

    return LABELS


def label_names() -> Tuple[str, ...]:
    """Return suggested label names."""

    return tuple(label.name for label in LABELS)


def label_manifest_dict() -> Dict[str, Dict[str, str]]:
    """Return a deterministic mapping suitable for JSON export."""

    return {label.name: {"color": label.color, "description": label.description} for label in LABELS}


def label_manifest_json() -> str:
    """Return JSON label manifest."""

    return json.dumps(label_manifest_dict(), indent=2, sort_keys=True)
