from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class AbsorptionLadder:
    summary_5min: str
    deep_summary: str
    variables: list[str] = field(default_factory=list)
    equations: list[str] = field(default_factory=list)
    claims_evidence: list[dict] = field(default_factory=list)
    oak_critique: list[str] = field(default_factory=list)
    tristan_connections: list[str] = field(default_factory=list)
    implementation_plan: list[str] = field(default_factory=list)
    flashcards: list[dict[str, str]] = field(default_factory=list)
    exam_questions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def build_absorption_ladder(result, claim_assessments: list | None = None) -> AbsorptionLadder:
    equations = [getattr(eq, "latex", str(eq)) for eq in getattr(result, "equations", [])]
    critique = list(getattr(result, "oak_findings", [])) or ["No OAK findings recorded; this is not proof of correctness."]
    claims = [assessment.to_dict() if hasattr(assessment, "to_dict") else dict(assessment) for assessment in (claim_assessments or [])]
    return AbsorptionLadder(
        summary_5min=f"Rosette extracted {len(getattr(result, 'blocks', []))} blocks, {len(equations)} equations and {len(getattr(result, 'claims', []))} claim candidates.",
        deep_summary="This document is represented as source-traced artifacts requiring consensus, evidence linking, dimensional OAK and reproduction checks before certification.",
        equations=equations,
        claims_evidence=claims,
        oak_critique=critique,
        tristan_connections=["Omega-ROSETTE-T", "OAK", "HGFM", "CVCD", "M-plus/M-minus"],
        implementation_plan=[
            "run rosette-fidelity",
            "build consensus artifacts",
            "link claims to evidence",
            "run equation dimensional OAK",
            "generate code only with source equation IDs and tests",
        ],
        flashcards=[
            {"q": "What is the Rosette OAK axiom?", "a": "Extraction is not truth; every artifact needs source trace and validation status."},
            {"q": "What is OAK honesty?", "a": "The system marks uncertainty instead of certifying unsupported outputs."},
        ],
        exam_questions=[
            "Which claims are unsupported?",
            "Which equations need dimensional checks?",
            "What data is missing for reproduction?",
        ],
    )
