"""Ω-AI-TRISTAN-LAB.

OAK-safe laboratory plus multi-repository execution fabric: ideas, documents,
capabilities, provenance, policy, execution capsules, and composable runtimes.
"""

from .adapter_forge import AdapterForge, AdapterPlan, RepositoryInspection
from .agent_harness import AgentHarness
from .bayes_tristan import BayesTristanEngine
from .capabilities import CapabilityGraph, CapabilityProvider, CapabilitySpec
from .capsule import ExecutionCapsule
from .ingest import ChunkRecord, DocumentIngestor, IngestedDocument
from .ip_classifier import IPClassifier
from .models import AgentStep, BayesAxisScore, IPClassification, OAKReport, OAKStatus, RevenuePath, TheoryCard
from .oak_eval import OAKEvaluator
from .policy import Permission, PolicyContext, PolicyDecision, PolicyKernel
from .rag_engine import MiniRAG
from .repo_registry import RepoRegistry, RepositoryHealth, RepositorySpec
from .reporting import ReportRenderer
from .revenue_mapper import RevenueMapper
from .runtime import CapabilityExecution, PipelineStep, PluginInfo, TristanPlugin, TristanRuntime
from .search_backends import LexicalSearchBackend, NullVectorBackend, SearchBackend, SearchResult
from .theory_to_prototype import TheoryPrototypeFactory
from .tir import Provenance, TristanArtifact, Uncertainty, stable_digest
from .workspace import Workspace, WorkspaceRun

__all__ = [
    "AdapterForge", "AdapterPlan", "AgentHarness", "AgentStep", "BayesAxisScore",
    "BayesTristanEngine", "CapabilityExecution", "CapabilityGraph", "CapabilityProvider",
    "CapabilitySpec", "ChunkRecord", "DocumentIngestor", "ExecutionCapsule",
    "IngestedDocument", "IPClassification", "IPClassifier", "LexicalSearchBackend",
    "MiniRAG", "NullVectorBackend", "OAKReport", "OAKStatus", "OAKEvaluator",
    "Permission", "PipelineStep", "PluginInfo", "PolicyContext", "PolicyDecision",
    "PolicyKernel", "Provenance", "RepoRegistry", "ReportRenderer", "RepositoryHealth",
    "RepositoryInspection", "RepositorySpec", "RevenueMapper", "RevenuePath", "SearchBackend",
    "SearchResult", "TheoryCard", "TheoryPrototypeFactory", "TristanArtifact", "TristanPlugin",
    "TristanRuntime", "Uncertainty", "Workspace", "WorkspaceRun", "stable_digest",
]
