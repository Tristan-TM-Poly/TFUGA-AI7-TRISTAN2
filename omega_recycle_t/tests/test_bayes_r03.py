from omega_recycle.bayes import BetaFunctionalPosterior, bayesian_route_preferences
from omega_recycle.bench import demo_problem


def test_beta_posterior_update_and_deterministic_route_preferences() -> None:
    materials, candidates = demo_problem()
    posterior = BetaFunctionalPosterior().updated(successes=8, failures=2)
    assert abs(posterior.mean - 0.75) < 1e-12
    first = bayesian_route_preferences(
        candidates[0].component, materials, candidates[0].routes, posterior, draws=256, seed=11
    )
    second = bayesian_route_preferences(
        candidates[0].component, materials, candidates[0].routes, posterior, draws=256, seed=11
    )
    assert first == second
    assert abs(sum(item.win_probability for item in first) - 1.0) < 1e-12
