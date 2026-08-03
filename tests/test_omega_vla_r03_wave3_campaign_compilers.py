from omega_vla_t.r03.wave3 import (
    CampaignConfig, IdentityAddress, audit_wave3,
    compile_property_test, compile_smtlib_counterexample,
    instantiate, run_campaign,
)


def test_compilers_preserve_claim_boundaries():
    address = IdentityAddress(
        "commutator.identity_zero", 2, "real", "dense", "none", "smoke"
    )
    schema, instance = instantiate(address)
    python_target = compile_property_test(schema, instance, trials=4)
    smt_target = compile_smtlib_counterexample(schema, instance)
    assert python_target.status == "GENERATED_UNEXECUTED"
    assert "assert report.passed" in python_target.source
    assert not python_target.formally_verified
    assert smt_target.status == "FORMAL_TARGET_UNCHECKED"
    assert "(check-sat)" in smt_target.source
    assert "not a universal proof" in smt_target.source
    assert smt_target.formal_proof_claimed is False


def test_campaign_is_deterministic_resumable_and_unique():
    config = CampaignConfig(count=12, seed=11, start_offset=17, trials_per_identity=2)
    first = run_campaign(config).to_dict()
    second = run_campaign(config).to_dict()
    assert first == second
    assert first["passed"]
    assert first["generated"] == 12
    assert first["unique_instances"] == 12
    assert first["next_offset"] == 29
    assert first["logical_frontier_size"] > 10_000
    assert first["permanent_total_cap"] is None
    assert first["theorem_claimed"] is False


def test_oak_passes():
    report = audit_wave3(seed=2026)
    assert report.passed, report.to_dict()
    assert report.status == "OAK_PASS_SOFTWARE_RESEARCH_FIXTURES_R0_3_WAVE_3"
    assert report.formal_proof_claimed is False
