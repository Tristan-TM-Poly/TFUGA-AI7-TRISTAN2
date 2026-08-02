from dataclasses import asdict, replace
from json import dumps, loads
from pathlib import Path
import sqlite3
import pytest

from omega_re_t.constraints import (
    Comparator,
    Constraint,
    ConstraintKind,
    ConstraintSet,
    NegativeSpaceRecord,
    infer_numeric_bounds,
)
from omega_re_t.frontier import (
    expand_case,
    frontier,
    frontier_manifest,
    perturbations,
    validate_frontier,
)
from omega_re_t.r02_cli import main
from omega_re_t.re16 import catalog, catalog_digest, validate_catalog
from omega_re_t.residuals import (
    ResidualCategory,
    ResidualMiner,
    ResidualRecord,
)
from omega_re_t.storage import (
    Checkpoint,
    JSONLStore,
    SQLiteEvidenceStore,
    content_hash,
)


def test_constraint_evaluation_and_ranking():
    constraints = ConstraintSet(
        (
            Constraint(
                "states-min",
                "states",
                Comparator.GE,
                2,
                ConstraintKind.CAPACITY,
            ),
            Constraint(
                "states-max",
                "states",
                Comparator.LE,
                4,
                ConstraintKind.CAPACITY,
            ),
            Constraint(
                "kind",
                "kind",
                Comparator.IN,
                {"fsm", "hybrid"},
                ConstraintKind.MEMBERSHIP,
            ),
        )
    )
    candidates = {
        "a": {"states": 2, "kind": "fsm"},
        "b": {"states": 8, "kind": "fsm"},
        "c": {"states": 3, "kind": "linear"},
    }
    assert set(constraints.filter(candidates)) == {"a"}
    ranked = constraints.ranked(candidates)
    assert ranked[0].candidate_id == "a"
    assert ranked[0].admissible


def test_constraint_tolerance_and_missing_fields():
    constraint = Constraint(
        "near",
        "x",
        Comparator.EQ,
        1.0,
        tolerance=0.1,
    )
    assert constraint.evaluate({"x": 1.05})
    assert not constraint.evaluate({})
    assert Constraint(
        "absent",
        "x",
        Comparator.ABSENT,
    ).evaluate({})


def test_minimal_unsatisfied_core_deduplicates_predicates():
    constraints = ConstraintSet(
        (
            Constraint("a", "x", Comparator.GE, 2),
            Constraint("b", "x", Comparator.GE, 2),
            Constraint("c", "y", Comparator.EXISTS),
        )
    )
    assert constraints.minimal_unsatisfied_core({"x": 1}) == (
        "a",
        "c",
    )


def test_negative_space_becomes_constraint():
    record = NegativeSpaceRecord(
        "no-error",
        ("A", "B"),
        "ERROR",
        10,
        0.9,
        provenance=("trace",),
    )
    constraint = record.as_constraint("output")
    assert constraint.evaluate({"output": "OK"})
    assert not constraint.evaluate({"output": "ERROR"})


def test_numeric_bounds():
    constraints = infer_numeric_bounds(
        "latency",
        (0.1, 0.2, 0.3),
        provenance=("instrument",),
    )
    assert constraints.evaluate(
        "inside",
        {"latency": 0.2},
    ).admissible
    assert not constraints.evaluate(
        "outside",
        {"latency": 0.5},
    ).admissible


def test_jsonl_store_roundtrip_and_tamper_detection(tmp_path: Path):
    path = tmp_path / "records.jsonl"
    store = JSONLStore(path)
    store.append({"b": 2, "a": 1})
    assert tuple(store.read()) == ({"a": 1, "b": 2},)
    path.write_text(
        path.read_text().replace('"a":1', '"a":9')
    )
    with pytest.raises(ValueError):
        tuple(store.read())


def test_checkpoint_hash_chain():
    first = Checkpoint.create("c", 0, {"round": 0})
    second = Checkpoint.create(
        "c",
        1,
        {"round": 1},
        first.checkpoint_hash,
    )
    assert first.verify() and second.verify()
    assert not replace(second, state={"round": 2}).verify()


def test_sqlite_store_campaign_and_verification(tmp_path: Path):
    with SQLiteEvidenceStore(tmp_path / "e.sqlite") as store:
        store.create_campaign(
            "c",
            "a" * 64,
            metadata={"domain": "synthetic"},
        )
        store.add_observation("o", "c", 0, {"x": 1})
        store.add_hypothesis("h", "c", 0, {"model": "fsm"})
        store.add_artifact("a", "c", "report", {"ok": True})
        first = Checkpoint.create("c", 0, {"round": 0})
        store.add_checkpoint(first)
        second = Checkpoint.create(
            "c",
            1,
            {"round": 1},
            first.checkpoint_hash,
        )
        store.add_checkpoint(second)
        assert store.verify_campaign("c") == ()
        assert store.observations("c") == ({"x": 1},)
        assert store.latest_checkpoint("c").sequence == 1


