from __future__ import annotations

import pytest

from omega_aero_hydro_propulsion_t.materials import default_material_atlas
from omega_aero_hydro_propulsion_t.mission import demo_air_mission
from omega_aero_hydro_propulsion_t.models import default_air, demo_rotor
from omega_aero_hydro_propulsion_t.multifidelity import (
    FidelityDefinition,
    MultiFidelityPolicy,
    ResourceEnvelope,
    expanded_fault_scenarios,
    expanded_uncertainty_cases,
    merge_shard_reports,
    plan_shards,
    run_multifidelity_campaign,
    screen_f0,
)
from omega_aero_hydro_propulsion_t.r04_oak import (
    permissive_r04_policy,
    relaxed_r04_constraints,
    run_r04_benchmarks,
)
from omega_aero_hydro_propulsion_t.system_optimizer import (
    InfiniteSystemFrontier,
    SystemSearchConstraints,
)


@pytest.fixture(scope="module")
def context():
    return {
        "rotor": demo_rotor(),
        "medium": default_air(),
        "mission": demo_air_mission(),
        "atlas": default_material_atlas(),
        "frontier": InfiniteSystemFrontier(namespace="r04-test"),
        "policy": permissive_r04_policy(),
        "constraints": relaxed_r04_constraints(),
    }


@pytest.fixture(scope="module")
def full_campaign(context):
    return run_multifidelity_campaign(
        context["rotor"],
        context["medium"],
        context["mission"],
        campaign_id="r04-test-campaign",
        start_index=0,
        count=4,
        resources=ResourceEnvelope(max_cost_units=1_000.0, checkpoint_interval=2),
        frontier=context["frontier"],
        atlas=context["atlas"],
        constraints=context["constraints"],
        policy=context["policy"],
    )


def test_fidelity_definition_rejects_phantom_stage():
    with pytest.raises(ValueError):
        FidelityDefinition("F9_MAGIC", 1.0, "invalid").validate()


def test_policy_labels_do_not_claim_physical_fidelity():
    policy = MultiFidelityPolicy()
    assert all(
        not stage.physical_fidelity_claim
        for stage in (policy.f0, policy.f1, policy.f2)
    )
    assert policy.to_dict()["permanent_total_cap"] is None


def test_f0_screen_is_deterministic(context):
    vector = context["frontier"].vector_at(7, context["atlas"])
    left = screen_f0(
        context["rotor"],
        context["medium"],
        context["mission"],
        vector,
        atlas=context["atlas"],
        constraints=context["constraints"],
        policy=context["policy"],
    )
    right = screen_f0(
        context["rotor"],
        context["medium"],
        context["mission"],
        vector,
        atlas=context["atlas"],
        constraints=context["constraints"],
        policy=context["policy"],
    )
    assert left == right
    assert len(left.evidence_hash) == 64
    assert left.physics_certified is False


def test_expanded_stress_scenarios_are_unique():
    uncertainties = expanded_uncertainty_cases()
    faults = expanded_fault_scenarios()
    assert len(uncertainties) > 5
    assert len(faults) > 4
    assert len({item.name for item in uncertainties}) == len(uncertainties)
    assert len({item.name for item in faults}) == len(faults)


def test_shard_plan_exactly_covers_requested_range():
    manifests = plan_shards(
        campaign_id="coverage",
        start_index=10,
        count=11,
        shard_count=3,
    )
    covered = [
        index
        for manifest in manifests
        for index in range(manifest.start_index, manifest.end_index_exclusive)
    ]
    assert covered == list(range(10, 21))
    assert len(covered) == len(set(covered))
    assert all(len(item.seed_digest) == 64 for item in manifests)


def test_campaign_executes_three_evidence_stages(full_campaign):
    assert full_campaign.f0_count == 4
    assert full_campaign.f1_count > 0
    assert full_campaign.f2_count > 0
    assert len(full_campaign.evidence_events) >= full_campaign.f0_count
    assert full_campaign.physics_certified is False


def test_campaign_respects_resource_envelope(full_campaign):
    assert full_campaign.consumed_cost_units <= full_campaign.resources.max_cost_units
    assert 0.0 <= full_campaign.backpressure.pressure_ratio <= 1.0
    assert full_campaign.backpressure.next_recommended_count >= 1


