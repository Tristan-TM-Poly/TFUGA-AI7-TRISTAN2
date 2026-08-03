import math
import pytest

from omega_re_t.open_world_smc_r06 import (
    Observation,
    Particle,
    effective_sample_size,
    gaussian_likelihood,
    inject_novelty_particles,
    normalize_particles,
    posterior_by_class,
    run_smc,
    systematic_resample,
)


def predictor(particle, experiment):
    x = {"a": 0.0, "b": 1.0, "c": 2.0}[experiment]
    if particle.model_class == "linear":
        return particle.parameter * x
    if particle.model_class == "quadratic":
        return particle.parameter * x * x
    return particle.parameter + x


def base_particles():
    return (
        Particle("l0", "linear", 0.5, 1, "test"),
        Particle("l1", "linear", 1.0, 1, "test"),
        Particle("q0", "quadratic", 0.5, 1, "test"),
        Particle("q1", "quadratic", 1.0, 1, "test"),
    )


def test_normalize_and_class_mass():
    normalized = normalize_particles(base_particles())
    assert sum(item.weight for item in normalized) == pytest.approx(1)
    assert posterior_by_class(normalized) == {"linear": 0.5, "quadratic": 0.5}


def test_duplicate_ids_rejected():
    with pytest.raises(ValueError):
        normalize_particles((Particle("x", "a", 1, 1, "p"), Particle("x", "b", 2, 1, "p")))


def test_gaussian_likelihood_peak():
    assert gaussian_likelihood(1, 1, 0.5) > gaussian_likelihood(1, 2, 0.5)
    with pytest.raises(ValueError):
        gaussian_likelihood(1, 1, 0)


def test_effective_sample_size_bounds():
    normalized = normalize_particles(base_particles())
    assert effective_sample_size(normalized) == pytest.approx(4)


def test_resample_is_deterministic():
    normalized = normalize_particles(base_particles())
    assert systematic_resample(normalized, seed=4, sequence=2) == systematic_resample(normalized, seed=4, sequence=2)


def test_novelty_injection_triggered():
    injected = inject_novelty_particles(base_particles(), residual=5, threshold=2, count=3, seed=9)
    assert posterior_by_class(injected)["__novelty__"] > 0
    assert len(injected) == 7


def test_novelty_not_injected_below_threshold():
    assert inject_novelty_particles(base_particles(), residual=1, threshold=2, count=3, seed=9) == base_particles()


def test_run_smc_deterministic_and_bounded():
    observations = (Observation("a", 0, 0.2), Observation("b", 1, 0.2), Observation("c", 4, 0.2))
    left = run_smc(base_particles(), observations, predictor, seed=3)
    right = run_smc(base_particles(), observations, predictor, seed=3)
    assert left == right
    assert len(left.rounds) == 3
    assert math.isclose(sum(left.posterior_by_class.values()), 1)
    assert left.claim.endswith("only")


def test_invalid_ess_fraction_rejected():
    with pytest.raises(ValueError):
        run_smc(base_particles(), (), predictor, ess_fraction=0)


def test_invalid_observation_rejected():
    with pytest.raises(ValueError):
        run_smc(base_particles(), (Observation("a", 0, 0),), predictor)
