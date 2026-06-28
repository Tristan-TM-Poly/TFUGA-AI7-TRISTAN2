"""Public metadata adapter interface.

Adapters normalize public metadata records into dictionaries consumable by
ResearchAtom. They do not scrape restricted full text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Protocol, Tuple


class PublicMetadataAdapter(Protocol):
    name: str

    def normalize(self, records: Iterable[Dict[str, object]]) -> Tuple[Dict[str, object], ...]:
        ...


@dataclass(frozen=True)
class GenericPublicMetadataAdapter:
    name: str = "generic_public_metadata"

    def normalize(self, records: Iterable[Dict[str, object]]) -> Tuple[Dict[str, object], ...]:
        normalized = []
        for index, record in enumerate(records, start=1):
            title = str(record.get("title") or record.get("name") or f"Untitled public record {index}")
            normalized.append(
                {
                    "atom_id": str(record.get("atom_id") or record.get("id") or f"public-record-{index}"),
                    "title": title,
                    "authors": record.get("authors") or record.get("creators") or (),
                    "year": record.get("year"),
                    "source": str(record.get("source") or self.name),
                    "link": str(record.get("link") or record.get("url") or ""),
                    "abstract": str(record.get("abstract") or record.get("summary") or ""),
                    "keywords": record.get("keywords") or record.get("subjects") or (),
                    "departments": record.get("departments") or record.get("divisions") or (),
                    "professors": record.get("professors") or record.get("supervisors") or (),
                    "claims": record.get("claims") or (),
                    "methods": record.get("methods") or (),
                    "limitations": record.get("limitations") or (),
                    "datasets": record.get("datasets") or (),
                    "code_links": record.get("code_links") or (),
                }
            )
        return tuple(normalized)
