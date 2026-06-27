"""ProductBench-T for Ω-GAME-T+++.

Score product plans and launch drafts. The score is a prioritization signal only;
it is not evidence of revenue, market fit, or scientific validation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from ..productizer import ProductPlan
from .launch_forge import LaunchDraft


@dataclass(slots=True)
class ProductBenchMetrics:
    value: float = 0.5
    clarity: float = 0.5
    differentiation: float = 0.5
    feasibility: float = 0.5
    testability: float = 0.5
    revenue_potential: float = 0.5
    strategic_fit: float = 0.5
    risk: float = 0.2
    scope_creep: float = 0.2
    ip_uncertainty: float = 0.2

    def __post_init__(self) -> None:
        for key, value in asdict(self).items():
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{key} must be in [0, 1], got {value!r}")

    def score(self) -> float:
        positive = (
            0.18 * self.value
            + 0.15 * self.clarity
            + 0.15 * self.differentiation
            + 0.15 * self.feasibility
            + 0.15 * self.testability
            + 0.12 * self.revenue_potential
            + 0.10 * self.strategic_fit
        )
        penalty = 0.10 * self.risk + 0.08 * self.scope_creep + 0.07 * self.ip_uncertainty
        return max(0.0, min(1.0, positive - penalty))

    def level(self) -> str:
        score = self.score()
        if score >= 0.95:
            return "plus_ultra"
        if score >= 0.90:
            return "excellent"
        if score >= 0.80:
            return "priority"
        if score >= 0.60:
            return "prototype"
        return "needs_work"


@dataclass(slots=True)
class ProductBenchResult:
    product_name: str
    target_engine: str
    metrics: ProductBenchMetrics
    notes: list[str]

    @property
    def score(self) -> float:
        return self.metrics.score()

    @property
    def level(self) -> str:
        return self.metrics.level()

    def to_dict(self) -> dict[str, object]:
        return {
            "product_name": self.product_name,
            "target_engine": self.target_engine,
            "score": self.score,
            "level": self.level,
            "metrics": asdict(self.metrics),
            "notes": list(self.notes),
        }


class ProductBench:
    """Deterministic MVP product scorer."""

    def evaluate(self, product_plan: ProductPlan, launch_draft: LaunchDraft | None = None) -> ProductBenchResult:
        metrics = self._metrics_for(product_plan, launch_draft)
        notes = self._notes_for(product_plan, launch_draft, metrics)
        return ProductBenchResult(
            product_name=product_plan.product_name,
            target_engine=product_plan.target_engine,
            metrics=metrics,
            notes=notes,
        )

    def evaluate_many(self, pairs: list[tuple[ProductPlan, LaunchDraft | None]]) -> list[ProductBenchResult]:
        return [self.evaluate(product, launch) for product, launch in pairs]

    def _metrics_for(self, product_plan: ProductPlan, launch_draft: LaunchDraft | None) -> ProductBenchMetrics:
        deliverable_count = len(product_plan.deliverables)
        value_count = len(product_plan.value_props)
        revenue_count = len(product_plan.revenue_paths)
        risk_count = len(product_plan.risks)
        blockers = len(launch_draft.blockers) if launch_draft else risk_count
        channels = len(launch_draft.channels) if launch_draft else 1
        demo_assets = len(launch_draft.demo_assets) if launch_draft else deliverable_count
        return ProductBenchMetrics(
            value=min(1.0, 0.55 + 0.08 * value_count),
            clarity=min(1.0, 0.55 + 0.05 * deliverable_count),
            differentiation=min(1.0, 0.60 + 0.04 * len(product_plan.target_engine)),
            feasibility=max(0.20, min(1.0, 0.92 - 0.04 * deliverable_count - 0.03 * risk_count)),
            testability=min(1.0, 0.55 + 0.05 * demo_assets + 0.03 * channels),
            revenue_potential=min(1.0, 0.50 + 0.08 * revenue_count),
            strategic_fit=0.90 if product_plan.target_engine in {"CircuitDungeon-T", "EnergyCivilization-T", "FounderRPG-T"} else 0.78,
            risk=min(1.0, 0.10 + 0.05 * risk_count + 0.02 * blockers),
            scope_creep=min(1.0, 0.12 + 0.04 * deliverable_count + 0.03 * len(product_plan.audience)),
            ip_uncertainty=0.35 if "review" in product_plan.ip_classification else 0.15,
        )

    def _notes_for(
        self,
        product_plan: ProductPlan,
        launch_draft: LaunchDraft | None,
        metrics: ProductBenchMetrics,
    ) -> list[str]:
        notes = [
            "ProductBench is a prioritization signal, not proof of revenue.",
            f"Product level: {metrics.level()}",
            f"Revenue paths counted: {len(product_plan.revenue_paths)}",
        ]
        if metrics.scope_creep > 0.45:
            notes.append("Scope creep is elevated; reduce deliverables or audience breadth.")
        if metrics.ip_uncertainty >= 0.35:
            notes.append("IP/public status requires review before external release.")
        if launch_draft:
            notes.append(f"Launch status: {launch_draft.status}/{launch_draft.public_release}")
        return notes


def default_product_bench() -> ProductBench:
    return ProductBench()


__all__ = ["ProductBench", "ProductBenchMetrics", "ProductBenchResult", "default_product_bench"]
