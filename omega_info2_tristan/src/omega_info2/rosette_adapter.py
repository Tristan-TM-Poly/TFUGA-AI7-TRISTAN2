"""Rosette-Tristan adapter for Ω-INFO²-T.

Rosette extracts PDF structure; this adapter converts a Rosette-like payload
into an InfoObject while preserving page/bbox/method/confidence provenance.
No extraction is treated as truth: claims remain OAK-testable/raw until checked.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .models import Claim, InfoObject, InfoScores, MetaInformation, OAKStatus, Provenance, ProvenanceStep, RawObject, UncertaintyTensor, clamp01
from .source_trust import SourceTrustInput, score_source


@dataclass(slots=True)
class SourceSpan:
    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    method: str = "unknown"
    confidence: float = 0.5

    def __post_init__(self) -> None:
        self.confidence = clamp01(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RosetteClaim:
    text: str
    domain: str = "general"
    span: SourceSpan = field(default_factory=SourceSpan)
    evidence_ids: list[str] = field(default_factory=list)
    counterevidence_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RosetteExtraction:
    document_id: str
    source: str
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    language: str = "unknown"
    license: str = "unknown"
    claims: list[RosetteClaim] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)
    equations: list[str] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)
    figures: list[dict[str, Any]] = field(default_factory=list)
    extraction_tool: str = "rosette-tristan"
    extraction_version: str = "0.1.0"


def rosette_to_info_object(extraction: RosetteExtraction) -> InfoObject:
    """Convert a RosetteExtraction into an OAK-safe InfoObject."""
    avg_confidence = _average_claim_confidence(extraction.claims)
    source_trust = score_source(
        SourceTrustInput(
            reputation=0.55,
            traceability=0.85 if extraction.source else 0.2,
            reproducibility=avg_confidence,
            freshness=0.5,
            independence=0.5,
            opacity=1.0 - avg_confidence,
            primary_source=True,
        )
    )
    claims = [
        Claim(
            text=item.text,
            domain=item.domain,
            source_id=f"{extraction.document_id}:p{item.span.page}" if item.span.page is not None else extraction.document_id,
            evidence_ids=item.evidence_ids,
            counterevidence_ids=item.counterevidence_ids,
            uncertainty=1.0 - item.span.confidence,
            oak_status=OAKStatus.PARSED,
            next_test="Verify Rosette extraction against rendered PDF page/bbox and link evidence/counter-evidence.",
        )
        for item in extraction.claims
    ]
    provenance_steps = [
        ProvenanceStep(
            operation="rosette_extract_pdf",
            tool=extraction.extraction_tool,
            tool_version=extraction.extraction_version,
            parameters={"source": extraction.source, "document_id": extraction.document_id},
            confidence=avg_confidence,
            information_loss=1.0 - avg_confidence,
            errors_detected=[],
        )
    ]
    for idx, claim in enumerate(extraction.claims):
        provenance_steps.append(
            ProvenanceStep(
                operation=f"claim_span_{idx}",
                tool=claim.span.method,
                parameters=claim.span.to_dict(),
                confidence=claim.span.confidence,
                information_loss=1.0 - claim.span.confidence,
            )
        )
    obj = InfoObject(
        id=f"info2_rosette_{extraction.document_id}",
        raw_object=RawObject(type="pdf", location=extraction.source, content_preview=extraction.title),
        claims=claims,
        concepts=extraction.concepts,
        equations=extraction.equations,
        datasets=[table.get("id", f"table:{i}") for i, table in enumerate(extraction.tables)],
        meta=MetaInformation(
            source=extraction.source,
            author=", ".join(extraction.authors) if extraction.authors else None,
            license=extraction.license,
            language=extraction.language,
            domain="rosette_pdf",
        ),
        provenance=Provenance(
            extraction_tool=extraction.extraction_tool,
            extraction_version=extraction.extraction_version,
            transformations=provenance_steps,
        ),
        uncertainty=UncertaintyTensor(
            source_uncertainty=0.15 if extraction.source else 0.75,
            interpretation_uncertainty=1.0 - avg_confidence,
            temporal_uncertainty=0.5,
            license_uncertainty=0.8 if extraction.license == "unknown" else 0.2,
        ),
        scores=InfoScores(
            truth=0.35,
            utility=0.65,
            fertility=0.70,
            novelty=0.50,
            testability=0.75 if claims else 0.30,
            safety=0.70,
            risk=0.25,
            freshness=0.50,
            ip_sensitivity=0.45 if extraction.license == "unknown" else 0.20,
            source_trust=source_trust,
        ),
    )
    if extraction.figures:
        obj.oak.residue.append("Figures extracted by Rosette require visual verification before claims are trusted.")
    if extraction.tables:
        obj.oak.residue.append("Tables extracted by Rosette require cell-level fidelity checks before numeric use.")
    return obj


def _average_claim_confidence(claims: list[RosetteClaim]) -> float:
    if not claims:
        return 0.5
    return clamp01(sum(claim.span.confidence for claim in claims) / len(claims))
