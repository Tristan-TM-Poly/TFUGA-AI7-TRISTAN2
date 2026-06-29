"""Demo for the Daily Omega War Room pipeline.

Run from the repository root:

    python examples/daily_omega_war_room_demo.py

The demo uses synthetic source-backed-style items only. It does not fetch news,
create GitHub issues, publish claims, or disclose private inventions.
"""

from __future__ import annotations

from datetime import date

from sage_tristan.daily_omega_briefing import BriefingItem, OakCheck, Source, rank_items, render_markdown
from sage_tristan.daily_omega_router import render_war_room_markdown, make_issue_spec


def build_demo_items() -> list[BriefingItem]:
    return [
        BriefingItem(
            title="Agentic workflow benchmark for Tristan automation",
            topic_anchor="ai_automation_agents",
            signal_type=("opportunity", "tooling"),
            why_it_matters=(
                "Agentic workflows are useful only when they become measurable. "
                "A small benchmark can separate real automation leverage from demo hype."
            ),
            actionable_opportunity=(
                "Create a tiny benchmark that measures time saved, error rate, and OAK review burden "
                "for one repeated Tristan workflow."
            ),
            oak_check=OakCheck(
                claim_status="prototype_opportunity",
                risk="A flashy agent demo may fail on repeatability, permissions, or hidden manual work.",
                falsification_route="Run the workflow ten times against a manual baseline and compare time, failures, and corrections.",
                m_minus_warning="Do not count automation as progress unless manual friction is actually reduced.",
            ),
            sources=(
                Source(
                    title="Local repository workflow and Daily Omega PR context",
                    source_type="technical_report",
                    url_or_identifier="repo:TFUGA-AI7-TRISTAN2/pull/45",
                    source_quality=4,
                ),
            ),
            next_action="Open an OAKBench issue for one repeated ChatGPT-to-GitHub workflow.",
            scores={
                "freshness": 5,
                "credibility": 4,
                "tristan_fit": 5,
                "actionability": 5,
                "leverage": 5,
                "scarcity": 3,
                "oak_clarity": 5,
                "ip_revenue": 3,
                "hype_penalty": 1,
                "duplication_penalty": 0,
                "source_penalty": 1,
            },
            business_funding_signal="Could become a reusable automation service or internal productivity IP.",
            ip_signal="Keep implementation details private until the workflow moat is clear.",
        ),
        BriefingItem(
            title="Prior-art tracker for papers, patents, and university tech transfer",
            topic_anchor="papers_patents",
            signal_type=("patent", "paper", "opportunity"),
            why_it_matters=(
                "Tristan's invention pipeline needs a clean boundary between external prior art and "
                "private generated ideas."
            ),
            actionable_opportunity=(
                "Start a structured prior-art manifest and require every IP-like briefing item to record "
                "what is already public."
            ),
            oak_check=OakCheck(
                claim_status="prototype_opportunity",
                risk="Without prior-art tracking, public sources and private inventions can be mixed too early.",
                falsification_route="For each candidate invention, record at least three related public sources before promotion.",
                m_minus_warning="Do not publish protectable Tristan-generated mechanisms before IP classification.",
            ),
            sources=(
                Source(
                    title="Daily Omega prior-art tracker protocol",
                    source_type="technical_report",
                    url_or_identifier="data/prior_art/README.md",
                    source_quality=4,
                ),
            ),
            next_action="Create the first prior-art entry template and link it to one briefing item.",
            scores={
                "freshness": 4,
                "credibility": 4,
                "tristan_fit": 5,
                "actionability": 5,
                "leverage": 5,
                "scarcity": 4,
                "oak_clarity": 5,
                "ip_revenue": 5,
                "hype_penalty": 0,
                "duplication_penalty": 0,
                "source_penalty": 1,
            },
            business_funding_signal="Protects licensing, publication, and company formation paths.",
            ip_signal="prior_art_review",
        ),
    ]


def main() -> None:
    ranked = rank_items(build_demo_items())
    print(render_markdown(date(2026, 6, 24), "Europe/Berlin", ranked))
    print("\n---\n")
    print(render_war_room_markdown(ranked))
    print("\n--- Issue specs ---\n")
    for item in ranked:
        issue = make_issue_spec(item)
        print(issue.title)
        print("Labels:", ", ".join(issue.labels))
        print()


if __name__ == "__main__":
    main()
