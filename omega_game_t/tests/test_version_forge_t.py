from omega_game import (
    FeedbackDecision,
    FeedbackLoopResult,
    FeedbackSignal,
    VersionChange,
    default_version_forge,
)


def _feedback():
    return FeedbackLoopResult(
        product_name="CircuitDungeon-T Lesson Pack",
        target_engine="CircuitDungeon-T",
        confidence_score=0.62,
        decision=FeedbackDecision(
            decision="build_targeted_mini_demo",
            confidence_score=0.62,
            rationale="Signals justify a targeted mini-demo.",
            next_version="v0.2-targeted-mini-demo",
        ),
        feedback_signals=[
            FeedbackSignal(
                signal_type="use_case",
                strength="medium",
                source="private_feedback",
                evidence="reviewer described a use case",
                next_action="create targeted mini-demo",
            )
        ],
        m_plus=["concrete_use_case_found"],
        m_minus=["pricing_not_validated", "ip_review_still_required"],
        oak_controls=["no_external_action_from_feedback_loop"],
        next_actions=["create_v0_2_notes"],
    )


def test_version_forge_creates_internal_version_plan():
    plan = default_version_forge().forge(_feedback())

    assert plan.product_name == "CircuitDungeon-T Lesson Pack"
    assert plan.target_engine == "CircuitDungeon-T"
    assert plan.version == "v0.2-targeted-mini-demo"
    assert plan.release_type == "internal_iteration"
    assert plan.changes
    assert "no_public_release_from_version_plan" in plan.release_criteria.oak_gates


def test_version_plan_to_dict_has_contract_keys():
    payload = default_version_forge().forge(_feedback()).to_dict()

    assert set(payload) == {
        "product_name",
        "target_engine",
        "version",
        "release_type",
        "confidence_score",
        "changes",
        "release_criteria",
        "changelog",
        "next_actions",
    }
    assert payload["release_criteria"]["blockers"]


def test_version_plan_markdown_contains_criteria_and_changelog():
    markdown = default_version_forge().forge(_feedback()).to_markdown()

    assert "## Planned changes" in markdown
    assert "## Release criteria" in markdown
    assert "## Changelog draft" in markdown


def test_version_change_rejects_bad_category():
    try:
        VersionChange(category="bad", description="x", source_memory="x")
    except ValueError as exc:
        assert "category" in str(exc)
    else:
        raise AssertionError("VersionChange accepted bad category")


def test_version_forge_many_preserves_count():
    plans = default_version_forge().forge_many([_feedback(), _feedback()])

    assert len(plans) == 2
