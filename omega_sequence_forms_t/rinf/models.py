"""Typed R∞ models for the Ω-SUITE-FORM-T∞ research operating system.

The R∞ layer is intentionally separate from the compact R0.1 public API.  It
models a potentially unbounded research campaign while preserving finite,
auditable execution receipts.  No finite-prefix candidate is promoted to a
global identity without an explicit proof artifact.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum, IntEnum
from fractions import Fraction
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, Sequence


class EvidenceLevel(IntEnum):
    """OAK evidence ladder shared by every R∞ detector and compiler."""

    VISUAL_PATTERN = 0
    OBSERVED_FIT = 1
    HELD_OUT_PREDICTION = 2
    ADVERSARIAL_VALIDATION = 3
    SYMBOLIC_IDENTITY = 4
    MATHEMATICAL_PROOF = 5
    FORMAL_PROOF = 6


class Maturity(str, Enum):
    SPECIFICATION = "specification"
    PROTOTYPE = "prototype"
    TESTED_FIXTURE = "tested_fixture"
    RESEARCH_TOOL = "research_tool"
    CERTIFIED_COMPONENT = "certified_component"


class FamilyClass(str, Enum):
    EXPLICIT = "explicit"
    RECURRENT = "recurrent"
    GENERATING = "generating"
    OPERATOR = "operator"
    SPECTRAL = "spectral"
    INTEGRAL = "integral"
    ARITHMETIC = "arithmetic"
    AUTOMATIC = "automatic"
    ASYMPTOTIC = "asymptotic"
    STOCHASTIC = "stochastic"
    MULTIVARIATE = "multivariate"
    ALGORITHMIC = "algorithmic"


class TransformationClass(str, Enum):
    INDEX = "index"
    VALUE = "value"
    DIFFERENCE = "difference"
    CONVOLUTION = "convolution"
    GENERATING = "generating"
    INTEGRAL = "integral"
    ARITHMETIC = "arithmetic"
    SPECTRAL = "spectral"
    SYMBOLIC = "symbolic"
    PROOF = "proof"
    RESIDUAL = "residual"
    COMPILATION = "compilation"


@dataclass(frozen=True, order=True)
class CellAddress:
    """A stable five-axis address in the logical R∞ research space."""

    family: int
    transformation: int
    validator: int
    regime: int
    domain: int

    def __post_init__(self) -> None:
        for name, value in self.as_mapping().items():
            if value < 0:
                raise ValueError(f"{name} must be non-negative")

    def as_mapping(self) -> dict[str, int]:
        return {
            "family": self.family,
            "transformation": self.transformation,
            "validator": self.validator,
            "regime": self.regime,
            "domain": self.domain,
        }

    def render(self) -> str:
        return (
            f"f{self.family:03d}.t{self.transformation:03d}."
            f"v{self.validator:03d}.r{self.regime:02d}.d{self.domain:02d}"
        )

    @classmethod
    def parse(cls, text: str) -> "CellAddress":
        try:
            parts = text.split(".")
            if len(parts) != 5:
                raise ValueError
            prefixes = ("f", "t", "v", "r", "d")
            values = []
            for part, prefix in zip(parts, prefixes):
                if not part.startswith(prefix):
                    raise ValueError
                values.append(int(part[len(prefix):]))
            return cls(*values)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid cell address: {text!r}") from exc

    def digest(self) -> str:
        return sha256(self.render().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AnalyticFamily:
    family_id: str
    index: int
    label: str
    family_class: FamilyClass
    representation: str
    detector_ids: tuple[str, ...]
    compiler_ids: tuple[str, ...]
    invariants: tuple[str, ...]
    proof_obligations: tuple[str, ...]
    risk_tags: tuple[str, ...]
    maturity: Maturity = Maturity.SPECIFICATION
    exact_capable: bool = False
    multivariate_capable: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.family_id or not self.label:
            raise ValueError("family_id and label are required")
        if self.index < 0:
            raise ValueError("family index must be non-negative")
        if not self.representation:
            raise ValueError("representation must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["family_class"] = self.family_class.value
        payload["maturity"] = self.maturity.value
        return payload


@dataclass(frozen=True)
class TransformationSpec:
    transformation_id: str
    index: int
    label: str
    transformation_class: TransformationClass
    source_classes: tuple[FamilyClass, ...]
    target_classes: tuple[FamilyClass, ...]
    exact_when: tuple[str, ...]
    proof_obligations: tuple[str, ...]
    risk_tags: tuple[str, ...]
    invertible: bool = False
    lossy: bool = False
    maturity: Maturity = Maturity.SPECIFICATION

    def __post_init__(self) -> None:
        if not self.transformation_id or not self.label:
            raise ValueError("transformation_id and label are required")
        if self.index < 0:
            raise ValueError("transformation index must be non-negative")
        if self.lossy and self.invertible:
            raise ValueError("a lossy transformation cannot be globally invertible")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["transformation_class"] = self.transformation_class.value
        payload["source_classes"] = [item.value for item in self.source_classes]
        payload["target_classes"] = [item.value for item in self.target_classes]
        payload["maturity"] = self.maturity.value
        return payload


@dataclass(frozen=True)
class AntiPatternSpec:
    antipattern_id: str
    index: int
    name: str
    context: str
    detector: str
    countercheck: str
    severity: int
    blocks_promotion_above: EvidenceLevel
    explanation: str

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("antipattern index must be non-negative")
        if not 1 <= self.severity <= 5:
            raise ValueError("severity must lie in [1, 5]")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["blocks_promotion_above"] = int(self.blocks_promotion_above)
        payload["blocks_promotion_label"] = self.blocks_promotion_above.name
        return payload


@dataclass(frozen=True)
class CampaignBudget:
    """Finite execution resources without a permanent conceptual cell cap."""

    wall_time_seconds: float | None = None
    memory_megabytes: int | None = None
    storage_megabytes: int | None = None
    compute_units: int | None = None
    materialized_cell_cap: int | None = None
    minimum_marginal_value: float = 0.0
    minimum_value_cost_ratio: float = 0.0

    def __post_init__(self) -> None:
        numeric = {
            "wall_time_seconds": self.wall_time_seconds,
            "memory_megabytes": self.memory_megabytes,
            "storage_megabytes": self.storage_megabytes,
            "compute_units": self.compute_units,
            "materialized_cell_cap": self.materialized_cell_cap,
        }
        for name, value in numeric.items():
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive when supplied")
        if self.minimum_marginal_value < 0 or self.minimum_value_cost_ratio < 0:
            raise ValueError("marginal thresholds must be non-negative")

    @property
    def has_permanent_cell_cap(self) -> bool:
        return False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["has_permanent_cell_cap"] = False
        return payload


@dataclass(frozen=True)
class EvidenceArtifact:
    artifact_id: str
    kind: str
    digest: str
    statement: str
    provenance: str
    assumptions: tuple[str, ...] = ()
    reproducible: bool = False

    @classmethod
    def from_payload(
        cls,
        *,
        artifact_id: str,
        kind: str,
        statement: str,
        provenance: str,
        payload: Mapping[str, Any],
        assumptions: Sequence[str] = (),
        reproducible: bool = False,
    ) -> "EvidenceArtifact":
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return cls(
            artifact_id=artifact_id,
            kind=kind,
            digest=sha256(canonical.encode("utf-8")).hexdigest(),
            statement=statement,
            provenance=provenance,
            assumptions=tuple(assumptions),
            reproducible=reproducible,
        )


@dataclass
class FormCandidateRInf:
    candidate_id: str
    family_id: str
    expression: str
    parameters: dict[str, Any]
    assumptions: tuple[str, ...]
    evidence_level: EvidenceLevel
    observed_terms: int
    observed_matches: int
    held_out_terms: int = 0
    held_out_matches: int = 0
    adversarial_checks: int = 0
    adversarial_passes: int = 0
    complexity_bits: int = 0
    residual_norm: Fraction | float = Fraction(0)
    proof_obligations: list[str] = field(default_factory=list)
    risk_tags: list[str] = field(default_factory=list)
    evidence: list[EvidenceArtifact] = field(default_factory=list)
    global_identity_proved: bool = False
    formal_proof_completed: bool = False

    def __post_init__(self) -> None:
        counts = (
            self.observed_terms,
            self.observed_matches,
            self.held_out_terms,
            self.held_out_matches,
            self.adversarial_checks,
            self.adversarial_passes,
        )
        if any(value < 0 for value in counts):
            raise ValueError("validation counts must be non-negative")
        if self.observed_matches > self.observed_terms:
            raise ValueError("observed matches exceed observed terms")
        if self.held_out_matches > self.held_out_terms:
            raise ValueError("held-out matches exceed held-out terms")
        if self.adversarial_passes > self.adversarial_checks:
            raise ValueError("adversarial passes exceed checks")
        if self.formal_proof_completed and not self.global_identity_proved:
            raise ValueError("formal proof completion implies a global identity proof")
        if self.global_identity_proved and self.evidence_level < EvidenceLevel.MATHEMATICAL_PROOF:
            raise ValueError("global identity proof requires OAK-5 or above")

    @property
    def observed_fit(self) -> bool:
        return self.observed_terms > 0 and self.observed_terms == self.observed_matches

    @property
    def held_out_prediction(self) -> bool:
        return self.held_out_terms > 0 and self.held_out_terms == self.held_out_matches

    @property
    def adversarial_validation(self) -> bool:
        return self.adversarial_checks > 0 and self.adversarial_checks == self.adversarial_passes

    def canonical_payload(self) -> dict[str, Any]:
        payload = {
            "candidate_id": self.candidate_id,
            "family_id": self.family_id,
            "expression": self.expression,
            "parameters": _json_safe(self.parameters),
            "assumptions": list(self.assumptions),
            "evidence_level": int(self.evidence_level),
            "evidence_label": self.evidence_level.name,
            "observed_terms": self.observed_terms,
            "observed_matches": self.observed_matches,
            "held_out_terms": self.held_out_terms,
            "held_out_matches": self.held_out_matches,
            "adversarial_checks": self.adversarial_checks,
            "adversarial_passes": self.adversarial_passes,
            "complexity_bits": self.complexity_bits,
            "residual_norm": _json_safe(self.residual_norm),
            "proof_obligations": list(self.proof_obligations),
            "risk_tags": list(self.risk_tags),
            "evidence": [asdict(item) for item in self.evidence],
            "global_identity_proved": self.global_identity_proved,
            "formal_proof_completed": self.formal_proof_completed,
        }
        return payload

    def digest(self) -> str:
        canonical = json.dumps(self.canonical_payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CampaignCellResult:
    address: CellAddress
    status: str
    marginal_value: float
    estimated_cost: float
    candidate_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    residue_ids: tuple[str, ...] = ()
    failure_codes: tuple[str, ...] = ()

    @property
    def value_cost_ratio(self) -> float:
        if self.estimated_cost <= 0:
            return float("inf") if self.marginal_value > 0 else 0.0
        return self.marginal_value / self.estimated_cost

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["address"] = self.address.render()
        payload["value_cost_ratio"] = self.value_cost_ratio
        return payload


@dataclass
class CampaignReceipt:
    campaign_id: str
    catalog_digest: str
    seed: int
    budget: CampaignBudget
    selected_cells: int
    executed_cells: int
    accepted_candidates: int
    rejected_candidates: int
    counterexamples: int
    results: list[CampaignCellResult]
    stop_reason: str
    permanent_total_cap: None = None
    global_identity_proved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "omega-sequence-forms-rinf-campaign/1",
            "campaign_id": self.campaign_id,
            "catalog_digest": self.catalog_digest,
            "seed": self.seed,
            "budget": self.budget.to_dict(),
            "selected_cells": self.selected_cells,
            "executed_cells": self.executed_cells,
            "accepted_candidates": self.accepted_candidates,
            "rejected_candidates": self.rejected_candidates,
            "counterexamples": self.counterexamples,
            "results": [item.to_dict() for item in self.results],
            "stop_reason": self.stop_reason,
            "permanent_total_cap": None,
            "global_identity_proved": self.global_identity_proved,
        }

    def digest(self) -> str:
        canonical = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()


def canonical_digest(items: Iterable[Mapping[str, Any]]) -> str:
    hasher = sha256()
    for item in items:
        encoded = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        hasher.update(encoded.encode("utf-8"))
        hasher.update(b"\n")
    return hasher.hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Fraction):
        return value.numerator if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    return value
