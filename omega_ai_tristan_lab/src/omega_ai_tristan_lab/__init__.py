"""Ω-AI-TRISTAN-LAB.

A small OAK-safe scaffold that converts ideas into structured theory cards,
agent plans, evaluation reports, IP classification, and revenue maps.
"""

from .agent_harness import AgentHarness
from .bayes_tristan import BayesTristanEngine
from .ip_classifier import IPClassifier
from .models import (
    AgentStep,
    BayesAxisScore,
    IPClassification,
    OAKReport,
    OAKStatus,
    RevenuePath,
    TheoryCard,
)
from .oak_eval import OAKEvaluator
from .rag_engine import MiniRAG
from .revenue_mapper import RevenueMapper
from .theory_to_prototype import TheoryPrototypeFactory

__all__ = [
    "AgentHarness",
    "AgentStep",
    "BayesAxisScore",
    "BayesTristanEngine",
    "IPClassification",
    "IPClassifier",
    "MiniRAG",
    "OAKReport",
    "OAKStatus",
    "OAKEvaluator",
    "RevenueMapper",
    "RevenuePath",
    "TheoryCard",
    "TheoryPrototypeFactory",
]
