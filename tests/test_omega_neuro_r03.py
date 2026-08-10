from omega_neuro_t.benchmark import run_p1_benchmark
from omega_neuro_t.dataset import observations_from_jsonl, synthetic_p1_bundle
from omega_neuro_t.provenance import verify_payload
from omega_neuro_t.split import group_kfold, split_signature


def _model_map(report):
    return {model["name"]: model for model in report["models"]}


def _ablation_map(report):
    return {item["name"]: item for item in report["ablations"]}


def test_manifest_verifies_exact_payload_and_rejects_tampering():
    records, payload, manifest = synthetic_p1_bundle(groups=8, trials_per_group=4)
    assert verify_payload(manifest, payload)
    assert not verify_payload(manifest, payload + b"tamper")
    roundtrip = observations_from_jsonl(payload, manifest)
    assert roundtrip == records


def test_group_kfold_has_no_group_leakage_and_is_deterministic():
    records, _, _ = synthetic_p1_bundle(groups=12, trials_per_group=4)
    first = group_kfold(records, folds=4, seed="fixed")
    second = group_kfold(records, folds=4, seed="fixed")
    assert split_signature(first) == split_signature(second)
    held_out = set()
    for train, test in first:
        train_groups = {record.group_id for record in train}
        test_groups = {record.group_id for record in test}
        assert train_groups.isdisjoint(test_groups)
        held_out.update(record.sample_id for record in test)
    assert held_out == {record.sample_id for record in records}


def test_planted_address_effect_beats_scalar_baseline():
    report = run_p1_benchmark(groups=24, trials_per_group=8, noise_scale=0.02)
    models = _model_map(report)
    assert models["address_aware"]["predictive_loss"] < models["scalar"]["predictive_loss"]
    assert models["address_plus_context"]["predictive_loss"] < models["address_aware"]["predictive_loss"]
    assert report["oak"]["candidate_justified"] is True
    assert report["biological_promotion_allowed"] is False


def test_ablation_recovers_planted_address_and_context_information():
    report = run_p1_benchmark(groups=24, trials_per_group=8, noise_scale=0.01)
    ablations = _ablation_map(report)
    assert ablations["remove_address_interactions"]["loss_delta_vs_full"] > 0
    assert ablations["remove_context"]["loss_delta_vs_full"] > 0


def test_benchmark_report_is_exactly_reproducible_for_same_inputs():
    first = run_p1_benchmark(groups=16, trials_per_group=6, noise_scale=0.03, split_seed="same")
    second = run_p1_benchmark(groups=16, trials_per_group=6, noise_scale=0.03, split_seed="same")
    assert first == second
    assert first["manifest"]["sha256"] == second["manifest"]["sha256"]
    assert first["split_signature"] == second["split_signature"]
