import pytest

from omega_game import CouncilScores, GMCouncil, default_gm_council
from omega_game.engines import TextWorldEngine


def test_council_scores_reject_out_of_range_values():
    with pytest.raises(ValueError):
        CouncilScores(fun=1.2)


def test_default_gm_council_has_canonical_agents():
    council = default_gm_council()
    names = {agent.name for agent in council.agents}

    assert names == {
        "GM-Narrator",
        "GM-Strategist",
        "GM-Teacher",
        "GM-Scientist",
        "GM-Economist",
        "GM-Mycelium",
        "GM-OAK",
        "GM-Memory",
    }


def test_gm_council_deliberates_and_records_memory():
    engine = TextWorldEngine.demo_world()
    council = default_gm_council()

    decision = council.deliberate(engine.world)

    assert decision.accepted
    assert decision.selected_vote.agent
    assert len(decision.all_votes) == 8
    assert engine.world.memory[-1]["type"] == "gm_council_decision"
    assert council.m_plus.entries


def test_gm_council_decision_payload_is_serializable_dict():
    engine = TextWorldEngine.demo_world()
    decision = default_gm_council().deliberate(engine.world)
    payload = decision.to_dict()

    assert payload["accepted"] is True
    assert "selected_vote" in payload
    assert "all_votes" in payload
    assert "oak_metrics" in payload


def test_gm_council_can_use_custom_empty_agent_list_by_post_init_default():
    council = GMCouncil(agents=[])

    assert len(council.agents) == 8
