"""ResearchAtom model for Ω-ABSORB-POLY-PROF-T.

A ResearchAtom is a legal, source-grounded, compact representation of a public
research output. It is designed for metadata, abstracts, claims, methods, and
OAK routing without copying restricted full text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

from .zero_touch_oak import OAKCompileResult, compile_oak


@dataclass(frozen=True)
class ResearchAtom:
    atom_id: str
    title: str
    authors: Tuple[str, ...]
    year: int | None = None
    source: str = "public_metadata"
    link: str = ""
    abstract: str = ""
    keywords: Tuple[str, ...] = ()
    departments: Tuple[str, ...] = ()
    professors: Tuple[str, ...] = ()
    claims: Tuple[str, ...] = ()
    methods: Tuple[str, ...] = ()
    limitations: Tuple[str, ...] = ()
    datasets: Tuple[str, ...] = ()
    code_links: Tuple[str, ...] = ()
    oak: OAKCompileResult | None = None

    def legal_absorption_level(self) -> str:
        if self.abstract:
            return "metadata_plus_abstract"
        return "metadata_only"

    def with_oak(self) -> "ResearchAtom":
        benefits: Dict[str, float] = {
            "teaching": 0.55 + 0.05 * min(4, len(self.keywords)),
            "research": 0.65 + 0.05 * min(4, len(self.methods)),
            "grant": 0.50 + 0.04 * min(5, len(self.claims)),
            "prototype": 0.45 + 0.05 * min(4, len(self.methods)),
            "reproducibility": 0.35 + 0.10 * bool(self.datasets) + 0.15 * bool(self.code_links),
        }
        risks: Dict[str, float] = {
            "overclaim": 0.55 if self.claims and not self.limitations else 0.25,
            "copyright": 0.10 if self.legal_absorption_level() == "metadata_only" else 0.20,
            "confidentiality": 0.05,
            "complexity": min(0.80, 0.06 * (len(self.claims) + len(self.methods))),
        }
        evidence_count = 1 + bool(self.abstract) + len(self.code_links) + len(self.datasets)
        return ResearchAtom(
            atom_id=self.atom_id,
            title=self.title,
            authors=self.authors,
            year=self.year,
            source=self.source,
            link=self.link,
            abstract=self.abstract,
            keywords=self.keywords,
            departments=self.departments,
            professors=self.professors,
            claims=self.claims,
            methods=self.methods,
            limitations=self.limitations,
            datasets=self.datasets,
            code_links=self.code_links,
            oak=compile_oak(self.title, benefits, risks, evidence_count=int(evidence_count)),
        )


def atom_from_public_record(record: Dict[str, object]) -> ResearchAtom:
    """Create a ResearchAtom from a public metadata record.

    The function only consumes caller-provided metadata/abstract fields. It does
    not fetch or copy restricted full text.
    """

    def tup(key: str) -> Tuple[str, ...]:
        value = record.get(key, ())
        if isinstance(value, str):
            return (value,) if value else ()
        if isinstance(value, (list, tuple)):
            return tuple(str(item) for item in value if str(item))
        return ()

    year_value = record.get("year")
    year = int(year_value) if isinstance(year_value, int) or (isinstance(year_value, str) and year_value.isdigit()) else None
    atom = ResearchAtom(
        atom_id=str(record.get("atom_id") or record.get("id") or record.get("title") or "research_atom"),
        title=str(record.get("title") or "Untitled research atom"),
        authors=tup("authors"),
        year=year,
        source=str(record.get("source") or "public_metadata"),
        link=str(record.get("link") or ""),
        abstract=str(record.get("abstract") or ""),
        keywords=tup("keywords"),
        departments=tup("departments"),
        professors=tup("professors"),
        claims=tup("claims"),
        methods=tup("methods"),
        limitations=tup("limitations"),
        datasets=tup("datasets"),
        code_links=tup("code_links"),
    )
    return atom.with_oak()
