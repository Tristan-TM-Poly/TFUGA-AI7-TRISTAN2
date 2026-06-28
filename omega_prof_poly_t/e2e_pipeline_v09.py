"""End-to-end demo pipeline covering v0.3 through v0.9."""

from __future__ import annotations

from dataclasses import dataclass

from .absorb_public_research import absorb_public_records
from .collaboration_markdown import CollaborationMarkdown, render_collaboration_markdown
from .collaboration_recommender import recommend_collaborations
from .department_bridge_report import DepartmentBridgeReport, render_department_bridge_report
from .department_bridge_scoring import score_department_bridge
from .fixture_artifact_generator import FixtureArtifactRun, generate_fixture_artifacts
from .fixture_loader_v08 import demo_combined_fixture_records
from .portfolio_optimizer import optimize_portfolio
from .professor_genome import build_all_professor_genomes
from .research_opportunity_compiler import compile_research_opportunities
from .roadmap_compiler import RoadmapPlan, compile_portfolio_roadmap
from .source_record_validation import RecordValidationReport, validate_public_records
from .opportunity_ranker import rank_opportunity_bundles


@dataclass(frozen=True)
class EndToEndV09Result:
    validation: RecordValidationReport
    artifact_run: FixtureArtifactRun
    department_report: DepartmentBridgeReport
    collaboration_markdown: CollaborationMarkdown
    roadmap: RoadmapPlan
    next_action: str


def run_v09_e2e_pipeline() -> EndToEndV09Result:
    records = demo_combined_fixture_records()
    validation = validate_public_records(records)
    absorption = absorb_public_records(records)
    genomes = build_all_professor_genomes(absorption.atoms)
    artifact_run = generate_fixture_artifacts(records)
    department_report = render_department_bridge_report(score_department_bridge(genomes))
    collaboration_markdown = render_collaboration_markdown(recommend_collaborations(genomes))
    ranking = rank_opportunity_bundles(compile_research_opportunities(absorption.atoms))
    portfolio = optimize_portfolio(ranking, max_items=3)
    roadmap = compile_portfolio_roadmap(portfolio)
    return EndToEndV09Result(
        validation=validation,
        artifact_run=artifact_run,
        department_report=department_report,
        collaboration_markdown=collaboration_markdown,
        roadmap=roadmap,
        next_action="persist_e2e_artifacts",
    )
