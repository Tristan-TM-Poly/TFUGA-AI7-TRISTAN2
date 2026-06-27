from omega_game import TheorySpec, default_productizer, default_theory_compiler


def _plan_for(theory_name: str):
    world = default_theory_compiler().compile(TheorySpec(theory_name))
    return default_productizer().productize(world)


def test_productizer_turns_circuits_world_into_lesson_pack():
    plan = _plan_for("Ω-CIRCUITS-T")

    assert plan.target_engine == "CircuitDungeon-T"
    assert "Lesson Pack" in plan.product_name
    assert "education_license" in plan.revenue_paths
    assert "run_oakbench_before_launch" in plan.oak_controls


def test_productizer_turns_energy_world_into_strategy_demo():
    plan = _plan_for("Ω-ENERGY-T")

    assert plan.target_engine == "EnergyCivilization-T"
    assert "Strategy" in plan.product_name
    assert "serious_game_license" in plan.revenue_paths


def test_productizer_turns_proof_world_into_training_plan():
    plan = _plan_for("Ω-PREUVE-T")

    assert plan.target_engine == "ProofDetective-T"
    assert "Evidence" in plan.product_name
    assert "avoid_real_person_accusations" in plan.oak_controls


def test_productizer_turns_founder_world_into_incubator_tool():
    plan = _plan_for("Ω-COMP-REV-IP")

    assert plan.target_engine == "FounderRPG-T"
    assert "Incubator" in plan.product_name
    assert "human_review_for_legal_or_ip_steps" in plan.oak_controls


def test_productizer_turns_physics_world_into_interactive_lab():
    plan = _plan_for("Ω-LASER-T")

    assert plan.target_engine == "PhysicsSandbox-T"
    assert "Interactive Lab" in plan.product_name
    assert "show_domain_of_validity" in plan.oak_controls


def test_productizer_turns_game_world_into_mycelium_product():
    plan = _plan_for("Ω-GAME-T")

    assert plan.target_engine == "MyceliumRPG-T"
    assert "Research Universe" in plan.product_name


def test_product_plan_to_dict_has_contract_keys():
    payload = _plan_for("Ω-CIRCUITS-T").to_dict()

    assert set(payload) == {
        "product_name",
        "source_theory",
        "target_engine",
        "audience",
        "value_props",
        "deliverables",
        "revenue_paths",
        "ip_classification",
        "oak_controls",
        "launch_steps",
        "risks",
    }
    assert payload["launch_steps"]
