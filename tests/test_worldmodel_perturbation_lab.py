from tools.worldmodel_perturbation_lab import (
    EntropyBand,
    InsightStatus,
    RealityAnchor,
    choose_entropy_band,
    perturb_worldmodel,
)


def test_low_divergence_is_low_entropy():
    assert choose_entropy_band(0.1, has_anchor=False) == EntropyBand.LOW


def test_medium_divergence_with_anchor_is_fertile():
    assert choose_entropy_band(0.5, has_anchor=True) == EntropyBand.MEDIUM


def test_high_stakes_forces_quarantine():
    assert choose_entropy_band(0.2, has_anchor=True, high_stakes=True) == EntropyBand.QUARANTINE


def test_unanchored_output_is_vision():
    packet = perturb_worldmodel(
        seed="new theory",
        candidate_insight="A strange metaphor about world models",
        divergence=0.4,
        anchor=None,
    )
    assert packet.status == InsightStatus.VISION
    assert packet.safe_next_action == "Add RealityAnchor before prototype or external action."


def test_anchored_medium_entropy_output_becomes_prototype():
    anchor = RealityAnchor(
        definition="A controlled perturbation of conceptual attractors.",
        example="Generate three hypotheses then require tests.",
        test="Check whether each hypothesis has a falsification path.",
        limitation="Does not prove truth.",
        risk="May create attractive but false stories.",
        residue="Needs benchmark.",
    )
    packet = perturb_worldmodel(
        seed="world model lab",
        candidate_insight="Use entropy to generate but OAK to reconsolidate",
        divergence=0.5,
        anchor=anchor,
    )
    assert packet.entropy_band == EntropyBand.MEDIUM
    assert packet.status == InsightStatus.PROTOTYPE


def test_substance_boundary_violation_quarantines():
    packet = perturb_worldmodel(
        seed="bad request",
        candidate_insight="dose and extraction details",
        divergence=0.5,
    )
    assert packet.status == InsightStatus.QUARANTINED
    assert "substance_use_boundary_violation" in packet.oak_warnings
