from __future__ import annotations

from omega_generator_discovery_t.catalog import (
    audit_catalog,
    catalog_statistics,
    query_generators,
)


def test_massive_catalog_counts_and_links() -> None:
    report = audit_catalog()
    assert report.valid
    assert report.generators == 8192
    assert report.benchmarks == 16384
    assert report.linked_generators == 8192
    assert not report.duplicate_generator_ids
    assert not report.missing_generator_links
    assert not report.wrong_benchmark_coverage


def test_catalog_balances_domains_families_and_scales() -> None:
    stats = catalog_statistics()
    assert stats["generators"] == 8192
    assert len(stats["domains"]) == 32
    assert len(stats["families"]) == 32
    assert len(stats["scales"]) == 8
    assert set(stats["domains"].values()) == {256}
    assert set(stats["families"].values()) == {256}
    assert set(stats["scales"].values()) == {1024}


def test_query_returns_full_spectral_translation_scale_atlas() -> None:
    records = query_generators(domain="spectral", family="translation", limit=None)
    assert len(records) == 8
    assert {record.scale for record in records} == {
        "atomic", "molecular", "micro", "meso",
        "macro", "system", "network", "multiscale",
    }
    assert all(len(record.benchmark_ids) == 2 for record in records)


def test_query_can_select_noninvertible_candidates() -> None:
    records = query_generators(family="projection", limit=64)
    assert records
    assert all(not record.supports_inverse for record in records)


def test_fingerprint_is_stable_shape() -> None:
    report = audit_catalog()
    assert len(report.fingerprint) == 64
    int(report.fingerprint, 16)
