"""Demo for reusable Daily Omega supervision.

Run from repository root:

    python examples/daily_omega_supervisor_demo.py

The demo prints a review decision and an issue specification. It never creates
GitHub issues and never publishes private invention content.
"""

from __future__ import annotations

from sage_tristan.daily_omega_briefing import BriefingItem, OakCheck, Source
from sage_tristan.daily_omega_supervisor import supervise_issue_spec


def build_item() -> BriefingItem:
    return BriefingItem(
        title="Reusable OAK supervisor for Daily Omega signals",
        topic_anchor="ai_automation_agents",
        signal_type=("opportunity", "tooling"),
        why_it_matters=(
            "A reusable supervisor lets the same Daily Omega signal become a report, issue spec, "
            "memory note, or prior-art record without unsafe automatic publication."
        ),
        actionable_opportunity="Use a dry-run decision as the default bridge between signal and GitHub issue.",
        oak_check=OakCheck(
            claim_status="prototype_opportunity",
            risk="Automatic issue creation can expose weak claims or private IP if not reviewed.",
            falsification_route="Try a low-quality or confidential item and verify that it stays in review mode.",
            m_minus_warning="Do not confuse reusable with automatic; keep OAK gates explicit.",
        ),
        sources=(
            Source(
                title="Daily Omega reusable supervisor module",
                source_type="technical_report",
                url_or_identifier="sage_tristan/daily_omega_supervisor.py",
                source_quality=4,
            ),
        ),
        next_action="Run the supervisor in dry-run mode and inspect the issue spec.",
        scores={
            "freshness": 5,
            "credibility": 4,
            "tristan_fit": 5,
            "actionability": 5,
            "leverage": 5,
            "scarcity": 4,
            "oak_clarity": 5,
            "ip_revenue": 4,
            "hype_penalty": 0,
            "duplication_penalty": 0,
            "source_penalty": 0,
        },
        business_funding_signal="Can become an internal operating system primitive for reusable project triage.",
        ip_signal="private_research",
    )


def main() -> None:
    decision = supervise_issue_spec(build_item(), dry_run=True)
    print(decision.render_markdown())
    print("--- Issue body preview ---")
    print(decision.issue_spec.body[:1200])


if __name__ == "__main__":
    main()
