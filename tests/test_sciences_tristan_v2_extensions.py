from sage_tristan.sciences_tristan.science_card import ScienceCard
from sage_tristan.sciences_tristan.v2_extensions import (
    CanonScore,
    ClaimTransmuter,
    MemoryMinusEngine,
    OAKCourt,
    OAKDecision,
    OAKStatus,
    PromotionGates,
    Residue,
    ResidueMiner,
    ScienceOrganism,
    portfolio_dashboard,
)


def make_card(**overrides):
    data = {
        "id": "ST-H-2000",
        "name": "Fractal conductor claim",
        "kind": "hypothesis",
        "branch": "physics",
        "statement": "Fractal conductor implies superconductivity.",
        "status_oak": "Omega_2",
        "bayes_tristan": {
            "true": 0.20,
            "useful": 0.85,
            "fertile": 0.95,
            "testable": 0.70,
            "safe": 0.65,
            "compressible": 0.75,
            "novel": 0.80,
            "valuable": 0.75,
        },
        "assumptions": ["Graph geometry affects response."],
        "predictions": ["A measurable signature should exist."],
        "baselines": ["regular lattice", "random graph"],
        "tests": [
            {
                "name": "spectral_response",
                "metric": "frequency-response peak separation",
                "success_condition": "distinguishable from baselines",
                "falsifier": "no robust difference versus baselines",
                "cost": "low",
            }
        ],
        "positive_memory": [],
        "negative_memory": ["No material claim without measurement."],
        "residues": ["Material interpretation untested."],
        "links": [],
        "next_actions": ["Build a prototype simulation."],
    }
    data.update(overrides)
    return ScienceCard.from_mapping(data)


def test_high_fertility_is_not_high_canon():
    card = make_card()
    assert card.bayes_tristan.fertile > card.bayes_tristan.true
    assert CanonScore.from_card(card).value() < card.priority()


def test_claim_transmuter_reduces_material_overclaim():
    result = ClaimTransmuter().transmute("Fractal conductor implies superconductivity.", branch="physics")
    assert "résistance nulle" in result.safe_claim
    assert "signature spectrale" in result.testable_claim
    assert result.triggered_rules


def test_memory_minus_detects_physics_overclaim():
    card = make_card()
    triggers = MemoryMinusEngine().detect(card)
    assert triggers
    assert triggers[0]["name"] == "no_material_claim_without_measurement"


def test_promotion_gate_blocks_missing_later_artifacts():
    card = make_card()
    result = PromotionGates().check(card, OAKStatus.OMEGA_3)
    assert result.passed is True
    blocked = PromotionGates().check(card, OAKStatus.OMEGA_4)
    assert blocked.passed is False
    assert "promotion must move one OAK gate at a time" in blocked.blockers


def test_oak_court_transmutes_risky_claim():
    card = make_card()
    review = OAKCourt().review(card)
    assert review.verdict["decision"] == OAKDecision.TRANSMUTE.value
    assert review.memory_minus["triggered_anti_rules"]
    assert review.verdict["canon_score"] < 0.75


def test_residue_miner_generates_child_hypotheses():
    residue = Residue(
        source="FFWT-HAC-CVCD-v0",
        gap="model fails on high-noise chirp signals",
        possible_causes=["missing phase feature", "wrong scale window"],
        fertility_score=0.82,
    )
    children = ResidueMiner().mine(residue)
    assert len(children) == 2
    assert "missing phase feature" in children[0]["claim"]


def test_science_organism_wraps_card_with_immune_system():
    organism = ScienceOrganism.from_card(make_card())
    data = organism.as_dict()
    assert data["genome"]["statement"]
    assert data["immune_system"]["memory_negative"]
    assert data["phenotype"]["safe_claim"]


def test_portfolio_dashboard_reports_risk_and_oak_status():
    card = make_card()
    dashboard = portfolio_dashboard([card])
    assert dashboard["total_cards"] == 1
    assert dashboard["by_branch"]["physics"] == 1
    assert dashboard["high_risk_claims"]
