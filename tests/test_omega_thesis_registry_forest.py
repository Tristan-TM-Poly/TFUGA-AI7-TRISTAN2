from omega_generative_closure_t.core import MaxMinVector
from omega_thesis_factory_t.core import example_seed
from omega_thesis_factory_t.forest import ZoomPolicy
from omega_thesis_factory_t.registry_forest import compile_registry_forest


def _vector(value: float) -> MaxMinVector:
    return MaxMinVector(
        verified_value=value,
        evidence=value,
        reuse=value,
        reachability=value,
        regenerability=value,
        fertility=value,
        cost=0.1,
        structural_debt=0.1,
        proof_debt=0.1,
        semantic_debt=0.1,
        uncertainty=0.1,
        irreversibility=0.0,
    )


def test_registry_zoom_requires_explicit_vectors_and_holds_missing_seeds():
    forest, receipt = compile_registry_forest(
        {"OMEGA_TRANSFORM_T": _vector(0.9)},
        policy=ZoomPolicy(min_power_density=0.1, max_active_children=5, max_order=1),
    )
    assert receipt.score_inference_performed is False
    assert receipt.oak_status_promoted is False
    assert receipt.scored_seed_ids == ("OMEGA_TRANSFORM_T",)
    assert "OMEGA_AUTO2_T" in receipt.held_seed_ids
    assert receipt.selected_seed_ids == ("OMEGA_TRANSFORM_T",)
    child = forest.children(receipt.parent_id)[0]
    assert child.order == 1
    assert child.status == "C"


def test_registry_zoom_caps_child_status_to_source_seed_maturity():
    forest, receipt = compile_registry_forest(
        {"OMEGA_AUTO2_T": _vector(0.9)},
        mother_seed=example_seed(),
        policy=ZoomPolicy(min_power_density=0.1, max_active_children=5, max_order=1),
    )
    child = forest.children(receipt.parent_id)[0]
    assert child.status == "B"
    assert child.local_claims


def test_registry_zoom_uses_go_max_min_budget_without_claiming_global_optimum():
    forest, receipt = compile_registry_forest(
        {
            "OMEGA_TRANSFORM_T": _vector(0.9),
            "OMEGA_AUTO2_T": _vector(0.4),
        },
        policy=ZoomPolicy(min_power_density=0.1, max_active_children=1, max_order=1),
    )
    assert len(forest.children(receipt.parent_id)) == 1
    assert receipt.selected_seed_ids == ("OMEGA_TRANSFORM_T",)
    assert receipt.zoom_receipt.global_optimum_claimed is False
