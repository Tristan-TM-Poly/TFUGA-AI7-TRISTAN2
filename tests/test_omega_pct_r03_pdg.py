import json

from omega_pct_t.r03max.pdg_absorber import absorb_snapshot


def test_snapshot_absorber_versions_and_quarantines(tmp_path):
    records = [
        {"pdg_id": 11, "name": "electron", "status": "established", "mass_gev": 0.000511},
        {"pdg_id": 11, "name": "duplicate", "status": "established"},
        {"name": "missing-id", "status": "unknown"},
    ]
    manifest = absorb_snapshot(
        records,
        edition="2026",
        cutoff_date="2026-01-15",
        source_locator="test-fixture",
        output_directory=tmp_path,
    )
    assert manifest.accepted_count == 1
    assert manifest.quarantine_count == 2
    assert (tmp_path / "manifest.json").exists()
    payload = json.loads((tmp_path / "manifest.json").read_text())
    assert payload["cutoff_date"] == "2026-01-15"
