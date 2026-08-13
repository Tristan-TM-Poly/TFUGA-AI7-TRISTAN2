from omega_uvtc_t import CompileRequest, Effect, KnowledgeMake, KnowledgeNode, KnowledgeStatus, PowerDensityInput, Primitive, UTIRProgram, compile_intent, instruction, power_density, superoptimize

def test_16_primitives_cover_six_kernels():
    from omega_uvtc_t.model import Kernel
    assert len(Primitive) == 16
    assert {instruction(p).kernel for p in Primitive} == set(Kernel)

def test_intent_compiler_is_deterministic_and_oak_bounded():
    req = CompileRequest("analyze system", "validated artifact", formal=True)
    a = compile_intent(req); b = compile_intent(req)
    assert a.fingerprint == b.fingerprint
    assert a.count(Primitive.SEARCH) == 1
    assert a.count(Primitive.PROVE) == 1
    assert a.instructions[-1].primitive == Primitive.CRYSTALLIZE

def test_superoptimizer_dedups_but_preserves_replication():
    base = instruction(Primitive.SEARCH, args={"q": "same"})
    replica = instruction(Primitive.MEASURE, args={"q": "same"}, independent_replication=True)
    r = superoptimize(UTIRProgram("p", (base, base, replica, replica)))
    assert r.after_count == 3
    assert sum(i.independent_replication for i in r.program.instructions) == 2

def test_safe_pruning_uses_optimistic_gain():
    weak = instruction(Primitive.BRANCH, predicted_verified_gain=0.01, gain_uncertainty=0.01, cost=0.10, risk=0.01)
    r = superoptimize(UTIRProgram("p", (instruction(Primitive.STATE), weak, instruction(Primitive.OAK))))
    assert Primitive.BRANCH not in [i.primitive for i in r.program.instructions]

def test_non_elidable_effect_is_never_deduped():
    a = instruction(Primitive.TRANSFORM, args={"x": 1}, effects=(Effect.WRITE,))
    assert superoptimize(UTIRProgram("p", (a, a))).after_count == 2

def test_knowledge_make_scc_cascade():
    nodes = (KnowledgeNode("A", "dataset", "ha", status=KnowledgeStatus.VALIDATED), KnowledgeNode("B", "model", "hb", ("A",), status=KnowledgeStatus.VALIDATED), KnowledgeNode("C", "claim", "hc", ("B", "D"), status=KnowledgeStatus.VALIDATED), KnowledgeNode("D", "claim", "hd", ("C",), status=KnowledgeStatus.VALIDATED), KnowledgeNode("E", "artifact", "he", ("C",), status=KnowledgeStatus.VALIDATED), KnowledgeNode("X", "other", "hx", status=KnowledgeStatus.VALIDATED))
    result = KnowledgeMake(nodes).invalidate(["B"])
    assert set(result.invalidated) == {"B", "C", "D", "E"}
    state = {n.node_id: n.status for n in result.nodes}
    assert state["A"] == KnowledgeStatus.VALIDATED
    assert state["E"] == KnowledgeStatus.STALE

def test_power_density_boundary():
    assert power_density(PowerDensityInput(2, 1, 1, 1, 0, 0, 0)) == 1.5
