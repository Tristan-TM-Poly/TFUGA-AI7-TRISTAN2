from omega_re_t.active import expected_information_gain_bits, select_experiment
from omega_re_t.bayes import posterior_entropy_bits, posterior_map, score_candidates
from omega_re_t.fsm import canonical_demo_machine, enumerate_mealy_machines


def population():
    return tuple(
        enumerate_mealy_machines(
            state_count=2,
            input_alphabet=("A", "B"),
            output_alphabet=("0", "1"),
            max_candidates=1_000,
        )
    )


def test_exact_enumerator_cardinality_and_unique_ids():
    candidates = population()
    assert len(candidates) == 256
    assert len({candidate.candidate_id for candidate in candidates}) == 256


def test_machine_round_trip_and_behavior():
    machine = canonical_demo_machine()
    assert machine.run(("A", "B", "A"))[0] == ("0", "0", "0")
    restored = machine.from_spec(machine.to_spec())
    assert restored.run(("B", "A", "A", "B")) == machine.run(("B", "A", "A", "B"))
    assert restored.candidate_id == machine.candidate_id


def test_active_experiment_has_positive_information_gain():
    candidates = population()
    experiment = select_experiment(candidates, alphabet=("A", "B"), max_length=4)
    assert experiment is not None
    assert experiment.expected_information_gain_bits > 0.0
    assert experiment.expected_partition_count > 1
    assert experiment.utility <= experiment.expected_information_gain_bits


def test_bayes_concentrates_on_consistent_candidate():
    candidates = population()
    oracle = canonical_demo_machine()
    observations = [
        oracle.observe(("A", "B", "A")),
        oracle.observe(("B", "B", "A", "A")),
        oracle.observe(("A", "A", "B", "B")),
    ]
    scores = score_candidates(candidates, observations)
    distribution = posterior_map(scores)
    assert distribution[oracle.candidate_id] > 0.0
    assert scores[0].mismatches == 0
    assert posterior_entropy_bits(scores) >= 0.0


def test_information_gain_respects_degenerate_population():
    oracle = canonical_demo_machine()
    assert expected_information_gain_bits((oracle,), ("A", "B")) == 0.0
