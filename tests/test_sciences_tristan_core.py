from sage_tristan.sciences_tristan import AITOAK, BayesTristanEngine, ScienceCard


def _card(**overrides):
    data = {
        "id": "ST-H-9999",
        "name": "Test card",
        "kind": "hypothesis",
        "branch": "ffwt_hac_cvcd",
        "statement": "A candidate multi-scale signal pipeline may improve anomaly detection.",
        "status_oak": "Omega_2",
        "bayes_tristan": {
            "true": 0.55,
            "useful": 0.90,
            "fertile": 0.95,
            "testable": 0.90,
            "safe": 0.95,
            "compressible": 0.80,
            "novel": 0.75,
            "valuable": 0.85,
        },
        "tests": [
            {
                "name": "baseline_comparison",
                "metric": "AUROC",
                "success_condition": "beats FFT baseline",
                "falsifier": "no improvement after ablation",
                "cost": "low",
            }
        ],
        "next_actions": ["Run the first benchmark."],
    }
    data.update(overrides)
    return ScienceCard.from_mapping(data)


def test_science_card_priority_is_normalized():
    card = _card()
    assert 0.0 <= card.priority() <= 1.0
    assert card.status_oak.value == "Omega_2"


def test_bayes_tristan_engine_ranks_cards():
    strong = _card(id="ST-H-1000", name="strong")
    weak = _card(
        id="ST-H-1001",
        name="weak",
        bayes_tristan={
            "true": 0.20,
            "useful": 0.20,
            "fertile": 0.20,
            "testable": 0.20,
            "safe": 0.60,
            "compressible": 0.20,
            "novel": 0.20,
            "valuable": 0.20,
        },
    )
    engine = BayesTristanEngine([weak, strong])
    assert engine.top(1)[0].id == "ST-H-1000"
    assert engine.portfolio_report()["total_cards"] == 2


def test_ait_oak_produces_review_with_falsifier():
    card = _card()
    review = AITOAK().review(card)
    assert review.card_id == card.id
    assert review.suggested_tests
    assert review.falsifiers
    assert "Candidate" in review.safe_claim
