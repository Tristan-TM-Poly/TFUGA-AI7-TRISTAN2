from omega_re_t.benchmark import run_benchmark
from omega_re_t.campaign import reconstruct_fsm
from omega_re_t.fsm import canonical_demo_machine, enumerate_mealy_machines
from omega_re_t.models import AuthorizationMode, AuthorizationScope


def population():
    return tuple(
        enumerate_mealy_machines(
            state_count=2,
            input_alphabet=("A", "B"),
            output_alphabet=("0", "1"),
            max_candidates=1_000,
        )
    )


def authorization(*actions):
    return AuthorizationScope(
        mode=AuthorizationMode.RESEARCH_SANDBOX,
        purpose="unit test",
        permitted_actions=tuple(actions),
        reference="test-fixture",
    )


def test_campaign_recovers_canonical_behavior():
    result = reconstruct_fsm(
        oracle=canonical_demo_machine(),
        candidates=population(),
        authorization=authorization("query_oracle"),
        max_rounds=12,
        max_experiment_length=5,
        validation_max_length=8,
    )
    assert result.rounds > 0
    assert result.exact_behavior_recovered
    assert result.top_candidate_id == canonical_demo_machine().candidate_id
    assert result.posterior_entropy_bits < 1.0e-8
    assert result.identifiability_debt_bits < 1.0e-8
    assert result.oak_report is not None
    assert result.oak_report.decision in {"CONDITIONAL", "PROMOTE"}


def test_campaign_fails_closed_without_authorization():
    try:
        reconstruct_fsm(
            oracle=canonical_demo_machine(),
            candidates=population(),
            authorization=authorization("store_observation"),
        )
    except PermissionError as error:
        assert "query_oracle" in str(error)
    else:
        raise AssertionError("Expected authorization failure")


def test_benchmark_is_deterministic_and_active_succeeds():
    candidates = population()
    first = run_benchmark(candidates, seeds=tuple(range(8)), max_rounds=12, max_length=5)
    second = run_benchmark(candidates, seeds=tuple(range(8)), max_rounds=12, max_length=5)
    assert first == second
    assert first.active_success_rate == 1.0
    assert first.mean_active_rounds <= first.mean_passive_rounds or first.passive_success_rate < 1.0
