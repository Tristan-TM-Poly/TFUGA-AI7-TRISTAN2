from pathlib import Path

import pytest

from omega_compute_physics_t.atlas import EmpiricalResourceModel, FeatureSpec
from omega_compute_physics_t.benchmark_contract import (
    BenchmarkContract,
    BenchmarkRisk,
    InputAxis,
    gate_contract,
)
from omega_compute_physics_t.complexity_ir import compile_source_ir
from omega_compute_physics_t.dag_resources import DAGEdge, DAGNode, compose_dag
from omega_compute_physics_t.fleet_stage_a import scan_checkout_fleet
from omega_compute_physics_t.machine_genome import calibrate_machine, fingerprint_machine
from omega_compute_physics_t.tropical import directional_dominance


def test_benchmark_contract_blocks_risky_or_untrusted_execution():
    contract = BenchmarkContract(
        contract_id="x",
        repository="owner/repo",
        commit_sha="abc123",
        module="pkg.mod",
        callable_name="f",
        axes=(InputAxis("n", (10.0, 100.0)),),
        fixture="fixture_v1",
        trusted_checkout=False,
        risk=BenchmarkRisk(network=True),
    )
    gate = gate_contract(contract)
    assert gate["decision"] == "block"
    assert any("trusted_checkout" in reason for reason in gate["reasons"])
    assert any("network" in reason for reason in gate["reasons"])


def test_benchmark_contract_allows_bounded_policy_compatible_candidate():
    contract = BenchmarkContract(
        contract_id="x",
        repository="owner/repo",
        commit_sha="abc123",
        module="pkg.mod",
        callable_name="f",
        axes=(InputAxis("n", (10.0, 100.0)),),
        fixture="fixture_v1",
        trusted_checkout=True,
        timeout_s=2.0,
    )
    assert contract.executable
    assert gate_contract(contract)["decision"] == "allow"


def test_complexity_ir_extracts_structural_operations():
    source = """
def f(xs):
    total = 0
    for row in xs:
        for x in row:
            if x > 0:
                total += g(x)
    return total
"""
    ir = compile_source_ir(source, module="m.py")[0]
    assert ir.max_loop_depth == 2
    assert ir.op_count("LOOP") == 2
    assert ir.op_count("BRANCH") == 1
    assert ir.op_count("CALL") == 1
    assert "g" in ir.call_targets


def test_machine_genome_is_measured_but_bounded():
    base = fingerprint_machine()
    assert base.python
    calibrated = calibrate_machine(repeats=1, scalar_iterations=1000, copy_bytes=1024)
    assert calibrated.scalar_ops_per_s and calibrated.scalar_ops_per_s > 0
    assert calibrated.bytes_copy_per_s and calibrated.bytes_copy_per_s > 0


def test_dag_critical_path_and_cycle_guard():
    nodes = [DAGNode("A", 2.0), DAGNode("B", 3.0), DAGNode("C", 4.0)]
    edges = [DAGEdge("A", "C", 0.5), DAGEdge("B", "C", 0.2)]
    report = compose_dag(nodes, edges)
    assert report.critical_path == ("B", "C")
    assert report.critical_path_s == pytest.approx(7.2)
    with pytest.raises(ValueError):
        compose_dag([DAGNode("A", 1), DAGNode("B", 1)], [DAGEdge("A", "B"), DAGEdge("B", "A")])


def test_tropical_direction_changes_dominant_multivariate_term():
    variables = ("a", "b")
    model = EmpiricalResourceModel(
        target="time",
        variables=variables,
        features=(
            FeatureSpec("monomial", variables, (2, 1)),
            FeatureSpec("monomial", variables, (1, 3)),
        ),
        coefficients=(2.0, 3.0),
        n_samples=10,
        domain={"a": (1.0, 100.0), "b": (1.0, 100.0)},
        rmse=0.0,
        r2=1.0,
        ridge=0.0,
    )
    isotropic = directional_dominance(model, (1.0, 1.0))
    a_heavy = directional_dominance(model, (3.0, 1.0))
    assert isotropic.degree == pytest.approx(4.0)
    assert isotropic.dominant_terms == ("a*b^3",)
    assert a_heavy.degree == pytest.approx(7.0)
    assert a_heavy.dominant_terms == ("a^2*b",)


def test_fleet_stage_a_scans_multiple_checkouts_without_execution(tmp_path: Path):
    r1 = tmp_path / "r1"
    r2 = tmp_path / "r2"
    r1.mkdir(); r2.mkdir()
    (r1 / "a.py").write_text("def f(n):\n    for i in range(n):\n        pass\n", encoding="utf-8")
    (r2 / "b.py").write_text("def g(n):\n    return [i*i for i in range(n)]\n", encoding="utf-8")
    genomes, report = scan_checkout_fleet({"R1": r1, "R2": r2}, benchmark_limit=10)
    assert set(genomes) == {"R1", "R2"}
    assert len(report.repositories) == 2
    assert report.workloads == 2
    assert report.benchmark_seeds
