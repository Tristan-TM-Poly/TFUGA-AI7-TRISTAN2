import pytest

from omega_sc_hg_t import (
    BondChannel,
    OrbitalChannel,
    PhononChannel,
    SuperconductingCandidate,
    adaptive_filter,
    audit_candidate,
    borophene_2026_seed,
    compare_counterfactuals,
    pareto_front,
    tc_uncertainty_envelope,
)


def candidate(name="reference", *, lam=1.0, omega=500.0, stability=0.2, phase=200.0, practical=0.8):
    return SuperconductingCandidate(
        name=name,
        formula="B",
        dimensionality="2D-bilayer",
        bonds=(BondChannel("B-B bridge", "interlayer", True, 1.0, 1.7, 0.8),),
        orbitals=(
            OrbitalChannel("p_xy", "in-plane", 0.7, 0.5),
            OrbitalChannel("p_z", "out-of-plane", 0.8, 0.5),
        ),
        phonons=(
            PhononChannel("in-plane", "xy", omega, lam * 0.55, stability),
            PhononChannel("out-of-plane", "z", omega * 0.8, lam * 0.45, stability),
        ),
        phase_ordering_ceiling_k=phase,
        synthesis_score=practical,
        defect_robustness=practical,
        substrate_robustness=practical,
    )


def test_pairing_proxy_is_positive_and_strengthens_with_lambda():
    weak = candidate("weak", lam=0.5)
    strong = candidate("strong", lam=1.2)
    assert strong.pairing_tc_k() > weak.pairing_tc_k() > 0.0


def test_phase_ceiling_limits_usable_tc_without_claiming_bkt():
    c = candidate(phase=5.0)
    assert c.pairing_tc_k() > 5.0
    assert c.usable_tc_k() == pytest.approx(5.0)


def test_uncertainty_envelope_orders_quantiles():
    env = tc_uncertainty_envelope(candidate())
    assert env.samples == 27
    assert env.minimum_k <= env.q05_k <= env.median_k <= env.q95_k <= env.maximum_k


def test_negative_stability_margin_is_rejected():
    report = audit_candidate(candidate(stability=-0.01))
    assert report.status == "REJECT"
    assert any("negative" in finding for finding in report.findings)


def test_adaptive_filter_records_stage_counts():
    good = candidate("good")
    unstable = candidate("unstable", stability=-0.2)
    selected, trace = adaptive_filter([good, unstable], min_oak_score=0.0)
    assert trace.input_count == 2
    assert trace.structurally_stable_count == 1
    assert [row.candidate.name for row in selected] == ["good"]


def test_pareto_front_keeps_tradeoff_candidates():
    high_tc_low_practical = candidate("hot", lam=1.4, practical=0.2)
    lower_tc_practical = candidate("practical", lam=0.8, practical=0.95)
    names = {c.name for c in pareto_front([high_tc_low_practical, lower_tc_practical])}
    assert names == {"hot", "practical"}


def test_counterfactual_comparison_requires_explicit_second_candidate():
    reference = candidate("bonded", lam=1.2)
    intervention = candidate("ablated", lam=0.6)
    result = compare_counterfactuals(reference, intervention, intervention_label="remove interlayer bond in independent calculation")
    assert result["delta_tc_k"] > 0


def test_borophene_seed_marks_68k_as_theory_not_measurement():
    claims = borophene_2026_seed()
    tc = next(claim for claim in claims if claim.value == 68.0)
    assert tc.evidence_status == "THEORETICAL_PREDICTION"
    assert "experimental" in tc.caveat.lower()
