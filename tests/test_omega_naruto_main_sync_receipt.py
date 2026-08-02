import json
from pathlib import Path


def test_main_sync_receipt_declares_non_destructive_scope() -> None:
    receipt_path = Path("omega_naruto_hmagfm/main_sync_receipt.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert receipt["base_main_sha"] == "111eeac1059555701a6682a771fda9ddd407c921"
    assert receipt["status"] == "content_reconciled_pending_merge_parent"
    assert "not scientific validation" in receipt["non_claim"]
