from omega_game import (
    PricingHypothesis,
    TheorySpec,
    default_demo_forge,
    default_issue_forge,
    default_launch_forge,
    default_productizer,
    default_revenue_forge,
    default_sprint_forge,
    default_theory_compiler,
)


def _revenue_for(theory_name: str):
    world = default_theory_compiler().compile(TheorySpec(theory_name))
    product = default_productizer().productize(world)
    issue_set = default_issue_forge().forge(product)
    sprint = default_sprint_forge().forge(issue_set)
    demo = default_demo_forge().forge(product, sprint)
    launch = default_launch_forge().forge(product, demo)
    return default_revenue_forge().forge(product, launch)


def test_revenue_forge_creates_internal_hypothesis_for_circuit_product():
    plan = _revenue_for("Ω-CIRCUITS-T")

    assert plan.product_name == "CircuitDungeon-T Lesson Pack"
    assert plan.target_engine == "CircuitDungeon-T"
    assert plan.status == "internal_revenue_hypothesis"
    assert plan.offers
    assert "no_automatic_selling" in plan.oak_controls


def test_revenue_plan_to_dict_has_contract_keys():
    payload = _revenue_for("Ω-ENERGY-T").to_dict()

    assert set(payload) == {
        "product_name",
        "target_engine",
        "status",
        "offers",
        "channel_map",
        "success_signals",
        "oak_controls",
        "product_bench",
        "next_actions",
    }
    assert payload["offers"]
    assert payload["product_bench"]["score"] >= 0.0


def test_revenue_markdown_contains_offers_and_controls():
    plan = _revenue_for("Ω-GAME-T")
    markdown = plan.to_markdown()

    assert "## Offers" in markdown
    assert "## OAK controls" in markdown
    assert plan.target_engine in markdown


def test_pricing_hypothesis_rejects_negative_amount():
    try:
        PricingHypothesis(tier="bad", amount=-1, currency="CAD", billing_model="test", evidence_needed=[])
    except ValueError as exc:
        assert "amount" in str(exc)
    else:
        raise AssertionError("PricingHypothesis accepted negative amount")


def test_revenue_forge_many_preserves_count():
    compiler = default_theory_compiler()
    productizer = default_productizer()
    issue_forge = default_issue_forge()
    sprint_forge = default_sprint_forge()
    demo_forge = default_demo_forge()
    launch_forge = default_launch_forge()
    revenue_forge = default_revenue_forge()
    worlds = compiler.compile_many([TheorySpec("Ω-CIRCUITS-T"), TheorySpec("Ω-ENERGY-T")])
    products = productizer.productize_many(worlds)
    issue_sets = issue_forge.forge_many(products)
    sprints = sprint_forge.forge_many(issue_sets)
    demos = demo_forge.forge_many(list(zip(products, sprints)))
    launches = launch_forge.forge_many(list(zip(products, demos)))
    revenue_plans = revenue_forge.forge_many(list(zip(products, launches)))

    assert len(revenue_plans) == 2
