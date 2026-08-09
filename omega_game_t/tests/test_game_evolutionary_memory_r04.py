from __future__ import annotations

from omega_game.engines.evolution import seed_population
from omega_game.engines.evolutionary_memory import (
    EvolutionaryMemory,
    HallOfFame,
    MemoryRecord,
    evaluate_anti_forgetting,
)
from omega_game.engines.simulation import AgentGenome, ArenaConfig
from omega_game.engines.tournament import run_round_robin
from omega_game.engines.verification import FuzzFailure, FuzzReport


def _tournament(population):
    return run_round_robin(population, seeds=(2, 3), config=ArenaConfig(max_steps=10), mirrored=True)


def test_memory_record_hash_is_deterministic() -> None:
    a = MemoryRecord.create("minus", "bug", {"seed": 7, "flags": ["x"]})
    b = MemoryRecord.create("minus", "bug", {"flags": ["x"], "seed": 7})
    assert a.memory_id == b.memory_id
    assert a.evidence_hash == b.evidence_hash


def test_hall_of_fame_admits_ranked_champions() -> None:
    population = seed_population(5, seed=4)
    tournament = _tournament(population)
    hall = HallOfFame()
    admitted = hall.admit(population, tournament, generation=0, top_k=2)
    ranking = tournament.ranking()
    assert [record.agent.agent_id for record in admitted] == [ranking[0].agent_id, ranking[1].agent_id]
    assert [record.rank for record in admitted] == [1, 2]
    assert len(hall.records()) == 2


def test_hall_receipts_and_challenge_order_are_deterministic() -> None:
    population = seed_population(4, seed=12)
    tournament = _tournament(population)
    first = HallOfFame()
    second = HallOfFame()
    first.admit(population, tournament, generation=3, top_k=3)
    second.admit(population, tournament, generation=3, top_k=3)
    assert first.to_dict() == second.to_dict()
    assert [agent.agent_id for agent in first.challenge_agents()] == [agent.agent_id for agent in second.challenge_agents()]


def test_evolutionary_memory_turns_champions_into_m_plus() -> None:
    population = seed_population(4, seed=8)
    tournament = _tournament(population)
    memory = EvolutionaryMemory()
    admitted = memory.admit_tournament(population, tournament, generation=1, top_k=2)
    assert len(admitted) == 2
    assert len(memory.plus) == 2
    assert not memory.minus
    assert all(record.polarity == "plus" for record in memory.plus.values())


def test_fuzz_failures_feed_m_minus_and_deduplicate() -> None:
    report = FuzzReport(
        cases=3,
        seed=99,
        accepted_cases=1,
        failures=(
            FuzzFailure(case_index=0, seed=1001, flags=("determinism_failure",)),
            FuzzFailure(case_index=2, seed=1003, flags=("replay_hash_mismatch",)),
        ),
    )
    memory = EvolutionaryMemory()
    first = memory.ingest_fuzz_report(report)
    second = memory.ingest_fuzz_report(report)
    assert len(first) == 2
    assert [record.memory_id for record in first] == [record.memory_id for record in second]
    assert len(memory.minus) == 2


def test_manual_plus_minus_records_remain_separate() -> None:
    memory = EvolutionaryMemory()
    plus = memory.record_plus("strategy", {"name": "resource-first"})
    minus = memory.record_minus("counterexample", {"name": "deadlock"})
    assert plus.memory_id in memory.plus
    assert minus.memory_id in memory.minus
    assert plus.memory_id not in memory.minus


def test_anti_forgetting_report_is_deterministic() -> None:
    population = seed_population(4, seed=22)
    tournament = _tournament(population)
    hall = HallOfFame()
    hall.admit(population, tournament, generation=0, top_k=2)
    candidate = AgentGenome("candidate", seek_resource=0.8, aggression=0.4, conservation=0.5, exploration=0.2)
    kwargs = {
        "seeds": (5, 6),
        "config": ArenaConfig(max_steps=12),
        "threshold": 0.25,
    }
    a = evaluate_anti_forgetting(candidate, hall, **kwargs)
    b = evaluate_anti_forgetting(candidate, hall, **kwargs)
    assert a.to_json() == b.to_json()
    assert a.total_available_points == 8.0
    assert 0.0 <= a.score_fraction <= 1.0
    assert a.passed == (a.score_fraction >= 0.25)


def test_anti_forgetting_requires_historical_champions() -> None:
    try:
        evaluate_anti_forgetting(AgentGenome("candidate"), HallOfFame(), seeds=(1,))
    except ValueError:
        pass
    else:
        raise AssertionError("empty Hall of Fame should fail")


def test_invalid_memory_contracts_fail_closed() -> None:
    try:
        MemoryRecord.create("unknown", "bug", {})
    except ValueError:
        pass
    else:
        raise AssertionError("invalid polarity should fail")

    hall = HallOfFame()
    population = seed_population(3, seed=2)
    tournament = _tournament(population)
    try:
        hall.admit(population, tournament, generation=0, top_k=0)
    except ValueError:
        pass
    else:
        raise AssertionError("top_k=0 should fail")
