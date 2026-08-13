"""R0.3 measured-evidence court for the fractal thesis factory.

R0.2 already requires explicit GO MAX/MIN vectors. R0.3 makes those vectors
proof-carrying planning inputs: every normalized field must be attached to a
raw candidate measurement, a matched baseline, units, provenance, and an
explicit normalization rule. Missing evidence is HOLD. Synthetic fixtures are
HOLD by default and can be enabled only to exercise deterministic tests.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isfinite
from typing import Any, Literal, Mapping

from omega_generative_closure_t.core import MaxMinVector

from .core import ThesisSeed
from .forest import ThesisForest, ZoomCandidate, ZoomPolicy, ZoomReceipt, zoom_thesis
from .registry_forest import RegistryZoomReceipt, compile_registry_forest

Direction = Literal["HIGHER_BETTER", "LOWER_BETTER", "DESCRIPTIVE"]
Survival = Literal["SURVIVE", "PRUNE", "HOLD_EVIDENCE"]

VECTOR_FIELDS: tuple[str, ...] = (
    "verified_value", "evidence", "reuse", "reachability", "regenerability", "fertility",
    "cost", "structural_debt", "proof_debt", "semantic_debt", "uncertainty", "irreversibility",
)


@dataclass(frozen=True)
class MetricMeasurement:
    field: str
    normalized_value: float
    candidate_value: float
    baseline_value: float
    unit: str
    direction: Direction
    source_ref: str
    baseline_ref: str
    normalization_rule: str
    synthetic_fixture: bool = False

    def validate(self) -> None:
        if self.field not in VECTOR_FIELDS:
            raise ValueError(f"unknown GO MAX/MIN field: {self.field!r}")
        if not 0.0 <= float(self.normalized_value) <= 1.0:
            raise ValueError("normalized_value must be in [0, 1]")
        if not isfinite(float(self.candidate_value)) or not isfinite(float(self.baseline_value)):
            raise ValueError("candidate_value and baseline_value must be finite")
        if self.direction not in {"HIGHER_BETTER", "LOWER_BETTER", "DESCRIPTIVE"}:
            raise ValueError(f"invalid direction: {self.direction!r}")
        if not all(x.strip() for x in (self.unit, self.source_ref, self.baseline_ref, self.normalization_rule)):
            raise ValueError("unit, source_ref, baseline_ref, and normalization_rule are required")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class EvidenceVectorReceipt:
    candidate_id: str
    measurements: tuple[MetricMeasurement, ...]
    note: str = ""

    def validate(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id must not be empty")
        seen: set[str] = set()
        for measurement in self.measurements:
            measurement.validate()
            if measurement.field in seen:
                raise ValueError(f"duplicate measurement field: {measurement.field}")
            seen.add(measurement.field)

    @property
    def measured_fields(self) -> tuple[str, ...]:
        return tuple(m.field for m in self.measurements)

    @property
    def missing_fields(self) -> tuple[str, ...]:
        present = set(self.measured_fields)
        return tuple(name for name in VECTOR_FIELDS if name not in present)

    @property
    def complete(self) -> bool:
        self.validate()
        return not self.missing_fields

    @property
    def synthetic_fixture(self) -> bool:
        return any(m.synthetic_fixture for m in self.measurements)

    @property
    def eligible_by_default(self) -> bool:
        return self.complete and not self.synthetic_fixture

    def vector(self, *, allow_synthetic: bool = False) -> MaxMinVector:
        self.validate()
        if self.missing_fields:
            raise ValueError(f"incomplete evidence vector; missing {self.missing_fields!r}")
        if self.synthetic_fixture and not allow_synthetic:
            raise ValueError("synthetic fixture is not eligible for evidence selection")
        values = {m.field: float(m.normalized_value) for m in self.measurements}
        return MaxMinVector(**values)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": "omega-thesis/evidence-vector/v0.3",
            "candidate_id": self.candidate_id,
            "measurements": [m.to_dict() for m in self.measurements],
            "measured_fields": list(self.measured_fields),
            "missing_fields": list(self.missing_fields),
            "complete": self.complete,
            "synthetic_fixture": self.synthetic_fixture,
            "eligible_by_default": self.eligible_by_default,
            "score_inference_performed": False,
            "note": self.note,
        }


@dataclass(frozen=True)
class EvidenceCourtReceipt:
    candidate_ids: tuple[str, ...]
    eligible_ids: tuple[str, ...]
    held_ids: tuple[str, ...]
    selected_ids: tuple[str, ...]
    pruned_ids: tuple[str, ...]
    survival: tuple[tuple[str, Survival], ...]
    registry_receipt: RegistryZoomReceipt
    synthetic_fixture_used: bool = False
    score_inference_performed: bool = False
    causal_superiority_claimed: bool = False
    external_truth_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "omega-thesis/evidence-court/v0.3",
            "candidate_ids": list(self.candidate_ids),
            "eligible_ids": list(self.eligible_ids),
            "held_ids": list(self.held_ids),
            "selected_ids": list(self.selected_ids),
            "pruned_ids": list(self.pruned_ids),
            "survival": [{"candidate_id": key, "outcome": value} for key, value in self.survival],
            "registry_receipt": self.registry_receipt.to_dict(),
            "synthetic_fixture_used": self.synthetic_fixture_used,
            "score_inference_performed": self.score_inference_performed,
            "causal_superiority_claimed": self.causal_superiority_claimed,
            "external_truth_claimed": self.external_truth_claimed,
        }


def compile_evidence_registry_forest(
    receipts: Mapping[str, EvidenceVectorReceipt],
    *,
    mother_seed: ThesisSeed | None = None,
    policy: ZoomPolicy = ZoomPolicy(min_power_density=0.45, max_active_children=3, max_order=1),
    allow_synthetic: bool = False,
) -> tuple[ThesisForest, EvidenceCourtReceipt]:
    """Run the canonical seed court using only complete evidence receipts."""
    vectors: dict[str, MaxMinVector] = {}
    synthetic_used = False
    for candidate_id, receipt in receipts.items():
        if candidate_id != receipt.candidate_id:
            raise ValueError(f"receipt key/id mismatch: {candidate_id!r} != {receipt.candidate_id!r}")
        receipt.validate()
        if not receipt.complete:
            continue
        if receipt.synthetic_fixture:
            synthetic_used = True
            if not allow_synthetic:
                continue
        vectors[candidate_id] = receipt.vector(allow_synthetic=allow_synthetic)

    forest, registry = compile_registry_forest(vectors, mother_seed=mother_seed, policy=policy)
    candidate_ids = tuple(registry.registry_seed_ids)
    eligible = tuple(seed_id for seed_id in candidate_ids if seed_id in vectors)
    selected = tuple(registry.selected_seed_ids)
    held = tuple(seed_id for seed_id in candidate_ids if seed_id not in vectors)
    pruned = tuple(seed_id for seed_id in eligible if seed_id not in set(selected))
    survival: list[tuple[str, Survival]] = []
    for seed_id in candidate_ids:
        if seed_id in selected:
            outcome: Survival = "SURVIVE"
        elif seed_id in eligible:
            outcome = "PRUNE"
        else:
            outcome = "HOLD_EVIDENCE"
        survival.append((seed_id, outcome))
    return forest, EvidenceCourtReceipt(
        candidate_ids=candidate_ids,
        eligible_ids=eligible,
        held_ids=held,
        selected_ids=selected,
        pruned_ids=pruned,
        survival=tuple(survival),
        registry_receipt=registry,
        synthetic_fixture_used=synthetic_used and allow_synthetic,
    )


@dataclass(frozen=True)
class ThesisCandidateSpec:
    candidate_id: str
    segment: str
    title: str
    focus: str
    research_question: str
    baselines: tuple[str, ...] = field(default_factory=tuple)
    falsifiers: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if not all(x.strip() for x in (self.candidate_id, self.segment, self.title, self.focus, self.research_question)):
            raise ValueError("candidate_id, segment, title, focus, and research_question are required")


@dataclass(frozen=True)
class MeasuredZoomReceipt:
    parent_id: str
    candidate_ids: tuple[str, ...]
    eligible_ids: tuple[str, ...]
    held_ids: tuple[str, ...]
    selected_ids: tuple[str, ...]
    pruned_ids: tuple[str, ...]
    zoom_receipt: ZoomReceipt
    synthetic_fixture_used: bool = False
    score_inference_performed: bool = False
    oak_status_promoted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "omega-thesis/measured-zoom/v0.3",
            "parent_id": self.parent_id,
            "candidate_ids": list(self.candidate_ids),
            "eligible_ids": list(self.eligible_ids),
            "held_ids": list(self.held_ids),
            "selected_ids": list(self.selected_ids),
            "pruned_ids": list(self.pruned_ids),
            "zoom_receipt": self.zoom_receipt.to_dict(),
            "synthetic_fixture_used": self.synthetic_fixture_used,
            "score_inference_performed": self.score_inference_performed,
            "oak_status_promoted": self.oak_status_promoted,
        }


def compile_measured_children(
    forest: ThesisForest,
    parent_id: str,
    specs: tuple[ThesisCandidateSpec, ...],
    receipts: Mapping[str, EvidenceVectorReceipt],
    *,
    policy: ZoomPolicy,
    allow_synthetic: bool = False,
) -> MeasuredZoomReceipt:
    """Compile one measured ZOOM layer below any existing thesis node."""
    parent = forest.get(parent_id)
    eligible_specs: list[ThesisCandidateSpec] = []
    candidates: list[ZoomCandidate] = []
    synthetic_used = False
    for spec in specs:
        spec.validate()
        receipt = receipts.get(spec.candidate_id)
        if receipt is None:
            continue
        receipt.validate()
        if not receipt.complete:
            continue
        if receipt.synthetic_fixture:
            synthetic_used = True
            if not allow_synthetic:
                continue
        vector = receipt.vector(allow_synthetic=allow_synthetic)
        eligible_specs.append(spec)
        values = {name: float(getattr(vector, name)) for name in VECTOR_FIELDS}
        candidates.append(ZoomCandidate(
            segment=spec.segment,
            title=spec.title,
            focus=spec.focus,
            research_question=spec.research_question,
            baselines=spec.baselines,
            falsifiers=spec.falsifiers,
            **values,
        ))

    children, zoom_receipt = zoom_thesis(parent, tuple(candidates), policy=policy)
    by_segment = {spec.segment.strip().upper().replace("-", "_"): spec.candidate_id for spec in eligible_specs}
    selected_ids = tuple(by_segment[node.address.path[-1]] for node in children)
    for child in children:
        forest.add(child)
    all_ids = tuple(spec.candidate_id for spec in specs)
    eligible_ids = tuple(spec.candidate_id for spec in eligible_specs)
    held_ids = tuple(candidate_id for candidate_id in all_ids if candidate_id not in set(eligible_ids))
    pruned_ids = tuple(candidate_id for candidate_id in eligible_ids if candidate_id not in set(selected_ids))
    return MeasuredZoomReceipt(
        parent_id=parent_id,
        candidate_ids=all_ids,
        eligible_ids=eligible_ids,
        held_ids=held_ids,
        selected_ids=selected_ids,
        pruned_ids=pruned_ids,
        zoom_receipt=zoom_receipt,
        synthetic_fixture_used=synthetic_used and allow_synthetic,
    )
