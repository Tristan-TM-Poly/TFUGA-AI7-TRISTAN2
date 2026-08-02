from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Iterable, Mapping, Sequence
import json
import math

from .core import EpistemicStatus, InteractionSpec, LagrangianModel, ModelRegistry, ValidationIssue
from .physics import TwoBodyEvent


@dataclass(frozen=True)
class OAKCheck:
    id: str
    passed: bool
    gate: str
    message: str
    metric: float | str | bool | None = None
    threshold: float | str | bool | None = None
    severity: str = "error"
    evidence: tuple[str, ...] = ()


@dataclass
class OAKReport:
    model_id: str
    status: str
    checks: list[OAKCheck] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    falsifiers: list[str] = field(default_factory=list)
    residuals: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return all(check.passed or check.severity != "error" for check in self.checks)

    @property
    def score(self) -> float:
        weighted_total = 0.0
        weighted_passed = 0.0
        for check in self.checks:
            weight = 1.0 if check.severity == "error" else 0.25
            weighted_total += weight
            if check.passed:
                weighted_passed += weight
        return weighted_passed / weighted_total if weighted_total else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "status": self.status,
            "passed": self.passed,
            "score": self.score,
            "checks": [asdict(check) for check in self.checks],
            "assumptions": self.assumptions,
            "falsifiers": self.falsifiers,
            "residuals": self.residuals,
            "metadata": self.metadata,
        }

    def to_markdown(self) -> str:
        lines = [f"# OAK report — {self.model_id}", "", f"**Status:** `{self.status}`", f"**Verdict:** `{'PASS' if self.passed else 'FAIL'}`", f"**Score:** `{self.score:.4f}`", "", "## Checks", ""]
        lines.append("| Gate | Check | Result | Metric | Threshold | Message |")
        lines.append("|---|---|---:|---:|---:|---|")
        for check in self.checks:
            lines.append(f"| {check.gate} | `{check.id}` | {'PASS' if check.passed else 'FAIL'} | {check.metric} | {check.threshold} | {check.message} |")
        if self.assumptions:
            lines.extend(["", "## Assumptions", "", *[f"- {item}" for item in self.assumptions]])
        if self.falsifiers:
            lines.extend(["", "## Falsifiers", "", *[f"- {item}" for item in self.falsifiers]])
        if self.residuals:
            lines.extend(["", "## Residuals", "", "```json", json.dumps(self.residuals, indent=2, sort_keys=True), "```"])
        return "\n".join(lines) + "\n"


class OAKGate:
    def __init__(self, *, tolerance: float = 1e-9) -> None:
        self.tolerance = tolerance

    def audit_registry(self, registry: ModelRegistry, model_id: str = "omega-pct-registry") -> OAKReport:
        issues = registry.validate()
        checks = [
            OAKCheck(
                id=f"registry::{index}::{issue.code}", passed=issue.severity != "error", gate="ontology",
                message=issue.message, metric=issue.path, severity=issue.severity,
            )
            for index, issue in enumerate(issues)
        ]
        if not checks:
            checks.append(OAKCheck("registry.valid", True, "ontology", "All registry references and local constraints are valid."))
        for interaction in registry.interactions.values():
            balance = registry.interaction_balance(interaction.id)
            for key in interaction.expected_conservation:
                residual = balance.get(key, 0.0)
                checks.append(OAKCheck(
                    f"conservation::{interaction.id}::{key}", abs(residual) <= self.tolerance, "conservation",
                    f"Additive balance for {key}.", residual, self.tolerance,
                ))
        return OAKReport(model_id=model_id, status="established+effective+exploratory registry", checks=checks)

    def audit_event(self, event: TwoBodyEvent, model_id: str = "two-body-event") -> OAKReport:
        residual = event.conservation_residual()
        shell = event.on_shell_residuals()
        invariants = event.mandelstam()
        checks = [
            OAKCheck("event.energy_conservation", abs(residual.e) <= self.tolerance, "kinematics", "Energy conservation residual.", abs(residual.e), self.tolerance),
            OAKCheck("event.momentum_conservation", max(abs(residual.px), abs(residual.py), abs(residual.pz)) <= self.tolerance, "kinematics", "Three-momentum conservation residual.", max(abs(residual.px), abs(residual.py), abs(residual.pz)), self.tolerance),
            OAKCheck("event.on_shell", max(abs(value) for value in shell) <= 100 * self.tolerance, "kinematics", "External legs remain on shell within floating-point tolerance.", max(abs(value) for value in shell), 100 * self.tolerance),
            OAKCheck("event.mandelstam_sum", abs(invariants["s"] + invariants["t"] + invariants["u"] - sum(float(event.metadata.get(f"m{i}", 0.0)) ** 2 for i in range(1, 5))) <= 1000 * self.tolerance, "kinematics", "Mandelstam identity for 2→2 scattering.", abs(invariants["s"] + invariants["t"] + invariants["u"] - sum(float(event.metadata.get(f"m{i}", 0.0)) ** 2 for i in range(1, 5))), 1000 * self.tolerance),
        ]
        return OAKReport(
            model_id=model_id,
            status=str(event.metadata.get("model", "simulation")),
            checks=checks,
            assumptions=["Special-relativistic two-body center-of-mass kinematics.", "No detector smearing unless explicitly recorded."],
            falsifiers=["Non-zero conservation residual beyond numerical tolerance.", "External-leg mass-shell violation beyond tolerance."],
            residuals={"energy": residual.e, "px": residual.px, "py": residual.py, "pz": residual.pz, "max_shell": max(abs(value) for value in shell)},
            metadata={"mandelstam": invariants, **event.metadata},
        )

    def audit_lagrangian(self, model: LagrangianModel, target_mass_dimension: int = 4) -> OAKReport:
        from .core import DimensionVector
        issues = model.validate_dimensions(DimensionVector(mass=target_mass_dimension))
        checks = [OAKCheck(f"lagrangian::{index}", issue.severity != "error", "mathematics", issue.message, issue.path, severity=issue.severity) for index, issue in enumerate(issues)]
        if not checks:
            checks.append(OAKCheck("lagrangian.dimensions", True, "mathematics", f"All terms have target mass dimension {target_mass_dimension}."))
        checks.append(OAKCheck("lagrangian.cutoff", model.cutoff_gev is None or model.cutoff_gev > 0, "domain", "EFT cutoff is absent or positive.", model.cutoff_gev, ">0 or null"))
        return OAKReport(model.id, model.status.value, checks=checks, assumptions=["Natural units may be used by the symbolic model."], falsifiers=["A term has inconsistent dimensions.", "The declared domain exceeds its EFT cutoff without matching."])


def combine_reports(model_id: str, reports: Sequence[OAKReport]) -> OAKReport:
    combined = OAKReport(model_id, "combined")
    for report in reports:
        combined.checks.extend(report.checks)
        combined.assumptions.extend(item for item in report.assumptions if item not in combined.assumptions)
        combined.falsifiers.extend(item for item in report.falsifiers if item not in combined.falsifiers)
        combined.residuals.update({f"{report.model_id}:{key}": value for key, value in report.residuals.items()})
    combined.metadata["components"] = [report.model_id for report in reports]
    return combined
