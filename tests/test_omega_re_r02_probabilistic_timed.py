from math import isclose
import random
import pytest

from omega_re_t.probabilistic import (
    ProbabilisticObservation,
    ProbabilisticTransition,
    behavioral_distance,
    demo_probabilistic_pair,
    entropy_bits,
    expected_information_gain,
    posterior,
    predictive_distribution,
    total_variation,
)
from omega_re_t.timed import (
    LatencyModel,
    TimedObservation,
    choose_temporal_experiment,
    demo_timed_pair,
    temporal_separation,
)


def test_probabilistic_distribution_sums_to_one():
    left, _ = demo_probabilistic_pair()
    distribution = left.output_distribution(("A", "B"))
    assert isclose(sum(distribution.values()), 1.0)
    assert set(distribution) == {
        ("0", "0"),
        ("0", "1"),
        ("1", "0"),
        ("1", "1"),
    }


def test_probabilistic_sampling_is_reproducible():
    left, _ = demo_probabilistic_pair()
    assert left.sample(
        ("A", "B", "A"),
        seed=42,
    ) == left.sample(("A", "B", "A"), seed=42)


def test_probabilistic_posterior_prefers_generator():
    left, right = demo_probabilistic_pair()
    observations = tuple(
        ProbabilisticObservation(
            ("A", "B"),
            left.sample(("A", "B"), seed=index),
        )
        for index in range(100)
    )
    result = posterior((left, right), observations)
    assert result[left.machine_id] > 0.95


def test_expected_information_gain_is_discriminating():
    left, right = demo_probabilistic_pair()
    priors = {left.machine_id: 0.5, right.machine_id: 0.5}
    gain_a = expected_information_gain(
        (left, right),
        ("A",),
        priors,
    )
    gain_ab = expected_information_gain(
        (left, right),
        ("A", "B"),
        priors,
    )
    assert gain_a < 1.0e-12
    assert gain_ab > 0.05


def test_predictive_distribution_and_total_variation():
    left, right = demo_probabilistic_pair()
    priors = {left.machine_id: 0.5, right.machine_id: 0.5}
    mixture = predictive_distribution(
        (left, right),
        ("A", "B"),
        priors,
    )
    assert isclose(sum(mixture.values()), 1.0)
    distance = total_variation(
        left.output_distribution(("A", "B")),
        right.output_distribution(("A", "B")),
    )
    assert 0 < distance < 1
    assert behavioral_distance(
        left,
        right,
        (("A",), ("A", "B")),
    ) == distance


def test_probability_validation():
    with pytest.raises(ValueError):
        ProbabilisticTransition("S", {"0": 0, "1": 0})
    with pytest.raises(ValueError):
        ProbabilisticTransition("S", {"0": -1, "1": 2})


def test_entropy_normalises_weights():
    assert isclose(entropy_bits({"a": 2, "b": 2}), 1.0)


def test_timed_pair_selected_by_latency_difference():
    left, right = demo_timed_pair()
    selected = choose_temporal_experiment(
        (left, right),
        (("A",), ("B",), ("A", "B")),
    )
    assert selected == ("A", "B")
    assert temporal_separation(left, right, selected) > 0


def test_timed_likelihood_prefers_truth():
    left, right = demo_timed_pair()
    observation = left.sample(("A", "B"), seed=7)
    assert left.log_likelihood(observation) > right.log_likelihood(
        observation
    )


def test_timed_observation_validation_and_density_bounds():
    with pytest.raises(ValueError):
        TimedObservation(("A",), ("0",), (1, -1))
    model = LatencyModel(
        0.5,
        0.1,
        minimum=0.2,
        maximum=0.8,
    )
    assert model.log_density(0.1) < -100
    for seed in range(20):
        value = model.sample(random.Random(seed))
        assert 0.2 <= value <= 0.8
