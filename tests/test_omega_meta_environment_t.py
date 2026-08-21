from dataclasses import replace

import pytest

from omega_meta_environment_t import (
    EnvironmentalState,
    EnvironmentalTransformationGenome,
    EvidenceContract,
    EvidenceStatus,
    ResidualKind,
    ResidualPassport,
    audit,
)


def base_genome() -> EnvironmentalTransformationGenome:
    state = EnvironmentalState(
        state_id="S0",
        scale="watershed",
        observed_at="2026-08-21",
        indicators={"water": 1.0},
        provenance=("fixture",),
    )
    residual = ResidualPassport(
        residual_id="R0",
        kind=ResidualKind.WATER,
        magnitude=1.0,
        unit="u",
        origin="source",
        transformation="routing",
        destination="receiver",
        spatial_boundary="watershed + receiver",
        temporal_boundary="2026-2030",
        uncertainty=0.1,
        affected_entities=("community", "habitat"),
    )
    evidence = EvidenceContract(
        claim_id="C0",
        claim="bounded intervention improves target relative to baseline",
        status=EvidenceStatus.MEASURED,
        sources=("measurement",),
        boundary="watershed + receiver",
        baseline="pre-intervention",
        falsifier="no improvement or unacceptable transferred residual",
    )
    return EnvironmentalTransformationGenome(
        transformation_id="T0",
        state_before=state,
        goal="improve watershed viability",
        mechanism="bounded intervention",
        place="test territory",
        time_horizon="4 years",
        affected_entities=("community", "habitat"),
        residuals=(residual,),
        evidence=(evidence,),
        reversibility=0.8,
        authority_confirmed=True,
        monitoring_required=True,
        local_scope="pilot site",
        global_scope="watershed + supply chain",
    )


def test_nominal_fixture_passes_all_r01_gates():
    report = audit(base_genome())
    assert report.passed
    assert len(report.findings) == 8


def test_digest_is_deterministic():
    g = base_genome()
    assert g.digest() == g.digest()
    assert audit(g).report_digest == audit(g).report_digest


def test_missing_residual_destination_fails_accounting():
    g = base_genome()
    bad_r = replace(g.residuals[0], destination="")
    report = audit(replace(g, residuals=(bad_r,)))
    assert not report.passed
    assert not next(f for f in report.findings if f.gate == "G1_RESIDUAL_ACCOUNTING").passed


def test_simulation_cannot_be_promoted_to_reality():
    report = audit(replace(base_genome(), simulation_claimed_as_reality=True))
    assert not next(f for f in report.findings if f.gate == "G2_SIMULATION_NE_REALITY").passed


def test_compensation_cannot_be_promoted_to_restoration():
    report = audit(replace(base_genome(), compensation_claimed_as_restoration=True))
    assert not next(f for f in report.findings if f.gate == "G3_COMPENSATION_NE_RESTORATION").passed


def test_high_irreversibility_requires_authority_and_high_confidence_evidence():
    g = base_genome()
    weak = replace(g.evidence[0], status=EvidenceStatus.SIMULATED, sources=("model",))
    report = audit(replace(
        g,
        reversibility=0.1,
        authority_confirmed=False,
        evidence=(weak,),
    ))
    assert not next(
        f for f in report.findings
        if f.gate == "G4_IRREVERSIBILITY_AUTHORITY_EVIDENCE"
    ).passed


def test_local_and_global_scope_must_not_be_collapsed():
    g = base_genome()
    report = audit(replace(g, global_scope=g.local_scope))
    assert not next(f for f in report.findings if f.gate == "G5_LOCAL_NE_GLOBAL").passed


def test_residual_bearing_action_requires_monitoring():
    report = audit(replace(base_genome(), monitoring_required=False))
    assert not next(f for f in report.findings if f.gate == "G6_MONITORING").passed


def test_affected_entities_are_mandatory():
    report = audit(replace(base_genome(), affected_entities=()))
    assert not next(f for f in report.findings if f.gate == "G7_AFFECTED_ENTITIES").passed


def test_invalid_uncertainty_is_rejected():
    with pytest.raises(ValueError):
        replace(base_genome().residuals[0], uncertainty=1.5)
