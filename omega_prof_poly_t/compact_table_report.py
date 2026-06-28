"""Compact table reports for Omega absorb v1.3."""

from __future__ import annotations

from typing import Iterable

from .opportunity_ranker import OpportunityRanking, RankedOpportunity
from .portfolio_optimizer import PortfolioSelection
from .source_record_validation import RecordValidationReport


def _row(values: Iterable[object]) -> str:
    return " | ".join(str(value) for value in values)


def render_compact_table(ranking: OpportunityRanking, limit: int = 10) -> str:
    lines = [_row(("rank", "atom_id", "score", "path", "next")), _row(("---", "---", "---", "---", "---"))]
    for item in ranking.ranked[:limit]:
        lines.append(_row((item.rank, item.atom_id, f"{item.score:.4f}", item.recommended_path, item.next_action)))
    return "\n".join(lines) + "\n"


def render_portfolio_table(portfolio: PortfolioSelection) -> str:
    lines = [_row(("kind", "rank", "atom_id", "score", "path")), _row(("---", "---", "---", "---", "---"))]
    for item in portfolio.selected:
        lines.append(_row(("selected", item.rank, item.atom_id, f"{item.score:.4f}", item.recommended_path)))
    for item in portfolio.skipped[:10]:
        lines.append(_row(("skipped", item.rank, item.atom_id, f"{item.score:.4f}", item.recommended_path)))
    return "\n".join(lines) + "\n"


def render_validation_table(report: RecordValidationReport) -> str:
    lines = [_row(("level", "record_id", "source_id", "field", "message")), _row(("---", "---", "---", "---", "---"))]
    for finding in report.findings:
        lines.append(_row((finding.level, finding.record_id, finding.source_id, finding.field, finding.message)))
    if not report.findings:
        lines.append(_row(("ok", "all", "all", "all", "clean")))
    return "\n".join(lines) + "\n"


def render_ranked_items_table(items: Iterable[RankedOpportunity]) -> str:
    return render_compact_table(OpportunityRanking(ranked=tuple(items), top_next_action="table_only"))