def test_sqlite_transaction_rolls_back(tmp_path: Path):
    with SQLiteEvidenceStore(tmp_path / "e.sqlite") as store:
        store.create_campaign("c", "a" * 64)
        with pytest.raises(sqlite3.IntegrityError):
            with store.transaction():
                store.connection.execute(
                    "INSERT INTO observations VALUES(?,?,?,?,?)",
                    ("o", "c", 0, "{}", content_hash({})),
                )
                store.connection.execute(
                    "INSERT INTO observations VALUES(?,?,?,?,?)",
                    ("o", "c", 1, "{}", content_hash({})),
                )
        assert store.observations("c") == ()


def test_re16_catalog_is_complete_and_deterministic():
    cases = catalog()
    assert len(cases) == 16
    assert validate_catalog(cases) == ()
    assert catalog_digest(cases) == catalog_digest(catalog())
    assert all(case.metadata["synthetic"] for case in cases)
    assert len({case.digest for case in cases}) == 16


def test_re16_families_are_diverse():
    families = {case.family for case in catalog()}
    assert {
        "automata",
        "probabilistic",
        "timed",
        "formats",
        "protocols",
        "physical",
        "hybrid",
        "process",
        "versions",
        "ai_behavior",
        "residuals",
        "cleanroom",
    } <= families


def test_residual_miner_detects_bias():
    record = ResidualRecord(
        "bias",
        (2, 3, 4, 5),
        (1, 2, 3, 4),
    )
    assessment = ResidualMiner().assess(record)
    assert assessment.category is ResidualCategory.SYSTEMATIC_BIAS
    assert assessment.confidence > 0.9


def test_residual_miner_uses_version_context():
    record = ResidualRecord(
        "versions",
        (0, 1, 0, 1),
        (0, 0, 0, 0),
        context={"version_count": 2},
    )
    assessment = ResidualMiner().assess(record)
    assert assessment.category is ResidualCategory.VERSION_MIXTURE


def test_unknown_unknown_radar_flags_structure():
    records = (
        ResidualRecord(
            "unknown",
            (0, 0.1, 0.4, 0.9, 1.6),
            (0, 0, 0, 0, 0),
        ),
        ResidualRecord("zero", (1, 1, 1), (1, 1, 1)),
    )
    flagged = ResidualMiner().unknown_unknown_radar(
        records,
        threshold=0.2,
    )
    assert "unknown" in flagged
    assert "zero" not in flagged


def test_re256_cardinality_and_cross_product():
    values = frontier()
    assert len(values) == len(catalog()) * len(perturbations()) == 256
    assert len({case.frontier_id for case in values}) == 256
    assert validate_frontier(values) == ()


def test_each_seed_has_all_perturbations():
    values = frontier()
    expected = {
        item.perturbation_id for item in perturbations()
    }
    for seed in catalog():
        assert {
            case.perturbation_id
            for case in values
            if case.seed_case_id == seed.case_id
        } == expected


def test_frontier_manifest_separates_materialization_and_proof():
    manifest = frontier_manifest()
    assert manifest["case_count"] == 256
    assert manifest["claims"]["materialized_cases"] == 256
    assert manifest["claims"]["executed_cases"] == 0
    assert manifest["claims"]["scientifically_verified_cases"] == 0
    assert manifest["claims"][
        "logical_space_is_not_execution"
    ] is True


def test_missing_provenance_perturbation_blocks_promotion():
    case = expand_case(
        catalog()[0],
        next(
            item
            for item in perturbations()
            if item.perturbation_id == "P10"
        ),
    )
    assert case.expected["oak_expectation"] == "oak_fail_closed"
    assert all(
        observation.get("provenance_removed")
        for observation in case.observations
    )


def test_true_model_omission_flags_unknown_unknown():
    seed = catalog()[0]
    case = expand_case(
        seed,
        next(
            item
            for item in perturbations()
            if item.perturbation_id == "P15"
        ),
    )
    assert len(case.candidate_models) <= len(seed.candidate_models)
    assert (
        case.expected["oak_expectation"]
        == "raise_unknown_unknown"
    )


def test_catalog_cli(tmp_path: Path):
    output = tmp_path / "catalog.json"
    assert main(["catalog", "--output", str(output)]) == 0
    payload = loads(output.read_text())
    assert payload["count"] == 16
    assert payload["issues"] == []


def test_frontier_cli_materializes_re256(tmp_path: Path):
    report = tmp_path / "report.json"
    atlas = tmp_path / "re256.json"
    assert main(
        [
            "frontier",
            "--materialize",
            str(atlas),
            "--output",
            str(report),
        ]
    ) == 0
    payload = loads(report.read_text())
    materialized = loads(atlas.read_text())
    assert payload["manifest"]["case_count"] == 256
    assert len(materialized["cases"]) == 256


def test_probability_timed_and_database_cli(tmp_path: Path):
    probability = tmp_path / "prob.json"
    timed = tmp_path / "timed.json"
    database = tmp_path / "database.json"
    assert main(
        ["demo-prob", "--seed", "7", "--output", str(probability)]
    ) == 0
    assert main(["demo-timed", "--output", str(timed)]) == 0
    assert main(["db-demo", "--output", str(database)]) == 0
    probability_payload = loads(probability.read_text())
    timed_payload = loads(timed.read_text())
    database_payload = loads(database.read_text())
    assert probability_payload["information_gain_bits"] > 0
    assert timed_payload["selected"] == ["A", "B"]
    assert database_payload["verification_errors"] == []
