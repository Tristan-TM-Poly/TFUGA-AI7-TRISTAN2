from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Iterable


@dataclass
class EvidenceSet:
    equations: list[str] = field(default_factory=list)
    figures: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass
class ClaimAssessment:
    claim_id: str
    text: str
    evidence: EvidenceSet
    counter_checks: list[str]
    oak_status: str
    classification: str

    def to_dict(self) -> dict:
        data = asdict(self)
        return data


def classify_claim(evidence: EvidenceSet) -> tuple[str, str]:
    if evidence.equations and evidence.figures:
        return "CLAIM_SUPPORTED_BY_EQUATION_AND_FIGURE", "partially_supported"
    if evidence.equations:
        return "CLAIM_SUPPORTED_BY_EQUATION", "partially_supported"
    if evidence.figures:
        return "CLAIM_SUPPORTED_BY_FIGURE", "partially_supported"
    if evidence.tables:
        return "CLAIM_SUPPORTED_BY_TABLE", "partially_supported"
    if evidence.citations:
        return "CLAIM_SUPPORTED_BY_CITATION", "weakly_supported"
    return "CLAIM_UNSUPPORTED", "uncertain"


def default_counter_checks(text: str) -> list[str]:
    low = text.lower()
    checks = ["identify baseline", "link claim to explicit evidence", "search for counter-assumptions"]
    if "noise" in low or "noisy" in low:
        checks.extend(["test non-Gaussian noise", "test high-noise regime"])
    if "improve" in low or "better" in low:
        checks.append("compare against baseline under identical conditions")
    if "stable" in low or "stability" in low:
        checks.append("test stability outside reported parameter range")
    return checks


def build_claim_graph(claims: Iterable, equations: Iterable | None = None) -> list[ClaimAssessment]:
    eq_ids = [f"E{idx}" for idx, _ in enumerate(equations or [], 1)]
    assessments: list[ClaimAssessment] = []
    for idx, claim in enumerate(claims, 1):
        text = getattr(claim, "claim", str(claim))
        evidence = EvidenceSet()
        low = text.lower()
        if any(word in low for word in ["equation", "model", "dynamics", "state"]):
            evidence.equations = eq_ids[:2]
        if "figure" in low or "fig." in low:
            evidence.figures = ["F1"]
        if "table" in low:
            evidence.tables = ["T1"]
        if "citation" in low or "reference" in low:
            evidence.citations = ["R1"]
        classification, oak_status = classify_claim(evidence)
        assessments.append(
            ClaimAssessment(
                claim_id=f"C{idx}",
                text=text,
                evidence=evidence,
                counter_checks=default_counter_checks(text),
                oak_status=oak_status,
                classification=classification,
            )
        )
    return assessments
