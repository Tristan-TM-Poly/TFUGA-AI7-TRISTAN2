from __future__ import annotations

import json
import subprocess
import sys

from omega_prototype_portfolio_t.grand_atlas import (
    ARTIFACT_TYPES,
    CANONICAL_MEMORY,
    compile_grand_atlas,
    grand_atlas_report,
    memory_markdown,
)
from omega_prototype_portfolio_t.seed import seed_snapshot
from omega_prototype_portfolio_t.seed_grand_atlas import FAMILY_SPECS, GRAND_ATLAS_MINIMUM


def test_grand_atlas_adds_108_new_entries():
    assert sum(len(items) for items in FAMILY_SPECS.values()) == 108


def test_grand_atlas_minimum_and_unique_ids():
    snapshot = seed_snapshot()
    assert len(snapshot.prototypes) >= GRAND_ATLAS_MINIMUM
    assert len({item.prototype_id for item in snapshot.prototypes}) == len(snapshot.prototypes)


def test_grand_atlas_has_at_least_12_families_and_15_types():
    report = grand_atlas_report(seed_snapshot())
    assert report["family_count"] >= 12
    assert report["artifact_type_count"] >= 15
    assert set(report["artifact_type_counts"]).issubset(ARTIFACT_TYPES)


def test_r01_showcase_is_preserved_as_legacy_family():
    report = grand_atlas_report(seed_snapshot())
    assert report["legacy_r01_count"] == 23


def test_memory_forbids_exhaustiveness_and_volume_inflation():
    joined = "\n".join(CANONICAL_MEMORY).lower()
    assert "never an exhaustive inventory" in joined
    assert "line count" in joined
    assert "all-repository" in joined


def test_report_is_review_only():
    report = grand_atlas_report(seed_snapshot())
    assert report["exhaustiveness_claimed"] is False
    assert report["truth_probability_claimed"] is False
    assert report["external_action_performed"] is False
    assert report["merge_authorized"] is False
    assert report["publication_authorized"] is False


def test_grand_atlas_bundle_is_deterministic(tmp_path):
    snapshot = seed_snapshot()
    one, two = tmp_path / "one", tmp_path / "two"
    r1 = compile_grand_atlas(snapshot, one)
    r2 = compile_grand_atlas(snapshot, two)
    assert r1 == r2
    assert all((one / name).read_bytes() == (two / name).read_bytes() for name in r1)
    manifest = json.loads((one / "manifest.json").read_text())
    assert manifest["entry_count"] >= GRAND_ATLAS_MINIMUM
    assert manifest["exhaustiveness_claimed"] is False


def test_memory_markdown_contains_canonical_header():
    text = memory_markdown(seed_snapshot())
    assert "Canonical Memory R0.2" in text
    assert "registry pointer != live repository truth" in text


def test_cli_grand_atlas(tmp_path):
    output = tmp_path / "atlas.json"
    subprocess.run(
        [sys.executable, "-m", "omega_prototype_portfolio_t", "grand-atlas", "--output", str(output)],
        check=True,
    )
    payload = json.loads(output.read_text())
    assert payload["entry_count"] >= GRAND_ATLAS_MINIMUM
    assert payload["family_count"] >= 12


def test_cli_memory(tmp_path):
    output = tmp_path / "memory.md"
    subprocess.run(
        [sys.executable, "-m", "omega_prototype_portfolio_t", "memory", "--output", str(output)],
        check=True,
    )
    assert "Persistent rules" in output.read_text()
