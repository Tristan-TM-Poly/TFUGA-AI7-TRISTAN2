from sage_tristan.sciences_tristan.hyper_best import (
    BenchmarkArenaForge,
    ImpactRouter,
    PaperForge,
    PrototypeForge,
    TheoryReactor,
    autonomous_research_loop,
)
from sage_tristan.sciences_tristan.science_card import ScienceCard


def make_card(**overrides):
    data = {
        "id": "ST-H-4000",
        "name": "FFWT HAC CVCD benchmark",
        "kind": "hypothesis",
        "branch": "ffwt_hac_cvcd",
        "statement": "Candidate multi-scale features may improve structured signal classification.",
        "status_oak": "Omega_2",
        "bayes_tristan": {
            "true": 0.50,
            "useful": 0.90,
            "fertile": 0.95,
            "testable": 0.90,
            "safe": 0.95,
            "compressible": 0.80,
            "novel": 0.75,
            "valuable": 0.85,
        },
        "assumptions": ["The data contains multi-scale structure."],
        "predictions": ["A baseline comparison can detect value or failure."],
        "baselines": ["FFT", "classical_wavelets", "PCA"],
        "tests": [
            {
                "name": "baseline_comparison",
                "metric": "F1 and AUROC",
                "success_condition": "beats at least one fair baseline",
                "falsifier": "no gain after ablation",
                "cost": "low",
            }
        ],
        "positive_memory": [],
        "negative_memory": ["Do not treat feature novelty as evidence."],
        "residues": [],
        "links": [],
        "next_actions": ["Build benchmark scaffold."],
    }
    data.update(overrides)
    return ScienceCard.from_mapping(data)


def test_prototype_forge_creates_contract_with_limits():
    card = make_card()
    contract = PrototypeForge().plan(card)
    assert contract.files
    assert contract.minimal_functions
    assert "universal validity" in contract.does_not_prove
    assert "baseline" in contract.required_for_promotion


def test_benchmark_arena_includes_baselines_metrics_and_ablations():
    card = make_card()
    prototype = PrototypeForge().plan(card)
    arena = BenchmarkArenaForge().build(card, prototype)
    assert "FFT" in arena.baselines
    assert arena.metrics
    assert "baseline_only" in arena.ablations
    assert "beats_baseline" in arena.promote_if


def test_paper_forge_seed_is_not_claim_of_truth():
    card = make_card()
    prototype = PrototypeForge().plan(card)
    arena = BenchmarkArenaForge().build(card, prototype)
    paper = PaperForge().draft_seed(card, arena)
    assert paper.title.endswith("OAK-Grounded Study")
    assert any("not canon" in slot for slot in paper.limitation_slots)


def test_impact_router_routes_low_status_to_next_test():
    card = make_card(status_oak="Omega_2")
    route = ImpactRouter().route(card)
    assert "prototype_plan" in route.outputs
    assert "next test" in route.reason


def test_theory_reactor_generates_research_objects():
    card = make_card()
    reaction = TheoryReactor().react(card)
    assert "organism" in reaction
    assert "oak_court" in reaction
    assert "prototype_contract" in reaction
    assert "benchmark_arena" in reaction
    assert "paper_seed" in reaction
    assert "impact_route" in reaction
    assert reaction["predicted_residue_children"]


def test_autonomous_research_loop_generates_next_verifiable_tests_not_truth():
    result = autonomous_research_loop([make_card()])
    assert result["total_cards"] == 1
    assert "auto-truth" in result["law"]
    assert result["reactions"][0]["prototype_contract"]
