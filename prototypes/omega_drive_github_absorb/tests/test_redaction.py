from omega_drive_github_absorb.redaction import redact_manifest, redact_oak_report


def test_redact_manifest_removes_raw_drive_values():
    manifest = [
        {
            "source_url": "https://drive.google.com/drive/folders/SECRET",
            "normalized_url": "https://drive.google.com/drive/folders/SECRET",
            "drive_file_id": "SECRET",
            "source_url_sha256": "a" * 64,
            "kind": "folder",
            "oak_status": "ALLOW_INVENTORY_ONLY",
        }
    ]
    redacted = redact_manifest(manifest)
    assert redacted[0]["source_url"] == "REDACTED"
    assert redacted[0]["normalized_url"] == "REDACTED"
    assert redacted[0]["drive_file_id"] == "REDACTED"
    assert redacted[0]["source_url_sha256"] == "a" * 64


def test_redact_oak_report_removes_unknown_links():
    report = {"unknown_links": ["https://drive.google.com/private"], "objects_count": 1}
    safe = redact_oak_report(report)
    assert safe["unknown_links"] == ["REDACTED"]
    assert safe["objects_count"] == 1
