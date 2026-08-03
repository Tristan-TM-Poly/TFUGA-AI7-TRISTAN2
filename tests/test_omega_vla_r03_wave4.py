from pathlib import Path
import tempfile

import numpy as np

from omega_vla_t.r03.wave4 import (
    CounterexampleFrontier,
    CounterexampleRecord,
    CounterexampleRegistry,
    SearchState,
    execute_builtin_campaign,
    minimize_counterexample,
    plan_campaign,
    run_oakbench,
)
from omega_vla_t.r03.wave4.cli import main
from omega_vla_t.r03.wave4.models import MatrixWitness


def test_frontier_roundtrip_and_scale():
    frontier = CounterexampleFrontier()
    assert frontier.size > 10**9
    for index in (0, 1, 1000, frontier.size // 2, frontier.size - 1):
        assert frontier.encode(frontier.decode(index)) == index


def test_campaign_determinism_and_resume():
    first = plan_campaign(1024, 100)
    second = plan_campaign(1024, 100)
    assert first == second
    assert first["generated"] == 100
    assert first["next_offset"] == 1124
    assert first["permanent_total_cap"] is None


def test_false_commutativity_finds_minimized_counterexample():
    report = execute_builtin_campaign(
        "unconditional_commutativity",
        dimension=2,
        scalar_system="real",
        family="dense",
        seed=2026,
        trials=8,
    )
    assert report["record"] is not None
    assert report["record"]["witness"]["relative_residual"] > 1e-8
    assert report["theorem_claimed"] is False


def test_true_finite_transpose_fixture_has_no_witness():
    report = execute_builtin_campaign(
        "transpose_product",
        dimension=4,
        scalar_system="complex",
        family="dense",
        seed=17,
        trials=8,
    )
    assert report["state"] == "SEARCHED_NO_WITNESS"


def test_projection_assumption_is_respected():
    report = execute_builtin_campaign(
        "projection_idempotence",
        dimension=4,
        scalar_system="complex",
        family="projection",
        seed=17,
        trials=8,
    )
    assert report["state"] == "SEARCHED_NO_WITNESS"


def test_minimizer_preserves_noncommutativity():
    environment = {
        "A": np.array([[0, 1], [0, 0]], dtype=np.complex128),
        "B": np.array([[0, 0], [1, 0]], dtype=np.complex128),
    }

    def predicate(env):
        return np.linalg.norm(env["A"] @ env["B"] - env["B"] @ env["A"]) > 1e-8

    minimized, trace = minimize_counterexample(environment, predicate)
    assert predicate(minimized)
    assert trace.after_dimension <= trace.before_dimension
    assert trace.after_nonzeros <= trace.before_nonzeros


def test_registry_content_deduplication():
    witness = MatrixWitness(
        matrices={"A": (({"real": 1.0, "imag": 0.0},),)},
        absolute_residual=1.0,
        relative_residual=1.0,
        assumptions_passed=True,
    )
    record = CounterexampleRecord(
        record_id="mminus4-test",
        conjecture_id="test",
        plan_digest="a" * 64,
        state=SearchState.COUNTEREXAMPLE_FOUND,
        witness=witness,
    )
    with tempfile.TemporaryDirectory() as directory:
        registry = CounterexampleRegistry(Path(directory) / "registry.sqlite3")
        assert registry.put(record) is True
        assert registry.put(record) is False
        assert registry.count() == 1
        assert registry.export_jsonl(Path(directory) / "records.jsonl") == 1


def test_cli_and_oak(tmp_path):
    manifest = tmp_path / "manifest.json"
    oak = tmp_path / "oak.json"
    assert main(["manifest", "--output", str(manifest)]) == 0
    assert main(["oak", "--output", str(oak)]) == 0
    assert run_oakbench()["passed"] is True
