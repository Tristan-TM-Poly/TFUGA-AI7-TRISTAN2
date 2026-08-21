"""Ω Capability OS cross-skill transplant adapter.

Reuses the canonical Capability OS genome and the R0.10 replay/provenance courts.
This module does not create a second capability ontology. It evaluates whether
an already-declared capability can transfer across multiple declared skill
contexts without authority widening, provenance collapse, decision instability,
or historical/counterfactual regression.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from omega_capability_os_t.core import Capability
from omega_generative_closure_t.reprovenance_replay import (
    FrozenSlice,
    CounterfactualReplayReport,
    HistoricalReplayReport,
    ProvenanceIndependenceReport,
    CrossRunReproducibilityReport,
    counterfactual_replay,
    cross_run_reproducibility,
    historical_replay,
    provenance_independence,
)


@dataclass(frozen=True)
class SkillContext:
    skill_id: str
    domain: str
    required_inputs: frozenset[str]
    required_outputs: frozenset[str]
    max_authority: str = "read"

    @classmethod
    def make(
        cls,
        skill_id: str,
        domain: str,
        required_inputs: Iterable[str] = (),
        required_outputs: Iterable[str] = (),
        max_authority: str = "read",
    ) -> "SkillContext":
        return cls(
            str(skill_id),
            str(domain),
            frozenset(map(str, required_inputs)),
            frozenset(map(str, required_outputs)),
            str(max_authority),
        )


@dataclass(frozen=True)
class SkillTransferResult:
    skill_id: str
    domain: str
    input_compatible: bool
    output_compatible: bool
    authority_compatible: bool
    passed: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class CapabilityTransplantReport:
    capability_id: str
    contexts: tuple[SkillTransferResult, ...]
    transfer_ratio: float
    provenance: ProvenanceIndependenceReport
    reproducibility: CrossRunReproducibilityReport
    historical: HistoricalReplayReport
    counterfactual: CounterfactualReplayReport
    decision: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "PROMOTE means one declared Capability OS capability survived the supplied finite cross-skill interfaces, "
        "provenance, replay and authority courts; it is not universal skill compatibility, semantic equivalence, "
        "real-world effectiveness, or authority to invoke external actions."
    )


_AUTHORITY_ORDER = {"read": 0, "draft": 1, "write": 2, "irreversible": 3}


def _authority_compatible(capability: Capability, context: SkillContext) -> bool:
    return _AUTHORITY_ORDER.get(capability.authority, 99) <= _AUTHORITY_ORDER.get(context.max_authority, -1)


def evaluate_capability_transplant(
    capability: Capability,
    contexts: Iterable[SkillContext],
    *,
    frozen_slices: Iterable[FrozenSlice],
    training_provenance_ids: Iterable[str],
    runs: Mapping[str, Mapping[str, str]],
    historical_expected: Mapping[str, str],
    historical_candidate: Mapping[str, str],
    counterfactual_observations: Iterable[tuple[float, float]],
    min_transfer_ratio: float = 1.0,
) -> CapabilityTransplantReport:
    if not 0.0 <= float(min_transfer_ratio) <= 1.0:
        raise ValueError("min_transfer_ratio must be in [0, 1]")

    items = tuple(contexts)
    results: list[SkillTransferResult] = []
    for context in items:
        input_ok = context.required_inputs.issubset(set(capability.consumes))
        output_ok = context.required_outputs.issubset(set(capability.produces))
        authority_ok = _authority_compatible(capability, context)
        blockers: list[str] = []
        if not input_ok:
            blockers.append("input_contract_not_covered")
        if not output_ok:
            blockers.append("output_contract_not_covered")
        if not authority_ok:
            blockers.append("authority_widening_required")
        results.append(
            SkillTransferResult(
                context.skill_id,
                context.domain,
                input_ok,
                output_ok,
                authority_ok,
                not blockers,
                tuple(blockers),
            )
        )

    transfer_ratio = 0.0 if not results else sum(item.passed for item in results) / len(results)
    provenance = provenance_independence(
        frozen_slices,
        training_provenance_ids=training_provenance_ids,
    )
    reproducibility = cross_run_reproducibility(runs)
    historical = historical_replay(historical_expected, historical_candidate)
    counterfactual = counterfactual_replay(counterfactual_observations)

    blockers: list[str] = []
    if not results:
        blockers.append("missing_skill_contexts")
    if transfer_ratio < min_transfer_ratio:
        blockers.append("cross_skill_transfer_below_threshold")
    for prefix, report in (
        ("provenance", provenance),
        ("reproducibility", reproducibility),
        ("historical", historical),
        ("counterfactual", counterfactual),
    ):
        if report.oak_status != "PASS":
            blockers.extend(f"{prefix}:{item}" for item in report.blockers)

    return CapabilityTransplantReport(
        capability_id=capability.capability_id,
        contexts=tuple(results),
        transfer_ratio=transfer_ratio,
        provenance=provenance,
        reproducibility=reproducibility,
        historical=historical,
        counterfactual=counterfactual,
        decision="PROMOTE" if not blockers else "HOLD",
        blockers=tuple(blockers),
    )
