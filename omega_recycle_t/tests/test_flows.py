from omega_recycle import Candidate, Component, ConstrainedRecoveryOptimizer, FlowConstraints, Material, RecoveryMode, RecoveryRoute


def test_global_constraint_can_change_local_preference() -> None:
    materials = {"copper": Material("copper", 8.0)}
    c1 = Component("a", "a", 1.0, {"copper": 1.0}, 100.0)
    c2 = Component("b", "b", 1.0, {"copper": 1.0}, 90.0)
    expensive_reuse = RecoveryRoute(RecoveryMode.REUSE, process_cost=8.0)
    cheap_recycle = RecoveryRoute(RecoveryMode.MATERIAL_RECYCLE, process_cost=0.0)
    candidates = (Candidate(c1, (expensive_reuse, cheap_recycle)), Candidate(c2, (expensive_reuse, cheap_recycle)))
    result = ConstrainedRecoveryOptimizer(materials).optimize(candidates, FlowConstraints(max_process_cost=12.0))
    assert result.evaluated_combinations == 4
    assert result.feasible_combinations >= 1
    assert result.plan.modes().count("reuse") <= 1


def test_infeasible_global_constraints_are_explicit() -> None:
    materials = {"copper": Material("copper", 8.0)}
    c = Component("a", "a", 1.0, {"copper": 1.0}, 100.0, disassembly_cost=1.0)
    candidate = Candidate(c, (RecoveryRoute(RecoveryMode.REUSE),))
    optimizer = ConstrainedRecoveryOptimizer(materials)
    try:
        optimizer.optimize((candidate,), FlowConstraints(max_process_cost=0.0))
    except ValueError as exc:
        assert "no feasible" in str(exc)
    else:
        raise AssertionError("expected infeasible optimization")
