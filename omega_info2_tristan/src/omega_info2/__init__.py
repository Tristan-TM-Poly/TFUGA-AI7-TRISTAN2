"""Ω-INFO²-T — Information de l'information de Tristan."""

from .bayes_tristan import BayesTristanReport, BayesTristanUpdater, BayesTristanVector, EvidenceVector
from .chatgpt_oak_gate import (
    ChatGPTFailureRule,
    ChatGPTOAKDecision,
    ChatGPTOAKGate,
    DEFAULT_FAILURE_RULES,
    GitHubRunContext,
    GitHubWorkflowState,
)
from .cvcd_compressor import CVCDCompressor, CVCDInvariant, CVCDReport
from .graph import Info2Graph
from .half_life import freshness_score, half_life_days
from .m_minus_registry import MMinusEntry, MMinusRegistry
from .models import (
    Claim,
    InfoAction,
    InfoObject,
    InfoScores,
    MetaInformation,
    OAKReport,
    OAKStatus,
    Provenance,
    ProvenanceStep,
    RawObject,
    Route,
    UncertaintyTensor,
)
from .oak_gate import OAKInfoGate
from .pipeline import Info2Pipeline, Info2PipelineResult
from .rosette_adapter import RosetteClaim, RosetteExtraction, SourceSpan, rosette_to_info_object
from .router import route_information
from .source_trust import SourceTrustInput, score_source

__all__ = [
    "BayesTristanReport",
    "BayesTristanUpdater",
    "BayesTristanVector",
    "CVCDCompressor",
    "CVCDInvariant",
    "CVCDReport",
    "ChatGPTFailureRule",
    "ChatGPTOAKDecision",
    "ChatGPTOAKGate",
    "Claim",
    "DEFAULT_FAILURE_RULES",
    "EvidenceVector",
    "GitHubRunContext",
    "GitHubWorkflowState",
    "Info2Pipeline",
    "Info2PipelineResult",
    "InfoAction",
    "InfoObject",
    "InfoScores",
    "MetaInformation",
    "MMinusEntry",
    "MMinusRegistry",
    "OAKInfoGate",
    "OAKReport",
    "OAKStatus",
    "Provenance",
    "ProvenanceStep",
    "RawObject",
    "RosetteClaim",
    "RosetteExtraction",
    "Route",
    "SourceSpan",
    "SourceTrustInput",
    "UncertaintyTensor",
    "Info2Graph",
    "rosette_to_info_object",
    "score_source",
    "route_information",
    "freshness_score",
    "half_life_days",
]
