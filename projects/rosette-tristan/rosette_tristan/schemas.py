from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class BBox:
    """Page-local bounding box in PDF coordinate space when available."""

    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class SourceRef:
    """Trace from a Rosette artifact back to its source document region."""

    path: str
    page: int | None = None
    span_start: int | None = None
    span_end: int | None = None
    bbox: BBox | None = None
    extractor: str = "text"
    method: str = "text"

    def stable_id(self) -> str:
        return ":".join(
            str(part)
            for part in [
                self.path,
                self.page if self.page is not None else "nopage",
                self.span_start if self.span_start is not None else "nostart",
                self.span_end if self.span_end is not None else "noend",
                self.extractor,
            ]
        )


@dataclass
class ConfidenceTensor:
    """Rosette confidence tensor for extraction and downstream artifacts."""

    text: float = 0.9
    layout: float = 0.55
    math: float = 0.5
    table: float = 0.0
    figure: float = 0.0
    citation: float = 0.0
    code: float = 0.0
    theory: float = 0.45
    reproduction: float = 0.0

    def average(self) -> float:
        values = [
            self.text,
            self.layout,
            self.math,
            self.table,
            self.figure,
            self.citation,
            self.code,
            self.theory,
            self.reproduction,
        ]
        return sum(values) / len(values)


@dataclass
class Block:
    kind: str
    text: str
    source: SourceRef
    confidence: float = 0.9
    oak_status: str = "usable"
    confidence_tensor: ConfidenceTensor = field(default_factory=ConfidenceTensor)


@dataclass
class Equation:
    latex: str
    source: SourceRef
    confidence: float = 0.82
    oak_status: str = "usable"
    notes: list[str] = field(default_factory=list)
    confidence_tensor: ConfidenceTensor = field(default_factory=lambda: ConfidenceTensor(math=0.82, theory=0.55))


@dataclass
class Claim:
    claim: str
    source: SourceRef | None = None
    evidence_ids: list[str] = field(default_factory=list)
    confidence: float = 0.55
    oak_status: str = "uncertain"
    confidence_tensor: ConfidenceTensor = field(default_factory=lambda: ConfidenceTensor(text=0.75, theory=0.55))


@dataclass
class ExtractorRun:
    name: str
    status: str
    pages: int = 0
    blocks: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass
class RosetteResult:
    input_path: str
    sha256: str
    blocks: list[Block]
    equations: list[Equation]
    claims: list[Claim]
    oak_findings: list[str]
    memory_minus: list[str]
    extractor_runs: list[ExtractorRun] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
