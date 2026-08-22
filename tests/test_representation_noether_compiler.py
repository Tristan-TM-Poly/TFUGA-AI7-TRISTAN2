from dataclasses import replace

from sage_tristan.discovery_path_ir import gauss_ceres_reconstruction
from sage_tristan.greatsages import get_profile
from sage_tristan.representation_noether_compiler import (
    InvariantMeasurement,
    InvariantStatus,
    MetricKind,
    MorphismStatus,
    RepresentationBundle,
    RepresentationCompiler,
    RepresentationMorphismR05,
    audit_discovery_path_representations,
    ceres_representation_compiler,
    noether_audit,
)


def test_invariant_defect_and_tolerance_are_explicit():
    conserved = InvariantMeasurement("i", 1.0, 1.01, scale=1.0, tolerance=0.02)
    broken = InvariantMeasurement("j", 1.0, 1.20, scale=1.0, tolerance=0.02)
    assert conserved.defect == 0.01
    assert conserved.status is InvariantStatus.CONSERVED_WITHIN_TOLERANCE
    assert broken.status is InvariantStatus.BROKEN


def test_zero_confidence_invariant_is_indeterminate():
    measurement = InvariantMeasurement("i", 1.0, 2.0, confidence=0.0)
    assert measurement.status is InvariantStatus.INDETERMINATE


def test_complexity_gain_and_information_loss_are_dimensionless_proxies():
    morphism = RepresentationMorphismR05(
        "m",
        RepresentationBundle(("a",)),
        RepresentationBundle(("b",)),
        complexity_before=10.0,
        complexity_after=6.0,
        information_before=10.0,
        information_after=9.0,
        metric_kind=MetricKind.BENCHMARK_PROXY,
    )
    assert morphism.normalized_complexity_gain == 0.4
    assert morphism.information_loss == 0.1


def test_broken_invariant_quarantines_even_high_compression():
    compiler = ceres_representation_compiler()
    bad = compiler.morphism("ceres_lossy_shortcut_r05")
    receipt = noether_audit(bad)
    assert receipt.status is MorphismStatus.QUARANTINE
    assert "target_problem_identity" in receipt.broken_invariant_ids
    assert receipt.physical_conservation_law_claimed is False
    assert receipt.mathematical_theorem_claimed is False


def test_good_morphisms_are_admissible_software_models():
    compiler = ceres_representation_compiler()
    for morphism_id in (
        "ceres_rep_switch_r05",
        "ceres_residualize_r05",
        "ceres_orbit_reconstruction_r05",
    ):
        assert compiler.morphism(morphism_id).status is MorphismStatus.ADMISSIBLE_SOFTWARE_MODEL


def test_path_search_rejects_quarantined_shortcut_in_ranking():
    compiler = ceres_representation_compiler()
    best = compiler.best_path(
        ("historical_problem_statement",),
        ("orbit_reconstruction", "residual_space"),
        max_depth=4,
    )
    assert best is not None
    assert best.quarantined is False
    assert best.morphism_ids == (
        "ceres_rep_switch_r05",
        "ceres_residualize_r05",
        "ceres_orbit_reconstruction_r05",
    )
    assert "ceres_lossy_shortcut_r05" not in best.morphism_ids


def test_discovery_path_representation_changes_are_fully_covered():
    path = gauss_ceres_reconstruction(get_profile("gauss"))
    audit = audit_discovery_path_representations(path, ceres_representation_compiler())
    assert audit.all_changes_covered is True
    assert audit.promotable is True
    assert audit.uncovered_step_ids == ()
    assert audit.quarantined_morphism_ids == ()
    assert len(audit.covered_step_ids) == 3
    assert audit.noether_is_architectural_analogy is True


def test_missing_morphism_fails_closed_for_discovery_path():
    path = gauss_ceres_reconstruction(get_profile("gauss"))
    compiler = ceres_representation_compiler()
    incomplete = RepresentationCompiler(compiler.morphisms[:-2])
    audit = audit_discovery_path_representations(path, incomplete)
    assert audit.all_changes_covered is False
    assert audit.promotable is False
    assert audit.uncovered_step_ids


def test_information_inflation_gets_explicit_penalty():
    base = ceres_representation_compiler().morphism("ceres_rep_switch_r05")
    inflated = replace(base, morphism_id="inflated", information_after=1.2)
    assert inflated.information_inflation > 0
    assert inflated.penalty > base.penalty


def test_compiler_bounds_cycles_and_requires_positive_depth():
    a = RepresentationBundle(("a",))
    b = RepresentationBundle(("b",))
    ab = RepresentationMorphismR05("ab", a, b, 1, 0.9, 1, 1)
    ba = RepresentationMorphismR05("ba", b, a, 1, 0.9, 1, 1)
    compiler = RepresentationCompiler((ab, ba))
    assert compiler.best_path(("a",), ("b",), max_depth=2) is not None
    try:
        compiler.enumerate_paths(("a",), ("b",), max_depth=0)
    except ValueError as exc:
        assert "max_depth" in str(exc)
    else:
        raise AssertionError("max_depth=0 must fail closed")
