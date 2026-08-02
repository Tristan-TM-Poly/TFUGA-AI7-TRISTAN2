from datetime import datetime, timezone
import pytest

from omega_re_t.authorization import (
    AuthorizationAction,
    AuthorizationContract,
    AuthorizationGate,
    AuthorizationRequest,
    DataClass,
    Decision,
    StopCondition,
    synthetic_contract,
)
from omega_re_t.re_ir import (
    EdgeKind,
    EpistemicLevel,
    IREdge,
    IRHyperedge,
    IRNode,
    NodeKind,
    REIRGraph,
    make_claim_bundle,
)


def test_synthetic_contract_roundtrip_and_digest():
    contract = synthetic_contract("alpha")
    restored = AuthorizationContract.from_json(contract.to_json())
    assert restored.digest == contract.digest
    assert restored.subject_id == "alpha"
    assert restored.is_active(datetime.now(timezone.utc))


def test_authorization_gate_allows_declared_observation():
    gate = AuthorizationGate(synthetic_contract())
    result = gate.evaluate(
        AuthorizationRequest(
            AuthorizationAction.OBSERVE,
            DataClass.SYNTHETIC,
        )
    )
    assert result.decision is Decision.ALLOW
    assert result.allowed


def test_authorization_gate_fails_closed_for_undeclared_data():
    gate = AuthorizationGate(synthetic_contract())
    request = AuthorizationRequest(
        AuthorizationAction.OBSERVE,
        DataClass.CONFIDENTIAL,
    )
    result = gate.evaluate(request)
    assert result.decision is Decision.DENY
    assert "data_class_not_allowed" in result.reasons
    with pytest.raises(PermissionError):
        gate.require(request)


def test_sensitive_action_requires_review_even_if_listed():
    base = synthetic_contract()
    contract = AuthorizationContract(
        contract_id="sensitive",
        subject_id="toy",
        authority="owner",
        purpose="test",
        allowed_actions=(
            base.allowed_actions
            | {AuthorizationAction.DESTRUCTIVE_TEST}
        ),
        allowed_data_classes=base.allowed_data_classes,
    )
    result = AuthorizationGate(contract).evaluate(
        AuthorizationRequest(
            AuthorizationAction.DESTRUCTIVE_TEST,
            DataClass.SYNTHETIC,
        )
    )
    assert result.decision is Decision.REQUIRE_REVIEW


def test_authorization_budget_and_clean_room_rules():
    contract = AuthorizationContract(
        contract_id="bounded",
        subject_id="toy",
        authority="owner",
        purpose="test",
        allowed_actions=frozenset({AuthorizationAction.QUERY}),
        max_experiments=2,
        max_cost=3,
        clean_room_required=True,
        stop_conditions=(
            StopCondition("scope", "stop on scope change"),
        ),
    )
    gate = AuthorizationGate(contract)
    assert (
        gate.evaluate(
            AuthorizationRequest(
                AuthorizationAction.QUERY,
                DataClass.SYNTHETIC,
                experiment_index=2,
            )
        ).decision
        is Decision.DENY
    )
    assert (
        gate.evaluate(
            AuthorizationRequest(
                AuthorizationAction.QUERY,
                DataClass.SYNTHETIC,
                accumulated_cost=4,
            )
        ).decision
        is Decision.DENY
    )
    assert (
        gate.evaluate(
            AuthorizationRequest(
                AuthorizationAction.QUERY,
                DataClass.SYNTHETIC,
            )
        ).decision
        is Decision.REQUIRE_REVIEW
    )


def test_reir_claim_bundle_has_provenance_and_path():
    graph = make_claim_bundle(
        "g",
        "claim",
        "system is stateful",
        (("trace:1", "order changed output"),),
    )
    assert graph.provenance_coverage == 1.0
    assert graph.shortest_path(
        "claim-evidence-0",
        "claim",
    ) == ("claim-evidence-0", "claim")
    assert graph.validate() == ()


def test_reir_roundtrip_digest_and_hyperedge():
    graph = REIRGraph("g")
    graph.add_node(
        IRNode(
            "a",
            NodeKind.OBSERVATION,
            "a",
            EpistemicLevel.OBSERVED,
            provenance=("p:a",),
            uncertainty=0,
        )
    )
    graph.add_node(
        IRNode(
            "b",
            NodeKind.OBSERVATION,
            "b",
            EpistemicLevel.OBSERVED,
            provenance=("p:b",),
            uncertainty=0,
        )
    )
    graph.add_node(
        IRNode(
            "h",
            NodeKind.HYPOTHESIS,
            "h",
            EpistemicLevel.INFERRED,
            provenance=("p:a", "p:b"),
        )
    )
    graph.add_hyperedge(
        IRHyperedge(
            "he",
            ("a", "b"),
            ("h",),
            EdgeKind.SUPPORTS,
            provenance=("analysis:1",),
            confidence=0.8,
        )
    )
    restored = REIRGraph.from_json(graph.to_json())
    assert restored.digest == graph.digest
    assert restored.neighbors("a", direction="out") == ("h",)


def test_reir_validation_blocks_verified_without_domain():
    graph = REIRGraph("bad")
    graph.add_node(
        IRNode(
            "v",
            NodeKind.CLAIM,
            "verified claim",
            EpistemicLevel.VERIFIED_WITHIN_DOMAIN,
            provenance=("replication",),
            uncertainty=0.1,
        )
    )
    issues = graph.validate()
    assert {issue.code for issue in issues} == {
        "missing_valid_domain",
        "unsupported_claim",
    }


def test_reir_merge_conflict_and_induced_subgraph():
    left = REIRGraph("left")
    right = REIRGraph("right")
    left.add_node(IRNode("n", NodeKind.ENTITY, "left"))
    right.add_node(IRNode("n", NodeKind.ENTITY, "right"))
    with pytest.raises(ValueError):
        left.merge(right)
    merged = left.merge(right, conflict="left")
    assert merged.nodes["n"].label == "left"
    assert (
        merged.induced_subgraph(("n",)).nodes["n"].label
        == "left"
    )


def test_reir_strongly_connected_components():
    graph = REIRGraph("cycle")
    for node_id in "abc":
        graph.add_node(
            IRNode(node_id, NodeKind.STATE, node_id)
        )
    graph.add_edge(
        IREdge("ab", "a", "b", EdgeKind.PRECEDES)
    )
    graph.add_edge(
        IREdge("ba", "b", "a", EdgeKind.PRECEDES)
    )
    graph.add_edge(
        IREdge("bc", "b", "c", EdgeKind.PRECEDES)
    )
    assert ("a", "b") in graph.strongly_connected_components()
