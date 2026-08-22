from omega_uvtc_t.artifact import GOArtifact, GateState, ReproCapsule, ValidationVector, validate_go_artifact
from omega_uvtc_t.certificates import certify_optimization
from omega_uvtc_t.compiler import CompileRequest, compile_intent
from omega_uvtc_t.knowledge import KnowledgeMake, KnowledgeNode, KnowledgeStatus
from omega_uvtc_t.model import Primitive, UTIRProgram, instruction
from omega_uvtc_t.optimizer import superoptimize
from omega_uvtc_t.pipeline import run_pipeline
from omega_uvtc_t.portfolio import GoCandidate, pareto_front, select_go_move
from omega_uvtc_t.residual import ResidualGenome, ResidualKind, ResidualRecord
from omega_uvtc_t.semantics import execute_abstract


def test_r02_semantics_accepts_compiled_program_and_keeps_obligations():
    receipt = execute_abstract(compile_intent(CompileRequest("analyze", "reviewable artifact", formal=True)))
    assert receipt.status == "PASS"
    assert receipt.final_state.oak_checked
    assert receipt.final_state.crystallized
    assert "formal_proof_receipt_required" in receipt.final_state.obligations
    assert "goartifact_validation_required" in receipt.final_state.obligations


def test_r02_semantics_blocks_invalid_order():
    program = UTIRProgram("bad", (instruction(Primitive.STATE), instruction(Primitive.CRYSTALLIZE)))
    receipt = execute_abstract(program)
    assert receipt.status == "BLOCK"
    assert "CRYSTALLIZE requires OAK" in receipt.blockers[0]


def test_r02_optimizer_certificate_preserves_replication_and_protected_trace():
    repeated = instruction(Primitive.SEARCH, args={"q": "same"})
    replica = instruction(Primitive.MEASURE, args={"q": "same"}, independent_replication=True)
    source = UTIRProgram("p", (
        instruction(Primitive.STATE), repeated, repeated, replica, replica,
        instruction(Primitive.FALSIFY), instruction(Primitive.OAK),
    ))
    report = superoptimize(source)
    cert = certify_optimization(source, report)
    assert cert.status == "PASS"
    assert cert.semantic_equivalence_proven is False
    assert cert.replication_multiset_preserved


def test_r02_artifact_reproducibility_pass_requires_capsule():
    artifact = GOArtifact(
        artifact_id="A", artifact_kind="software", content_hash="abc", tests=("t",), provenance=("p",),
        validation=ValidationVector(integrity=GateState.PASS, reproducibility=GateState.PASS),
    )
    report = validate_go_artifact(artifact)
    assert report.status == "HOLD"
    assert "reproducibility_pass_requires_capsule" in report.blockers


def test_r02_artifact_contract_passes_with_capsule():
    capsule = ReproCapsule("env", ("in",), ("dep",), ("step",), ("out",))
    artifact = GOArtifact(
        artifact_id="A", artifact_kind="software", content_hash="abc", evidence_refs=("E",),
        tests=("t",), provenance=("p",),
        validation=ValidationVector(integrity=GateState.PASS, reproducibility=GateState.PASS),
        repro_capsule=capsule,
    )
    assert validate_go_artifact(artifact).status == "PASS"


def test_r02_pareto_front_drops_dominated_candidate():
    a = GoCandidate("a", 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1)
    b = GoCandidate("b", 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2)
    c = GoCandidate("c", 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
    front = pareto_front((a, b, c))
    assert {x.candidate_id for x in front} == {"a", "c"}


def test_r02_go_selection_can_continue_or_stop():
    strong = GoCandidate("strong", 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1)
    weak = GoCandidate("weak", 1, 0, 0, 0, 0, 10, 10, 10, 10, 10, 10)
    assert select_go_move((strong,), minimum_density=0.1).recurse
    assert select_go_move((weak,), minimum_density=1.0).selected_id is None


def test_r02_residual_genome_prioritizes_uncertainty_aware_upper_proxy():
    a = ResidualRecord("a", ResidualKind.NUMERIC, "o", "p", "L2", 1.0, 0.0)
    b = ResidualRecord("b", ResidualKind.SEMANTIC, "o", "p", "mismatch", 0.5, 0.4)
    assert ResidualGenome((a, b)).research_priority()[0] == "b"


def test_r02_knowledge_make_preserves_scc_invalidation():
    nodes = (
        KnowledgeNode("A", "dataset", "ha", status=KnowledgeStatus.VALIDATED),
        KnowledgeNode("B", "model", "hb", ("A",), status=KnowledgeStatus.VALIDATED),
        KnowledgeNode("C", "claim", "hc", ("B", "D"), status=KnowledgeStatus.VALIDATED),
        KnowledgeNode("D", "claim", "hd", ("C",), status=KnowledgeStatus.VALIDATED),
    )
    assert set(KnowledgeMake(nodes).invalidate(["B"]).invalidated) == {"B", "C", "D"}


def test_r02_pipeline_is_deterministic_and_explicitly_bounded():
    req = CompileRequest("derive artifact", "reviewable output", formal=True)
    first = run_pipeline(req)
    second = run_pipeline(req)
    assert first.fingerprint == second.fingerprint
    assert first.status == "PASS"
    assert first.semantic_equivalence_proven is False
    assert "goartifact_validation_required" in first.unresolved_obligations
