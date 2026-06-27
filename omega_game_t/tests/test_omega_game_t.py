from omega_game import Entity, Event, GameQualityScore, OAKGate, RuleKernel, WorldGraph
from omega_game.engines import TextWorldEngine


def test_world_graph_snapshot_counts_entities_relations_and_hyperedges():
    world = WorldGraph()
    world.add_entity(Entity("p1", "player", "Player"))
    world.add_entity(Entity("v1", "village", "Village"))
    world.add_relation("p1", "visits", "v1")
    world.add_hyperedge("quest_seed", {"p1", "v1"})

    snapshot = world.snapshot()

    assert snapshot["entity_count"] == 2
    assert snapshot["relation_count"] == 1
    assert snapshot["hyperedge_count"] == 1
    assert snapshot["entity_kinds"] == ["player", "village"]


def test_oak_rejects_unknown_entities_and_unsafe_flags():
    world = WorldGraph()
    world.add_entity(Entity("p1", "player", "Player"))
    event = Event(
        event_id="e1",
        kind="quest",
        description="Bad quest",
        actors=["p1"],
        targets=["missing"],
        payload={"metric": "test", "risk_flags": ["dark_pattern"]},
    )

    report = OAKGate().validate(world, event)

    assert not report.accepted
    assert not report.coherent
    assert not report.safe
    assert not report.non_exploitative


def test_textworld_generates_oak_accepted_quest():
    engine = TextWorldEngine.demo_world()
    proposal = engine.tick()

    assert proposal.oak_report is not None
    assert proposal.oak_report.accepted
    assert engine.world.memory
    assert proposal.quest["quest"]


def test_rule_kernel_can_block_events():
    world = WorldGraph()
    world.add_entity(Entity("p1", "player", "Player"))
    event = Event(
        event_id="e1",
        kind="quest",
        description="Blocked",
        actors=["p1"],
        payload={"metric": "test"},
    )
    kernel = RuleKernel()
    kernel.add_rule(lambda _world, _event: (False, "blocked by test rule"))

    report = OAKGate().validate(world, event, kernel)

    assert not report.accepted
    assert "blocked by test rule" in report.reasons


def test_game_quality_score_is_bounded():
    score = GameQualityScore(fun=1, agency=1, coherence=1, novelty=1, fairness=1, learning=1)
    assert score.composite() == 1.0

    bad_score = GameQualityScore(friction=1, exploits=1)
    assert 0.0 <= bad_score.composite() <= 1.0
