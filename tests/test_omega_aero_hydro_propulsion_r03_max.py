from __future__ import annotations

import pytest

from omega_aero_hydro_propulsion_t.materials import default_material_atlas
from omega_aero_hydro_propulsion_t.mission import demo_air_mission
from omega_aero_hydro_propulsion_t.models import default_air, demo_rotor
from omega_aero_hydro_propulsion_t.system_optimizer import InfiniteSystemFrontier, SystemSearchConstraints, evaluate_system_candidate, run_system_campaign


def relaxed_constraints() -> SystemSearchConstraints:
    return SystemSearchConstraints(
        maximum_rotor_mass_kg=None,
        minimum_structural_safety_factor=0.05,
        maximum_overall_spl_db=None,
        minimum_robust_feasible_probability=0.0,
        minimum_safe_continuation_fraction=0.0,
        maximum_expected_shaft_energy_j=None,
        maximum_tip_mach=2.0,
    )


def test_material_atlas_has_provenance_and_no_engineering_allowables() -> None:
    atlas = default_material_atlas()
    assert len(atlas.names) >= 5
    assert all(not atlas.get_record(name).engineering_allowables for name in atlas.names)


def test_frontier_is_deterministic_and_has_no_total_cap() -> None:
    atlas = default_material_atlas()
    frontier = InfiniteSystemFrontier()
    assert frontier.vector_at(123, atlas) == frontier.vector_at(123, atlas)
    assert frontier.to_dict()["permanent_total_cap"] is None
    assert frontier.vector_at(10_000_000, atlas).frontier_index == 10_000_000


def test_frontier_vectors_stay_inside_declared_bounds() -> None:
    atlas = default_material_atlas()
    frontier = InfiniteSystemFrontier()
    for index in (0, 1, 2, 31, 999_999):
        vector = frontier.vector_at(index, atlas)
        assert frontier.diameter_scale_bounds[0] <= vector.diameter_scale <= frontier.diameter_scale_bounds[1]
        assert frontier.chord_scale_bounds[0] <= vector.chord_scale <= frontier.chord_scale_bounds[1]
        assert frontier.pitch_delta_bounds_deg[0] <= vector.pitch_delta_deg <= frontier.pitch_delta_bounds_deg[1]
        assert frontier.rpm_scale_bounds[0] <= vector.rpm_scale <= frontier.rpm_scale_bounds[1]


def test_candidate_produces_cross_domain_evidence_hash() -> None:
    atlas = default_material_atlas()
    vector = InfiniteSystemFrontier().vector_at(0, atlas)
    result = evaluate_system_candidate(
        demo_rotor(), default_air(), demo_air_mission(), vector,
        atlas=atlas, constraints=relaxed_constraints(),
    )
    assert len(result.evidence_hash) == 64
    assert result.structural.physics_certified is False
    assert result.acoustic.physics_certified is False
    assert result.robust_mission.physics_certified is False
    assert result.fault_envelope.physics_certified is False
    assert result.physics_certified is False


def test_impossible_mass_constraint_rejects_candidate() -> None:
    atlas = default_material_atlas()
    vector = InfiniteSystemFrontier().vector_at(0, atlas)
    constraints = SystemSearchConstraints(
        maximum_rotor_mass_kg=1e-9,
        minimum_structural_safety_factor=0.05,
        maximum_overall_spl_db=None,
        minimum_robust_feasible_probability=0.0,
        minimum_safe_continuation_fraction=0.0,
        maximum_tip_mach=2.0,
    )
    result = evaluate_system_candidate(
        demo_rotor(), default_air(), demo_air_mission(), vector,
        atlas=atlas, constraints=constraints,
    )
    assert not result.feasible
    assert "system:maximum_rotor_mass_kg" in result.violations


def test_campaign_is_finite_resource_bound_slice_of_unbounded_frontier() -> None:
    report = run_system_campaign(
        demo_rotor(), default_air(), demo_air_mission(),
        start_index=10, count=4, constraints=relaxed_constraints(), checkpoint_interval=2,
    )
    assert report.evaluated_count == 4
    assert report.next_index == 14
    assert report.permanent_total_cap is None
    assert [checkpoint.next_index for checkpoint in report.checkpoints] == [12, 14]


def test_campaign_resume_chain_matches_single_run() -> None:
    kwargs = {
        "base_design": demo_rotor(),
        "medium": default_air(),
        "mission": demo_air_mission(),
        "constraints": relaxed_constraints(),
        "checkpoint_interval": 2,
    }
    full = run_system_campaign(start_index=0, count=6, **kwargs)
    first = run_system_campaign(start_index=0, count=3, **kwargs)
    second = run_system_campaign(
        start_index=3, count=3,
        previous_chain_digest=first.final_chain_digest,
        **kwargs,
    )
    assert second.final_chain_digest == full.final_chain_digest


def test_campaign_candidate_ids_are_unique_and_pareto_is_subset() -> None:
    report = run_system_campaign(
        demo_rotor(), default_air(), demo_air_mission(),
        start_index=0, count=5, constraints=relaxed_constraints(), checkpoint_interval=5,
    )
    identifiers = {item.vector.candidate_id for item in report.candidates}
    assert len(identifiers) == report.evaluated_count
    assert all(item.vector.candidate_id in identifiers for item in report.pareto_front)
    assert report.best is not None


def test_campaign_is_deterministic() -> None:
    kwargs = dict(
        base_design=demo_rotor(), medium=default_air(), mission=demo_air_mission(),
        start_index=20, count=3, constraints=relaxed_constraints(), checkpoint_interval=3,
    )
    left = run_system_campaign(**kwargs)
    right = run_system_campaign(**kwargs)
    assert left.final_chain_digest == right.final_chain_digest
    assert [item.evidence_hash for item in left.candidates] == [item.evidence_hash for item in right.candidates]


def test_invalid_previous_digest_is_rejected() -> None:
    with pytest.raises(ValueError):
        run_system_campaign(
            demo_rotor(), default_air(), demo_air_mission(),
            start_index=0, count=1, constraints=relaxed_constraints(),
            previous_chain_digest="not-a-digest",
        )
