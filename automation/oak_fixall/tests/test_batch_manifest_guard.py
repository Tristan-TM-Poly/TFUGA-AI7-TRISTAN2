from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_batch_manifest_has_local_only_guard():
    text = (ROOT / "automation" / "oak_fixall" / "batch_report_manifest.yaml").read_text(encoding="utf-8")
    assert "local_files_only" in text
    assert "dry_run_only" in text
