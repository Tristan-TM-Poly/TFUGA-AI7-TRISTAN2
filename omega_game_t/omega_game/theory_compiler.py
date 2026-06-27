"""TheoryCompiler-T for Ω-GAME-T++.

Compile a Tristan theory branch into WorldDNA, RuleGenome, a target engine,
OAK notes, and a product path. This is a deterministic MVP compiler, not a
claim that the underlying theory has been scientifically validated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class TheorySpec:
    name: str
    concepts: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    goal: str = "playable_world"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("TheorySpec.name must be non-empty.")


@dataclass(slots=True)
class WorldDNA:
    name: str
    genre: str
    core_loop: list[str]
    invariants: list[str]
    memory_positive: list[str]
    memory_negative: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "genre": self.genre,
            "core_loop": list(self.core_loop),
            "invariants": list(self.invariants),
            "memory": {
                "positive": list(self.memory_positive),
                "negative": list(self.memory_negative),
            },
        }


@dataclass(slots=True)
class RuleGenome:
    id: str
    input: list[str]
    invariant: list[str]
    success: list[str]
    failure: list[str]
    oak: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class CompiledWorld:
    theory: TheorySpec
    target_engine: str
    world_dna: WorldDNA
    rule_genomes: list[RuleGenome]
    oak_notes: list[str]
    product_path: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "theory": asdict(self.theory),
            "target_engine": self.target_engine,
            "world_dna": self.world_dna.to_dict(),
            "rule_genomes": [rule.to_dict() for rule in self.rule_genomes],
            "oak_notes": list(self.oak_notes),
            "product_path": list(self.product_path),
        }


class TheoryCompiler:
    """MVP deterministic compiler from theory branch to playable-world blueprint."""

    def compile(self, theory: TheorySpec) -> CompiledWorld:
        key = self._normalize(theory.name)
        if "CIRCUITS" in key:
            return self._compile_circuits(theory)
        if "ENERGY" in key or "ENERG" in key:
            return self._compile_energy(theory)
        if "PREUVE" in key or "PROOF" in key:
            return self._compile_proof(theory)
        if "COMP" in key or "REV" in key or "FOUNDER" in key:
            return self._compile_founder(theory)
        if any(token in key for token in ["MECH", "PFT", "LASER", "BAT", "PHYSICS"]):
            return self._compile_physics(theory)
        if "GAME" in key:
            return self._compile_mycelium(theory)
        return self._compile_generic(theory)

    def compile_many(self, theories: list[TheorySpec]) -> list[CompiledWorld]:
        return [self.compile(theory) for theory in theories]

    @staticmethod
    def _normalize(name: str) -> str:
        return name.upper().replace("Ω", "OMEGA")

    def _compile_circuits(self, theory: TheorySpec) -> CompiledWorld:
        return CompiledWorld(
            theory=theory,
            target_engine="CircuitDungeon-T",
            world_dna=WorldDNA(
                name="CircuitDungeon-T",
                genre="educational_puzzle",
                core_loop=["observe", "hypothesize", "test_frequency", "read_feedback", "adapt"],
                invariants=["visible_units", "measurable_feedback", "virtual_model", "OAK_safe"],
                memory_positive=["solved_resonance", "understood_feedback"],
                memory_negative=["repeated_guessing", "unclear_units", "frequency_outside_window"],
            ),
            rule_genomes=[
                RuleGenome(
                    id="rlc_resonance_gate",
                    input=["frequency_hz", "inductance_henry", "capacitance_farad"],
                    invariant=["frequency_positive", "tolerance_visible", "units_visible"],
                    success=["frequency_within_window"],
                    failure=["frequency_outside_window"],
                    oak=["virtual_model", "measurable_feedback", "OAK_safe"],
                )
            ],
            oak_notes=["Simulation is educational and virtual.", "Expose units, tolerance and feedback."],
            product_path=["demo", "lesson_pack", "web_prototype", "paid_module"],
        )

    def _compile_energy(self, theory: TheorySpec) -> CompiledWorld:
        return CompiledWorld(
            theory=theory,
            target_engine="EnergyCivilization-T",
            world_dna=WorldDNA(
                name="EnergyCivilization-T",
                genre="strategy_simulation",
                core_loop=["forecast", "allocate", "serve_load", "measure_losses", "upgrade"],
                invariants=["battery_bounded", "losses_non_negative", "service_ratio_visible", "OAK_safe"],
                memory_positive=["served_load", "stable_colony"],
                memory_negative=["unserved_load", "wasted_surplus", "unclear_forecast"],
            ),
            rule_genomes=[
                RuleGenome(
                    id="microgrid_turn_balance",
                    input=["solar_power_w", "load_power_w", "battery_energy_wh", "dt_hour"],
                    invariant=["battery_energy_bounded", "losses_non_negative", "load_non_negative"],
                    success=["service_ratio_high", "energy_score_high"],
                    failure=["unserved_load", "excess_losses"],
                    oak=["educational_model", "visible_units", "OAK_safe"],
                )
            ],
            oak_notes=["Keep the model pedagogical.", "Always show served load, unmet load and losses."],
            product_path=["demo", "classroom_scenario", "strategy_map", "serious_game"],
        )

    def _compile_proof(self, theory: TheorySpec) -> CompiledWorld:
        return CompiledWorld(
            theory=theory,
            target_engine="ProofDetective-T",
            world_dna=WorldDNA(
                name="ProofDetective-T",
                genre="evidence_reasoning_game",
                core_loop=["collect_source", "classify_signal", "test_hypothesis", "seek_counterhypothesis", "preserve_chain"],
                invariants=["source_visible", "uncertainty_visible", "counterhypothesis_required", "OAK_safe"],
                memory_positive=["corroborated_bundle", "innocent_hypothesis_checked"],
                memory_negative=["unsupported_claim", "missing_source", "overconfidence"],
            ),
            rule_genomes=[
                RuleGenome(
                    id="evidence_ladder",
                    input=["source", "claim", "corroboration", "counterhypothesis"],
                    invariant=["no_unsourced_accusation", "uncertainty_visible"],
                    success=["corroborated_signal"],
                    failure=["unsupported_claim"],
                    oak=["legal_caution", "no_defamation", "OAK_safe"],
                )
            ],
            oak_notes=["Distinguish rumor, signal, clue, corroborated evidence and judicial proof."],
            product_path=["training_demo", "case_simulator", "institutional_course"],
        )

    def _compile_founder(self, theory: TheorySpec) -> CompiledWorld:
        return CompiledWorld(
            theory=theory,
            target_engine="FounderRPG-T",
            world_dna=WorldDNA(
                name="FounderRPG-T",
                genre="startup_strategy_rpg",
                core_loop=["idea", "prototype", "OAK", "ip_check", "market_test", "revenue"],
                invariants=["ip_status_visible", "cost_visible", "risk_visible", "OAK_safe"],
                memory_positive=["validated_offer", "clear_pitch"],
                memory_negative=["premature_disclosure", "unclear_customer", "unbounded_scope"],
            ),
            rule_genomes=[
                RuleGenome(
                    id="prototype_to_revenue_loop",
                    input=["idea", "prototype", "customer_signal", "ip_status"],
                    invariant=["ip_classification_before_publication", "cost_visible"],
                    success=["validated_customer_signal"],
                    failure=["scope_creep", "no_customer_signal"],
                    oak=["commercial_caution", "consent_required", "OAK_safe"],
                )
            ],
            oak_notes=["Classify IP before public disclosure.", "Use human approval for sensitive commercial actions."],
            product_path=["workshop_game", "incubator_tool", "founder_saas"],
        )

    def _compile_physics(self, theory: TheorySpec) -> CompiledWorld:
        return CompiledWorld(
            theory=theory,
            target_engine="PhysicsSandbox-T",
            world_dna=WorldDNA(
                name="PhysicsSandbox-T",
                genre="scientific_sandbox",
                core_loop=["model", "simulate", "measure_residue", "compare_baseline", "iterate"],
                invariants=["units_visible", "residue_visible", "domain_visible", "OAK_safe"],
                memory_positive=["stable_model", "baseline_matched"],
                memory_negative=["unstable_step", "unit_mismatch", "overclaim"],
            ),
            rule_genomes=[
                RuleGenome(
                    id="science_model_step",
                    input=["state", "parameters", "dt", "baseline"],
                    invariant=["units_visible", "dt_positive", "residue_measured"],
                    success=["bounded_residue"],
                    failure=["unstable_residue"],
                    oak=["educational_model", "no_overclaim", "OAK_safe"],
                )
            ],
            oak_notes=["Separate model, simulation, hypothesis and validation."],
            product_path=["lab_demo", "benchmark_pack", "interactive_lesson"],
        )

    def _compile_mycelium(self, theory: TheorySpec) -> CompiledWorld:
        return CompiledWorld(
            theory=theory,
            target_engine="MyceliumRPG-T",
            world_dna=WorldDNA(
                name="MyceliumRPG-T",
                genre="research_universe_rpg",
                core_loop=["explore_branch", "connect_theory", "solve_world_puzzle", "record_memory", "unlock_branch"],
                invariants=["branch_traceable", "memory_visible", "OAK_safe"],
                memory_positive=["theory_connection_found", "world_branch_unlocked"],
                memory_negative=["unlinked_lore", "unclear_objective"],
            ),
            rule_genomes=[
                RuleGenome(
                    id="theory_to_faction_link",
                    input=["theory", "faction", "quest", "invariant"],
                    invariant=["theory_traceable", "quest_has_measure"],
                    success=["fertile_connection"],
                    failure=["decorative_only"],
                    oak=["OAK_safe", "no_false_claim"],
                )
            ],
            oak_notes=["Make every faction traceable to a theory and a measurable invariant."],
            product_path=["lore_demo", "research_rpg", "community_world"],
        )

    def _compile_generic(self, theory: TheorySpec) -> CompiledWorld:
        safe_name = theory.name.replace(" ", "-")
        return CompiledWorld(
            theory=theory,
            target_engine="TextWorld-T",
            world_dna=WorldDNA(
                name=f"{safe_name}-World",
                genre="generic_theory_world",
                core_loop=["observe", "choose", "test", "record", "improve"],
                invariants=["OAK_safe", "memory_visible", "measurable_feedback"],
                memory_positive=["useful_pattern"],
                memory_negative=["unclear_rule", "weak_feedback"],
            ),
            rule_genomes=[
                RuleGenome(
                    id="generic_theory_loop",
                    input=["state", "choice", "feedback"],
                    invariant=["feedback_visible", "choice_visible"],
                    success=["measurable_improvement"],
                    failure=["unclear_feedback"],
                    oak=["OAK_safe"],
                )
            ],
            oak_notes=["Generic compilation requires human review before productization."],
            product_path=["text_demo", "prototype", "oakbench"],
        )


def default_theory_compiler() -> TheoryCompiler:
    return TheoryCompiler()


__all__ = [
    "CompiledWorld",
    "RuleGenome",
    "TheoryCompiler",
    "TheorySpec",
    "WorldDNA",
    "default_theory_compiler",
]
