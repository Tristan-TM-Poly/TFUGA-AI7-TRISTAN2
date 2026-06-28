"""Opportunity portfolio optimizer for Omega absorb v0.6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .opportunity_ranker import OpportunityRanking, RankedOpportunity


@dataclass(frozen=True)
class PortfolioSelection:
    selected: Tuple[RankedOpportunity, ...]
    skipped: Tuple[RankedOpportunity, ...]
    objective: str
    next_action: str


def optimize_portfolio(
    ranking: OpportunityRanking | Iterable[RankedOpportunity],
    max_items: int = 5,
    min_score: float = 0.0,
    diversify_paths: bool = True,
) -> PortfolioSelection:
    ranked = ranking.ranked if isinstance(ranking, OpportunityRanking) else tuple(ranking)
    selected = []
    skipped = []
    used_paths = set()
    for item in ranked:
        if item.score < min_score:
            skipped.append(item)
            continue
        if diversify_paths and item.recommended_path in used_paths and len(selected) < max_items - 1:
            skipped.append(item)
            continue
        selected.append(item)
        used_paths.add(item.recommended_path)
        if len(selected) >= max_items:
            break
    selected_ids = {item.atom_id for item in selected}
    skipped.extend(item for item in ranked if item.atom_id not in selected_ids and item not in skipped)
    return PortfolioSelection(
        selected=tuple(selected),
        skipped=tuple(skipped),
        objective="maximize_score_with_path_diversity",
        next_action="render_portfolio_backlog",
    )
