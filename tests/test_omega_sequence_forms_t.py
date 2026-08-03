from fractions import Fraction

import pytest

from omega_sequence_forms_t import CandidateKind, OAKLevel, discover_forms
from omega_sequence_forms_t.cli import benchmark_payload, main
from omega_sequence_forms_t.exact import solve_unique_linear_system
from omega_sequence_forms_t.finite import difference_table


def _candidate(report, kind: CandidateKind):
    return next(candidate for candidate in report.candidates if candidate.kind == kind)


def test_exact_linear_solver_accepts_overdetermined_consistent_system():
    solution = solve_unique_linear_system(
        [
            [Fraction(1), Fraction(1)],
            [Fraction(2), Fraction(1)],
            [Fraction(3), Fraction(1)],
        ],
        [Fraction(3), Fraction(5), Fraction(7)],
    )
    assert solution == [Fraction(2), Fraction(1)]


def test_difference_table_for_shifted_cubes():
    rows = difference_table(tuple(Fraction(value) for value in [1, 8, 27, 64, 125]))
    assert rows[3] == [Fraction(6), Fraction(6)]


def test_discovers_newton_polynomial_and_predicts_holdout():
    report = discover_forms([1, 8, 27, 64, 125, 216, 343, 512, 729])
    candidate = _candidate(report, CandidateKind.NEWTON_POLYNOMIAL)
    assert candidate.parameters["degree"] == 3
    assert candidate.evaluate(9) == 1000
    assert candidate.validation.predicts_held_out
    assert candidate.oak_level == OAKLevel.HELD_OUT_PREDICTION


def test_discovers_fibonacci_recurrence_and_generating_function():
    report = discover_forms([0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89])
    recurrence = _candidate(report, CandidateKind.LINEAR_RECURRENCE)
    generating = _candidate(report, CandidateKind.RATIONAL_GENERATING_FUNCTION)
    assert recurrence.parameters["coefficients"] == [Fraction(1), Fraction(1)]
    assert recurrence.evaluate(12) == 144
    assert generating.expression == "A(z) = (z) / (1 - z - z^2)"
    assert generating.evaluate(12) == 144


def test_broken_square_prefix_is_not_promoted_to_predictive_evidence():
    report = discover_forms([1, 4, 9, 16, 25, 36, 50])
    candidate = _candidate(report, CandidateKind.NEWTON_POLYNOMIAL)
    assert candidate.validation.held_out_terms == 2
    assert candidate.validation.held_out_matches == 1
    assert candidate.oak_level == OAKLevel.OBSERVED_FIT
    assert report.to_dict()["global_identity_proved"] is False


def test_rejects_vacuous_high_degree_interpolant():
    report = discover_forms([1, 2, 4, 8], holdout=0, max_degree=12, max_order=0)
    assert all(candidate.kind != CandidateKind.NEWTON_POLYNOMIAL for candidate in report.candidates)


def test_input_validation():
    with pytest.raises(ValueError):
        discover_forms([])
    with pytest.raises(ValueError):
        discover_forms([1, 2, 3], holdout=3)
    with pytest.raises(ValueError):
        discover_forms([1, 2, 3], holdout=-1)


def test_benchmark_and_cli_are_deterministic(tmp_path):
    payload = benchmark_payload()
    assert payload["passed"] is True
    assert payload["global_identity_proved"] is False

    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    assert main(["benchmark", "--output", str(first)]) == 0
    assert main(["benchmark", "--output", str(second)]) == 0
    assert first.read_bytes() == second.read_bytes()
