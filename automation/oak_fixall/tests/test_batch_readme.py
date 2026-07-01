from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_batch_quickstart_mentions_no_mutation():
    text = (ROOT / "automation" / "oak_fixall" / "README_BATCH.md").read_text(encoding="utf-8")
    assert "does not mutate repositories" in text
