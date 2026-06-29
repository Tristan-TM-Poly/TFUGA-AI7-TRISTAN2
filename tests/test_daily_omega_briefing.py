from datetime import date

import pytest

from sage_tristan.daily_omega_briefing import (
    BriefingItem,
    OakCheck,
    Source,
    rank_items,
    render_markdown,
    score_candidate,
)


def test_score_candidate_subtracts_penalties():
    score = score_candidate(
        {
            "freshness": 5,
            "credibility": 4,
            "tristan_fit": 5,
            "actionability": 4,
            "leverage": 4,
            "scarcity": 3,
            "oak_clarity": 5,
            "ip_revenue": 4,
            "hype_penalty": 2,
            "duplication_penalty": 1,
            "source_penalty": 0,
        }
    )
    assert score == 31


def test_score_candidate_rejects_out_of_bounds_values():
    with pytest.raises(ValueError):
        score_candidate({"freshness": 6})


def make_item(title: str, score: int, topic: str = "ai_automation_agents") -> BriefingItem:
    return BriefingItem(
        title=title,
        topic_anchor=topic,
        signal_type=("opportunity",),
        why_it_matters="This matters because it can be converted into a tested Tristan prototype.",
        actionable_opportunity="Create a small benchmark and compare it against the current baseline.",
        oak_check=OakCheck(
            claim_status="prototype_opportunity",
            risk="The result may be hype or may fail outside a narrow benchmark.",
            falsification_route="Run a reproducible baseline comparison before canon promotion.",
        ),
        sources=(
            Source(
                title="Example primary source",
                source_type="paper",
                url_or_identifier="example:source",
                source_quality=4,
            ),
        ),
        next_action="Open a GitHub issue with a minimal reproducible test.",
        scores={"freshness": score, "credibility": score, "tristan_fit": score},
        business_funding_signal="Could become a prototype-backed grant or product signal.",
        ip_signal="Run a private prior-art scan before public disclosure.",
    )


def test_rank_items_assigns_ranks_and_sorts_descending():
    low = make_item("Low signal", 1)
    high = make_item("High signal", 5)

    ranked = rank_items([low, high])

    assert [item.title for item in ranked] == ["High signal", "Low signal"]
    assert [item.rank for item in ranked] == [1, 2]


def test_render_markdown_contains_oak_and_synthesis():
    ranked = rank_items([make_item("Prototype signal", 5, "physics_energy_materials")])
    markdown = render_markdown(date(2026, 6, 24), "Europe/Berlin", ranked)

    assert "# Daily Ω Briefing — 2026-06-24" in markdown
    assert "**OAK check:**" in markdown
    assert "## Ω-CVCD synthesis" in markdown
    assert "Prototype signal" in markdown
