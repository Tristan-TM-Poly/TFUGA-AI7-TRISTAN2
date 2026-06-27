from omega_game import (
    FeedbackSignal,
    TheorySpec,
    default_demo_forge,
    default_feedback_loop,
    default_issue_forge,
    default_launch_forge,
    default_productizer,
    default_revenue_forge,
    default_sprint_forge,
    default_theory_compiler,
)


def _feedback_for(theory_name: str):
    world = default_theory_compiler().compile(TheorySpec(theory_name))
    product = default_productizer().productize(world)
    issue_set = default_issue_forge().forge(product)
    sprint = default_sprint_forge().forge(issue_set)
    demo = default_demo_forge().forge(product, sprint)
    launch = default_launch_forge().forge(product, demo)
    revenue = default_revenue_forge().forge(product, launch)
    return default_feedback_loop().run(revenue)


def test_feedback_loop_creates_result_for_circuit_product():
    result = _feedback_for("Ω-CIRCUITS-T")

    assert result.product_name == "CircuitDungeon-T Lesson Pack"
    assert result.target_engine == "CircuitDungeon-T"
    assert 0.0 <= result.confidence_score <= 1.0
    assert result.m_plus
    assert result.m_minus
    assert "no_external_action_from_feedback_loop" in result.oak_controls


def test_feedback_loop_strong_signal_selects_private_pilot_decision():
    revenue = _feedback_for("Ω-CIRCUITS-T")
    signal = FeedbackSignal(
        signal_type="pilot_request",
        strength="very_strong",
        source="private_feedback",
        evidence="reviewer asks to test with a group",
        next_action="prepare reviewed pilot scope",
    )
    result = default_feedback_loop().run(
        revenue_plan=_revenue_plan_for("Ω-CIRCUITS-T"),
        feedback_signals=[signal],
    )

    assert result.decision.decision == "prepare_reviewed_private_pilot"
    assert "pilot_interest_found" in result.m_plus


def _revenue_plan_for(theory_name: str):
    world = default_theory_compiler().compile(TheorySpec(theory_name))
    product = default_productizer().productize(world)
    issue_set = default_issue_forge().forge(product)
    sprint = default_sprint_forge().forge(issue_set)
    demo = default_demo_forge().forge(product, sprint)
    launch = default_launch_forge().forge(product, demo)
    return default_revenue_forge().forge(product, launch)


def test_feedback_signal_rejects_unknown_strength():
    try:
        FeedbackSignal(
            signal_type="interest",
            strength="unknown",
            source="private_feedback",
            evidence="x",
            next_action="clarify",
        )
    except ValueError as exc:
        assert "strength" in str(exc)
    else:
        raise AssertionError("FeedbackSignal accepted unknown strength")


def test_feedback_loop_to_dict_has_contract_keys():
    payload = _feedback_for("Ω-ENERGY-T").to_dict()

    assert set(payload) == {
        "product_name",
        "target_engine",
        "confidence_score",
        "decision",
        "feedback_signals",
        "m_plus",
        "m_minus",
        "oak_controls",
        "next_actions",
    }
    assert payload["decision"]["next_version"]


def test_feedback_loop_markdown_contains_memory_sections():
    result = _feedback_for("Ω-GAME-T")
    markdown = result.to_markdown()

    assert "## M+" in markdown
    assert "## M-" in markdown
    assert "## OAK controls" in markdown


def test_feedback_loop_many_preserves_count():
    plans = [_revenue_plan_for("Ω-CIRCUITS-T"), _revenue_plan_for("Ω-ENERGY-T")]
    results = default_feedback_loop().run_many(plans)

    assert len(results) == 2
