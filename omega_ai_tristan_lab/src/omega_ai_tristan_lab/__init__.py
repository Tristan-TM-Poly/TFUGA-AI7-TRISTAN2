"""Ω-AI-TRISTAN-LAB.

OAK-safe scaffold that converts ideas and local documents into structured
theory cards, agent plans, evaluation reports, IP classifications, revenue maps,
and persisted artifacts.
"""

from .agent_harness import AgentHarness
from .bayes_tristan import BayesTristanEngine
from .ingest import ChunkRecord, DocumentIngestor, IngestedDocument
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
from .reporting import ReportRenderer
from .revenue_mapper import RevenueMapper
from .search_backends import LexicalSearchBackend, NullVectorBackend, SearchBackend, SearchResult
from .theory_to_prototype import TheoryPrototypeFactory
from .workspace import Workspace, WorkspaceRun

__all__ = [
    "AgentHarness",
    "AgentStep",
    "BayesAxisScore",
    "BayesTristanEngine",
    "ChunkRecord",
    "DocumentIngestor",
    "IngestedDocument",
    "IPClassification",
    "IPClassifier",
    "LexicalSearchBackend",
    "MiniRAG",
    "NullVectorBackend",
    "OAKReport",
    "OAKStatus",
    "OAKEvaluator",
    "ReportRenderer",
    "RevenueMapper",
    "RevenuePath",
    "SearchBackend",
    "SearchResult",
    "TheoryCard",
    "TheoryPrototypeFactory",
    "Workspace",
    "WorkspaceRun",
]
