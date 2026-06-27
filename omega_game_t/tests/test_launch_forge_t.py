from omega_game import (
    LandingPageDraft,
    TheorySpec,
    default_demo_forge,
    default_issue_forge,
    default_launch_forge,
    default_productizer,
    default_sprint_forge,
    default_theory_compiler,
)


def _draft_for(theory_name: str):
    world = default_theory_compiler().compile(TheorySpec(theory_name))
    product = default_productizer().productize(world)
    issue_set = default_issue_forge().forge(product)
    sprint = default_sprint_forge().forge(issue_set)
    demo = default_demo_forge().forge(product, sprint)
    return default_launch_forge().forge(product, demo)


def test_launch_forge_creates_internal_draft_for_circuit_product():
    draft = _draft_for("Ω-CIRCUITS-T")

    assert draft.product_name == "CircuitDungeon-T Lesson Pack"
    assert draft.target_engine == "CircuitDungeon-T"
    assert draft.status == "internal_draft"
    assert draft.public_release == "blocked_until_review"
    assert "public_release_blocked_until_review" in draft.oak_checklist


def test_launch_draft_to_dict_has_contract_keys():
    payload = _draft_for("Ω-ENERGY-T").to_dict()

    assert set(payload) == {
        "title",
        "product_name",
        "target_engine",
        "status",
        "public_release",
        "landing_page",
        "pitch",
        "audience",
        "channels",
        "demo_assets",
        "oak_checklist",
        "blockers",
        "next_review_actions",
    }
    assert payload["landing_page"]["headline"]


def test_launch_markdown_contains_pitch_and_oak_sections():
    draft = _draft_for("Ω-GAME-T")
    markdown = draft.to_markdown()

    assert "## Landing page draft" in markdown
    assert "## Pitch draft" in markdown
    assert "## OAK checklist" in markdown
    assert draft.target_engine in markdown


def test_landing_page_rejects_empty_headline():
    try:
        LandingPageDraft(headline="", subheadline="s", bullets=["b"], call_to_action="review")
    except ValueError as exc:
        assert "headline" in str(exc)
    else:
        raise AssertionError("LandingPageDraft accepted empty headline")


def test_launch_forge_many_preserves_count():
    compiler = default_theory_compiler()
    productizer = default_productizer()
    issue_forge = default_issue_forge()
    sprint_forge = default_sprint_forge()
    demo_forge = default_demo_forge()
    launch_forge = default_launch_forge()
    worlds = compiler.compile_many([TheorySpec("Ω-CIRCUITS-T"), TheorySpec("Ω-ENERGY-T")])
    products = productizer.productize_many(worlds)
    issue_sets = issue_forge.forge_many(products)
    sprints = sprint_forge.forge_many(issue_sets)
    demos = demo_forge.forge_many(list(zip(products, sprints)))
    drafts = launch_forge.forge_many(list(zip(products, demos)))

    assert len(drafts) == 2
