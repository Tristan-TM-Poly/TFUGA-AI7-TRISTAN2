from __future__ import annotations

from .hybrid import (
    AffineFlow,
    HybridAutomaton,
    HybridMode,
    HybridTransition,
    Predicate,
    ResetRule,
)
from .reachability import Interval, ReachBox
from .temporal import TemporalProperty


def r03_axis_automaton() -> HybridAutomaton:
    variables = ("position_m", "velocity_mps", "temperature_k", "clock_s")
    zero = AffineFlow()
    startup = HybridMode(
        "startup",
        {
            "position_m": zero,
            "velocity_mps": zero,
            "temperature_k": zero,
            "clock_s": AffineFlow(1.0),
        },
        invariants=(Predicate("clock_s", "<=", 0.051),),
        description="synthetic interlock initialization",
    )
    tracking = HybridMode(
        "tracking",
        {
            "position_m": AffineFlow(coefficients={"velocity_mps": 1.0}),
            "velocity_mps": AffineFlow(0.5, {"velocity_mps": -4.0}),
            "temperature_k": AffineFlow(20.0),
            "clock_s": AffineFlow(1.0),
        },
        invariants=(
            Predicate("position_m", "<=", 0.24),
            Predicate("temperature_k", "<=", 303.25),
        ),
        description="bounded synthetic tracking and heating",
    )
    derated = HybridMode(
        "derated",
        {
            "position_m": AffineFlow(coefficients={"velocity_mps": 1.0}),
            "velocity_mps": AffineFlow(0.25, {"velocity_mps": -4.0}),
            "temperature_k": AffineFlow(-1.0),
            "clock_s": AffineFlow(1.0),
        },
        invariants=(
            Predicate("position_m", "<=", 0.24),
            Predicate("temperature_k", "<=", 320.0),
        ),
        description="reduced authority with synthetic cooling",
    )
    safe_shutdown = HybridMode(
        "safe_shutdown",
        {
            "position_m": AffineFlow(coefficients={"velocity_mps": 1.0}),
            "velocity_mps": AffineFlow(coefficients={"velocity_mps": -10.0}),
            "temperature_k": AffineFlow(-0.5),
            "clock_s": AffineFlow(1.0),
        },
        invariants=(
            Predicate("position_m", "<=", 0.26),
            Predicate("temperature_k", "<=", 330.0),
        ),
        description="latched low-energy computational fallback",
    )
    transitions = (
        HybridTransition(
            "startup-complete",
            "startup",
            "tracking",
            (Predicate("clock_s", ">=", 0.05),),
            resets=(ResetRule("clock_s", offset=0.0),),
            priority=10,
            minimum_dwell_s=0.05,
        ),
        HybridTransition(
            "thermal-derate",
            "tracking",
            "derated",
            (Predicate("temperature_k", ">=", 303.15),),
            resets=(ResetRule("clock_s", offset=0.0),),
            priority=10,
            minimum_dwell_s=0.05,
        ),
        HybridTransition(
            "timed-safe-shutdown",
            "derated",
            "safe_shutdown",
            (Predicate("clock_s", ">=", 0.50),),
            resets=(ResetRule("clock_s", offset=0.0),),
            priority=10,
            minimum_dwell_s=0.50,
        ),
    )
    return HybridAutomaton(
        automaton_id="omega-cps-r03-axis-fixture",
        variables=variables,
        modes=(startup, tracking, derated, safe_shutdown),
        transitions=transitions,
        initial_mode="startup",
        initial_state={
            "position_m": 0.0,
            "velocity_mps": 0.0,
            "temperature_k": 293.15,
            "clock_s": 0.0,
        },
        safe_modes=("startup", "tracking", "derated", "safe_shutdown"),
        emergency_mode="safe_shutdown",
    )


def r03_initial_box() -> ReachBox:
    return ReachBox({
        "position_m": Interval(-0.0005, 0.0005),
        "velocity_mps": Interval(-0.001, 0.001),
        "temperature_k": Interval(293.10, 293.20),
        "clock_s": Interval(0.0, 0.0),
    })


def r03_temporal_properties() -> tuple[TemporalProperty, ...]:
    return (
        TemporalProperty(
            "R03-ALWAYS-POSITION",
            "ALWAYS",
            "position remains inside the declared computational envelope",
            predicate=Predicate("position_m", "<=", 0.26),
        ),
        TemporalProperty(
            "R03-THERMAL-RESPONSE",
            "RESPONSE",
            "thermal threshold is followed by derating",
            trigger=Predicate("temperature_k", ">=", 303.15),
            response_mode="derated",
            within_s=0.02,
        ),
        TemporalProperty(
            "R03-MODE-SEQUENCE",
            "MODE_SEQUENCE",
            "startup, tracking, derating and fallback occur in order",
            mode_sequence=("startup", "tracking", "derated", "safe_shutdown"),
        ),
        TemporalProperty(
            "R03-EVENTUAL-FALLBACK",
            "EVENTUALLY",
            "the fixture eventually enters its low-energy fallback",
            target_mode="safe_shutdown",
            within_s=1.2,
        ),
    )


def r03_unsafe_condition() -> tuple[Predicate, ...]:
    return (Predicate("position_m", ">=", 0.27),)


def r03_adversarial_initial_box() -> ReachBox:
    return ReachBox({
        "position_m": Interval(0.269, 0.271),
        "velocity_mps": Interval(0.05, 0.10),
        "temperature_k": Interval(293.10, 293.20),
        "clock_s": Interval(0.0, 0.0),
    })
