"""Multimodal family-evidence ranking with uncertainty-preserving outputs."""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .evidence_models import EvidenceBundle
from .spectral_evidence import NumericSpectralRule, RuleEvaluation, evaluate_numeric_rule, fuse_rule_evaluations


class EvidenceEngine:
    def __init__(self, rules: Iterable[NumericSpectralRule]):
        self.rules = tuple(rules)
        self.by_modality: dict[str, list[NumericSpectralRule]] = defaultdict(list)
        for rule in self.rules:
            self.by_modality[rule.modality].append(rule)

    def evaluate(self, bundle: EvidenceBundle) -> dict[str, dict[str, object]]:
        sources = bundle.source_map()
        evaluations: dict[str, list[RuleEvaluation]] = defaultdict(list)
        candidate_filter = set(bundle.candidate_families)
        for observation in bundle.observations:
            quality = sources[observation.source_id].quality
            for rule in self.by_modality.get(observation.modality, ()):
                if candidate_filter and rule.family not in candidate_filter:
                    continue
                evaluations[rule.family].append(evaluate_numeric_rule(rule, observation, source_quality=quality))
        families = candidate_filter or set(evaluations)
        result: dict[str, dict[str, object]] = {}
        for family in sorted(families):
            fused = fuse_rule_evaluations(evaluations.get(family, ()))
            fused["evaluations"] = [item.to_dict() for item in evaluations.get(family, ())]
            fused["oak_boundary"] = "family compatibility, not molecular identification"
            result[family] = fused
        return result

    def rank(self, bundle: EvidenceBundle) -> list[tuple[str, float, str]]:
        results = self.evaluate(bundle)
        return sorted(
            ((family, float(value["score"]), str(value["status"])) for family, value in results.items()),
            key=lambda item: (-item[1], item[0]),
        )