def test_campaign_frontier_has_no_permanent_total_cap(full_campaign):
    assert full_campaign.permanent_total_cap is None
    assert full_campaign.frontier.to_dict()["permanent_total_cap"] is None
    assert full_campaign.policy.to_dict()["permanent_total_cap"] is None


def test_low_budget_activates_backpressure(context):
    report = run_multifidelity_campaign(
        context["rotor"],
        context["medium"],
        context["mission"],
        campaign_id="low-budget",
        start_index=100,
        count=5,
        resources=ResourceEnvelope(max_cost_units=2.0, checkpoint_interval=1),
        frontier=context["frontier"],
        atlas=context["atlas"],
        constraints=context["constraints"],
        policy=context["policy"],
    )
    assert report.f0_count == 2
    assert report.f1_count == 0
    assert report.consumed_cost_units == 2.0
    assert "resource_budget" in report.backpressure.stop_reason


def test_negative_memory_records_rejections_without_auto_exclusion(context):
    report = run_multifidelity_campaign(
        context["rotor"],
        context["medium"],
        context["mission"],
        campaign_id="strict-mminus",
        start_index=0,
        count=3,
        resources=ResourceEnvelope(max_cost_units=20.0, checkpoint_interval=1),
        frontier=context["frontier"],
        atlas=context["atlas"],
        constraints=SystemSearchConstraints(
            maximum_rotor_mass_kg=0.01,
            minimum_structural_safety_factor=1.5,
            maximum_overall_spl_db=80.0,
            minimum_robust_feasible_probability=1.0,
            minimum_safe_continuation_fraction=1.0,
            maximum_tip_mach=0.40,
        ),
        policy=context["policy"],
    )
    assert report.m_minus
    assert all("do not convert" in item.action for item in report.m_minus)


def test_shard_merge_matches_unsharded_evidence_chain(context, full_campaign):
    left = run_multifidelity_campaign(
        context["rotor"],
        context["medium"],
        context["mission"],
        campaign_id="r04-test-campaign",
        start_index=0,
        count=2,
        resources=ResourceEnvelope(max_cost_units=1_000.0, checkpoint_interval=1),
        frontier=context["frontier"],
        atlas=context["atlas"],
        constraints=context["constraints"],
        policy=context["policy"],
    )
    right = run_multifidelity_campaign(
        context["rotor"],
        context["medium"],
        context["mission"],
        campaign_id="r04-test-campaign",
        start_index=2,
        count=2,
        resources=ResourceEnvelope(max_cost_units=1_000.0, checkpoint_interval=1),
        frontier=context["frontier"],
        atlas=context["atlas"],
        constraints=context["constraints"],
        policy=context["policy"],
    )
    merged = merge_shard_reports((right, left), campaign_id="r04-test-campaign")
    assert merged.evaluated_count == full_campaign.f0_count
    assert merged.final_chain_digest == full_campaign.final_chain_digest
    assert merged.physics_certified is False


def test_shard_merge_rejects_gaps(context):
    left = run_multifidelity_campaign(
        context["rotor"],
        context["medium"],
        context["mission"],
        campaign_id="gap-test",
        start_index=0,
        count=1,
        resources=ResourceEnvelope(max_cost_units=200.0),
        frontier=context["frontier"],
        atlas=context["atlas"],
        constraints=context["constraints"],
        policy=context["policy"],
    )
    right = run_multifidelity_campaign(
        context["rotor"],
        context["medium"],
        context["mission"],
        campaign_id="gap-test",
        start_index=2,
        count=1,
        resources=ResourceEnvelope(max_cost_units=200.0),
        frontier=context["frontier"],
        atlas=context["atlas"],
        constraints=context["constraints"],
        policy=context["policy"],
    )
    with pytest.raises(ValueError, match="contiguous"):
        merge_shard_reports((left, right), campaign_id="gap-test")


def test_r04_oak_benchmarks_pass():
    report = run_r04_benchmarks()
    assert report.passed
    assert report.status == "CERTIFIED_COMPUTATIONAL_ADAPTIVE_MULTIFIDELITY_R0_4"
    assert report.physics_certified is False
