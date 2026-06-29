from sage_tristan.daily_omega_briefing import BriefingItem, OakCheck, Source
from sage_tristan.daily_omega_router import (
    classify_ip,
    make_issue_spec,
    render_war_room_markdown,
    route_branches,
    route_item,
)


def make_item(
    *,
    title="Agent battery patent signal",
    topic_anchor="ai_automation_agents",
    signal_type=("opportunity",),
    source_type="paper",
    ip_signal="",
    business_funding_signal="",
):
    return BriefingItem(
        title=title,
        topic_anchor=topic_anchor,
        signal_type=signal_type,
        why_it_matters="This signal can become a concrete Tristan prototype or prior-art review.",
        actionable_opportunity="Create a benchmark, route it to the canon, and open a reviewable issue.",
        oak_check=OakCheck(
            claim_status="prototype_opportunity",
            risk="The signal may be overhyped or insufficiently reproduced.",
            falsification_route="Compare against a baseline and reject if the claimed gain disappears.",
            m_minus_warning="Do not promote the claim without a source-backed test.",
        ),
        sources=(
            Source(
                title="Example source",
                source_type=source_type,
                url_or_identifier="example:source",
                source_quality=4,
            ),
        ),
        next_action="Draft a minimal issue with OAK criteria.",
        scores={
            "freshness": 5,
            "credibility": 4,
            "tristan_fit": 5,
            "actionability": 5,
            "leverage": 4,
            "scarcity": 3,
            "oak_clarity": 5,
            "ip_revenue": 4,
        },
        ip_signal=ip_signal,
        business_funding_signal=business_funding_signal,
    )


def test_route_branches_uses_keywords_and_topic_defaults():
    item = make_item(title="Battery agent automation workflow")
    branches = route_branches(item)

    assert "Ω-AUTO²-T" in branches
    assert "Ω-BAT-T" in branches
    assert "SAGE" in branches


def test_classify_ip_prioritizes_patents():
    item = make_item(source_type="patent", signal_type=("patent",))

    assert classify_ip(item) == "prior_art_review"


def test_classify_ip_detects_confidential_review_language():
    item = make_item(ip_signal="Possible patentable invention and licensing path.")

    assert classify_ip(item) == "confidential_ip_review"


def test_make_issue_spec_contains_oak_ip_sources_and_labels():
    item = make_item(
        title="Solar battery patent opportunity",
        topic_anchor="physics_energy_materials",
        source_type="patent",
        signal_type=("patent", "opportunity"),
    )

    issue = make_issue_spec(item)

    assert issue.title.startswith("[IP / prior-art review]")
    assert "## OAK check" in issue.body
    assert "## IP / revenue posture" in issue.body
    assert "## Sources" in issue.body
    assert "omega-daily" in issue.labels
    assert "ip-review" in issue.labels


def test_route_item_produces_memory_notes():
    item = make_item()
    route = route_item(item)

    assert route.m_plus
    assert route.m_minus
    assert route.issue_type in {
        "Prototype candidate",
        "Paper / patent digestion",
        "Revenue / funding experiment",
        "IP / prior-art review",
        "OAK falsification note",
    }


def test_render_war_room_markdown_contains_issue_recommendation():
    item = make_item().with_rank(1)
    markdown = render_war_room_markdown([item])

    assert "# Daily Ω War Room" in markdown
    assert "Canon branches" in markdown
    assert "Recommended issue title" in markdown
    assert "M+" in markdown
    assert "M-" in markdown
