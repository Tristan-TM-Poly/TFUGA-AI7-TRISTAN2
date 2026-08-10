from omega_neuro_t.dataset import synthetic_p1_dataset
from omega_neuro_t.robustness import (
    p1_permutation_negative_control,
    p1_split_stability,
    permute_addresses,
)


def test_address_permutation_preserves_label_counts_but_changes_assignment():
    records = synthetic_p1_dataset(groups=10, trials_per_group=4)
    permuted = permute_addresses(records, seed="fixed")
    assert sorted(record.address for record in records) == sorted(record.address for record in permuted)
    assert any(before.address != after.address for before, after in zip(records, permuted))
    assert [record.sample_id for record in records] == [record.sample_id for record in permuted]


def test_permutation_negative_control_destroys_planted_predictive_advantage():
    control = p1_permutation_negative_control(groups=24, trials_per_group=8, noise_scale=0.03)
    assert control["control_degrades_prediction"] is True
    assert control["loss_ratio"] > 20.0


def test_p1_decision_is_stable_across_distinct_group_splits():
    stability = p1_split_stability(("a", "b", "c", "d"), groups=24, trials_per_group=8)
    assert stability["distinct_split_signatures"] == 4
    assert stability["justified_fraction"] == 1.0
    assert stability["predictive_improvement_min"] > 0.1
