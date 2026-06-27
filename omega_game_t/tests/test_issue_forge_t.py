from omega_game import TheorySpec, default_issue_forge, default_productizer, default_theory_compiler


def _issue_set_for(theory_name: str):
    world = default_theory_compiler().compile(TheorySpec(theory_name))
    plan = default_productizer().productize(world)
    return default_issue_forge().forge(plan)


def test_issue_forge_creates_issue_set_for_circuit_product():
    issue_set = _issue_set_for("Ω-CIRCUITS-T")

    assert issue_set.product_name == "CircuitDungeon-T Lesson Pack"
    assert issue_set.target_engine == "CircuitDungeon-T"
    assert issue_set.issues
    assert "omega-game-t" in issue_set.label_plan.labels
    assert "ip-review" in issue_set.label_plan.labels


def test_issue_forge_creates_deliverable_and_oak_issues():
    issue_set = _issue_set_for("Ω-ENERGY-T")
    titles = [issue.title for issue in issue_set.issues]

    assert any("OAKBench" in title or "ProductBench" in title for title in titles)
    assert any("Reduce top OAK risks" in title for title in titles)
    assert any("Prepare launch-readiness" in title for title in titles)


def test_issue_spec_markdown_contains_acceptance_and_oak_controls():
    issue = _issue_set_for("Ω-CIRCUITS-T").issues[0]
    markdown = issue.to_markdown()

    assert "## Acceptance criteria" in markdown
    assert "## OAK controls" in markdown
    assert "## M+ expected" in markdown
    assert "## M- avoided" in markdown


def test_issue_set_to_dict_has_contract_keys():
    payload = _issue_set_for("Ω-CIRCUITS-T").to_dict()

    assert set(payload) == {
        "epic_title",
        "source_theory",
        "target_engine",
        "product_name",
        "milestone",
        "label_plan",
        "issues",
    }
    assert payload["issues"]


def test_issue_set_markdown_contains_epic_context():
    issue_set = _issue_set_for("Ω-GAME-T")
    markdown = issue_set.to_markdown()

    assert issue_set.epic_title in markdown
    assert issue_set.source_theory in markdown
    assert issue_set.target_engine in markdown


def test_issue_forge_many_preserves_count():
    compiler = default_theory_compiler()
    productizer = default_productizer()
    worlds = compiler.compile_many([TheorySpec("Ω-CIRCUITS-T"), TheorySpec("Ω-ENERGY-T")])
    plans = productizer.productize_many(worlds)
    issue_sets = default_issue_forge().forge_many(plans)

    assert len(issue_sets) == 2
