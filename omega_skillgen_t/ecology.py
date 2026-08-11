from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from .genome import genome_similarity


def ecology_audit(
    specs: Iterable[dict[str, Any]],
    duplicate_threshold: float = 0.82,
) -> dict[str, Any]:
    specs = list(specs)
    duplicates = []
    for index, a in enumerate(specs):
        for b in specs[index + 1 :]:
            similarity = genome_similarity(a, b)
            if similarity["score"] >= duplicate_threshold:
                duplicates.append(
                    {"a": a.get("name"), "b": b.get("name"), "similarity": similarity}
                )

    classes = Counter()
    missing_eval_classes = {}
    required = {"positive", "negative", "incomplete"}
    edge = {"edge", "adversarial"}
    for spec in specs:
        present = {
            str(case.get("class"))
            for case in spec.get("eval_cases", [])
            if isinstance(case, dict)
        }
        classes.update(present)
        missing = sorted(required - present)
        if not (present & edge):
            missing.append("edge_or_adversarial")
        if missing:
            missing_eval_classes[str(spec.get("name"))] = missing

    invariant_counts = Counter(
        invariant
        for spec in specs
        for invariant in spec.get("invariants", [])
    )
    return {
        "skill_count": len(specs),
        "duplicate_threshold": duplicate_threshold,
        "candidate_duplicate_pairs": sorted(
            duplicates, key=lambda item: -item["similarity"]["score"]
        ),
        "eval_class_presence": dict(classes),
        "skills_missing_eval_classes": missing_eval_classes,
        "shared_invariants": [
            {"invariant": invariant, "support": support}
            for invariant, support in invariant_counts.most_common()
            if support >= 2
        ],
        "compression_debt": len(duplicates),
        "note": "Ecology audit identifies review targets; similarity and repetition do not prove semantic equivalence or correctness.",
    }


def capability_gap_report(
    specs: Iterable[dict[str, Any]],
    desired_capabilities: Iterable[str],
) -> dict[str, Any]:
    specs = list(specs)
    text_by_skill = {
        str(spec.get("name")): " ".join(
            map(
                str,
                spec.get("use_when", [])
                + spec.get("workflow", [])
                + spec.get("outputs", []),
            )
        ).lower()
        for spec in specs
    }
    gaps = []
    coverage = {}
    desired_capabilities = list(desired_capabilities)
    for capability in desired_capabilities:
        token = capability.lower()
        matches = sorted(
            name for name, text in text_by_skill.items() if token in text
        )
        coverage[capability] = matches
        if not matches:
            gaps.append(capability)
    return {
        "desired": desired_capabilities,
        "coverage": coverage,
        "gaps": gaps,
        "note": "Lexical capability coverage is a planning heuristic, not proof the capability works.",
    }
