from dataclasses import replace

import pytest

from sage_tristan.discovery_path_ir import (
    DiscoveryPath,
    EpistemicState,
    PathStatus,
    PathStep,
    ResidualVector,
    ResourceCost,
    audit_path,
    compare_paths,
    compose_paths,
    counter_path_fixture,
    gauss_ceres_reconstruction,
)
from sage_tristan.greatsages import ClaimClass, get_profile


def test_ceres_reconstruction_is_valid_software_model_not_truth_claim():
    profile = get_profile("gauss")
    path = gauss_ceres_reconstruction(profile)
    audit = audit_path(profile, path)
    assert audit.status is PathStatus.VALID_SOFTWARE_MODEL
    assert audit.historical_truth_certified is False
    assert path.claim_class is ClaimClass.RECONSTRUCTION
    assert path.counterfactual is False


def test_target_is_withheld_initially_and_present_terminally():
    profile = get_profile("gauss")
    path = gauss_ceres_reconstruction(profile)
    audit = audit_path(profile, path)
    assert audit.initial_target_withheld is True
    assert audit.terminal_contains_target is True
    assert path.target_discovery_id not in path.initial_state.knowledge_ids
    assert path.target_discovery_id in path.terminal_state.knowledge_ids


def test_path_continuity_years_and_known_operators_hold():
    profile = get_profile("gauss")
    audit = audit_path(profile, gauss_ceres_reconstruction(profile))
    assert audit.continuity_valid is True
    assert audit.years_monotone is True
    assert audit.operators_known is True
    assert audit.evidence_leakage_free is True


def test_target_or_future_evidence_leak_is_quarantined():
    profile = get_profile("gauss")
    path = gauss_ceres_reconstruction(profile)
    leaked_step = replace(path.steps[0], evidence_ids=(path.target_discovery_id,))
    leaked = replace(path, path_id="leaked", steps=(leaked_step,) + path.steps[1:])
    audit = audit_path(profile, leaked)
    assert audit.status is PathStatus.QUARANTINE
    assert audit.evidence_leakage_free is False
    assert any("leaked" in failure for failure in audit.failures)


def test_unknown_operator_fails_closed():
    profile = get_profile("gauss")
    path = gauss_ceres_reconstruction(profile)
    bad_step = replace(path.steps[1], operator_id="imaginary_genius_operator")
    bad = replace(path, path_id="bad_operator", steps=(path.steps[0], bad_step, path.steps[2]))
    audit = audit_path(profile, bad)
    assert audit.status is PathStatus.QUARANTINE
    assert audit.operators_known is False


def test_cost_and_residual_budgets_are_positive_and_deterministic():
    path = gauss_ceres_reconstruction()
    assert path.total_cost > 0
    assert path.residual_budget > 0
    assert path.total_cost == gauss_ceres_reconstruction().total_cost
    assert path.residual_budget == gauss_ceres_reconstruction().residual_budget


def test_lineage_hash_is_stable_and_changes_with_path_content():
    path = gauss_ceres_reconstruction()
    same = gauss_ceres_reconstruction()
    counter = counter_path_fixture(path)
    assert len(path.lineage_hash) == 64
    assert path.lineage_hash == same.lineage_hash
    assert path.lineage_hash != counter.lineage_hash


def test_counter_path_exposes_parallax_in_operator_program():
    path = gauss_ceres_reconstruction()
    counter = counter_path_fixture(path)
    diff = compare_paths(path, counter)
    assert "representation_switch" in diff.left_only_operator_ids
    assert "anti_switch_stay_native" in diff.right_only_operator_ids
    assert "approximation_residual" in diff.shared_operator_ids
    assert "invariant_search" in diff.shared_operator_ids


def test_uncertainty_must_not_increase_across_valid_fixture():
    profile = get_profile("gauss")
    path = gauss_ceres_reconstruction(profile)
    audit = audit_path(profile, path)
    assert audit.uncertainty_nonincreasing is True
    assert path.terminal_state.uncertainty < path.initial_state.uncertainty


def test_resource_cost_and_residuals_reject_invalid_values():
    with pytest.raises(ValueError):
        ResourceCost(compute=-1)
    with pytest.raises(ValueError):
        ResidualVector(logical=1.1)


def test_path_structure_requires_exact_step_state_count():
    path = gauss_ceres_reconstruction()
    with pytest.raises(ValueError):
        DiscoveryPath(
            path_id="invalid",
            sage_id=path.sage_id,
            target_discovery_id=path.target_discovery_id,
            claim_class=path.claim_class,
            states=path.states,
            steps=path.steps[:1],
        )


def test_composition_requires_identical_boundary_and_preserves_lineage():
    base = gauss_ceres_reconstruction()
    s0, s1, s2, s3 = base.states
    p1, p2, p3 = base.steps
    left = DiscoveryPath(
        "left",
        base.sage_id,
        base.target_discovery_id,
        ClaimClass.RECONSTRUCTION,
        (s0, s1, s2),
        (p1, p2),
        base.source_ids,
    )
    right = DiscoveryPath(
        "right",
        base.sage_id,
        base.target_discovery_id,
        ClaimClass.RECONSTRUCTION,
        (s2, s3),
        (p3,),
        base.source_ids,
    )
    composed, receipt = compose_paths(left, right, composed_path_id="composed")
    assert composed.states == base.states
    assert composed.steps == base.steps
    assert receipt.boundary_state_id == s2.state_id
    assert receipt.lineage_hash == composed.lineage_hash

    wrong_boundary = EpistemicState("wrong", s2.year, s2.knowledge_ids)
    wrong_right = DiscoveryPath(
        "wrong_right",
        base.sage_id,
        base.target_discovery_id,
        ClaimClass.RECONSTRUCTION,
        (wrong_boundary, s3),
        (replace(p3, input_state_id="wrong"),),
        base.source_ids,
    )
    with pytest.raises(ValueError):
        compose_paths(left, wrong_right, composed_path_id="nope")
