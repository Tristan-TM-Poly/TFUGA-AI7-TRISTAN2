from omega_compute_physics_t.call_graph import CallEdge, CallGraphReport
from omega_compute_physics_t.fleet_opportunity import compile_fleet_opportunities
from omega_compute_physics_t.repo_scanner import FunctionGenome, ModuleGenome, RepositoryGenome


def _function(name: str, *, loops: int, calls: int) -> FunctionGenome:
    return FunctionGenome(
        module="m.py",
        qualified_name=name,
        line_start=1,
        line_end=10,
        loc=10,
        arguments=1,
        loops=loops,
        max_loop_depth=loops,
        branches=0,
        calls=calls,
        comprehensions=0,
        allocations=0,
        awaits=0,
        yields=0,
        direct_recursion=False,
        async_function=False,
        structural_scaling_candidate="candidate",
    )


def test_r06_to_r07_bridge_ranks_graph_central_code_for_measurement():
    leaf = _function("leaf", loops=1, calls=0)
    central = _function("central", loops=2, calls=1)
    genome = RepositoryGenome(
        root="/tmp/repo",
        modules=(ModuleGenome("m.py", (leaf, central), ()),),
        python_files=1,
        functions=2,
        total_loc=20,
        max_loop_depth=2,
        recursive_functions=0,
        async_functions=0,
    )
    graph = CallGraphReport(
        nodes=("m.py:leaf", "m.py:central"),
        edges=(CallEdge("m.py:leaf", "m.py:central", "test"),),
        unresolved_calls={},
        strongly_connected_components=(("m.py:leaf",), ("m.py:central",)),
        recursive_components=(),
        fan_in={"m.py:leaf": 0, "m.py:central": 1},
        fan_out={"m.py:leaf": 1, "m.py:central": 0},
    )
    report = compile_fleet_opportunities(
        "repo",
        genome,
        graph,
        confidence_debts={"m.py:central": 0.2, "m.py:leaf": 0.2},
    )
    assert len(report.evidence) == 2
    scores = {row.node: row.measurement_priority for row in report.decisions}
    assert scores["m.py:central"] > scores["m.py:leaf"]
    assert "runtime hotspots" in report.oak_warning
