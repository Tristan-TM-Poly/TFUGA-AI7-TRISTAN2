from dataclasses import replace

import pytest

from sage_tristan.greatsages import get_profile
from sage_tristan.greatsages_time_machine import operator_registry
from sage_tristan.representation_noether_compiler import ceres_representation_compiler
from sage_tristan.tensor_research_compiler import (
    CognitiveProgram,
    Instruction,
    LLMTRegistry,
    Opcode,
    PermissionScope,
    PersonLLMT,
    ProgramStatus,
    ShadowFactory,
    ShadowMirror,
    ShadowOutput,
    ShadowRole,
    SparseTensorCoalitionCompiler,
    ValueType,
    audit_program,
    bridge_program_to_ceres_path,
    ceres_cognitive_program,
    compile_report,
    person_llmt_from_profile,
    synergy_receipt,
    synthetic_tensor_fixture,
    tensor_merge,
)


def test_gauss_bridge_is_logical_model_not_person():
    llmt = person_llmt_from_profile(get_profile("gauss"))
    assert llmt.person_id == "gauss"
    assert llmt.model_not_person is True
    assert llmt.historical_mind_certified is False
    assert "representation_switch" in llmt.operator_ids
    assert llmt.source_ids


def test_person_llmt_refuses_historical_mind_certification():
    with pytest.raises(ValueError):
        PersonLLMT(
            "x",
            "v1",
            ("corpus",),
            ("source",),
            ("op",),
            ("rep",),
            ("cap",),
            historical_mind_certified=True,
        )


def test_registry_rejects_duplicate_people():
    llmt = PersonLLMT("x", "v1", (), (), ("op",), ("rep",), ("cap",))
    with pytest.raises(ValueError):
        LLMTRegistry((llmt, llmt))


def test_private_shadow_requires_consent():
    registry = LLMTRegistry(
        (
            PersonLLMT(
                "person_public",
                "v1",
                (),
                ("source",),
                ("op",),
                ("rep",),
                ("cap",),
                permission_scope=PermissionScope.PUBLIC_ONLY,
            ),
        )
    )
    factory = ShadowFactory(registry)
    with pytest.raises(PermissionError):
        factory.create(
            "person_public",
            role=ShadowRole.SOLVER,
            domain="test",
            mirror=ShadowMirror.MODERN,
            operator_ids=("op",),
            representation_ids=("rep",),
            objective="test",
            requires_private_data=True,
        )


def test_shadow_is_ephemeral_and_operator_subset_is_enforced():
    registry, _ = synthetic_tensor_fixture()
    factory = ShadowFactory(registry)
    shadow = factory.create(
        "person_a",
        role=ShadowRole.SOLVER,
        domain="inverse_problem",
        mirror=ShadowMirror.COMPUTATIONAL,
        operator_ids=("representation_switch",),
        representation_ids=("native",),
        objective="test",
    )
    assert shadow.ephemeral is True
    assert shadow.model_not_person is True
    with pytest.raises(ValueError):
        factory.create(
            "person_a",
            role=ShadowRole.SOLVER,
            domain="inverse_problem",
            mirror=ShadowMirror.COMPUTATIONAL,
            operator_ids=("not_supported",),
            representation_ids=("native",),
            objective="test",
        )


def test_sparse_go_max_router_selects_small_complementary_coalition():
    registry, problem = synthetic_tensor_fixture()
    receipt = SparseTensorCoalitionCompiler(registry).compile(problem, max_llmts=3)
    assert receipt.selected_person_ids == ("person_a", "person_b")
    assert receipt.rejected_person_ids == ("person_c",)
    assert receipt.uncovered_capabilities == ()
    assert receipt.stop_reason == "required_capabilities_covered"
    assert receipt.greedy_heuristic_not_global_optimum is True
    assert receipt.full_tensor_materialized is False
    assert all(item.marginal_gain > 0 for item in receipt.marginals)


def test_router_obeys_risk_budget():
    registry, problem = synthetic_tensor_fixture()
    risky = replace(registry.get("person_b"), risk=0.9)
    constrained = LLMTRegistry((registry.get("person_a"), risky, registry.get("person_c")))
    receipt = SparseTensorCoalitionCompiler(constrained).compile(problem)
    assert "residual_control" in receipt.uncovered_capabilities


