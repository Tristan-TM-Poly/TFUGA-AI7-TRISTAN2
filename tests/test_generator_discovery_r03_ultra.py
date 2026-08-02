from pathlib import Path

import pytest

from omega_generator_discovery_t.ultra_catalog import (
    DEFAULT_ROOT,
    audit_ultra_catalog,
    catalog_statistics,
    deterministic_validation_sample,
    export_subatlas,
    get_generator,
    load_manifest,
    query_generators,
    related_bundle,
)


ROOT = DEFAULT_ROOT


def test_ultra_manifest_counts() -> None:
    counts = load_manifest(ROOT)["counts"]
    assert counts == {
        "generators": 65536,
        "benchmarks": 131072,
        "hyperedges": 65536,
        "negative_controls": 65536,
        "validations": 65536,
        "total_jsonl_records": 393216,
    }


def test_ultra_full_audit_is_valid() -> None:
    report = audit_ultra_catalog(ROOT)
    assert report.valid
    assert report.orphan_benchmarks == 0
    assert report.orphan_hyperedges == 0
    assert report.missing_negative_controls == 0
    assert report.missing_validations == 0
    assert report.high_risk_not_exhaustive == 0
    assert report.duplicate_coordinate_groups == 0


def test_every_domain_family_cell_has_64_generators() -> None:
    records = query_generators(root=ROOT, domain="spectral", family="translation", limit=100)
    assert len(records) == 64
    assert {record.scale for record in records} == {
        "atomic", "molecular", "micro", "meso", "macro", "system", "network", "multiscale"
    }
    assert {record.representation for record in records} == {
        "state", "operator", "observable", "hypergraph"
    }
    assert {record.regime for record in records} == {"local_linear", "finite_nonlinear"}


def test_noninvertible_sectors_are_explicit() -> None:
    records = query_generators(
        root=ROOT, family="projection", supports_inverse=False, limit=10000
    )
    assert len(records) == 2048
    assert all(record.payload["requires_singular_sector"] for record in records)


def test_generator_bundle_has_all_linked_artifacts() -> None:
    record = get_generator("GEN3-000000", ROOT)
    bundle = related_bundle(record.id, ROOT)
    assert bundle["generator"]["id"] == record.id
    assert len(bundle["benchmarks"]) == 2
    assert len(bundle["hyperedges"]) >= 1
    assert bundle["negative_control"]["generator_id"] == record.id
    assert bundle["validation"]["generator_id"] == record.id


def test_high_risk_validation_is_exhaustive() -> None:
    sample = deterministic_validation_sample(root=ROOT, modulus=65536, residue=0)
    high_risk_count = len(query_generators(root=ROOT, risk_tier="high", limit=10000))
    # query limit is intentionally bounded; the sample must contain at least every
    # high-risk record plus the deterministic residue record.
    assert len(sample) > high_risk_count
    assert "GEN3-000000" in sample


def test_statistics_are_balanced() -> None:
    stats = catalog_statistics(ROOT)
    assert stats["total_records"] == 393216
    assert set(stats["distributions"]["domain"].values()) == {2048}
    assert set(stats["distributions"]["family"].values()) == {2048}
    assert set(stats["distributions"]["scale"].values()) == {8192}
    assert set(stats["distributions"]["representation"].values()) == {16384}
    assert set(stats["distributions"]["regime"].values()) == {32768}


def test_fingerprint_is_sha256() -> None:
    fingerprint = audit_ultra_catalog(ROOT).combined_fingerprint
    assert len(fingerprint) == 64
    int(fingerprint, 16)


def test_query_rejects_unbounded_response() -> None:
    with pytest.raises(ValueError):
        query_generators(root=ROOT, limit=10001)


def test_export_subatlas_is_reproducible(tmp_path: Path) -> None:
    first = export_subatlas(
        tmp_path / "first.jsonl", root=ROOT, domain="crystal", family="rotation", limit=8
    )
    second = export_subatlas(
        tmp_path / "second.jsonl", root=ROOT, domain="crystal", family="rotation", limit=8
    )
    assert first["bundles"] == 8
    assert first["sha256"] == second["sha256"]
    assert (tmp_path / "first.jsonl").read_bytes() == (tmp_path / "second.jsonl").read_bytes()
