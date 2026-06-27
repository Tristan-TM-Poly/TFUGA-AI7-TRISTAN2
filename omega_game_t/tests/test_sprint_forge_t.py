from omega_game import (
    SprintTask,
    TheorySpec,
    default_issue_forge,
    default_productizer,
    default_sprint_forge,
    default_theory_compiler,
)


def _sprint_for(theory_name: str):
    world = default_theory_compiler().compile(TheorySpec(theory_name))
    plan = default_productizer().productize(world)
    issue_set = default_issue_forge().forge(plan)
    return default_sprint_forge().forge(issue_set)


def test_sprint_forge_creates_sprint_for_circuit_product():
    sprint = _sprint_for("Ω-CIRCUITS-T")

    assert sprint.target_engine == "CircuitDungeon-T"
    assert sprint.tasks
    assert sprint.total_points == sum(task.estimate_points for task in sprint.tasks)
    assert "no_external_release_from_sprint_plan" in sprint.oak_gates


def test_sprint_forge_prioritizes_p0_tasks_first():
    sprint = _sprint_for("Ω-ENERGY-T")
    priorities = [task.priority for task in sprint.tasks]

    first_p1_index = priorities.index("p1") if "p1" in priorities else len(priorities)
    assert all(priority == "p0" for priority in priorities[:first_p1_index])


def test_sprint_task_rejects_invalid_priority():
    try:
        SprintTask(
            task_id="bad",
            title="Bad",
            source_issue_title="Bad",
            priority="p9",
            estimate_points=1,
            execution_order=1,
            acceptance_criteria=["ok"],
            oak_gates=["ok"],
            definition_of_done=["ok"],
        )
    except ValueError as exc:
        assert "priority" in str(exc)
    else:
        raise AssertionError("SprintTask accepted invalid priority")


def test_sprint_plan_to_dict_has_contract_keys():
    payload = _sprint_for("Ω-CIRCUITS-T").to_dict()

    assert set(payload) == {
        "name",
        "source_epic",
        "source_theory",
        "target_engine",
        "cadence",
        "total_points",
        "tasks",
        "oak_gates",
        "definition_of_done",
    }
    assert payload["tasks"]


def test_sprint_plan_markdown_contains_oak_and_dod():
    sprint = _sprint_for("Ω-GAME-T")
    markdown = sprint.to_markdown()

    assert "## OAK gates" in markdown
    assert "## Definition of Done" in markdown
    assert sprint.target_engine in markdown


def test_sprint_forge_many_preserves_count():
    compiler = default_theory_compiler()
    productizer = default_productizer()
    issue_forge = default_issue_forge()
    worlds = compiler.compile_many([TheorySpec("Ω-CIRCUITS-T"), TheorySpec("Ω-ENERGY-T")])
    plans = productizer.productize_many(worlds)
    issue_sets = issue_forge.forge_many(plans)
    sprints = default_sprint_forge().forge_many(issue_sets)

    assert len(sprints) == 2
