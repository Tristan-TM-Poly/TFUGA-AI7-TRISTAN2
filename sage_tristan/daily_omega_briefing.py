"""Daily Omega Briefing helpers.

This module turns candidate world signals into a compact, ranked briefing.
It is intentionally dependency-free so it can run in lightweight automation,
tests, notebooks, or future GitHub issue factories.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Mapping

TOPIC_ANCHORS = {
    "ai_automation_agents",
    "physics_energy_materials",
    "quebec_canada_innovation",
    "startups_ip_revenues",
    "papers_patents",
    "world_tech_geopolitics",
}

POSITIVE_SCORE_FIELDS = (
    "freshness",
    "credibility",
    "tristan_fit",
    "actionability",
    "leverage",
    "scarcity",
    "oak_clarity",
    "ip_revenue",
)

PENALTY_SCORE_FIELDS = (
    "hype_penalty",
    "duplication_penalty",
    "source_penalty",
)


@dataclass(frozen=True)
class Source:
    """A compact source reference for one briefing item."""

    title: str
    source_type: str
    url_or_identifier: str
    source_quality: int = 3

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("source title cannot be empty")
        if not self.url_or_identifier.strip():
            raise ValueError("source url_or_identifier cannot be empty")
        if not 0 <= self.source_quality <= 5:
            raise ValueError("source_quality must be between 0 and 5")


@dataclass(frozen=True)
class OakCheck:
    """OAK guardrail for a candidate signal."""

    claim_status: str
    risk: str
    falsification_route: str
    limit: str = ""
    uncertainty: str = ""
    m_minus_warning: str = ""

    def __post_init__(self) -> None:
        if not self.claim_status.strip():
            raise ValueError("claim_status cannot be empty")
        if not self.risk.strip():
            raise ValueError("risk cannot be empty")
        if not self.falsification_route.strip():
            raise ValueError("falsification_route cannot be empty")


@dataclass(frozen=True)
class BriefingItem:
    """One candidate item before or after ranking."""

    title: str
    topic_anchor: str
    signal_type: tuple[str, ...]
    why_it_matters: str
    actionable_opportunity: str
    oak_check: OakCheck
    sources: tuple[Source, ...]
    next_action: str
    scores: Mapping[str, int]
    business_funding_signal: str = ""
    ip_signal: str = ""
    rank: int | None = None

    def __post_init__(self) -> None:
        if self.topic_anchor not in TOPIC_ANCHORS:
            raise ValueError(f"unknown topic anchor: {self.topic_anchor}")
        if not self.sources:
            raise ValueError("at least one source is required")
        if not self.signal_type:
            raise ValueError("at least one signal_type is required")
        if not self.next_action.strip():
            raise ValueError("next_action cannot be empty")

    @property
    def final_score(self) -> int:
        return score_candidate(self.scores)

    def with_rank(self, rank: int) -> "BriefingItem":
        return BriefingItem(
            title=self.title,
            topic_anchor=self.topic_anchor,
            signal_type=self.signal_type,
            why_it_matters=self.why_it_matters,
            actionable_opportunity=self.actionable_opportunity,
            oak_check=self.oak_check,
            sources=self.sources,
            next_action=self.next_action,
            scores=self.scores,
            business_funding_signal=self.business_funding_signal,
            ip_signal=self.ip_signal,
            rank=rank,
        )


def _bounded_score(value: int, field_name: str) -> int:
    if not isinstance(value, int):
        raise TypeError(f"{field_name} must be an int")
    if not 0 <= value <= 5:
        raise ValueError(f"{field_name} must be between 0 and 5")
    return value


def score_candidate(scores: Mapping[str, int]) -> int:
    """Return PowerScore-style rank score for one candidate.

    Missing fields are treated as zero so early prototypes can remain lightweight.
    Values outside 0..5 fail fast to avoid accidental overconfidence.
    """

    positive = sum(_bounded_score(int(scores.get(field, 0)), field) for field in POSITIVE_SCORE_FIELDS)
    penalty = sum(_bounded_score(int(scores.get(field, 0)), field) for field in PENALTY_SCORE_FIELDS)
    return positive - penalty


def rank_items(candidates: Iterable[BriefingItem], limit: int = 5) -> list[BriefingItem]:
    """Rank candidates and return the top `limit` with rank fields assigned."""

    if limit < 1:
        raise ValueError("limit must be positive")
    ranked = sorted(candidates, key=lambda item: item.final_score, reverse=True)[:limit]
    return [item.with_rank(index + 1) for index, item in enumerate(ranked)]


def render_markdown(briefing_date: date, timezone: str, items: Iterable[BriefingItem]) -> str:
    """Render a daily briefing in the compact Markdown contract."""

    ranked_items = list(items)
    lines: list[str] = [f"# Daily Ω Briefing — {briefing_date.isoformat()}", "", f"Timezone: `{timezone}`", ""]

    for item in ranked_items:
        rank = item.rank if item.rank is not None else "?"
        lines.extend(
            [
                f"## {rank}. {item.title}",
                f"**Topic:** {item.topic_anchor}",
                f"**Signal:** {', '.join(item.signal_type)}",
                f"**Score:** {item.final_score}",
                f"**Why it matters:** {item.why_it_matters}",
                f"**Opportunity:** {item.actionable_opportunity}",
                f"**OAK check:** {item.oak_check.risk} Falsification: {item.oak_check.falsification_route}",
                f"**Business/funding signal:** {item.business_funding_signal or 'Not specified'}",
                f"**Next action:** {item.next_action}",
                "**Sources:**",
            ]
        )
        for source in item.sources:
            lines.append(f"- {source.title} ({source.source_type}) — {source.url_or_identifier}")
        lines.append("")

    if ranked_items:
        best = ranked_items[0]
        lines.extend(
            [
                "## Ω-CVCD synthesis",
                f"- **Invariant of the day:** high-score signals need source-backed action plus OAK falsification.",
                f"- **Best prototype candidate:** {best.next_action}",
                f"- **Best IP/revenue candidate:** {best.ip_signal or best.business_funding_signal or 'Review after prior-art scan.'}",
                f"- **Main M- warning:** do not promote source-light hype into canon.",
                f"- **One action today:** {best.next_action}",
            ]
        )

    return "\n".join(lines).strip() + "\n"


__all__ = [
    "BriefingItem",
    "OakCheck",
    "Source",
    "TOPIC_ANCHORS",
    "rank_items",
    "render_markdown",
    "score_candidate",
]
