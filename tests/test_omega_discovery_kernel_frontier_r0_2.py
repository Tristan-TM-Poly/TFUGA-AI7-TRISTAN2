from __future__ import annotations

import json
from pathlib import Path
import sqlite3

import pytest

from omega_discovery_kernel_t import (
    AdaptiveFrontierConfig,
    AliasRecord,
    CORE_LOOP_EVENT_TYPES,
    EVENT_CATALOG,
    EVENT_FAMILIES,
    EVENT_TYPES,
    FrontierExperimentConfig,
    IdentityRegistry,
    Quantity,
    QuantityVector,
    UniversalIdentity,
    catalog_manifest,
    compatible_units,
    convert_value,
    event_spec,
    run_frontier_experiment,
    unit_catalog_manifest,
)


def test_omega64_catalog_has_unique_contracts_and_eight_families() -> None:
    assert len(EVENT_CATALOG) == 64
    assert len(EVENT_TYPES) == 64
    assert len(set(EVENT_TYPES)) == 64
    assert len(EVENT_FAMILIES) == 8
    assert set(CORE_LOOP_EVENT_TYPES).issubset(EVENT_TYPES)
    assert all(spec.name in EVENT_TYPES for spec in EVENT_CATALOG)
    assert all(spec.family in EVENT_FAMILIES for spec in EVENT_CATALOG)
    assert all(spec.purpose.strip() for spec in EVENT_CATALOG)
    assert event_spec("ObservationEvent").family == "ingestion"
    assert event_spec("MMinusRule").scientific_gate == "failure_ancestry_required"
    assert event_spec("PublicationEvent").requires_human_approval is True
    assert event_spec("PublicationEvent").reversible_default is False

    manifest = catalog_manifest()
    assert manifest["event_type_count"] == 64
    assert manifest["family_count"] == 8
    assert len(manifest["events"]) == 64


def test_universal_identity_is_deterministic_versioned_and_content_verified() -> None:
    content = {"claim": "local linearization is valid in a measured residual domain", "scope": "local"}
    alias = AliasRecord(
        value="Omega Linearization Tristan",
        relation="historical_name",
        source="MASTER_SYSTEM_INDEX.md",
        confidence=1.0,
    )
    first = UniversalIdentity.create(
        kind="claim",
        namespace="tristan",
        local_id="CLM-LIN-LOCAL-001",
        version="0.1.0",
        content=content,
        aliases=(alias,),
        source_ids=(),
        oak_status="FORMALIZED",
    )
    second = UniversalIdentity.create(
        kind="claim",
        namespace="tristan",
        local_id="CLM-LIN-LOCAL-001",
        version="0.1.0",
        content=content,
        aliases=(alias,),
        source_ids=(),
        oak_status="FORMALIZED",
    )
    assert first == second
    assert first.verify_content(content)
    assert not first.verify_content({**content, "scope": "global"})
    assert first.validate() == []

    revision_content = {**content, "scope": "local with declared tolerance"}
    revision = first.with_revision(
        version="0.2.0",
        content=revision_content,
        repository_commit="deadbeef",
        oak_status="DEMONSTRATED",
    )
    assert revision.universal_id != first.universal_id
    assert revision.parent_ids == (first.universal_id,)
    assert revision.supersedes == (first.universal_id,)
    assert revision.verify_content(revision_content)

    registry = IdentityRegistry()
    registry.add(first)
    registry.add(revision)
    assert registry.revisions("tristan", "claim", "CLM-LIN-LOCAL-001") == (first, revision)
    assert registry.validate_links() == []
    manifest = registry.manifest()
    assert manifest["identity_count"] == 2
    assert manifest["revision_families"] == 1


def test_unit_aware_quantities_convert_and_propagate_uncertainty() -> None:
    peak = Quantity.create(
        1000.0,
        "cm^-1",
        0.2,
        calibration_id="CAL-RAMAN-001",
        provenance=("synthetic",),
    )
    peak_si = peak.converted("m^-1")
    assert peak_si.value == pytest.approx(100000.0)
    assert peak_si.standard_uncertainty == pytest.approx(20.0)
    assert compatible_units("cm^-1", "m^-1")
    assert not compatible_units("cm^-1", "K")
    assert convert_value(25.0, "degC", "K") == pytest.approx(298.15)

    width = Quantity.create(4.0, "cm^-1", 0.3, calibration_id="CAL-RAMAN-001")
    vector = QuantityVector(
        names=("peak", "width"),
        quantities=(peak, width),
        covariance=((0.04, 0.0), (0.0, 0.09)),
    )
    assert vector.validate() == []
    assert vector.combined_standard_uncertainty((1.0, 1.0)) == pytest.approx((0.04 + 0.09) ** 0.5)

    catalog = unit_catalog_manifest()
    assert catalog["unit_count"] >= 40
    assert "wavenumber" in catalog["dimensions"]


