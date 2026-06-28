"""Generate local artifacts from combined fixture records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from .absorb_public_research import absorb_public_records
from .artifact_summaries import ArtifactSummary, build_artifact_summary
from .generated_report_artifacts import ArtifactManifest, build_report_artifacts
from .opportunity_ranker import rank_opportunity_bundles
from .professor_backlog_report import render_all_professor_backlogs
from .professor_genome import build_all_professor_genomes
from .research_opportunity_compiler import compile_research_opportunities


@dataclass(frozen=True)
class FixtureArtifactRun:
    manifest: ArtifactManifest
    summary: ArtifactSummary
    ranking_count: int
    professor_count: int
    next_action: str


def generate_fixture_artifacts(records: Iterable[Dict[str, object]]) -> FixtureArtifactRun:
    absorption = absorb_public_records(records)
    genomes = build_all_professor_genomes(absorption.atoms)
    ranking = rank_opportunity_bundles(compile_research_opportunities(absorption.atoms))
    reports = render_all_professor_backlogs(genomes, ranking)
    manifest = build_report_artifacts(reports, base_dir="generated/omega_absorb_poly_prof_v08")
    summary = build_artifact_summary(manifest)
    return FixtureArtifactRun(
        manifest=manifest,
        summary=summary,
        ranking_count=len(ranking.ranked),
        professor_count=len(genomes),
        next_action="persist_fixture_artifacts",
    )
