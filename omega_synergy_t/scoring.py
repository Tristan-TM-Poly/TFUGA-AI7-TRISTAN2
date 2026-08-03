"""Multi-objective scoring for synergy hypotheses.

All scores are scheduling heuristics. They never promote a hypothesis to proof.
"""
from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
from typing import Callable, Iterable

from .models import CreationDNA, InterfaceContract, SynergyCandidate, SynergyStage, SynergyTensor, Authority, stable_id
from .ontology import domain_complementarity, jaccard, type_compatibility


@dataclass(frozen=True, slots=True)
class ScoreWeights:
    semantic_resonance: float = 0.08
    complementarity: float = 0.16
    interface_compatibility: float = 0.12
    closure_gain: float = 0.16
    evidence: float = 0.12
    causal_readiness: float = 0.06
    reuse: float = 0.08
    option_value: float = 0.07
    product_value: float = 0.05
    risk: float = 0.13
    integration_cost: float = 0.09
    uncertainty: float = 0.08
    debt: float = 0.06


def _mean(values: Iterable[float], default: float = 0.0) -> float:
    data = list(values)
    return sum(data) / len(data) if data else default


def _capability_need_matches(provider: CreationDNA, target: CreationDNA) -> list[tuple[float, str, str, InterfaceContract]]:
    matches: list[tuple[float, str, str, InterfaceContract]] = []
    for capability in provider.capabilities:
        for need in target.needs:
            compatibility = type_compatibility(capability.output_types, need.desired_output_types)
            if compatibility < 0.2:
                continue
            source_type = capability.output_types[0] if capability.output_types else "artifact"
            target_type = need.desired_output_types[0] if need.desired_output_types else "artifact"
            contract = InterfaceContract(
                id=stable_id("IFC", provider.id, target.id, capability.id, need.id),
                source_type=source_type,
                target_type=target_type,
                mappings={source_type: target_type},
                preserved_invariants=sorted(set(capability.invariants) | {"provenance_preservation"}),
                declared_losses=sorted(set(capability.losses)),
                tests=["schema_validation", "round_trip_when_reversible", "provenance_integrity"],
                reversible=not capability.losses,
                confidence=compatibility,
            )
            matches.append((compatibility, capability.id, need.id, contract))
    return matches


def pair_tensor(left: CreationDNA, right: CreationDNA, co_mentions: float = 0.0, weights: ScoreWeights | None = None) -> tuple[SynergyTensor, list[str], list[str], list[InterfaceContract], list[str]]:
    weights = weights or ScoreWeights()
    semantic = min(1.0, 0.75 * jaccard(left.tokens[:60], right.tokens[:60]) + 0.25 * co_mentions)
    domain_comp = domain_complementarity(left.domains, right.domains)
    forward = _capability_need_matches(left, right)
    backward = _capability_need_matches(right, left)
    matches = forward + backward
    interface = max((item[0] for item in matches), default=0.0)
    matched_needs = sorted({item[2] for item in matches})
    transformations = []
    for _, capability_id, need_id, contract in matches:
        transformations.append(f"{capability_id} => {need_id} via {contract.id}")
    closure_denominator = max(1, len(left.needs) + len(right.needs))
    closure_gain = min(1.0, len(matched_needs) / closure_denominator)
    evidence = math.sqrt(max(0.0, left.evidence_score) * max(0.0, right.evidence_score))
    causal_readiness = min(1.0, 0.15 + 0.35 * interface + 0.25 * evidence + 0.25 * closure_gain)
    reuse = min(1.0, (len(left.paths) + len(right.paths)) / 20.0 + 0.2 * bool(matches))
    option_value = min(1.0, (len(left.expansion_options) + len(right.expansion_options)) / 12.0)
    product_value = min(1.0, 0.45 * ("business" in left.domains or "business" in right.domains) + 0.25 * closure_gain + 0.2 * evidence)
    risk = min(1.0, max(left.aggregate_risk, right.aggregate_risk) + 0.1 * bool(set(left.domains) ^ set(right.domains)))
    integration_cost = min(1.0, 0.15 + 0.08 * abs(len(left.capabilities) - len(right.needs)) + 0.15 * (1.0 - interface))
    uncertainty = min(1.0, _mean([*left.uncertainty.values(), *right.uncertainty.values()], 0.6))
    duplication = jaccard({cap.name for cap in left.capabilities}, {cap.name for cap in right.capabilities})
    debt = min(1.0, 0.25 * duplication + 0.15 * (len(left.paths) + len(right.paths) > 50) + 0.2 * (interface < 0.15))

    positive = (
        weights.semantic_resonance * semantic
        + weights.complementarity * domain_comp
        + weights.interface_compatibility * interface
        + weights.closure_gain * closure_gain
        + weights.evidence * evidence
        + weights.causal_readiness * causal_readiness
        + weights.reuse * reuse
        + weights.option_value * option_value
        + weights.product_value * product_value
    )
    negative = (
        weights.risk * risk
        + weights.integration_cost * integration_cost
        + weights.uncertainty * uncertainty
        + weights.debt * debt
    )
    total = max(0.0, min(1.0, positive - negative + 0.18))

    flags: list[str] = []
    if semantic > 0.35 and not matches:
        flags.append("semantic_similarity_without_capability_need_match")
    if duplication > 0.6:
        flags.append("possible_redundancy")
    if interface < 0.15:
        flags.append("interface_missing_or_weak")
    if risk > 0.55:
        flags.append("high_risk_requires_human_gate")
    if evidence < 0.2:
        flags.append("weak_evidence")
    if total < 0.12:
        flags.append("negative_or_negligible_expected_synergy")

    tensor = SynergyTensor(
        semantic_resonance=round(semantic, 6),
        complementarity=round(domain_comp, 6),
        interface_compatibility=round(interface, 6),
        closure_gain=round(closure_gain, 6),
        evidence=round(evidence, 6),
        causal_readiness=round(causal_readiness, 6),
        reuse=round(reuse, 6),
        option_value=round(option_value, 6),
        product_value=round(product_value, 6),
        risk=round(risk, 6),
        integration_cost=round(integration_cost, 6),
        uncertainty=round(uncertainty, 6),
        debt=round(debt, 6),
        total=round(total, 6),
    )
    return tensor, transformations, matched_needs, [item[3] for item in matches], flags


