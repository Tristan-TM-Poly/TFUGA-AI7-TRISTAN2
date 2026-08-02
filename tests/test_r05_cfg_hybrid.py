import pytest

from omega_re_t.bounded_cfg_r05 import BoundedCFG, propose_terminal_extensions
from omega_re_t.nonlinear_hybrid_r05 import (
    HybridGuard,
    NonlinearHybridSystem,
    PolynomialDynamics,
    fit_polynomial_dynamics,
    polynomial_features,
)


def grammar():
    return BoundedCFG(
        start="S",
        terminal_rules={"N": ("id",), "EQ": ("=",), "V": ("1", "2")},
        binary_rules={"S": (("N", "R"),), "R": (("EQ", "V"),)},
    )


def test_cfg_accepts_and_rejects():
    assert grammar().parse(("id", "=", "1")).accepted
    assert not grammar().parse(("id", "1", "=")).accepted


def test_cfg_budget_is_enforced():
    with pytest.raises(ValueError):
        grammar().parse(("id", "=", "1"), max_tokens=2)


def test_cfg_generation_is_bounded_and_deterministic():
    first = grammar().generate(max_tokens=3, max_sentences=10)
    second = grammar().generate(max_tokens=3, max_sentences=10)
    assert first == second
    assert ("id", "=", "1") in first
    assert len(first) == 2


def test_terminal_extension_is_conservative():
    proposals = propose_terminal_extensions(
        grammar(),
        accepted_examples=(("new",), ("safe",)),
        rejected_examples=(("new",), ("bad",)),
    )
    assert proposals == (("EQ", "safe"),)


def test_polynomial_feature_shape():
    assert polynomial_features((2.0,), 2) == (1.0, 2.0, 4.0)
    assert polynomial_features((1.0, 2.0), 2) == (1.0, 1.0, 2.0, 1.0, 2.0, 4.0)


def test_polynomial_fit_recovers_quadratic():
    samples = []
    for value in (-2.0, -1.0, 0.0, 1.0, 2.0):
        samples.append(((value,), (1.0 + 2.0 * value + 3.0 * value * value,)))
    model = fit_polynomial_dynamics(samples, degree=2, ridge=1.0e-12)
    assert model.derivative((1.5,))[0] == pytest.approx(10.75, rel=1e-7)


def test_underdetermined_fit_is_blocked():
    with pytest.raises(ValueError, match="underdetermined"):
        fit_polynomial_dynamics([((0.0,), (0.0,)), ((1.0,), (1.0,))], degree=2)


def test_hybrid_guard_switches_mode():
    rising = PolynomialDynamics(((1.0, 0.0),), degree=1)
    falling = PolynomialDynamics(((-1.0, 0.0),), degree=1)
    system = NonlinearHybridSystem(
        modes={"up": rising, "down": falling},
        guards=(HybridGuard("up", "down", lambda state: state[0] >= 1.0),),
    )
    trace = system.simulate(initial_mode="up", initial_state=(0.0,), dt=0.5, steps=4)
    assert any(point.mode == "down" for point in trace)
    assert trace[-1].state[0] < trace[2].state[0]


def test_hybrid_envelope_blocks_divergence():
    dynamics = PolynomialDynamics(((1000.0, 0.0),), degree=1)
    system = NonlinearHybridSystem(modes={"m": dynamics})
    with pytest.raises(OverflowError):
        system.simulate(initial_mode="m", initial_state=(0.0,), dt=1.0, steps=2, state_limit=100.0)
