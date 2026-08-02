from math import pi
import pytest
from omega_pct_t.physics import (
    decay_lifetime_from_width, generate_qed_emu_events, qed_emu_dsigma_domega_massless,
    qed_emu_event, two_flavor_probability,
)
from omega_pct_t.oak import OAKGate

@pytest.mark.parametrize("theta", [0.1, 0.5, 1.2, 2.4, 3.0])
def test_qed_event_conserves_four_momentum(theta):
    event = qed_emu_event(10.0, theta, 0.3)
    report = OAKGate(tolerance=1e-9).audit_event(event)
    assert report.passed, report.to_markdown()


def test_massless_cross_section_proxy_positive_and_forward_enhanced():
    forward = qed_emu_dsigma_domega_massless(100.0, 0.2)
    central = qed_emu_dsigma_domega_massless(100.0, pi / 2)
    assert forward > central > 0


def test_forward_singularity_is_guarded():
    with pytest.raises(ValueError):
        qed_emu_dsigma_domega_massless(100.0, 0.0)


def test_event_generation_reproducible():
    left = generate_qed_emu_events(8, 10.0, seed=42)
    right = generate_qed_emu_events(8, 10.0, seed=42)
    assert [(event.theta, event.phi) for event in left] == [(event.theta, event.phi) for event in right]


def test_two_flavour_probability_bounds():
    value = two_flavor_probability(0.59, 2.5e-3, 295.0, 0.6)
    assert 0 <= value <= 1


def test_width_lifetime_inverse_relation():
    assert decay_lifetime_from_width(2.0) == pytest.approx(decay_lifetime_from_width(1.0) / 2)
