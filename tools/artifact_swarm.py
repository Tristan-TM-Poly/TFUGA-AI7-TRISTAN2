"""Artifact Swarm for Ω-AIT-AUTONOMOUS-PROPULSION-MESH-T.

Selects the natural next repository artifact for a branch state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class BranchNeed(StrEnum):
    IDEA_WITHOUT_PROOF = "idea_without_proof"
    TOOL_WITHOUT_BENCHMARK = "tool_without_benchmark"
    THEORY_WITHOUT_STRUCTURE = "theory_without_structure"
    UNHANDLED_RISK = "unhandled_risk"
    REPEATED_ERROR = "repeated_error"
    FERTILE_BRANCH = "fertile_branch"


@dataclass(frozen=True)
class ArtifactChoice:
    need: BranchNeed
    artifact: str
    path_hint: str


CHOICES = {
    BranchNeed.IDEA_WITHOUT_PROOF: ("test_tool.py", "tests/"),
    BranchNeed.TOOL_WITHOUT_BENCHMARK: ("benchmark.md", "benchmarks/"),
    BranchNeed.THEORY_WITHOUT_STRUCTURE: ("schema.json", "schemas/"),
    BranchNeed.UNHANDLED_RISK: ("oak_report.md", "docs/oak_reports/"),
    BranchNeed.REPEATED_ERROR: ("m_minus.yaml", "safety/"),
    BranchNeed.FERTILE_BRANCH: ("roadmap.md", "docs/roadmaps/"),
}


def choose_artifact(need: BranchNeed) -> ArtifactChoice:
    artifact, path_hint = CHOICES[need]
    return ArtifactChoice(need, artifact, path_hint)
