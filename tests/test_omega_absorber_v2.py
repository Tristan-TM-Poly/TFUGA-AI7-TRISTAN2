from __future__ import annotations

import json
from pathlib import Path

from omega_prof_poly_t.absorb_query import build_canon_packets, search_output, write_canon_packets
from omega_prof_poly_t.drive_manifest_adapter import audit_manifest, normalize_drive_manifest
from omega_prof_poly_t.mminus_absorber import entries_from_oak_report, summarize_entries
from omega_prof_poly_t.universal_absorber import absorb_path, write_outputs


def test_query_and_canon_packets_from_absorber_output(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "omega.md").write_text(
        "Theory: CVCD creates testable HGFM claims. OAK requires evidence and counter-evidence.",
        encoding="utf-8",
    )
    out = tmp_path / "out"
    write_outputs(absorb_path(corpus), out)

    hits = search_output(out, "CVCD HGFM OAK", limit=5)
    packets = build_canon_packets(out, max_packets=3)
    packet_path = write_canon_packets(out, packets)

    assert hits
    assert packets
    assert packet_path.exists()


def test_drive_manifest_adapter_json(tmp_path: Path) -> None:
    manifest = tmp_path / "drive.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "id": "abc123",
                    "name": "theory.pdf",
                    "mimeType": "application/pdf",
                    "size": "42",
                    "webViewLink": "https://drive.google.com/file/d/abc123/view",
                }
            ]
        ),
        encoding="utf-8",
    )

    items = normalize_drive_manifest(manifest)
    audit = audit_manifest(items)

    assert len(items) == 1
    assert audit["pdf_like_items"] == 1
    assert "missing_content_hash_until_downloaded" in audit["warnings"]


def test_mminus_entries_from_oak_report(tmp_path: Path) -> None:
    report = tmp_path / "oak_report.json"
    report.write_text(
        json.dumps(
            {
                "publishable": False,
                "warnings": ["pdf_no_extractable_text_possible_scan"],
                "blocked_or_review_claims": 2,
            }
        ),
        encoding="utf-8",
    )

    entries = entries_from_oak_report(report)
    summary = summarize_entries(entries)

    assert summary["entries"] == 2
    assert summary["by_severity"]["high"] == 1
