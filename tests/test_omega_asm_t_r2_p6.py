from __future__ import annotations

import copy
import json

import pytest

from omega_asm_t.cli import main
from omega_asm_t.replication import (
    aggregate_p5_reports,
    canonical_machine_identity,
    machine_fingerprint,
    validate_p5_replication_input,
)


SHA_A = "a" * 64
SHA_B = "b" * 64


def _machine(*, model: str = "143", cache_size: int = 32 * 1024, extra_feature: str | None = None):
    features = ["avx2", "sse2"]
    if extra_feature:
        features.append(extra_feature)
    return {
        "schema_version": 1,
        "architecture": "x86_64",
        "vendor": "GenuineIntel",
        "family": "6",
        "model": model,
        "stepping": "8",
        "model_name": "Test CPU",
        "isa_features": features,
        "caches": [
            {
                "index": "index0",
                "level": 1,
                "cache_type": "Data",
                "size_bytes": cache_size,
                "line_size_bytes": 64,
                "ways_of_associativity": 8,
                "number_of_sets": 64,
                "shared_cpu_list": "0-1",
            }
        ],
        "frequency_context": {
            "current_khz": 3500000,
            "scaling_governor": "performance",
        },
        "runner": {"name": "runner-a"},
        "claim_scope": "observational_hardware_context_only",
    }


def _p5(
    *,
    machine=None,
    sha: str = SHA_A,
    availability: str = "available",
    ipc: float | None = 2.0,
    branch_miss_rate: float | None = 0.1,
):
    return {
        "schema_version": 1,
        "evidence_level": "P5-hardware-counters",
        "availability": availability,
        "claim_scope": "single_execution_context_only",
        "authority": "review_only",
        "machine": machine if machine is not None else _machine(),
        "binary": {"path": "/tmp/bench", "exists": True, "size_bytes": 1234, "sha256": sha},
        "derived": {
            "ipc": ipc,
            "cycles_per_instruction": None if ipc in (None, 0) else 1.0 / ipc,
            "branch_miss_rate": branch_miss_rate,
            "cache_miss_rate": 0.05,
        },
    }


def test_canonical_machine_identity_ignores_ephemeral_runner_and_frequency():
    left = _machine()
    right = copy.deepcopy(left)
    right["frequency_context"]["current_khz"] = 4100000
    right["frequency_context"]["scaling_governor"] = "schedutil"
    right["runner"]["name"] = "runner-b"
    assert canonical_machine_identity(left) == canonical_machine_identity(right)
    assert machine_fingerprint(left) == machine_fingerprint(right)


def test_machine_fingerprint_changes_when_model_changes():
    assert machine_fingerprint(_machine(model="143")) != machine_fingerprint(_machine(model="151"))


def test_machine_fingerprint_changes_when_cache_identity_changes():
    assert machine_fingerprint(_machine(cache_size=32 * 1024)) != machine_fingerprint(
        _machine(cache_size=48 * 1024)
    )


def test_machine_fingerprint_changes_when_isa_feature_mask_changes():
    assert machine_fingerprint(_machine()) != machine_fingerprint(_machine(extra_feature="avx512f"))


def test_validate_p5_requires_binary_hash_for_available_evidence():
    report = _p5()
    report["binary"] = None
    errors = validate_p5_replication_input(report)
    assert any("SHA-256" in item for item in errors)


def test_three_available_same_target_same_binary_reaches_identified_target_replication():
    reports = [_p5(ipc=1.8), _p5(ipc=2.0), _p5(ipc=2.2)]
    campaign = aggregate_p5_reports(reports, min_replicates=3)
    assert campaign["status"] == "replicated_identified_target"
    assert campaign["available_report_count"] == 3
    assert len(campaign["groups"]) == 1
    group = campaign["groups"][0]
    assert group["qualifies_for_identified_target_replication"] is True
    assert group["metrics"]["ipc"]["median"] == pytest.approx(2.0)
    assert group["binary_sha256"] == SHA_A


def test_two_reports_are_insufficient_for_default_p6_threshold():
    campaign = aggregate_p5_reports([_p5(), _p5()])
    assert campaign["status"] == "insufficient_replication"
    assert campaign["groups"][0]["available_count"] == 2
    assert campaign["groups"][0]["qualifies_for_identified_target_replication"] is False


