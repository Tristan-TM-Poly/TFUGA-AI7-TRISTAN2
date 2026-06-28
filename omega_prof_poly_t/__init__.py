"""Omega-PROF-POLY-T package."""

from .absorb_public_research import AbsorptionReport, absorb_public_records, demo_public_research_records
from .artifact_summaries import ArtifactSummary, build_artifact_summary
from .backlog_packet_templates import BacklogPacket, render_backlog_packet
from .claim_graph import ClaimGraph, ClaimNode, build_claim_graph
from .cli import VERSION, run_cli
from .collaboration_markdown import CollaborationMarkdown, render_collaboration_markdown
from .collaboration_recommender import CollaborationPlan, CollaborationRecommendation, recommend_collaborations
from .core import (
    Evidence,
    OAKDecision,
    OAKStatus,
    ProfessorSignal,
    build_project_forge_prompt,
    evaluate_signal,
    rank_signals,
)
from .course_memory_minus import CourseAntiError, CourseMemoryMinus, build_course_memory_minus
from .coursecvcd import CourseCVCDPacket, CourseInput, generate_coursecvcd
from .department_bridge_report import DepartmentBridgeReport, render_department_bridge_report
from .department_bridge_scoring import DepartmentBridgeScore, score_department_bridge, score_recommendation_bridge
from .documentation_index import DocumentationEntry, DocumentationIndex, build_documentation_index, render_documentation_index
from .e2e_pipeline_v09 import EndToEndV09Result, run_v09_e2e_pipeline
from .enriched_graph_exports import professor_graph_to_enriched_graphml
from .export_commands import ExportPayloads, build_export_payloads
from .fixture_artifact_generator import FixtureArtifactRun, generate_fixture_artifacts
from .fixture_loader_v08 import combine_fixture_records, demo_combined_fixture_records
from .generated_report_artifacts import ArtifactManifest, GeneratedArtifact, build_report_artifacts
from .grant_forge import GrantInput, GrantPacket, forge_grant, grant_score
from .graph_exports import professor_graph_to_graphml, professor_graph_to_json
from .ip_oak_gate import IPGatePacket, IPInput, IPStatus, classify_ip
from .json_exports import packet_digest, to_deterministic_json, to_plain_data
from .lab_oakbench import LabInput, LabOAKBenchPacket, generate_lab_oakbench
from .method_graph import MethodGraph, MethodNode, build_method_graph
from .opportunity_ranker import OpportunityRanking, RankedOpportunity, rank_opportunity_bundles, score_bundle
from .package_status import PackageStatusReport, build_package_status_report
from .poly_public_adapters import ExpertiseLikeAdapter, PolyPublieLikeAdapter
from .poly_research_twin import PolyResearchTwin, build_poly_research_twin
from .portfolio_optimizer import PortfolioSelection, optimize_portfolio
from .prior_art_packet import PriorArtPacket, generate_prior_art_packet
from .professor_backlog_report import ProfessorBacklogReport, render_all_professor_backlogs, render_professor_backlog
from .professor_genome import ProfessorResearchGenome, build_all_professor_genomes, build_professor_genome
from .professor_graph import HyperEdge, Node, ProfessorGraph, demo_professor_graph
from .professor_graph_integration import research_atoms_to_professor_graph
from .project_forge import ProjectInput, ProjectPacket, forge_project
from .public_metadata_adapters import GenericPublicMetadataAdapter, PublicMetadataAdapter
from .public_source_registry import PublicSource, PublicSourceRegistry, default_public_source_registry
from .release_bundle import ReleaseBundle, build_release_bundle
from .release_bundle_writer import ReleaseBundleWriteResult, WrittenBundleFile, write_release_bundle
from .reports import render_packet_report
from .research_atom import ResearchAtom, atom_from_public_record
from .research_opportunity_compiler import (
    ResearchOpportunityBundle,
    ResearchOpportunityCompilation,
    compile_atom_opportunities,
    compile_research_opportunities,
)
from .roadmap_compiler import RoadmapPlan, RoadmapStep, compile_portfolio_roadmap, render_roadmap_markdown
from .source_record_validation import RecordValidationFinding, RecordValidationReport, validate_public_records
from .source_selection import available_demo_sources, select_demo_records
from .version_manifest import VersionEntry, VersionManifest, build_version_manifest
from .zero_touch_oak import BlockedActionPacket, GateStatus, OAKCompileResult, compile_oak

