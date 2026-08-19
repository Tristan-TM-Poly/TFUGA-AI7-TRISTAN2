from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_prime_value_t.certificate import verify_certificate
from omega_prime_value_t.r02.benchmark import deterministic_benchmark
from omega_prime_value_t.r02.engine import CampaignEngine
from omega_prime_value_t.r02.models import TaskState
from omega_prime_value_t.r02.ntt_kernel import convolution, naive_convolution, ntt, validate_convolution
from omega_prime_value_t.r02.planner import CampaignPlanner, PlannerPolicy, verify_manifest
from omega_prime_value_t.r02.portfolio import PortfolioAllocator
from omega_prime_value_t.r02.registry import LocalPrimeRegistry, prime_fingerprint
from omega_prime_value_t.r02.storage import CampaignStore


def test_planner_manifest_is_deterministic() -> None:
    policy = PlannerPolicy(8, 10, 1, 127, 17)
    first = CampaignPlanner(policy).build()
    second = CampaignPlanner(policy).build()
    assert first == second
    assert first.sha256 == second.sha256
    assert verify_manifest(first)


def test_planner_uses_contiguous_ordinals_and_shards() -> None:
    manifest = CampaignPlanner(PlannerPolicy(8, 8, 1, 99, 7)).build()
    assert [task.ordinal for task in manifest.tasks] == list(range(manifest.task_count))
    assert manifest.shard_count == (manifest.task_count + 6) // 7
    assert len({task.task_id for task in manifest.tasks}) == manifest.task_count


def test_planner_values_follow_proth_form() -> None:
    manifest = CampaignPlanner(PlannerPolicy(8, 12, 1, 33, 5)).build()
    for task in manifest.tasks:
        assert task.value == task.k * 2**task.exponent + 1
        assert task.k % 2 == 1
        assert task.k < 2**task.exponent
        assert task.value < 2**64


@pytest.mark.parametrize(
    "policy",
    [
        PlannerPolicy(0, 2),
        PlannerPolicy(5, 4),
        PlannerPolicy(5, 5, 10, 1),
        PlannerPolicy(5, 5, shard_size=0),
        PlannerPolicy(5, 5, max_value=2**64),
    ],
)
def test_planner_rejects_invalid_policy(policy: PlannerPolicy) -> None:
    with pytest.raises(ValueError):
        CampaignPlanner(policy)


def test_manifest_tamper_detection() -> None:
    payload = CampaignPlanner(PlannerPolicy(8, 8, 1, 31, 8)).build().to_dict()
    payload["tasks"][0]["value"] = "999"
    assert not verify_manifest(payload)


def test_store_load_is_idempotent(tmp_path: Path) -> None:
    manifest = CampaignPlanner(PlannerPolicy(8, 8, 1, 31, 8)).build()
    with CampaignStore(tmp_path / "campaign.db") as store:
        assert store.load_manifest(manifest) == manifest.task_count
        assert store.load_manifest(manifest) == 0
        assert store.integrity_check()
        assert store.checkpoint(manifest.campaign_id)["pending"] == manifest.task_count


def test_store_pending_order(tmp_path: Path) -> None:
    manifest = CampaignPlanner(PlannerPolicy(8, 8, 1, 31, 8)).build()
    with CampaignStore(tmp_path / "campaign.db") as store:
        store.load_manifest(manifest)
        tasks = list(store.iter_pending(manifest.campaign_id, limit=4))
        assert [task.ordinal for task in tasks] == [0, 1, 2, 3]
        assert all(task.state is TaskState.PLANNED for task in tasks)


def test_campaign_resume_processes_each_task_once(tmp_path: Path) -> None:
    manifest = CampaignPlanner(PlannerPolicy(8, 10, 1, 127, 13)).build()
    with CampaignStore(tmp_path / "campaign.db") as store:
        engine = CampaignEngine(store, sieve_bound=500)
        first = engine.execute(manifest, max_tasks=19)
        checkpoint = store.checkpoint(manifest.campaign_id)
        second = engine.execute(manifest)
        third = engine.execute(manifest)
        assert first.processed == 19
        assert checkpoint["pending"] == manifest.task_count - 19
        assert second.processed == manifest.task_count - 19
        assert third.processed == 0
        assert store.checkpoint(manifest.campaign_id)["pending"] == 0
        assert store.integrity_check()


def test_campaign_certificates_verify_and_registry_matches(tmp_path: Path) -> None:
    manifest = CampaignPlanner(PlannerPolicy(8, 10, 1, 127, 17)).build()
    with CampaignStore(tmp_path / "campaign.db") as store:
        summary = CampaignEngine(store, sieve_bound=500).execute(manifest)
        certificates = store.certificate_payloads(manifest.campaign_id)
        assert summary.certified == len(certificates) > 0
        assert all(verify_certificate(certificate)[0] for certificate in certificates)
        registry = LocalPrimeRegistry(store)
        assert registry.count() == len(certificates)
        assert all(registry.contains(int(certificate["candidate"]["value"])) for certificate in certificates)


