"""Artifact Compiler for Tristan AIT Reality Forge.

Compiles a forged idea into a repository artifact plan: theory doc, schema,
tool, tests, M- registry, and OAK report. It does not execute irreversible
changes or bypass review.
"""

from __future__ import annotations

from dataclasses import dataclass

from tools.counterworld_generator import CounterworldPack, generate_counterworlds
from tools.failure_oracle import FailureOracleReport, predict_failure_modes
from tools.proof_ladder import ProofAssessment, assess_proof_level
from tools.reality_gradient import RealityAssessment, assess_reality_level


@dataclass(frozen=True)
class ArtifactPlan:
    theory_doc: str
    schema: str
    tool: str
    tests: str
    m_minus: str
    oak_report: str


@dataclass(frozen=True)
class CompiledIdea:
    idea: str
    reality: RealityAssessment
    proof: ProofAssessment
    failures: FailureOracleReport
    counterworlds: CounterworldPack
    artifacts: ArtifactPlan
    safe_next_action: str


def slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned[:60] or "idea"


def compile_idea_to_artifacts(
    idea: str,
    *,
    has_testable_claim: bool = True,
    has_prototype: bool = False,
    has_local_test: bool = False,
    has_measurement: bool = False,
) -> CompiledIdea:
    """Create a conservative artifact plan for an idea."""

    slug = slugify(idea)
    reality = assess_reality_level(
        has_testable_claim=has_testable_claim,
        has_prototype=has_prototype,
        has_local_test=has_local_test,
        has_measurement=has_measurement,
    )
    proof = assess_proof_level(
        has_toy_test=has_local_test,
        has_benchmark=has_measurement,
    )
    failures = predict_failure_modes(idea)
    counterworlds = generate_counterworlds(idea, high_stakes=failures.no_touch_required)

    artifacts = ArtifactPlan(
        theory_doc=f"docs/theories/{slug}.md",
        schema=f"schemas/{slug}.schema.json",
        tool=f"tools/{slug}.py",
        tests=f"tests/test_{slug}.py",
        m_minus=f"safety/m_minus_{slug}.yaml",
        oak_report=f"docs/oak_reports/{slug}_oak_report.md",
    )

    if failures.no_touch_required:
        next_action = "NO-TOUCH: keep as theory/quarantine and route qualified review."
    elif int(reality.level) < 3:
        next_action = "Add RealityAnchor before artifact implementation."
    elif int(proof.level) < 3:
        next_action = "Create toy test before stronger claims."
    else:
        next_action = "Create reversible branch/draft PR with tests and OAK report."

    return CompiledIdea(
        idea=idea,
        reality=reality,
        proof=proof,
        failures=failures,
        counterworlds=counterworlds,
        artifacts=artifacts,
        safe_next_action=next_action,
    )
