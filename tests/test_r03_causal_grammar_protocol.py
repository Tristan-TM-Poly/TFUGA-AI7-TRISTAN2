import pytest
from omega_re_t.causal import CausalEdge, CausalGraph, Intervention, InterventionResult, intervention_effect, mutual_information, rank_edge_candidates
from omega_re_t.grammar import FieldKind, infer_delimited_grammar
from omega_re_t.protocol import ProtocolStep, ProtocolTrace, infer_protocol_model, propose_protocol_experiments


def test_causal_graph_and_effect():
    graph = CausalGraph()
    graph.add_edge(CausalEdge("x", "m", confidence=0.8))
    graph.add_edge(CausalEdge("m", "y", confidence=0.9))
    assert graph.topological_order() == ("x", "m", "y")
    assert graph.descendants("x") == frozenset({"m", "y"})
    with pytest.raises(ValueError):
        graph.add_edge(CausalEdge("y", "x"))
    results = (
        InterventionResult(Intervention("x", 0), "y", (0.0, 0.2)),
        InterventionResult(Intervention("x", 1), "y", (1.0, 1.2)),
    )
    estimate = intervention_effect(results, treatment_variable="x", outcome_variable="y", treated_value=1, control_value=0)
    assert estimate.average_treatment_effect == pytest.approx(1.0)


def test_mutual_information_and_rank():
    records = [
        {"x": 0, "y": 0, "z": 0}, {"x": 0, "y": 0, "z": 1},
        {"x": 1, "y": 1, "z": 0}, {"x": 1, "y": 1, "z": 1},
    ]
    assert mutual_information(records, "x", "y") == pytest.approx(1.0)
    candidates = rank_edge_candidates(records, ("x", "y", "z"))
    assert candidates[0].association_bits >= candidates[-1].association_bits


def test_delimited_grammar():
    report = infer_delimited_grammar(
        ["1|alpha|true", "2|beta|false", "3|alpha|true"],
        field_names=("id", "kind", "enabled"),
    )
    assert report.grammar.delimiter == "|"
    assert report.grammar.fields[0].kind is FieldKind.INTEGER
    assert report.grammar.fields[1].kind is FieldKind.ENUM
    assert report.grammar.fields[2].kind is FieldKind.BOOLEAN
    assert report.grammar.parse("4|alpha|false")["id"] == "4"
    with pytest.raises(ValueError):
        report.grammar.parse("not-int|alpha|false")


def test_protocol_inference_and_experiments():
    traces = (
        ProtocolTrace((ProtocolStep("HELLO", "READY", 10), ProtocolStep("DATA", "OK", 20), ProtocolStep("CLOSE", "BYE", 5))),
        ProtocolTrace((ProtocolStep("HELLO", "READY", 12), ProtocolStep("CLOSE", "BYE", 6))),
    )
    report = infer_protocol_model(traces)
    assert report.trace_count == 2
    assert report.model.replay(("HELLO",))
    experiments = propose_protocol_experiments((report.model, report.model), report.request_alphabet, max_depth=2)
    assert experiments