def test_campaign_receipt_conservation(tmp_path: Path) -> None:
    manifest = CampaignPlanner(PlannerPolicy(8, 9, 1, 99, 11)).build()
    with CampaignStore(tmp_path / "campaign.db") as store:
        summary = CampaignEngine(store).execute(manifest)
        accounted = (
            summary.filtered_composites
            + summary.composites
            + summary.probable_primes
            + summary.failed
        )
        assert accounted == summary.processed
        assert len(summary.receipts) == summary.processed
        assert summary.failed == 0


def test_registry_rejects_duplicate_certificate(tmp_path: Path) -> None:
    manifest = CampaignPlanner(PlannerPolicy(8, 8, 1, 31, 8)).build()
    with CampaignStore(tmp_path / "campaign.db") as store:
        CampaignEngine(store).execute(manifest)
        certificate = store.certificate_payloads(manifest.campaign_id)[0]
        registry = LocalPrimeRegistry(store)
        count = registry.count()
        assert not registry.register(manifest.campaign_id, certificate)
        assert registry.count() == count


def test_prime_fingerprint_is_stable_and_domain_separated() -> None:
    assert prime_fingerprint(97) == prime_fingerprint(97)
    assert prime_fingerprint(97) != prime_fingerprint(193)
    assert len(prime_fingerprint(97)) == 64


@pytest.mark.parametrize(
    "values,modulus",
    [
        ([1], 97),
        ([1, 2], 97),
        ([0, 1, 2, 3], 97),
        ([5, -2, 9, 100, 4, 7, 6, 1], 998244353),
    ],
)
def test_ntt_round_trip(values: list[int], modulus: int) -> None:
    transformed = ntt(values, modulus)
    restored = ntt(transformed, modulus, inverse=True)
    assert restored == [value % modulus for value in values]


def test_ntt_rejects_non_power_of_two() -> None:
    with pytest.raises(ValueError):
        ntt([1, 2, 3], 97)


def test_ntt_rejects_length_above_two_adicity() -> None:
    with pytest.raises(ValueError):
        ntt(list(range(64)), 97)


@pytest.mark.parametrize(
    "left,right,modulus",
    [
        ([], [1], 97),
        ([1], [], 97),
        ([1], [2], 97),
        ([1, 2, 3], [4, 5], 97),
        ([1, 2, 3, 4, 5, 6, 7], [8, 9, 10, 11, 12], 998244353),
        ([100, -2, 3], [4, 200, -7], 998244353),
    ],
)
def test_convolution_matches_naive(left: list[int], right: list[int], modulus: int) -> None:
    assert convolution(left, right, modulus) == naive_convolution(left, right, modulus)


def test_convolution_validation_receipt() -> None:
    receipt = validate_convolution([1, 2, 3], [4, 5], 998244353)
    assert receipt["matches_naive"] is True
    assert receipt["result"] == [4, 13, 22, 15]


def test_portfolio_initial_exploration_is_deterministic() -> None:
    allocator = PortfolioAllocator()
    choices = []
    for _ in range(3):
        choice = allocator.choose()
        choices.append(choice)
        allocator.observe(choice, 1.0)
    assert choices == ["prestige", "product", "research"]


def test_portfolio_product_evidence_increases_weight() -> None:
    allocator = PortfolioAllocator()
    allocator.observe("prestige", 0.1, 4)
    allocator.observe("research", 2.0, 2)
    allocator.observe("product", 8.0, 2)
    weights = allocator.recommended_weights()
    assert weights["product"] > weights["research"] > weights["prestige"]
    assert sum(weights.values()) == pytest.approx(1.0, abs=2e-8)


def test_portfolio_report_oak_boundaries() -> None:
    report = PortfolioAllocator().report()
    assert report["claims"] == {
        "financial_return_predicted": False,
        "record_probability_certified": False,
        "allocation_is_advisory": True,
    }


def test_portfolio_rejects_unknown_arm_and_bad_cost() -> None:
    allocator = PortfolioAllocator()
    with pytest.raises(KeyError):
        allocator.observe("unknown", 1)
    with pytest.raises(ValueError):
        allocator.observe("product", 1, 0)


def test_benchmark_is_deterministic_and_complete() -> None:
    first = deterministic_benchmark()
    second = deterministic_benchmark()
    assert first == second
    assert first["status"] == "CERTIFIED_RESUMABLE_PRIME_CAMPAIGN_FIXTURES_R0_2"
    assert first["manifest_verified"] is True
    assert first["all_certificates_verified"] is True
    assert first["database"]["integrity_check"] is True
    assert first["ntt_convolution"]["matches_naive"] is True
    assert first["checkpoint_after_first"]["pending"] > 0
    assert first["checkpoint_final"]["pending"] == 0
    assert first["claims"] == {
        "campaign_is_infinite": False,
        "external_novelty_checked": False,
        "record_claimed": False,
        "market_demand_proven": False,
        "secret_prime_material_generated": False,
    }


def test_benchmark_json_round_trip() -> None:
    payload = deterministic_benchmark()
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
