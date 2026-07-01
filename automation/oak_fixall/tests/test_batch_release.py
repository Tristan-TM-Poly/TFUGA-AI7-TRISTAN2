from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_batch_release_is_advisory_local_first():
    text = (ROOT / "automation" / "oak_fixall" / "BATCH_REPORT_RELEASE.md").read_text(encoding="utf-8")
    assert "advisory" in text
    assert "local-first" in text
