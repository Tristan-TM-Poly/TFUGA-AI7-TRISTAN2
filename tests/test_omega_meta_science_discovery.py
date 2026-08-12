from __future__ import annotations

import json
import math
import subprocess
import sys

import pytest

from omega_meta_science_t.benchmark import build_fixture
from omega_meta_science_t.discovery import (
    InvariantTransportMap,
    RepresentationRoute,
    ScientificIR,
    TheoryAdapter,
    compile_counterexample,
    compile_residual_genome,
    epistemic_jacobian,
    representation_arbitrage,
    run_discovery_dynamics_demo,
    transport_invariants,
    unknown_unknown_radar,
)


def test_scientific_ir_validates_declared_contract() -> None:
    ir = ScientificIR(
        object_id="toy",
        variables=("x", "y"),
        relations=("y=x",),
        units=(("x", "arb"), ("y", "arb")),
        assumptions=("deterministic",),
        observables=("y",),
        domain="x>=0",
        tests=("observe y != x",),
        provenance="fixture:test",
    )
    assert ir.validate() == ()


def test_scientific_ir_fails_closed_on_missing_context() -> None:
    ir = ScientificIR(
        object_id="",
        variables=("x",),
        relations=(),
        units=(("z", "arb"),),
        assumptions=(),
        observables=("y",),
        domain="",
        tests=(),
        provenance="",
    )
    errors = set(ir.validate())
    assert "missing_object_id" in errors
    assert "missing_provenance" in errors
    assert "missing_relations" in errors
    assert "missing_tests" in errors
    assert "observable_not_declared:y" in errors
    assert "unit_for_unknown_variable:z" in errors


def test_theory_adapter_exposes_discovery_abi() -> None:
    linear = build_fixture().theories[0]
    adapter = TheoryAdapter(linear)
    assert adapter.predict(2.0) == 2.0
    assert adapter.falsify(2.0, 2.0) is False
    assert adapter.falsify(2.0, 4.0) is True
    assert adapter.provenance() == "theory:T_linear"
    assert adapter.represent() == ("symbolic", "program")


def test_epistemic_jacobian_matches_toy_analytic_sensitivity() -> None:
    report = epistemic_jacobian(build_fixture().theories, 2.0, step=1e-6)
    # For y=x vs y=x^2, population prediction variance is
    # D(x)=(x-x^2)^2/4, so D'(2)=3.
    assert report.derivative == pytest.approx(3.0, rel=1e-5, abs=1e-5)
    assert "not a gradient of truth" in report.oak_boundary


def test_residual_genome_detects_structure_without_claiming_cause() -> None:
    genome = compile_residual_genome((-0.25, 0.0, 0.75, 2.0))
    assert genome.rms > 0.0
    assert genome.slope > 0.0
    assert "systematic_bias_candidate" in genome.signatures
    assert "trend_candidate" in genome.signatures


def test_counterexample_compiler_finds_strongest_declared_candidate() -> None:
    linear, quadratic = build_fixture().theories
    candidate = compile_counterexample(
        TheoryAdapter(linear), quadratic.predict, (0.0, 1.0, 2.0, 3.0)
    )
    assert candidate.x == 3.0
    assert candidate.residual == pytest.approx(6.0)
    assert candidate.falsifies is True


def test_representation_arbitrage_uses_fidelity_gate_before_cost() -> None:
    decision = representation_arbitrage(
        (
            RepresentationRoute("native", 10.0, 0.0, 0.0, 1.0),
            RepresentationRoute("transformed", 2.0, 1.0, 0.01, 0.99),
            RepresentationRoute("lossy-fast", 0.1, 0.1, 0.20, 0.70),
        )
    )
    assert decision.selected.route_id == "transformed"
    assert "lossy-fast" in decision.rejected_routes
    assert "native" in decision.eligible_routes


def test_invariant_transport_requires_complete_declared_map() -> None:
    report = transport_invariants(
        ("charge", "energy"),
        InvariantTransportMap("A", "B", (("charge", "flow"),)),
    )
    assert report.transported == ("flow",)
    assert report.missing == ("energy",)
    assert report.certified_for_declared_map is False


def test_unknown_unknown_radar_is_ranked_heuristic() -> None:
    problem = build_fixture()
    quadratic = problem.theories[1]
    signals = unknown_unknown_radar(
        (0.0, 1.0, 2.0, 3.0),
        problem.theories,
        quadratic.predict,
        representation_instability={3.0: 1.0, 2.0: 0.2},
        coverage={0.0: 1.0, 1.0: 1.0, 2.0: 0.5, 3.0: 0.0},
    )
    assert signals[0].x == 3.0
    assert signals[0].score >= signals[-1].score
    assert "heuristic candidate signal" in signals[0].oak_boundary


def test_discovery_dynamics_demo_composes_all_primitives() -> None:
    report = run_discovery_dynamics_demo()
    assert report.scientific_ir_valid is True
    assert report.counterexample.x == 3.0
    assert report.counterexample.falsifies is True
    assert report.arbitrage.selected.route_id == "transformed"
    assert report.transport.certified_for_declared_map is True
    assert report.radar[0].x == 3.0
    assert report.jacobian.derivative == pytest.approx(3.0, rel=1e-4)


def test_discovery_cli_replays_json() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "omega_meta_science_t.discovery_cli", "--compact"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["scientific_ir_valid"] is True
    assert payload["arbitrage"]["selected"]["route_id"] == "transformed"
    assert payload["counterexample"]["falsifies"] is True