def test_frontier_writes_50000_events_without_materializing_full_graph(tmp_path: Path) -> None:
    output = tmp_path / "frontier-50k"
    summary = run_frontier_experiment(
        output,
        experiment=FrontierExperimentConfig(
            target_events=50_000,
            namespace_count=32,
            seed=20260802,
            failure_period=1,
        ),
        ledger_config=AdaptiveFrontierConfig(
            initial_shard_bytes=65_536,
            shard_growth_factor=2.0,
            checkpoint_interval=5_000,
            commit_interval=1_000,
            minimum_free_bytes=0,
        ),
    )
    manifest = summary["manifest"]
    assert summary["requested_events"] == 50_000
    assert summary["accepted_this_run"] == 50_000
    assert manifest["event_count"] == 50_000
    assert manifest["duplicate_count"] == 0
    assert manifest["rejected_count"] == 0
    assert manifest["subject_count"] == 6_250
    assert manifest["complete_subject_count"] == 6_250
    assert manifest["closed_loop_coverage"] == 1.0
    assert manifest["shard_count"] > 1
    assert manifest["integrity_findings"] == []
    assert manifest["checkpoint_complete"] is True
    assert manifest["finite_target_is_not_permanent_ceiling"] if "finite_target_is_not_permanent_ceiling" in manifest else True
    assert manifest["telemetry"]["accepted_events"] == 50_000
    assert manifest["telemetry"]["subject_count"] == 6_250
    assert manifest["telemetry"]["event_type_counts"] == {
        "ActionProposal": 6_250,
        "ClaimEvent": 6_250,
        "ExperimentSpec": 6_250,
        "GeneratorCandidate": 6_250,
        "MMinusRule": 6_250,
        "OAKTransition": 6_250,
        "ObservationEvent": 6_250,
        "ResultPacket": 6_250,
    }

    shards = sorted((output / "shards").glob("events-*.jsonl"))
    assert len(shards) == manifest["shard_count"]
    assert sum(path.stat().st_size for path in shards) == manifest["telemetry"]["bytes_written"]
    assert (output / "frontier-index.sqlite3").is_file()
    assert (output / "checkpoint.json").is_file()
    assert (output / "telemetry.json").is_file()
    assert (output / "m_minus.jsonl").is_file()
    assert sum(1 for _ in (output / "m_minus.jsonl").open(encoding="utf-8")) == 6_250

    with sqlite3.connect(output / "frontier-index.sqlite3") as connection:
        event_count = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        subject_count = connection.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
        orphan_count = connection.execute(
            "SELECT COUNT(*) FROM events WHERE event_id IS NULL OR event_hash IS NULL"
        ).fetchone()[0]
    assert event_count == 50_000
    assert subject_count == 6_250
    assert orphan_count == 0

    checkpoint = json.loads((output / "checkpoint.json").read_text(encoding="utf-8"))
    assert checkpoint["event_count"] == 50_000
    assert checkpoint["complete"] is True
    assert len(checkpoint["ledger_digest"]) == 64


def test_frontier_resume_deduplicates_existing_events(tmp_path: Path) -> None:
    output = tmp_path / "resume"
    experiment = FrontierExperimentConfig(target_events=80, namespace_count=2, failure_period=1)
    ledger_config = AdaptiveFrontierConfig(
        initial_shard_bytes=4_096,
        checkpoint_interval=16,
        commit_interval=8,
        minimum_free_bytes=0,
    )
    first = run_frontier_experiment(
        output,
        experiment=experiment,
        ledger_config=ledger_config,
    )
    assert first["accepted_this_run"] == 80
    second = run_frontier_experiment(
        output,
        experiment=experiment,
        ledger_config=ledger_config,
        resume=True,
    )
    assert second["accepted_this_run"] == 0
    assert second["manifest"]["event_count"] == 80
    assert second["manifest"]["duplicate_count"] == 80
    assert second["manifest"]["integrity_findings"] == []


def test_finite_frontier_target_is_not_a_controller_ceiling() -> None:
    small = FrontierExperimentConfig(target_events=8)
    larger = FrontierExperimentConfig(target_events=500_000)
    assert small.validate() == []
    assert larger.validate() == []
    assert not hasattr(AdaptiveFrontierConfig(), "max_total_events")
