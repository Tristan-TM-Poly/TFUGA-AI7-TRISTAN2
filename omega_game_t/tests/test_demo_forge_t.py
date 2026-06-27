from omega_game import (
    DemoScene,
    TheorySpec,
    default_demo_forge,
    default_issue_forge,
    default_productizer,
    default_sprint_forge,
    default_theory_compiler,
)


def _demo_for(theory_name: str):
    world = default_theory_compiler().compile(TheorySpec(theory_name))
    product = default_productizer().productize(world)
    issue_set = default_issue_forge().forge(product)
    sprint = default_sprint_forge().forge(issue_set)
    return default_demo_forge().forge(product, sprint)


def test_demo_forge_creates_demo_for_circuit_product():
    demo = _demo_for("Ω-CIRCUITS-T")

    assert demo.product_name == "CircuitDungeon-T Lesson Pack"
    assert demo.target_engine == "CircuitDungeon-T"
    assert len(demo.scenes) >= 6
    assert "demo_is_internal_until_reviewed" in demo.oak_checklist


def test_demo_plan_to_dict_has_contract_keys():
    payload = _demo_for("Ω-ENERGY-T").to_dict()

    assert set(payload) == {
        "title",
        "product_name",
        "target_engine",
        "audience",
        "opening_hook",
        "scenes",
        "oak_checklist",
        "success_signals",
        "rehearsal_steps",
    }
    assert payload["scenes"]


def test_demo_markdown_contains_oak_and_success_signals():
    demo = _demo_for("Ω-GAME-T")
    markdown = demo.to_markdown()

    assert "## OAK checklist" in markdown
    assert "## Success signals" in markdown
    assert demo.target_engine in markdown


def test_demo_scene_rejects_empty_id():
    try:
        DemoScene(scene_id="", title="Bad", narration="n", action="a")
    except ValueError as exc:
        assert "scene_id" in str(exc)
    else:
        raise AssertionError("DemoScene accepted empty scene_id")


def test_demo_forge_many_preserves_count():
    compiler = default_theory_compiler()
    productizer = default_productizer()
    issue_forge = default_issue_forge()
    sprint_forge = default_sprint_forge()
    demo_forge = default_demo_forge()
    worlds = compiler.compile_many([TheorySpec("Ω-CIRCUITS-T"), TheorySpec("Ω-ENERGY-T")])
    products = productizer.productize_many(worlds)
    issue_sets = issue_forge.forge_many(products)
    sprints = sprint_forge.forge_many(issue_sets)
    demos = demo_forge.forge_many(list(zip(products, sprints)))

    assert len(demos) == 2
