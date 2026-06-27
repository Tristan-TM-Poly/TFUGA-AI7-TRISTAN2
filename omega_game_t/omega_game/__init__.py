"""Ω-GAME-T — GameEngines & GameMasters de Tristan.

Minimal OAK-safe MVP package for playable worlds, GameMaster agents,
CVCD quest generation, memory, and text-world simulation.
"""

from .core import Entity, Event, GameQualityScore, RuleKernel, WorldGraph
from .cvcd import CVCDState, QuestCVCD, WorldCompressor
from .forge import (
    IssueForge,
    IssueSet,
    IssueSpec,
    LabelPlan,
    MilestonePlan,
    SprintForge,
    SprintPlan,
    SprintTask,
    default_issue_forge,
    default_sprint_forge,
)
from .gm import GameMasterAgent, GMProposal
from .gm_council import CouncilScores, GMCouncil, GMCouncilDecision, GMVote, default_gm_council
from .memory import MMinusMemory, MPlusMemory
from .oak import OAKGate, OAKReport
from .productizer import ProductPlan, Productizer, default_productizer
from .theory_compiler import (
    CompiledWorld,
    RuleGenome,
    TheoryCompiler,
    TheorySpec,
    WorldDNA,
    default_theory_compiler,
)

__all__ = [
    "Entity",
    "Event",
    "GameQualityScore",
    "RuleKernel",
    "WorldGraph",
    "CVCDState",
    "QuestCVCD",
    "WorldCompressor",
    "IssueForge",
    "IssueSet",
    "IssueSpec",
    "LabelPlan",
    "MilestonePlan",
    "SprintForge",
    "SprintPlan",
    "SprintTask",
    "default_issue_forge",
    "default_sprint_forge",
    "GameMasterAgent",
    "GMProposal",
    "CouncilScores",
    "GMCouncil",
    "GMCouncilDecision",
    "GMVote",
    "default_gm_council",
    "MMinusMemory",
    "MPlusMemory",
    "OAKGate",
    "OAKReport",
    "ProductPlan",
    "Productizer",
    "default_productizer",
    "CompiledWorld",
    "RuleGenome",
    "TheoryCompiler",
    "TheorySpec",
    "WorldDNA",
    "default_theory_compiler",
]
