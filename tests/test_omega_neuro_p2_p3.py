from omega_neuro_t.hypothesis_campaign import (
    run_p2_benchmark,
    run_p2_p3_campaign,
    run_p3_benchmark,
    synthetic_p2_bundle,
    synthetic_p3_bundle,
)
from omega_neuro_t.split import group_kfold


def _models(report):
    return {item["name"]: item for item in report["models"]}


def test_p2_state_tensor_beats_scalar_with_ablation_and_negative_controls():
    report = run_p2_benchmark()
    models = _models(report)

    assert report["hypothesis"] == "P2_SYNAPTIC_STATE_TENSOR"
    assert report["biological_promotion_allowed"] is False
    assert report["oak"]["candidate_justified"] is True
    assert models["synapse_state_tensor"]["predictive_loss"] < models["scalar_synapse"]["predictive_loss"] * 0.25
    assert report["negative_control"]["degradation_vs_candidate"] > 0.005
    assert all(item["loss_delta_vs_full"] > 0.002 for item in report["ablations"])


def test_p3_higher_order_model_beats_pairwise_and_fails_when_motifs_are_permuted():
    report = run_p3_benchmark()
    models = _models(report)

    assert report["hypothesis"] == "P3_HIGHER_ORDER_WIRING"
    assert report["biological_promotion_allowed"] is False
    assert report["oak"]["candidate_justified"] is True
    assert models["higher_order_hypergraph"]["predictive_loss"] < models["pairwise_graph"]["predictive_loss"] * 0.10
    assert report["negative_control"]["degradation_vs_candidate"] > 0.05
    assert all(item["loss_delta_vs_full"] > 0.002 for item in report["ablations"])


def test_p2_and_p3_reuse_same_group_leakage_barrier():
    for records, _, _ in (synthetic_p2_bundle(groups=10), synthetic_p3_bundle(groups=10)):
        for train, test in group_kfold(records, folds=5, seed="shared-leakage-test"):
            assert {record.group_id for record in train}.isdisjoint(
                {record.group_id for record in test}
            )


def test_campaign_is_deterministic_and_never_promotes_synthetic_biology():
    first = run_p2_p3_campaign()
    second = run_p2_p3_campaign()

    assert first == second
    assert first["software_validation_passed"] is True
    assert first["biological_promotion_allowed"] is False
    assert all(
        report["biological_promotion_allowed"] is False
        for report in first["reports"].values()
    )
