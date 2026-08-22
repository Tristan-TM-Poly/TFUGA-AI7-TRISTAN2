import json

from omega_ait_llmt_allt_t.core import MissionIR, compile_mission, constitution, default_genome, demo_bundle, mutate_genome, regeneration_receipt


def test_low_residual_selects_no_action():
    report = compile_mission(MissionIR(mission_id="closed", residual=0.01, complexity=100, uncertainty=1.0, risk=1.0))
    assert report["status"] == "NO_ACTION"
    assert report["topology"] == "NO_ACTION"


def test_simple_work_selects_go_min():
    report = compile_mission(MissionIR(mission_id="simple", residual=0.4, complexity=5, uncertainty=0.05, risk=0.05, required_capabilities=("reasoning",)))
    assert report["status"] == "CANDIDATE_FOR_REVIEW"
    assert report["topology"] == "GO_MIN"


def test_insufficient_evidence_abstains():
    report = compile_mission(MissionIR(mission_id="uncertain", residual=0.8, complexity=60, uncertainty=0.8, risk=0.2, evidence_count=0))
    assert report["status"] == "ABSTAIN_MORE_EVIDENCE"
    assert report["auto_promotion"] is False


def test_failed_hard_gate_blocks_non_compensatorily():
    report = compile_mission(MissionIR(mission_id="blocked", residual=1.0, complexity=100, uncertainty=0.0, risk=0.0, authority_ok=False))
    assert report["status"] == "BLOCKED"
    assert report["topology"] == "NO_ACTION"
    assert report["failed_gates"] == ["authority"]
    assert report["external_action_performed"] is False


def test_complex_crossdomain_selects_allt():
    report = compile_mission(MissionIR(mission_id="complex", residual=0.9, complexity=90, uncertainty=0.6, risk=0.4, required_capabilities=("physics", "code", "simulation", "search", "verification", "counterfactual")))
    assert report["topology"] == "ALLT"
    assert report["representation"] == "simulation"
    assert report["authority"] == "review_only"


def test_mutation_never_auto_promotes():
    receipt = mutate_genome(default_genome(), residual_signal="verifier monoculture", verified_gain=0.2)
    assert receipt.status == "CANDIDATE"
    assert receipt.auto_promotion is False
    assert receipt.rollback_available is True


def test_constitution_has_required_separations():
    c = constitution()
    assert c["hard_gates_are_non_compensatory"] is True
    assert c["generator_is_judge"] is False
    assert c["capability_implies_authority"] is False
    assert c["automatic_promotion_allowed"] is False
    assert c["no_zero_touch_without_observability"] is True


def test_regeneration_seed_is_deterministic():
    assert regeneration_receipt() == regeneration_receipt()


def test_demo_bundle_is_json_roundtrippable_and_has_expected_cases():
    decoded = json.loads(json.dumps(demo_bundle(), sort_keys=True))
    reports = {r["mission_id"]: r for r in decoded["reports"]}
    assert reports["simple.min"]["topology"] == "GO_MIN"
    assert reports["research.fertile"]["status"] == "ABSTAIN_MORE_EVIDENCE"
    assert reports["crossdomain.complex"]["topology"] == "ALLT"
    assert reports["authority.blocked"]["status"] == "BLOCKED"
