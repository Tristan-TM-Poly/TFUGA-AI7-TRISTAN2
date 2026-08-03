from dataclasses import replace
import pytest

from omega_re_t.calibration_chain_r06 import CalibrationRun, build_chain, classify_trend, compare_run_sets, verify_chain
from omega_re_t.experiment_registry_r06 import ExperimentRegistry, ExperimentSpec


def runs():
    return (
        CalibrationRun("r0", "sha256:d0", "sha256:m0", 10, 0.2, 0.5, 0.1),
        CalibrationRun("r1", "sha256:d1", "sha256:m1", 20, 0.1, 0.4, 0.05),
        CalibrationRun("r2", "sha256:d2", "sha256:m2", 30, 0.12, 0.39, 0.06),
    )


def test_trends():
    assert classify_trend(None, runs()[0]) == "baseline"
    assert classify_trend(runs()[0], runs()[1]) == "improved"
    assert classify_trend(runs()[1], runs()[2]) == "mixed"


def test_chain_verifies_and_is_deterministic():
    left = build_chain(runs())
    right = build_chain(runs())
    assert left == right
    assert verify_chain(left) == (True, ())


def test_tampered_chain_detected():
    chain = list(build_chain(runs()))
    chain[1] = replace(chain[1], receipt_digest="sha256:bad")
    valid, errors = verify_chain(chain)
    assert not valid
    assert any(error.startswith("digest:1") for error in errors)


def test_compare_run_sets_finds_divergence():
    left = build_chain(runs())
    changed = list(runs())
    changed[2] = replace(changed[2], brier_score=0.5)
    right = build_chain(changed)
    report = compare_run_sets(left, right)
    assert report["first_divergence"] == 2
    assert not report["identical"]


def test_duplicate_run_id_rejected():
    with pytest.raises(ValueError):
        build_chain((runs()[0], runs()[0]))


def spec(identifier="e"):
    return ExperimentSpec(identifier, {"x": 1.0}, "signal", "synthetic-owned", True, 0.1, 1.0)


def test_registry_register_observe_audit():
    registry = ExperimentRegistry()
    digest = registry.register(spec())
    record = registry.append_observation("e", value=1, uncertainty=0.1, instrument_digest="sha256:i", timestamp_label="t0", source="fixture")
    assert record.experiment_digest == digest
    assert registry.audit()["valid"] is True
    assert len(registry.snapshot()) == 1


def test_registry_idempotent_same_spec_but_blocks_rebinding():
    registry = ExperimentRegistry()
    first = registry.register(spec())
    assert registry.register(spec()) == first
    with pytest.raises(ValueError):
        registry.register(ExperimentSpec("e", {"x": 2.0}, "signal", "synthetic-owned", True, 0.1, 1.0))


def test_unregistered_observation_rejected():
    registry = ExperimentRegistry()
    with pytest.raises(KeyError):
        registry.append_observation("missing", value=1, uncertainty=0.1, instrument_digest="sha256:i", timestamp_label="t", source="x")


def test_invalid_scientific_count_rejected():
    bad = CalibrationRun("bad", "sha256:d", "sha256:m", 1, 0.1, 0.2, 0.1, -1)
    with pytest.raises(ValueError):
        build_chain((bad,))


def test_registry_snapshot_order_is_deterministic():
    registry = ExperimentRegistry()
    registry.register(spec("z"))
    registry.register(spec("a"))
    assert [item.spec.experiment_id for item in registry.snapshot()] == ["a", "z"]
