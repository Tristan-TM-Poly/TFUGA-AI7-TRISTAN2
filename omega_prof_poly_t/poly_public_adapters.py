"""Specialized public metadata adapters for Omega absorb v0.6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from .public_metadata_adapters import GenericPublicMetadataAdapter


@dataclass(frozen=True)
class PolyPublieLikeAdapter(GenericPublicMetadataAdapter):
    name: str = "polypublie_like_public_metadata"

    def normalize(self, records: Iterable[Dict[str, object]]) -> Tuple[Dict[str, object], ...]:
        normalized = []
        for index, record in enumerate(records, start=1):
            title = str(record.get("title") or record.get("dc.title") or f"PolyPublie record {index}")
            normalized.append(
                {
                    "atom_id": str(record.get("id") or record.get("identifier") or f"polypublie-{index}"),
                    "title": title,
                    "authors": record.get("authors") or record.get("creators") or record.get("dc.creator") or (),
                    "year": record.get("year") or record.get("date") or record.get("dc.date"),
                    "source": str(record.get("source") or self.name),
                    "link": str(record.get("link") or record.get("identifier_uri") or record.get("url") or ""),
                    "abstract": str(record.get("abstract") or record.get("description") or record.get("dc.description") or ""),
                    "keywords": record.get("keywords") or record.get("subjects") or record.get("dc.subject") or (),
                    "departments": record.get("departments") or record.get("division") or record.get("divisions") or (),
                    "professors": record.get("professors") or record.get("directors") or record.get("supervisors") or (),
                    "claims": record.get("claims") or (),
                    "methods": record.get("methods") or (),
                    "limitations": record.get("limitations") or (),
                    "datasets": record.get("datasets") or (),
                    "code_links": record.get("code_links") or (),
                }
            )
        return tuple(normalized)


@dataclass(frozen=True)
class ExpertiseLikeAdapter(GenericPublicMetadataAdapter):
    name: str = "expertise_like_public_metadata"

    def normalize(self, records: Iterable[Dict[str, object]]) -> Tuple[Dict[str, object], ...]:
        normalized = []
        for index, record in enumerate(records, start=1):
            professor = str(record.get("professor") or record.get("name") or f"Professor {index}")
            expertise = record.get("expertise") or record.get("keywords") or record.get("domains") or ()
            normalized.append(
                {
                    "atom_id": str(record.get("id") or f"expertise-{index}"),
                    "title": f"Expertise profile: {professor}",
                    "authors": (professor,),
                    "year": record.get("year"),
                    "source": str(record.get("source") or self.name),
                    "link": str(record.get("link") or record.get("url") or ""),
                    "abstract": str(record.get("summary") or "Public expertise profile metadata."),
                    "keywords": expertise,
                    "departments": record.get("departments") or record.get("department") or (),
                    "professors": (professor,),
                    "claims": record.get("claims") or (),
                    "methods": record.get("methods") or (),
                    "limitations": record.get("limitations") or ("expertise_profile_not_full_publication",),
                    "datasets": (),
                    "code_links": (),
                }
            )
        return tuple(normalized)
