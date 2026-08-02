from __future__ import annotations

from omega_unbounded_t.governance import (
    IterationObservation,
    ObjectiveVector,
    ReflexMemoryLedger,
    StopGate,
    StopPolicy,
    dominates,
    pareto_front,
)


def test_user_interrupt_stops_immediately():
    decision = StopGate().observe(
        IterationObservation(
            objective_reached=False,
            authoritative_validation=False,
            marginal_information_gain=1.0,
            repetition_score=0.0,
            critical_new_risk=True,
            user_interrupt=True,
        )
    )

    assert decision.should_stop is True
    assert decision.priority == 100


def test_sufficient_proof_and_low_information_stop_the_loop():
    gate = StopGate()
    decision = gate.observe(
        IterationObservation(
            objective_reached=True,
            authoritative_validation=True,
            marginal_information_gain=0.01,
            repetition_score=0.95,
            validation_fingerprint="authoritative-proof-a",
        )
    )

    assert decision.should_stop is True
    assert "marginal information is low" in " ".join(decision.reasons)


def test_second_equivalent_validation_blocks_a_third():
    gate = StopGate(
        StopPolicy(
            minimum_marginal_information=0.0,
            maximum_repetition_score=1.0,
            maximum_equivalent_validations=2,
            maximum_stagnant_observations=10,
        )
    )
    first = gate.observe(
        IterationObservation(
            objective_reached=True,
            authoritative_validation=True,
            marginal_information_gain=0.2,
            repetition_score=0.2,
            validation_fingerprint="same-proof",
        )
    )
    second = gate.observe(
        IterationObservation(
            objective_reached=True,
            authoritative_validation=True,
            marginal_information_gain=0.2,
            repetition_score=0.2,
            validation_fingerprint="same-proof",
        )
    )

    assert first.should_stop is False
    assert second.should_stop is True
    assert second.equivalent_validations == 2


def test_critical_new_risk_keeps_investigation_open():
    decision = StopGate().observe(
        IterationObservation(
            objective_reached=True,
            authoritative_validation=True,
            marginal_information_gain=0.0,
            repetition_score=1.0,
            validation_fingerprint="proof",
            critical_new_risk=True,
        )
    )

    assert decision.should_stop is False
    assert decision.priority == 90


def test_negative_memory_rule_blocks_known_overiteration(tmp_path):
    path = tmp_path / "m_minus_reflex.jsonl"
    ledger = ReflexMemoryLedger(path)
    rule = ledger.record_overiteration()

    assert ledger.is_blocked(
        "repeat_equivalent_validation",
        trigger="objective_reached_and_authoritative_validation_obtained",
    )
    assert rule.event_id in path.read_text(encoding="utf-8")

    restored = ReflexMemoryLedger(path)
    assert restored.block_reasons("repeat_equivalent_validation") == (rule.event_id,)


def test_pareto_front_keeps_tradeoffs_and_removes_dominated_points():
    fast = ObjectiveVector(
        name="fast",
        maximize={"quality": 1.0, "throughput": 10.0},
        minimize={"memory": 8.0},
    )
    lean = ObjectiveVector(
        name="lean",
        maximize={"quality": 1.0, "throughput": 8.0},
        minimize={"memory": 4.0},
    )
    dominated = ObjectiveVector(
        name="dominated",
        maximize={"quality": 1.0, "throughput": 7.0},
        minimize={"memory": 9.0},
    )

    assert dominates(fast, dominated) is True
    assert {point.name for point in pareto_front((fast, lean, dominated))} == {"fast", "lean"}
