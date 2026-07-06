"""Patent thesis seed model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PatentThesisSeed:
    patent_id: str
    title: str
    status: str = "unknown"
    domains: tuple[str, ...] = field(default_factory=tuple)
    core_problem: str = ""
    core_solution: str = ""
    independent_claims: tuple[str, ...] = field(default_factory=tuple)
    dependent_claims: tuple[str, ...] = field(default_factory=tuple)
    prototype_targets: tuple[str, ...] = field(default_factory=tuple)
    business_targets: tuple[str, ...] = field(default_factory=tuple)
    oak_risks: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if not self.patent_id:
            raise ValueError("patent_id is required")
        if not self.title:
            raise ValueError("title is required")
        if not self.independent_claims:
            raise ValueError("at least one independent claim summary is required")

    def to_dict(self) -> dict:
        self.validate()
        return {
            "patent_id": self.patent_id,
            "title": self.title,
            "status": self.status,
            "domains": list(self.domains),
            "core_problem": self.core_problem,
            "core_solution": self.core_solution,
            "independent_claims": list(self.independent_claims),
            "dependent_claims": list(self.dependent_claims),
            "prototype_targets": list(self.prototype_targets),
            "business_targets": list(self.business_targets),
            "oak_risks": list(self.oak_risks),
        }


def example_seed() -> PatentThesisSeed:
    return PatentThesisSeed(
        patent_id="EXAMPLE-PATENT-T",
        title="Example technical document thesis seed",
        status="unknown",
        domains=("software", "analysis"),
        core_problem="Convert a technical document into a structured thesis plan.",
        core_solution="Extract claim summaries, risks, prototype targets, and product hypotheses.",
        independent_claims=("A system for converting a technical record into a structured review package.",),
        dependent_claims=("The package includes prototype, benchmark, and product hypothesis sections.",),
        prototype_targets=("parser", "report", "demo"),
        business_targets=("research assistant", "portfolio scanner"),
        oak_risks=("status unknown", "requires expert review", "prototype not validated"),
    )
