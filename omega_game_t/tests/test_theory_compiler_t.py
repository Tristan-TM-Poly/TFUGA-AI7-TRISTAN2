from omega_game import TheorySpec, default_theory_compiler


def test_theory_compiler_compiles_circuits_to_circuit_dungeon():
    compiled = default_theory_compiler().compile(TheorySpec("Ω-CIRCUITS-T"))

    assert compiled.target_engine == "CircuitDungeon-T"
    assert compiled.world_dna.name == "CircuitDungeon-T"
    assert compiled.rule_genomes[0].id == "rlc_resonance_gate"
    assert compiled.product_path


def test_theory_compiler_compiles_energy_to_energy_civilization():
    compiled = default_theory_compiler().compile(TheorySpec("Ω-ENERGY-T"))

    assert compiled.target_engine == "EnergyCivilization-T"
    assert compiled.world_dna.name == "EnergyCivilization-T"
    assert compiled.rule_genomes[0].id == "microgrid_turn_balance"


def test_theory_compiler_compiles_proof_to_proof_detective():
    compiled = default_theory_compiler().compile(TheorySpec("Ω-PREUVE-T"))

    assert compiled.target_engine == "ProofDetective-T"
    assert compiled.world_dna.name == "ProofDetective-T"
    assert "counterhypothesis_required" in compiled.world_dna.invariants


def test_theory_compiler_compiles_founder_branch():
    compiled = default_theory_compiler().compile(TheorySpec("Ω-COMP-REV-IP"))

    assert compiled.target_engine == "FounderRPG-T"
    assert compiled.rule_genomes[0].id == "prototype_to_revenue_loop"


def test_theory_compiler_compiles_physics_branch():
    compiled = default_theory_compiler().compile(TheorySpec("Ω-LASER-T"))

    assert compiled.target_engine == "PhysicsSandbox-T"
    assert compiled.rule_genomes[0].id == "science_model_step"


def test_theory_compiler_compiles_game_branch_to_mycelium_rpg():
    compiled = default_theory_compiler().compile(TheorySpec("Ω-GAME-T"))

    assert compiled.target_engine == "MyceliumRPG-T"
    assert compiled.world_dna.name == "MyceliumRPG-T"


def test_theory_compiler_generic_fallback_is_textworld():
    compiled = default_theory_compiler().compile(TheorySpec("Ω-UNKNOWN-T"))

    assert compiled.target_engine == "TextWorld-T"
    assert compiled.rule_genomes[0].id == "generic_theory_loop"


def test_compiled_world_to_dict_has_contract_keys():
    payload = default_theory_compiler().compile(TheorySpec("Ω-CIRCUITS-T")).to_dict()

    assert set(payload) == {"theory", "target_engine", "world_dna", "rule_genomes", "oak_notes", "product_path"}
    assert payload["world_dna"]["memory"]["positive"]
