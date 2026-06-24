"""Ω-ST++++ hyper-best research reactor primitives.

The goal of this module is not to automate truth. It automates the generation
of the next verifiable research objects: child hypotheses, prototype contracts,
benchmark arenas, residue nodes, paper seeds and impact routes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .science_card import ScienceCard
from .v2_extensions import OAKCourt, Residue, ResidueMiner, ScienceOrganism


@dataclass
class PrototypeContract:
    card_id: str
    prototype_name: str
    files: list[str]
    minimal_functions: list[str]
    proves: list[str]
    does_not_prove: list[str]
    required_for_promotion: list[str]
    expected_outputs: list[str]

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class BenchmarkArena:
    hypothesis_id: str
    prototype_name: str
    baselines: list[str]
    metrics: list[str]
    ablations: list[str]
    promote_if: list[str]
    demote_if: list[str]

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class PaperSeed:
    title: str
    abstract_slots: list[str]
    contribution_slots: list[str]
    method_slots: list[str]
    experiment_slots: list[str]
    limitation_slots: list[str]
    reproducibility_slots: list[str]

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class ImpactRoute:
    card_id: str
    status_oak: str
    outputs: list[str]
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class PrototypeForge:
    """Generate conservative prototype contracts from cards."""

    def plan(self, card: ScienceCard) -> PrototypeContract:
        slug = card.name.lower().replace(" ", "_").replace("/", "_")[:48]
        branch = card.branch
        if branch == "ffwt_hac_cvcd":
            files = [
                "prototypes/ffwt_hac_cvcd/synthetic_data.py",
                "prototypes/ffwt_hac_cvcd/baselines.py",
                "prototypes/ffwt_hac_cvcd/features.py",
                "prototypes/ffwt_hac_cvcd/ablation.py",
                "prototypes/ffwt_hac_cvcd/benchmark.py",
                "prototypes/ffwt_hac_cvcd/report.py",
            ]
            functions = [
                "generate_synthetic_multiscale_signal",
                "extract_candidate_features",
                "extract_baseline_features",
                "run_ablation",
                "export_oak_report",
            ]
        elif branch == "physics":
            files = [
                "prototypes/fractal_rlc_lab/graphs.py",
                "prototypes/fractal_rlc_lab/admittance.py",
                "prototypes/fractal_rlc_lab/spectrum.py",
                "prototypes/fractal_rlc_lab/baselines.py",
                "prototypes/fractal_rlc_lab/report.py",
            ]
            functions = [
                "generate_graph",
                "assign_components",
                "build_admittance_matrix",
                "compute_frequency_response",
                "compare_baselines",
            ]
        else:
            files = [f"prototypes/{slug}/prototype.py", f"prototypes/{slug}/report.py"]
            functions = ["run_minimal_demo", "compare_to_baseline", "export_report"]

        return PrototypeContract(
            card_id=card.id,
            prototype_name=f"{slug}_v0",
            files=files,
            minimal_functions=functions,
            proves=["a minimal operational comparison can be run"],
            does_not_prove=["universal validity", "canon status", "external reproducibility"],
            required_for_promotion=["baseline", "metric", "recorded result", "residue policy"],
            expected_outputs=["benchmark_report.json", "residue_cards.json", "oak_summary.md"],
        )


class BenchmarkArenaForge:
    """Build benchmark arena contracts."""

    DEFAULT_METRICS = ["primary_metric", "runtime", "robustness", "interpretability"]

    def build(self, card: ScienceCard, prototype: PrototypeContract) -> BenchmarkArena:
        baselines = list(card.baselines) or ["manual_baseline", "random_baseline"]
        metrics = [str(test.get("metric")) for test in card.tests if test.get("metric")] or self.DEFAULT_METRICS
        ablations = ["full_model", "minimal_model", "baseline_only"]
        if card.branch == "ffwt_hac_cvcd":
            ablations.extend(["real_only", "no_cvcd", "no_fractal_scales"])
        return BenchmarkArena(
            hypothesis_id=card.id,
            prototype_name=prototype.prototype_name,
            baselines=baselines,
            metrics=metrics,
            ablations=ablations,
            promote_if=["beats_baseline", "survives_ablation", "stores_residue"],
            demote_if=["no_measurable_gain", "unstable_result", "decorative_complexity_only"],
        )


class PaperForge:
    """Create publication seeds from cards and benchmark intent."""

    def draft_seed(self, card: ScienceCard, benchmark: BenchmarkArena | None = None) -> PaperSeed:
        return PaperSeed(
            title=f"{card.name}: OAK-Grounded Study",
            abstract_slots=[
                "problem and motivation",
                "method and operational contribution",
                "benchmark setup",
                "main result or planned result",
                "limitations and residues",
            ],
            contribution_slots=[
                "safe formulation of the claim",
                "baseline comparison",
                "explicit ablation and residue policy",
            ],
            method_slots=["ScienceCard", "OAKCourt", "PrototypeContract", "BenchmarkArena"],
            experiment_slots=(benchmark.metrics if benchmark else ["baseline comparison", "ablation"]),
            limitation_slots=["not canon until evidence and reproducibility improve"],
            reproducibility_slots=["code path", "data generation seed", "metrics", "residue log"],
        )


class ImpactRouter:
    """Route validated cards to useful fruits."""

    def route(self, card: ScienceCard) -> ImpactRoute:
        rank = card.status_oak.rank
        if rank >= 7:
            outputs = ["product_page", "course_module", "release_plan", "grant_seed"]
            reason = "usable tool or technology-level status"
        elif rank >= 5:
            outputs = ["paper_draft", "collaboration_pitch", "open_source_package", "reproduction_plan"]
            reason = "reproduced or robust result"
        elif rank >= 4:
            outputs = ["technical_report", "github_demo", "notebook", "blog_post"]
            reason = "tested prototype with preliminary evidence"
        else:
            outputs = ["prototype_plan", "benchmark_contract", "oak_review"]
            reason = "not validated yet; route toward next test"
        return ImpactRoute(card_id=card.id, status_oak=card.status_oak.value, outputs=outputs, reason=reason)


class TheoryReactor:
    """Fission a card into the next research objects."""

    def react(self, card: ScienceCard) -> dict[str, Any]:
        organism = ScienceOrganism.from_card(card)
        oak = OAKCourt().review(card)
        prototype = PrototypeForge().plan(card)
        benchmark = BenchmarkArenaForge().build(card, prototype)
        paper = PaperForge().draft_seed(card, benchmark)
        impact = ImpactRouter().route(card)
        predicted_residue = Residue(
            source=prototype.prototype_name,
            gap="unknown until benchmark is executed",
            possible_causes=["baseline stronger than expected", "missing feature", "unclear metric"],
            fertility_score=0.5,
        )
        children = ResidueMiner().mine(predicted_residue)
        return {
            "organism": organism.as_dict(),
            "oak_court": oak.as_dict(),
            "prototype_contract": prototype.as_dict(),
            "benchmark_arena": benchmark.as_dict(),
            "paper_seed": paper.as_dict(),
            "impact_route": impact.as_dict(),
            "predicted_residue_children": children,
        }


def autonomous_research_loop(cards: Iterable[ScienceCard]) -> dict[str, Any]:
    """Generate next verifiable objects for a portfolio.

    This function does not run experiments. It creates the contracts and
    review objects that make experiments possible and auditable.
    """

    reactor = TheoryReactor()
    reactions = [reactor.react(card) for card in cards]
    return {
        "total_cards": len(reactions),
        "reactions": reactions,
        "law": "autonomy != auto-truth; autonomy = generation of next verifiable tests",
    }
