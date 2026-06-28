from omega_info2 import Info2Graph, InfoObject, InfoScores, OAKInfoGate, Route, route_information


def test_router_sends_high_fertility_testable_object_to_prototype():
    obj = InfoObject.example()
    obj.scores = InfoScores(
        truth=0.65,
        utility=0.8,
        fertility=0.9,
        testability=0.9,
        risk=0.2,
        source_trust=0.7,
    )
    OAKInfoGate().evaluate(obj)
    route = route_information(obj)
    assert route == Route.PROTOTYPE


def test_graph_contains_claim_and_action_nodes():
    obj = InfoObject.example()
    obj.scores = InfoScores(
        truth=0.65,
        utility=0.8,
        fertility=0.9,
        testability=0.9,
        risk=0.2,
        source_trust=0.7,
    )
    OAKInfoGate().evaluate(obj)
    route_information(obj)
    graph = Info2Graph.from_info_object(obj).to_dict()
    kinds = {node["kind"] for node in graph["nodes"]}
    assert "claim" in kinds
    assert "action" in kinds
