from omega_compute_physics_t.atlas import ResourceSample, fit_resource_model
from omega_compute_physics_t.fleet import build_fleet_atlas
from omega_compute_physics_t.meta_oak import (
    audit_representation_candidate,
    audit_residual_interpretation,
    audit_theory_ecology,
    audit_validated_model,
)
from omega_compute_physics_t.repo_scanner import RepositoryGenome, scan_python_source
from omega_compute_physics_t.representation import best_representation
from omega_compute_physics_t.residuals import discover_missing_variable_candidates
from omega_compute_physics_t.theory_foundry import generate_theory_competition
from omega_compute_physics_t.validation import fit_validated_resource_model


def ratio_samples():
    rows = []
    for a in (2.0, 4.0, 8.0, 16.0, 32.0, 64.0):
        for b in (1.0, 2.0, 4.0, 8.0):
            rows.append(
                ResourceSample(
                    variables={"a": a, "b": b},
                    resources={"time": 3.0 * a / b + 2.0},
                )
            )
    return rows


def test_representation_generator_discovers_ratio_compression():
    best = best_representation(ratio_samples(), "time", max_candidates=32)
    assert best.coordinate.label in {"a/b", "b/a"}
    assert best.relative_improvement > 0.5
    report = audit_representation_candidate(best)
    assert report.passes


def test_residual_intelligence_surfaces_hidden_metadata_association():
    rows = []
    for index in range(24):
        a = float((index % 6) + 1)
        hidden = float((index * 5) % 7)
        rows.append(
            ResourceSample(
                variables={"a": a},
                resources={"time": 2.0 * a + 5.0 * hidden},
                metadata={"hidden_pressure": hidden},
            )
        )
    model = fit_resource_model(
        rows,
        "time",
        max_total_degree=1,
        include_logs=False,
        include_xlogx=False,
    )
    report = discover_missing_variable_candidates(
        model,
        rows,
        "time",
        min_absolute_correlation=0.6,
    )
    assert report.structured_residuals_detected
    assert report.candidates[0].name == "hidden_pressure"
    assert audit_residual_interpretation(report).passes
    assert not audit_residual_interpretation(report, causal_claim_requested=True).passes


def test_theory_foundry_keeps_competitors_and_compact_ratio_theory():
    theories = generate_theory_competition(
        ratio_samples(),
        "time",
        max_representations=32,
    )
    assert len(theories) >= 2
    assert theories[0].cv_rmse <= theories[-1].cv_rmse
    assert any(theory.name == "a/b" for theory in theories[:5])
    assert audit_theory_ecology(theories[:5]).passes


def test_meta_oak_validated_model_has_calibration_partition():
    validated = fit_validated_resource_model(ratio_samples(), "time", seed=3)
    report = audit_validated_model(validated)
    assert report.passes
    assert validated.report.n_calibration >= 2


def test_static_repo_scanner_detects_nested_loops_and_recursion():
    source = '''
def quadratic(xs):
    total = 0
    for x in xs:
        for y in xs:
            total += x * y
    return total

def recurse(n):
    if n <= 1:
        return 1
    return n * recurse(n - 1)
'''
    module = scan_python_source(source, module="demo.py")
    by_name = {row.qualified_name: row for row in module.functions}
    assert by_name["quadratic"].max_loop_depth == 2
    assert by_name["quadratic"].structural_scaling_candidate == "O(n^2) loop-depth candidate"
    assert by_name["recurse"].direct_recursion
    assert "recursive" in by_name["recurse"].structural_scaling_candidate


def test_fleet_atlas_clusters_similar_static_workloads():
    module_a = scan_python_source(
        "def f(xs):\n    s=0\n    for x in xs:\n        s += x\n    return s\n",
        module="a.py",
    )
    module_b = scan_python_source(
        "def g(xs):\n    s=1\n    for x in xs:\n        s *= (x+1)\n    return s\n",
        module="b.py",
    )
    repo_a = RepositoryGenome("/a", (module_a,), 1, 1, 5, 1, 0, 0)
    repo_b = RepositoryGenome("/b", (module_b,), 1, 1, 5, 1, 0, 0)
    fleet = build_fleet_atlas({"repo-a": repo_a, "repo-b": repo_b}, similarity_threshold=0.85)
    assert len(fleet.repositories) == 2
    assert len(fleet.workloads) == 2
    assert any(len(family.members) == 2 for family in fleet.families)
