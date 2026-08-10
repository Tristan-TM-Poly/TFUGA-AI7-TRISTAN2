from omega_recycle import Candidate, Component, Material, RecoveryMode, RecoveryOptimizer, RecoveryRoute


def test_optimizer_is_deterministic_and_selects_best_route() -> None:
    materials = {"copper": Material("copper", 8.0)}
    c = Component(component_id="x", name="functional copper assembly", mass_kg=2.0, material_fractions={"copper": 1.0}, reuse_value=100.0, functional_probability=0.95)
    routes = (RecoveryRoute(RecoveryMode.MATERIAL_RECYCLE, process_cost=1.0), RecoveryRoute(RecoveryMode.REUSE))
    optimizer = RecoveryOptimizer(materials)
    first = optimizer.optimize([Candidate(c, routes)])
    second = optimizer.optimize([Candidate(c, routes)])
    assert first.modes() == second.modes() == ("reuse",)


def test_hazardous_component_marks_plan_dry_run_only() -> None:
    materials = {"copper": Material("copper", 8.0)}
    c = Component(component_id="battery", name="battery", mass_kg=2.0, material_fractions={"copper": 1.0}, reuse_value=20.0, hazardous=True)
    route = RecoveryRoute(RecoveryMode.REUSE)
    plan = RecoveryOptimizer(materials).optimize([Candidate(c, (route,))])
    assert plan.dry_run_only is True
    assert "certified_process_or_professional_handling_required" in plan.evaluations[0].warnings
