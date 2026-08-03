"""Ω-GITHUB-MYCELIUM-T∞: read-first, OAK-gated GitHub orchestration.

The package compiles intentions and repository snapshots into reviewable
multi-repository campaign plans.  It never merges, publishes, deploys, deletes,
or changes permissions by itself.
"""

from .intent import IntentCompiler
from .models import (
    ArtifactSpec,
    CampaignPlan,
    CampaignState,
    CreationRecord,
    EvidenceBundle,
    FindingSeverity,
    IntentContract,
    OAKFinding,
    PullRequestPlan,
    PullRequestSnapshot,
    RepositorySnapshot,
    RouteDecision,
    RouteDecisionRecord,
)
from .orchestrator import MyceliumOrchestrator
from .snapshot import SnapshotBundle

__all__ = [
    "ArtifactSpec",
    "CampaignPlan",
    "CampaignState",
    "CreationRecord",
    "EvidenceBundle",
    "FindingSeverity",
    "IntentCompiler",
    "IntentContract",
    "MyceliumOrchestrator",
    "OAKFinding",
    "PullRequestPlan",
    "PullRequestSnapshot",
    "RepositorySnapshot",
    "RouteDecision",
    "RouteDecisionRecord",
    "SnapshotBundle",
]

__version__ = "0.1.0"
