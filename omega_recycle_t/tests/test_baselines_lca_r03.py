from omega_recycle.baselines import compare_baselines
from omega_recycle.bench import demo_problem
from omega_recycle.lca import inventory_for_route


def test_baseline_suite_is_explicit_and_complete() -> None:
    materials, candidates = demo_problem()
    results = compare_baselines(candidates, materials)
    assert tuple(result.name for result in results) == (
        "canonical", "mass_only", "value_only", "no_preservation_prior"
    )
    assert all(len(result.plan.evaluations) == len(candidates) for result in results)


def test_lca_interface_is_mass_balanced_inventory_only() -> None:
    _, candidates = demo_problem()
    component = candidates[0].component
    route = candidates[0].routes[3]
    inventory = inventory_for_route(component, route)
    flows = {flow.name: flow for flow in inventory.flows}
    assert abs(flows["retained_product_mass"].amount + flows["residual_mass"].amount - component.mass_kg) < 1e-12
    assert inventory.claim_boundary == "inventory_only_no_lifecycle_impact_claim"
