from omega_re_t.probabilistic_r04 import (
    DirichletTransitionEstimator,
    Outcome,
    ProbabilisticTransducer,
    entropy_bits,
    total_variation,
)
from omega_re_t.symbolic_merge import PrefixTreeTransducer


def test_probabilistic_trace_probability_and_sampling_are_bounded():
    model = ProbabilisticTransducer(
        initial_state="s",
        transitions={
            ("s", "x"): {
                Outcome("s", "a"): 3,
                Outcome("s", "b"): 1,
            }
        },
    )
    assert model.trace_probability(("x",), ("a",)) == 0.75
    assert model.trace_probability(("x",), ("z",)) == 0.0
    assert model.sample_trace(("x", "x"), seed=4) == model.sample_trace(("x", "x"), seed=4)


def test_dirichlet_estimator_retains_uncertainty():
    support = {("s", "x"): [Outcome("s", "a"), Outcome("s", "b")]}
    estimator = DirichletTransitionEstimator(support, alpha=1)
    estimator.observe("s", "x", Outcome("s", "a"))
    posterior = estimator.posterior_distribution("s", "x")
    assert posterior[Outcome("s", "a")] == 2 / 3
    assert posterior[Outcome("s", "b")] == 1 / 3
    assert 0 < estimator.posterior_entropy("s", "x") <= 1


def test_distribution_metrics():
    a = {Outcome("s", "a"): 1.0}
    b = {Outcome("s", "b"): 1.0}
    assert total_variation(a, b) == 1.0
    assert entropy_bits((0.5, 0.5)) == 1.0


def test_symbolic_merge_finds_repeated_suffix_structure():
    tree = PrefixTreeTransducer.from_traces(
        [
            (("open", "read"), ("ok", "data")),
            (("reset", "read"), ("ok", "data")),
        ]
    )
    report = tree.merge_report(signature_depth=2)
    assert report.node_count == 5
    assert report.class_count < report.node_count
    assert not report.conflicts


def test_symbolic_conflicts_are_never_silently_merged():
    tree = PrefixTreeTransducer()
    tree.add_trace(("x",), ("a",))
    tree.add_trace(("x",), ("b",))
    report = tree.merge_report()
    assert len(report.conflicts) == 1
    assert tree.replay(("x",)) == ("a",)