__all__ = [
    "AbsorptionReport",
    "absorb_public_records",
    "demo_public_research_records",
    "ArtifactSummary",
    "build_artifact_summary",
    "BacklogPacket",
    "render_backlog_packet",
    "ClaimGraph",
    "ClaimNode",
    "build_claim_graph",
    "VERSION",
    "run_cli",
    "CollaborationMarkdown",
    "render_collaboration_markdown",
    "CollaborationPlan",
    "CollaborationRecommendation",
    "recommend_collaborations",
    "Evidence",
    "OAKDecision",
    "OAKStatus",
    "ProfessorSignal",
    "build_project_forge_prompt",
    "evaluate_signal",
    "rank_signals",
    "CourseAntiError",
    "CourseMemoryMinus",
    "build_course_memory_minus",
    "CourseCVCDPacket",
    "CourseInput",
    "generate_coursecvcd",
    "DepartmentBridgeReport",
    "render_department_bridge_report",
    "DepartmentBridgeScore",
    "score_department_bridge",
    "score_recommendation_bridge",
    "DocumentationEntry",
    "DocumentationIndex",
    "build_documentation_index",
    "render_documentation_index",
    "EndToEndV09Result",
    "run_v09_e2e_pipeline",
    "professor_graph_to_enriched_graphml",
    "ExportPayloads",
    "build_export_payloads",
    "FixtureArtifactRun",
    "generate_fixture_artifacts",
    "combine_fixture_records",
    "demo_combined_fixture_records",
    "ArtifactManifest",
    "GeneratedArtifact",
    "build_report_artifacts",
    "GrantInput",
    "GrantPacket",
    "forge_grant",
    "grant_score",
    "professor_graph_to_graphml",
    "professor_graph_to_json",
    "IPGatePacket",
    "IPInput",
    "IPStatus",
    "classify_ip",
    "packet_digest",
    "to_deterministic_json",
    "to_plain_data",
    "LabInput",
    "LabOAKBenchPacket",
    "generate_lab_oakbench",
    "MethodGraph",
    "MethodNode",
    "build_method_graph",
    "OpportunityRanking",
    "RankedOpportunity",
    "rank_opportunity_bundles",
    "score_bundle",
    "PackageStatusReport",
    "build_package_status_report",
    "ExpertiseLikeAdapter",
    "PolyPublieLikeAdapter",
    "PolyResearchTwin",
    "build_poly_research_twin",
    "PortfolioSelection",
    "optimize_portfolio",
    "PriorArtPacket",
    "generate_prior_art_packet",
    "ProfessorBacklogReport",
    "render_all_professor_backlogs",
    "render_professor_backlog",
    "ProfessorResearchGenome",
    "build_all_professor_genomes",
    "build_professor_genome",
    "HyperEdge",
    "Node",
    "ProfessorGraph",
    "demo_professor_graph",
    "research_atoms_to_professor_graph",
    "ProjectInput",
    "ProjectPacket",
    "forge_project",
    "GenericPublicMetadataAdapter",
    "PublicMetadataAdapter",
    "PublicSource",
    "PublicSourceRegistry",
    "default_public_source_registry",
    "ReleaseBundle",
    "build_release_bundle",
    "ReleaseBundleWriteResult",
    "WrittenBundleFile",
    "write_release_bundle",
    "render_packet_report",
    "ResearchAtom",
    "atom_from_public_record",
    "ResearchOpportunityBundle",
    "ResearchOpportunityCompilation",
    "compile_atom_opportunities",
    "compile_research_opportunities",
    "RoadmapPlan",
    "RoadmapStep",
    "compile_portfolio_roadmap",
    "render_roadmap_markdown",
    "RecordValidationFinding",
    "RecordValidationReport",
    "validate_public_records",
    "available_demo_sources",
    "select_demo_records",
    "VersionEntry",
    "VersionManifest",
    "build_version_manifest",
    "BlockedActionPacket",
    "GateStatus",
    "OAKCompileResult",
    "compile_oak",
]