def test_partial_and_unavailable_reports_do_not_count_toward_threshold():
    reports = [
        _p5(availability="available"),
        _p5(availability="available"),
        _p5(availability="partial"),
        _p5(availability="unavailable"),
    ]
    campaign = aggregate_p5_reports(reports)
    group = campaign["groups"][0]
    assert group["input_count"] == 4
    assert group["available_count"] == 2
    assert group["partial_count"] == 1
    assert group["unavailable_count"] == 1
    assert group["qualifies_for_identified_target_replication"] is False


def test_different_binary_hashes_are_never_combined():
    reports = [_p5(sha=SHA_A), _p5(sha=SHA_A), _p5(sha=SHA_B)]
    campaign = aggregate_p5_reports(reports)
    assert len(campaign["groups"]) == 2
    assert {group["binary_sha256"] for group in campaign["groups"]} == {SHA_A, SHA_B}
    assert campaign["status"] == "mixed_or_insufficient_targets"


def test_different_machine_fingerprints_are_never_combined_and_do_not_fake_replication():
    reports = [_p5(machine=_machine(model="143")), _p5(machine=_machine(model="151"))]
    campaign = aggregate_p5_reports(reports, min_replicates=2)
    assert len(campaign["groups"]) == 2
    assert len({group["machine_fingerprint"] for group in campaign["groups"]}) == 2
    assert campaign["status"] == "mixed_or_insufficient_targets"
    assert not any(group["qualifies_for_identified_target_replication"] for group in campaign["groups"])


def test_two_distinct_machine_groups_each_replicated_get_multiple_replicated_targets():
    reports = [
        _p5(machine=_machine(model="143"), ipc=1.9),
        _p5(machine=_machine(model="143"), ipc=2.0),
        _p5(machine=_machine(model="151"), ipc=2.1),
        _p5(machine=_machine(model="151"), ipc=2.2),
    ]
    campaign = aggregate_p5_reports(reports, min_replicates=2)
    assert len(campaign["groups"]) == 2
    assert campaign["status"] == "multiple_replicated_targets"
    assert all(group["qualifies_for_identified_target_replication"] for group in campaign["groups"])


def test_one_replicated_group_plus_extra_insufficient_group_has_precise_status():
    reports = [_p5(), _p5(), _p5(), _p5(sha=SHA_B)]
    campaign = aggregate_p5_reports(reports)
    assert campaign["status"] == "replicated_target_with_additional_groups"
    assert sum(group["qualifies_for_identified_target_replication"] for group in campaign["groups"]) == 1


def test_malformed_report_is_excluded_with_reason():
    campaign = aggregate_p5_reports([{"evidence_level": "P4-observational"}, _p5(), _p5(), _p5()])
    assert campaign["input_report_count"] == 4
    assert len(campaign["excluded_reports"]) == 1
    assert campaign["excluded_reports"][0]["index"] == 0
    assert campaign["status"] == "replicated_identified_target"


def test_uninformative_machine_identity_is_excluded():
    report = _p5(machine={"architecture": "unknown"})
    campaign = aggregate_p5_reports([report])
    assert campaign["eligible_report_count"] == 0
    assert "machine identity" in campaign["excluded_reports"][0]["reasons"][0]


def test_min_replicates_must_be_at_least_two():
    with pytest.raises(ValueError, match="at least 2"):
        aggregate_p5_reports([_p5()], min_replicates=1)


def test_cli_p6_aggregate_emits_replicated_campaign(tmp_path, capsys):
    paths = []
    for index, ipc in enumerate((1.9, 2.0, 2.1)):
        path = tmp_path / f"p5-{index}.json"
        path.write_text(json.dumps(_p5(ipc=ipc)), encoding="utf-8")
        paths.append(str(path))
    assert main(["p6-aggregate", *paths]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["evidence_level"] == "P6-replication-campaign"
    assert payload["status"] == "replicated_identified_target"
    assert payload["promotion_contract"]["universal_claim_allowed"] is False
