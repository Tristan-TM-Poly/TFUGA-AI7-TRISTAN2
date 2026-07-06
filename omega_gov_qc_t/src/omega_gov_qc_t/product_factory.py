"""Product factory primitives for Ω-GOV-QC-T."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

ProductMaturity = Literal["P0", "P1", "P2", "P3", "P4", "P5"]
RiskLevel = Literal["low", "medium", "high", "blocked"]


@dataclass(frozen=True)
class ProductCard:
    """A product candidate card for GovTech-Tristan."""

    product_id: str
    name: str
    mission: str
    target_users: List[str] = field(default_factory=list)
    input_data: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    risk_level: RiskLevel = "medium"
    maturity: ProductMaturity = "P0"
    oak_requirements: List[str] = field(default_factory=list)
    monetization_hypothesis: str = ""
    next_milestone: str = ""
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.product_id.strip():
            errors.append("product_id is required")
        if not self.name.strip():
            errors.append("name is required")
        if not self.mission.strip():
            errors.append("mission is required")
        if not self.target_users:
            errors.append("target_users are required")
        if not self.input_data:
            errors.append("input_data is required")
        if not self.outputs:
            errors.append("outputs are required")
        if not self.oak_requirements:
            errors.append("oak_requirements are required")
        if self.risk_level == "blocked" and self.maturity not in {"P0", "P1"}:
            errors.append("blocked products cannot mature beyond P1")
        return errors

    @property
    def is_demo_ready(self) -> bool:
        return not self.validate() and self.maturity in {"P1", "P2", "P3", "P4", "P5"}

    @property
    def requires_strict_review(self) -> bool:
        return self.risk_level in {"high", "blocked"}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "mission": self.mission,
            "target_users": list(self.target_users),
            "input_data": list(self.input_data),
            "outputs": list(self.outputs),
            "risk_level": self.risk_level,
            "maturity": self.maturity,
            "oak_requirements": list(self.oak_requirements),
            "monetization_hypothesis": self.monetization_hypothesis,
            "next_milestone": self.next_milestone,
            "is_demo_ready": self.is_demo_ready,
            "requires_strict_review": self.requires_strict_review,
            "notes": self.notes,
            "metadata": dict(self.metadata),
        }


@dataclass
class ProductFactory:
    """Registry and triage helper for GovTech product candidates."""

    products: Dict[str, ProductCard] = field(default_factory=dict)
    m_minus: List[str] = field(default_factory=list)

    def add(self, product: ProductCard) -> None:
        errors = product.validate()
        if errors:
            raise ValueError("Invalid ProductCard: " + "; ".join(errors))
        if product.product_id in self.products:
            self.m_minus.append(f"duplicate product ignored: {product.product_id}")
            raise ValueError(f"duplicate product_id: {product.product_id}")
        self.products[product.product_id] = product

    def demo_ready(self) -> List[ProductCard]:
        return [product for product in self.products.values() if product.is_demo_ready]

    def strict_review_required(self) -> List[ProductCard]:
        return [product for product in self.products.values() if product.requires_strict_review]

    def portfolio_report(self) -> Dict[str, Any]:
        by_maturity: Dict[str, int] = {}
        by_risk: Dict[str, int] = {}
        for product in self.products.values():
            by_maturity[product.maturity] = by_maturity.get(product.maturity, 0) + 1
            by_risk[product.risk_level] = by_risk.get(product.risk_level, 0) + 1
        return {
            "product_count": len(self.products),
            "demo_ready": [product.product_id for product in self.demo_ready()],
            "strict_review_required": [
                product.product_id for product in self.strict_review_required()
            ],
            "by_maturity": by_maturity,
            "by_risk": by_risk,
            "m_minus": list(self.m_minus),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "omega_gov_qc_t.product_factory.v0",
            "products": [product.to_dict() for product in self.products.values()],
            "portfolio_report": self.portfolio_report(),
        }
