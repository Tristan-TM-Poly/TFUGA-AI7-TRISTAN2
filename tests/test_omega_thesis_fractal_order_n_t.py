from omega_thesis_factory_t.core import example_seed
from omega_thesis_factory_t.forest import (
    ThesisForest,
    ThesisAddress,
    ZoomPolicy,
    dezoom_result,
    demo_zoom_candidates,
    root_thesis,
    thesis_forest_oak_report,
    zoom_thesis,
)


def test_order_n_zoom_and_oak_boundaries():
    root = root_thesis(example_seed())
    assert ThesisAddress(root.address.root, ("A", "B", "C")).order == 3
    children, receipt = zoom_thesis(
        root,
        demo_zoom_candidates(),
        policy=ZoomPolicy(min_power_density=0.45, max_active_children=2, max_order=8),
    )
    assert len(children) == 2
    assert all(child.order == 1 for child in children)
    assert all(child.status == root.status for child in children)
    assert receipt.oak_status_promoted is False
    assert dict(receipt.rejected)["DECORATIVE_BRANCH"] == "below_min_power_density"


def test_dezoom_is_review_only():
    forest = ThesisForest()
    root = root_thesis(example_seed())
    forest.add(root)
    children, _ = zoom_thesis(root, demo_zoom_candidates(), policy=ZoomPolicy(max_active_children=1))
    child = children[0]
    forest.add(child)
    receipt = dezoom_result(
        forest,
        child.id,
        result="bounded local result",
        scope="deterministic fixture",
        uncertainty=0.25,
    )
    assert receipt.ancestor_mutation_performed is False
    assert dict(receipt.propagation)[root.id] == "REVIEW"
    report = thesis_forest_oak_report(forest)
    assert report["order_is_epistemic_quality"] is False
    assert report["scientific_validity_certified"] is False
