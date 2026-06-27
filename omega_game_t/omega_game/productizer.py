"""Productizer-T for Ω-GAME-T++.

Convert a CompiledWorld into an OAK-safe product plan. This module prepares
plans only; it performs no external publication, sale, legal filing, or sending.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .theory_compiler import CompiledWorld, TheorySpec, default_theory_compiler


@dataclass(slots=True)
class ProductPlan:
    product_name: str
    source_theory: str
    target_engine: str
    audience: list[str]
    value_props: list[str]
    deliverables: list[str]
    revenue_paths: list[str]
    ip_classification: str
    oak_controls: list[str]
    launch_steps: list[str]
    risks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class Productizer:
    """Deterministic MVP product planner for compiled worlds."""

    def productize(self, compiled_world: CompiledWorld) -> ProductPlan:
        engine = compiled_world.target_engine
        if engine == "CircuitDungeon-T":
            return self._circuit_product(compiled_world)
        if engine == "EnergyCivilization-T":
            return self._energy_product(compiled_world)
        if engine == "ProofDetective-T":
            return self._proof_product(compiled_world)
        if engine == "FounderRPG-T":
            return self._founder_product(compiled_world)
        if engine == "PhysicsSandbox-T":
            return self._physics_product(compiled_world)
        if engine == "MyceliumRPG-T":
            return self._mycelium_product(compiled_world)
        return self._generic_product(compiled_world)

    def productize_theory(self, theory: TheorySpec) -> ProductPlan:
        return self.productize(default_theory_compiler().compile(theory))

    def productize_many(self, worlds: list[CompiledWorld]) -> list[ProductPlan]:
        return [self.productize(world) for world in worlds]

    def _base_controls(self) -> list[str]:
        return [
            "review_ip_status_before_public_release",
            "separate_learning_model_from_validated_claim",
            "human_review_for_external_publication",
            "record_limits_and_assumptions",
            "run_oakbench_before_launch",
        ]

    def _base_launch_steps(self) -> list[str]:
        return [
            "create_demo_script",
            "run_unit_tests",
            "run_oakbench_report",
            "prepare_readme_and_screenshots",
            "prepare_small_user_test",
            "review_ip_and_publication_status",
        ]

    def _circuit_product(self, world: CompiledWorld) -> ProductPlan:
        return ProductPlan(
            product_name="CircuitDungeon-T Lesson Pack",
            source_theory=world.theory.name,
            target_engine=world.target_engine,
            audience=["engineering_students", "teachers", "makers", "science_communicators"],
            value_props=[
                "learn RLC resonance through playable puzzles",
                "make units, tolerance and feedback visible",
                "turn circuit theory into measurable challenges",
            ],
            deliverables=["interactive_demo", "lesson_pack", "oakbench_report", "puzzle_set", "teacher_notes"],
            revenue_paths=["education_license", "premium_puzzle_modules", "workshop_package"],
            ip_classification="review_before_public_release",
            oak_controls=self._base_controls() + ["keep_hardware_guidance_out_of_game_scope"],
            launch_steps=self._base_launch_steps() + ["design_three_resonance_levels"],
            risks=["model_overclaim", "unclear_units", "too_much_guessing"],
        )

    def _energy_product(self, world: CompiledWorld) -> ProductPlan:
        return ProductPlan(
            product_name="EnergyCivilization-T Strategy Demo",
            source_theory=world.theory.name,
            target_engine=world.target_engine,
            audience=["energy_students", "climate_educators", "strategy_players", "microgrid_researchers"],
            value_props=[
                "understand storage, load and losses through play",
                "visualize service ratio and unmet demand",
                "teach resilience and tradeoffs in microgrid-like systems",
            ],
            deliverables=["strategy_demo", "scenario_pack", "oakbench_report", "energy_score_dashboard"],
            revenue_paths=["serious_game_license", "classroom_module", "consulting_demo"],
            ip_classification="review_before_public_release",
            oak_controls=self._base_controls() + ["show_model_limits_and_simplifications"],
            launch_steps=self._base_launch_steps() + ["create_sunny_and_stressed_scenarios"],
            risks=["overinterpreting_simplified_model", "unclear_loss_accounting"],
        )

    def _proof_product(self, world: CompiledWorld) -> ProductPlan:
        return ProductPlan(
            product_name="ProofDetective-T Evidence Training",
            source_theory=world.theory.name,
            target_engine=world.target_engine,
            audience=["students", "journalism_courses", "civic_education", "compliance_training"],
            value_props=[
                "distinguish rumor, signal, clue and corroborated evidence",
                "train counterhypothesis thinking",
                "teach careful source handling in a game format",
            ],
            deliverables=["case_simulator", "source_cards", "evidence_ladder", "oak_caution_report"],
            revenue_paths=["training_license", "course_module", "institutional_workshop"],
            ip_classification="review_before_public_release",
            oak_controls=self._base_controls() + ["avoid_real_person_accusations", "require_uncertainty_labels"],
            launch_steps=self._base_launch_steps() + ["create_fictional_case_dataset"],
            risks=["overconfidence", "source_confusion", "legal_sensitivity"],
        )

    def _founder_product(self, world: CompiledWorld) -> ProductPlan:
        return ProductPlan(
            product_name="FounderRPG-T Incubator Tool",
            source_theory=world.theory.name,
            target_engine=world.target_engine,
            audience=["founders", "incubators", "students", "innovation_programs"],
            value_props=[
                "simulate idea to prototype to customer signal",
                "make IP and scope decisions visible",
                "turn startup learning into a repeatable game loop",
            ],
            deliverables=["founder_scenario", "ip_checklist", "pitch_prompt_pack", "traction_scorecard"],
            revenue_paths=["incubator_license", "workshop_package", "premium_templates"],
            ip_classification="review_before_public_release",
            oak_controls=self._base_controls() + ["human_review_for_legal_or_ip_steps"],
            launch_steps=self._base_launch_steps() + ["create_one_hour_founder_sprint"],
            risks=["premature_publication", "scope_creep", "weak_customer_signal"],
        )

    def _physics_product(self, world: CompiledWorld) -> ProductPlan:
        return ProductPlan(
            product_name="PhysicsSandbox-T Interactive Lab",
            source_theory=world.theory.name,
            target_engine=world.target_engine,
            audience=["physics_students", "engineering_students", "research_prototypers"],
            value_props=[
                "turn models into inspectable simulations",
                "track residue, units and baseline comparisons",
                "separate hypothesis from validation",
            ],
            deliverables=["interactive_lab_demo", "model_cards", "residue_dashboard", "oakbench_report"],
            revenue_paths=["lab_module", "education_license", "research_demo_pack"],
            ip_classification="review_before_public_release",
            oak_controls=self._base_controls() + ["show_domain_of_validity"],
            launch_steps=self._base_launch_steps() + ["add_one_baseline_comparison"],
            risks=["model_instability", "unit_mismatch", "overclaim"],
        )

    def _mycelium_product(self, world: CompiledWorld) -> ProductPlan:
        return ProductPlan(
            product_name="MyceliumRPG-T Research Universe",
            source_theory=world.theory.name,
            target_engine=world.target_engine,
            audience=["researchers", "students", "builders", "community_members"],
            value_props=[
                "turn the Tristan corpus into a playable research universe",
                "connect theories, factions, quests and artifacts",
                "make memory and OAK visible inside the world",
            ],
            deliverables=["lore_demo", "world_map", "faction_cards", "quest_pack", "oakbench_report"],
            revenue_paths=["community_game", "premium_world_modules", "research_storytelling_pack"],
            ip_classification="review_before_public_release",
            oak_controls=self._base_controls() + ["trace_factions_to_theories"],
            launch_steps=self._base_launch_steps() + ["create_three_theory_factions"],
            risks=["decorative_lore_without_mechanics", "unclear_objective"],
        )

    def _generic_product(self, world: CompiledWorld) -> ProductPlan:
        return ProductPlan(
            product_name=f"{world.world_dna.name} Prototype",
            source_theory=world.theory.name,
            target_engine=world.target_engine,
            audience=["early_testers", "students", "builders"],
            value_props=["turn a theory into a minimal playable prototype"],
            deliverables=["text_demo", "readme", "oakbench_report"],
            revenue_paths=["prototype_review", "custom_module"],
            ip_classification="review_before_public_release",
            oak_controls=self._base_controls(),
            launch_steps=self._base_launch_steps(),
            risks=["generic_positioning", "unclear_audience"],
        )


def default_productizer() -> Productizer:
    return Productizer()


__all__ = ["ProductPlan", "Productizer", "default_productizer"]