def combine_tensors(tensors: Iterable[SynergyTensor], order: int) -> SynergyTensor:
    data = list(tensors)
    if not data:
        return SynergyTensor(*(0.0 for _ in range(14)))
    fields = [name for name in SynergyTensor.__dataclass_fields__ if name != "total"]
    values = {field: _mean(getattr(item, field) for item in data) for field in fields}
    bottleneck = min(item.interface_compatibility for item in data)
    order_penalty = max(0.0, 0.035 * (order - 2))
    positive = _mean(
        [values["semantic_resonance"], values["complementarity"], values["interface_compatibility"], values["closure_gain"], values["evidence"], values["causal_readiness"], values["reuse"], values["option_value"], values["product_value"]]
    )
    negative = _mean([values["risk"], values["integration_cost"], values["uncertainty"], values["debt"]])
    total = max(0.0, min(1.0, 0.68 * positive + 0.14 * bottleneck - 0.25 * negative + 0.16 - order_penalty))
    return SynergyTensor(**{key: round(value, 6) for key, value in values.items()}, total=round(total, 6))


def build_candidate(creations: list[CreationDNA], co_mentions: Callable[[str, str], float] | None = None) -> SynergyCandidate:
    ordered = sorted(creations, key=lambda item: item.name)
    pair_data = []
    all_transformations: list[str] = []
    all_needs: list[str] = []
    all_interfaces: list[InterfaceContract] = []
    all_flags: list[str] = []
    for left, right in itertools.combinations(ordered, 2):
        co = co_mentions(left.name, right.name) if co_mentions else 0.0
        tensor, transformations, needs, interfaces, flags = pair_tensor(left, right, co)
        pair_data.append(tensor)
        all_transformations.extend(transformations)
        all_needs.extend(needs)
        all_interfaces.extend(interfaces)
        all_flags.extend(flags)
    tensor = combine_tensors(pair_data, len(ordered)) if len(ordered) > 2 else pair_data[0]
    stage = SynergyStage.S3_INTERFACE if all_interfaces else SynergyStage.S1_RESONANCE
    if all_needs:
        stage = SynergyStage.S2_COMPLEMENTARITY
    candidate_id = stable_id("SYN", [item.id for item in ordered])
    return SynergyCandidate(
        id=candidate_id,
        systems=[item.name for item in ordered],
        order=len(ordered),
        stage=stage,
        authority=Authority.REVIEW_ONLY,
        tensor=tensor,
        transformations=sorted(set(all_transformations)),
        matched_needs=sorted(set(all_needs)),
        proposed_interfaces=sorted({item.id: item for item in all_interfaces}.values(), key=lambda item: item.id),
        anti_synergy_flags=sorted(set(all_flags)),
        causal_hypothesis="The composed capabilities close documented needs and outperform isolated components under controlled baselines.",
        simplest_baseline="Use the strongest isolated component or the simplest existing external solution.",
        provenance=sorted({path for item in ordered for path in item.paths}),
    )


def approximate_shapley(systems: list[str], value: Callable[[frozenset[str]], float], max_exact: int = 8) -> dict[str, float]:
    """Exact Shapley values for small coalitions; deterministic prefix approximation otherwise."""
    if not systems:
        return {}
    systems = sorted(set(systems))
    n = len(systems)
    if n > max_exact:
        base: dict[str, float] = {}
        coalition: frozenset[str] = frozenset()
        previous = value(coalition)
        for system in systems:
            coalition = coalition | {system}
            current = value(coalition)
            base[system] = current - previous
            previous = current
        return base
    result = {system: 0.0 for system in systems}
    factorial = math.factorial
    for system in systems:
        others = [item for item in systems if item != system]
        for size in range(len(others) + 1):
            for subset in itertools.combinations(others, size):
                coalition = frozenset(subset)
                weight = factorial(size) * factorial(n - size - 1) / factorial(n)
                result[system] += weight * (value(coalition | {system}) - value(coalition))
    return {key: round(value_, 6) for key, value_ in result.items()}


def decayed_confidence(initial: float, elapsed_days: float, half_life_days: float) -> float:
    if half_life_days <= 0:
        raise ValueError("half_life_days must be positive")
    return max(0.0, min(1.0, initial * 2 ** (-elapsed_days / half_life_days)))
