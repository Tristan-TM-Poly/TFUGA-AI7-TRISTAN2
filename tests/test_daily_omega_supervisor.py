from sage_tristan.daily_omega_briefing import BriefingItem, OakCheck, Source
from sage_tristan.daily_omega_supervisor import supervise_issue_spec, supervise_many


def make_item(
    *,
    title="Reusable signal",
    source_quality=4,
    ip_signal="",
    final_score_seed=5,
    oak=True,
):
    return BriefingItem(
        title=title,
        topic_anchor="ai_automation_agents",
        signal_type=("opportunity",),
        why_it_matters="This reusable signal can become a tested Daily Omega issue spec.",
        actionable_opportunity="Create a small dry-run issue spec and review it with OAK criteria.",
        oak_check=OakCheck(
            claim_status="prototype_opportunity",
            risk="The signal may be weak without repeatable evidence." if oak else " ",
            falsification_route="Compare against a baseline before promotion." if oak else " ",
        ),
        sources=(
            Source(
                title="Reusable source",
                source_type="technical_report",
                url_or_identifier="example:reusable",
                source_quality=source_quality,
            ),
        ),
        next_action="Create a reviewable spec before any public action.",
        scores={
            "freshness": final_score_seed,
            "credibility": final_score_seed,
            "tristan_fit": final_score_seed,
            "actionability": final_score_seed,
            "oak_clarity": final_score_seed,
        },
        ip_signal=ip_signal,
    )


def test_supervisor_dry_run_reviews_even_good_item():
    decision = supervise_issue_spec(make_item(), dry_run=True)

    assert decision.allowed is False
    assert decision.mode == "review_spec"
    assert any("dry-run" in reason for reason in decision.reasons)
    assert decision.issue_spec.title


def test_supervisor_allows_good_item_when_not_dry_run():
    decision = supervise_issue_spec(make_item(), dry_run=False)

    assert decision.allowed is True
    assert decision.mode == "create_issue"
    assert any("allowed" in reason for reason in decision.reasons)


def test_supervisor_reviews_low_quality_source():
    decision = supervise_issue_spec(make_item(source_quality=1), dry_run=False)

    assert decision.allowed is False
    assert any("source quality" in reason for reason in decision.reasons)


def test_supervisor_reviews_confidential_posture():
    decision = supervise_issue_spec(
        make_item(ip_signal="Possible patentable invention and confidential review."),
        dry_run=False,
    )

    assert decision.allowed is False
    assert any("posture" in reason for reason in decision.reasons)


def test_supervise_many_returns_decisions():
    decisions = supervise_many([make_item(), make_item(title="Second signal")])

    assert len(decisions) == 2
    assert all(decision.issue_spec.title for decision in decisions)


def test_decision_markdown_is_reusable():
    decision = supervise_issue_spec(make_item(), dry_run=True)
    markdown = decision.render_markdown()

    assert "Daily Omega Decision" in markdown
    assert "Issue spec" in markdown
    assert "Labels" in markdown
