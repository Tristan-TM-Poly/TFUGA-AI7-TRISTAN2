from __future__ import annotations

import pytest

from omega_cyber_physical_systems_t.evidence import SystemEvidenceReceipt, assess_receipt
from omega_cyber_physical_systems_t.inventory import InventoryConfig


def test_bench_receipt_without_calibration_and_raw_data_is_blocked():
    receipt = SystemEvidenceReceipt(
        receipt_id="incomplete-bench",
        tier="D5_BENCH_EXPERIMENT",
        artifact_sha256="a" * 64,
        provenance="synthetic negative control",
        method="incomplete bench claim",
        limitations=("no calibrated instrumentation or retained raw data",),
        metadata={
            "instrumentation": ["unidentified sensor"],
            "test_article_id": "synthetic-article",
            "uncertainty_budget": {},
            "raw_data_hash": "invalid",
        },
        origin="synthetic_fixture",
    )
    assessment = assess_receipt(receipt)
    assert assessment.accepted is False
    assert "missing_metadata:calibration_ids" in assessment.blockers
    assert "bench_test_requires_nonempty_uncertainty_budget" in assessment.blockers
    assert "bench_raw_data_hash_invalid" in assessment.blockers


def test_inventory_execution_budgets_must_be_positive():
    with pytest.raises(ValueError, match="finite scan budgets"):
        InventoryConfig(max_files_per_system=0, max_bytes_per_file=1024).validate()
    with pytest.raises(ValueError, match="finite scan budgets"):
        InventoryConfig(max_files_per_system=1, max_bytes_per_file=0).validate()
