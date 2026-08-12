import math

import pytest

from omega_cognitive_computer_t import (
    ArtifactType,
    CognitiveCompiler,
    CognitiveMemory,
    CognitiveRuntime,
    CognitiveState,
    EvidenceItem,
    Instruction,
    Opcode,
    Program,
    RepresentationMarket,
    RuntimeContext,
    TRISTAN_DISCOVER,
    ablation_profile,
    commutator,
    default_registry,
    discover_meta_skills,
    parse_assembly,
    pairwise_synergy,
    shapley_by_instruction,
    validate_crystallization,
)


def test_cir_fingerprint_is_stable_and_sensitive():
    a = CognitiveState(goals=["g"], objects={"b": 2, "a": 1})
    b = CognitiveState(goals=["g"], objects={"a": 1, "b": 2})
    assert a.fingerprint() == b.fingerprint()
    b.hypotheses.append("h")
    assert a.fingerprint() != b.fingerprint()


def test_evidence_strength_is_calibrated():
    with pytest.raises(ValueError):
        EvidenceItem("claim", strength=1.2)


def test_registry_declares_balancing_duals():
    r = default_registry()
    assert r.dual(Opcode.EXPAND) == Opcode.COMPRESS
    assert r.dual(Opcode.ZOOM) == Opcode.DEZOOM
    assert r.dual(Opcode.GENERALIZE) == Opcode.SPECIALIZE
    assert r.dual(Opcode.REMEMBER) == Opcode.FORGET


def test_assembly_aliases_compile():
    p = parse_assembly("REP geometric\nINV\nATTACK\nCRYST\n")
    assert p.opcodes() == (Opcode.REPRESENT, Opcode.INVARIANTS, Opcode.ATTACK, Opcode.CRYSTALLIZE)


def test_compiler_routes_math_to_proof_and_counterexample_work():
    p = CognitiveCompiler().compile("prove a theorem about polynomial zeros")
    assert p.metadata["fingerprint"]["domain"] == "mathematics"
    assert Opcode.PROVE in p.opcodes()
    assert Opcode.COUNTER in p.opcodes()
    assert Opcode.OAK in p.opcodes()


def test_runtime_is_transactional_and_jit_prunes_branch_explosion():
    state = CognitiveState(goals=["g"], hypotheses=[f"h{i}" for i in range(12)])
    p = Program("branch", (Instruction(Opcode.EXPAND), Instruction(Opcode.OAK)))
    result = CognitiveRuntime().run(p, state, context=RuntimeContext(branch_limit=5, budget=100, max_steps=30))
    assert len(result.state.hypotheses) <= 5
    assert any("PRUNE" in x for x in result.injected)
    assert result.trace
    assert all(t.before_fingerprint and t.after_fingerprint for t in result.trace)


def test_runtime_rolls_back_bad_hook():
    def bad_hook(state, inst, ctx):
        state.hypotheses.append("corruption")
        raise RuntimeError("boom")

    initial = CognitiveState(goals=["g"])
    result = CognitiveRuntime().run(Program("bad", (Instruction(Opcode.EXPAND),)), initial, context=RuntimeContext(budget=10, hooks={Opcode.EXPAND: bad_hook}))
    assert "corruption" not in result.state.hypotheses
    assert result.trace[0].rolled_back


def test_oak_never_equates_review_ready_with_truth():
    state = CognitiveState(goals=["g"], hypotheses=["h"], evidence=[EvidenceItem("h", "test", 0.7)])
    state.metadata["counter_hypotheses"] = ["not h"]
    result = CognitiveRuntime().run(Program("oak", (Instruction(Opcode.OAK),)), state, context=RuntimeContext(budget=10))
    assert result.state.metadata["oak"]["status"] == "review_ready"
    assert "not proof/truth" in result.state.metadata["oak"]["note"]


def test_crystallization_requires_seven_fields():
    incomplete = validate_crystallization({"spec": "x"})
    assert not incomplete.is_clear
    payload = {
        "artifact_type": ArtifactType.PROTOTYPE.value,
        "spec": "spec", "implementation": "impl", "test": "test", "baseline": "baseline",
        "result": "result", "provenance": "prov", "limitations": "limits",
    }
    complete = validate_crystallization(payload)
    assert complete.is_clear
    assert complete.record.artifact_type == ArtifactType.PROTOTYPE


def test_memory_retrieves_strategy_not_only_answer():
    mem = CognitiveMemory()
    state = CognitiveState(goals=["matrix determinant optimization"])
    p = Program("p", (Instruction(Opcode.REPRESENT, ("algebraic",)), Instruction(Opcode.ATTACK)))
    mem.remember_positive(state, "matrix determinant optimization", p, score=0.8)
    hits = mem.nearest("optimize matrix determinant")
    assert hits and hits[0][1].strategy == ("REPRESENT", "ATTACK")


def test_representation_market_keeps_exploration_floor():
    market = RepresentationMarket(("algebraic", "geometric", "numeric"), total_budget=1.0, exploration_floor=0.05)
    market.observe("geometric", information_gain=10, success=True)
    budgets = market.rebalance()
    assert math.isclose(sum(budgets.values()), 1.0, rel_tol=1e-9)
    assert all(v >= 0.05 for v in budgets.values())
    assert budgets["geometric"] > budgets["algebraic"]


def test_cognitive_algebra_detects_order_effect():
    state = CognitiveState(goals=["g"], hypotheses=["h"])
    report = commutator(Instruction(Opcode.EXPAND), Instruction(Opcode.PRUNE, ("2",)), state)
    assert report.distance > 0
    assert report.ab_fingerprint != report.ba_fingerprint


def test_superinstruction_is_composed_and_oak_gated():
    ops = TRISTAN_DISCOVER.opcodes()
    assert Opcode.REPRESENT in ops
    assert Opcode.ATTACK in ops
    assert Opcode.OAK in ops
    assert ops[-1] == Opcode.CRYSTALLIZE


def test_profiler_and_meta_skill_discovery_use_external_scoring():
    p = Program("toy", (Instruction(Opcode.REPRESENT), Instruction(Opcode.ATTACK), Instruction(Opcode.OAK)))
    score = lambda prog: float(len(prog.instructions))
    abl = ablation_profile(p, score)
    assert abl == {0: 1.0, 1: 1.0, 2: 1.0}
    shap = shapley_by_instruction(p, score)
    assert all(math.isclose(v, 1.0) for v in shap.values())
    syn = pairwise_synergy(p, score)
    assert all(math.isclose(v, 0.0) for v in syn.values())
    skills = discover_meta_skills([p.instructions, p.instructions], n=2, min_count=2)
    assert skills[0][0] == 2
