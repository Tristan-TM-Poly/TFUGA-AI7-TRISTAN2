from omega_re_t.active_learning import MembershipOracle, learn_bounded_mealy, words
from omega_re_t.nondeterministic import NDTransition, NondeterministicMealyMachine, bounded_trace_equivalence, infer_prefix_tree_transducer


def oracle_fn(word):
    state = 0
    outputs = []
    for symbol in word:
        if symbol == "a":
            outputs.append(str(state))
            state ^= 1
        else:
            outputs.append(str(state))
    return tuple(outputs)


def test_words_count_and_cache():
    assert len(words(("a", "b"), 3)) == 15
    oracle = MembershipOracle(oracle_fn)
    assert oracle.query(("a", "b")) == ("0", "1")
    assert oracle.query(("a", "b")) == ("0", "1")
    assert oracle.query_count == 1


def test_bounded_active_learning_exact():
    oracle = MembershipOracle(oracle_fn)
    report = learn_bounded_mealy(oracle, alphabet=("a", "b"), max_access_depth=4, max_probe_depth=2, validation_depth=4)
    assert report.exact_on_domain
    assert len(report.machine.states) == 2
    for word in words(("a", "b"), 4, include_empty=False):
        assert report.machine.run(word) == oracle_fn(word)
    assert report.machine.digest() == report.machine.digest()


def test_nondeterministic_machine_and_equivalence():
    machine = NondeterministicMealyMachine(
        states=("q0", "q1", "q2"), alphabet=("a",), outputs=("0", "1"), initial_states=("q0",),
        transitions=(NDTransition("q0", "a", "0", "q1"), NDTransition("q0", "a", "1", "q2")),
    )
    assert machine.accepted_output_words(("a",)) == frozenset({("0",), ("1",)})
    assert machine.determinism_violations() == (("q0", "a", 2),)
    assert machine.reachable_states() == frozenset({"q0", "q1", "q2"})
    report = bounded_trace_equivalence(machine, machine, max_depth=3)
    assert report.equivalent and not report.counterexamples


def test_prefix_tree_preserves_conflicts():
    model = infer_prefix_tree_transducer([(("a",), ("0",)), (("a",), ("1",))])
    assert model.accepted_output_words(("a",)) == frozenset({("0",), ("1",)})
