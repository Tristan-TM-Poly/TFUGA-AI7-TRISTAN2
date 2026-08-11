from __future__ import annotations

import re
from typing import Any, Iterable


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) >= 3
    }


def _skill_text(spec: dict[str, Any]) -> str:
    return " ".join(
        map(
            str,
            spec.get("use_when", [])
            + spec.get("workflow", [])
            + spec.get("outputs", []),
        )
    )


def plan_expansion(
    specs: Iterable[dict[str, Any]],
    desired_capabilities: Iterable[str],
    nearest: int = 3,
) -> dict[str, Any]:
    specs = list(specs)
    desired_capabilities = list(desired_capabilities)
    tasks = []
    coverage = {}
    indexed = [
        (str(spec.get("name")), _tokens(_skill_text(spec)))
        for spec in specs
    ]

    for capability in desired_capabilities:
        capability_tokens = _tokens(capability)
        scores = []
        for name, tokens in indexed:
            union = capability_tokens | tokens
            score = len(capability_tokens & tokens) / len(union) if union else 0.0
            scores.append((score, name))
        matches = [name for score, name in scores if score > 0]
        coverage[capability] = sorted(matches)
        if not matches:
            ranked = sorted(scores, key=lambda item: (-item[0], item[1]))[:nearest]
            tasks.append(
                {
                    "capability": capability,
                    "action": "generate_candidate_family",
                    "nearest_skills": [
                        {"name": name, "lexical_similarity": round(score, 6)}
                        for score, name in ranked
                    ],
                    "required_gates": [
                        "SkillSpec",
                        "negative control",
                        "edge/adversarial",
                        "trust review",
                        "behavioral eval before behavioral promotion",
                    ],
                    "auto_promote": False,
                }
            )

    return {
        "desired_count": len(desired_capabilities),
        "coverage": coverage,
        "generation_tasks": tasks,
        "note": "Capability planning is lexical/heuristic; generation tasks require OAK and behavioral evidence.",
    }