def test_ceres_program_is_type_safe_and_r05_gated():
    program = ceres_cognitive_program()
    audit = audit_program(
        program,
        allowed_operator_ids=operator_registry(get_profile("gauss")),
        representation_compiler=ceres_representation_compiler(),
    )
    assert audit.status is ProgramStatus.ADMISSIBLE_SOFTWARE_PROGRAM
    assert audit.type_safe is True
    assert audit.representation_gate_safe is True
    assert audit.unknown_operator_ids == ()
    assert audit.quarantined_morphism_ids == ()
    assert audit.program_is_execution_trace is False


def test_bad_type_transition_fails_closed():
    good = ceres_cognitive_program()
    bad_instruction = Instruction(
        "bad",
        Opcode.OAK,
        ValueType.CLAIM,
        ValueType.OAK_RECEIPT,
    )
    bad = CognitiveProgram(
        "bad_program",
        good.problem_id,
        (good.instructions[0], bad_instruction),
        (),
        max_cost=1.0,
        max_depth=5,
        stop_conditions=(),
    )
    audit = audit_program(
        bad,
        allowed_operator_ids=operator_registry(get_profile("gauss")),
        representation_compiler=ceres_representation_compiler(),
    )
    assert audit.status is ProgramStatus.QUARANTINE
    assert audit.type_safe is False


def test_missing_representation_backend_fails_closed():
    program = ceres_cognitive_program()
    empty = ceres_representation_compiler()
    empty = replace(empty, morphisms=())
    audit = audit_program(
        program,
        allowed_operator_ids=operator_registry(get_profile("gauss")),
        representation_compiler=empty,
    )
    assert audit.status is ProgramStatus.QUARANTINE
    assert audit.representation_gate_safe is False
    assert any("missing R0.5 morphism" in failure for failure in audit.failures)


def test_program_and_discovery_path_are_separate_but_operator_trace_matches():
    program = ceres_cognitive_program()
    path, receipt = bridge_program_to_ceres_path(program)
    assert receipt.exact_operator_trace_match is True
    assert receipt.program_is_execution_trace is False
    assert receipt.discovery_path_is_runtime_trace is True
    assert receipt.discovery_path_id == path.path_id
    assert receipt.program_operator_ids == (
        "representation_switch",
        "approximation_residual",
        "invariant_search",
    )


def test_tensor_merge_keeps_consensus_and_diff_without_truth_claim():
    receipt = tensor_merge(
        (
            ShadowOutput("s1", ("shared", "a"), ("same_source", "e1")),
            ShadowOutput("s2", ("shared", "b"), ("same_source", "e2")),
        )
    )
    assert receipt.consensus_claim_ids == ("shared",)
    assert receipt.consensus_is_truth is False
    assert receipt.evidence_independence_not_inferred is True
    assert receipt.unique_evidence_ids == ("e1", "e2", "same_source")
    diff = dict(receipt.divergent_claim_ids_by_shadow)
    assert diff["s1"] == ("a",)
    assert diff["s2"] == ("b",)


def test_synergy_receipt_is_not_causal_proof():
    receipt = synergy_receipt("a", "b", baseline=0.1, left=0.4, right=0.35, coalition=0.85)
    assert receipt.synergy == pytest.approx(0.2)
    assert receipt.causal_synergy_proven is False


def test_compile_report_exposes_oak_boundaries_and_sparse_tensor():
    report = compile_report()
    assert report["release"] == "R0.6"
    assert report["person_llmt_is_person"] is False
    assert report["shadow_is_person"] is False
    assert report["shadow_is_ephemeral"] is True
    assert report["consensus_is_truth"] is False
    assert report["synergy_is_causal_proof"] is False
    assert report["full_tensor_expansion_required"] is False
    assert report["routing_is_global_optimum_proven"] is False
    assert report["r05_representation_backend_required"] is True
    assert report["r04_runtime_trace_required"] is True
    assert report["program_audit"]["status"] == "admissible_software_program"
    assert report["program_path_bridge"]["exact_operator_trace_match"] is True
    assert report["synthetic_coalition"]["selected_person_ids"] == ("person_a", "person_b")
    assert report["sparse_tensor"]["materialized_shadow_count"] < report["sparse_tensor"]["coarse_theoretical_upper_bound"]
