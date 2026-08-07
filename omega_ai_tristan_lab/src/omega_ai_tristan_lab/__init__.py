"""Ω-AI-TRISTAN-LAB / Ω-TRISTAN-RUNTIME.

OAK-safe laboratory plus multi-repository execution fabric: capabilities,
provenance, policy, immutable integration locks and reproducible bundle plans.
"""

from .adapter_forge import AdapterForge, AdapterPlan, RepositoryInspection
from .agent_harness import AgentHarness
from .bayes_tristan import BayesTristanEngine
from .bundle import BundleFiles, BundlePlan
from .capabilities import CapabilityGraph, CapabilityProvider, CapabilitySpec
from .capsule import ExecutionCapsule
from .ingest import ChunkRecord, DocumentIngestor, IngestedDocument
from .integration import DEFAULT_R07_LOCK, IntegrationEvidence, IntegrationLock, PipelineProfile, RepositoryPin
from .integration_r08 import DEFAULT_R08_LOCK, ExecutionProbe, MatrixEvidence, R08IntegrationLock, RuntimePin
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
    "AdapterForge", "AdapterPlan", "AgentHarness", "AgentStep", "BayesAxisScore", "BayesTristanEngine",
    "BundleFiles", "BundlePlan", "CapabilityExecution", "CapabilityGraph", "CapabilityProvider", "CapabilitySpec",
    "ChunkRecord", "DEFAULT_R07_LOCK", "DEFAULT_R08_LOCK", "DocumentIngestor", "ExecutionCapsule", "ExecutionProbe",
    "IngestedDocument", "IntegrationEvidence", "IntegrationLock", "IPClassification", "IPClassifier",
    "LexicalSearchBackend", "MatrixEvidence", "MiniRAG", "NullVectorBackend", "OAKReport", "OAKStatus",
    "OAKEvaluator", "Permission", "PipelineProfile", "PipelineStep", "PluginInfo", "PolicyContext", "PolicyDecision",
    "PolicyKernel", "Provenance", "R08IntegrationLock", "RepoRegistry", "ReportRenderer", "RepositoryHealth",
    "RepositoryInspection", "RepositoryPin", "RepositorySpec", "RevenueMapper", "RevenuePath", "RuntimePin",
    "SearchBackend", "SearchResult", "TheoryCard", "TheoryPrototypeFactory", "TristanArtifact", "TristanPlugin",
    "TristanRuntime", "Uncertainty", "Workspace", "WorkspaceRun", "stable_digest",
]
