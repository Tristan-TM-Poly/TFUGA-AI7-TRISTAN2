"""Ω-GAME-T — GameEngines & GameMasters de Tristan.

Minimal OAK-safe MVP package for playable worlds, GameMaster agents,
CVCD quest generation, memory, and text-world simulation.
"""

from .core import Entity, Event, GameQualityScore, RuleKernel, WorldGraph
from .cvcd import CVCDState, QuestCVCD, WorldCompressor
from .gm import GameMasterAgent, GMProposal
from .gm_council import CouncilScores, GMCouncil, GMCouncilDecision, GMVote, default_gm_council
from .memory import MMinusMemory, MPlusMemory
from .oak import OAKGate, OAKReport

__all__ = [
    "Entity",
    "Event",
    "GameQualityScore",
    "RuleKernel",
    "WorldGraph",
    "CVCDState",
    "QuestCVCD",
    "WorldCompressor",
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
]
