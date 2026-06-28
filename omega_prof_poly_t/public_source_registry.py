"""Public metadata source registry for Omega absorb v0.8."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class PublicSource:
    source_id: str
    name: str
    mode: str
    allowed_fields: Tuple[str, ...]
    notes: Tuple[str, ...]


@dataclass(frozen=True)
class PublicSourceRegistry:
    sources: Tuple[PublicSource, ...]
    next_action: str

    def as_dict(self) -> Dict[str, PublicSource]:
        return {source.source_id: source for source in self.sources}


def default_public_source_registry() -> PublicSourceRegistry:
    return PublicSourceRegistry(
        sources=(
            PublicSource(
                source_id="polypublie_like",
                name="PolyPublie-like public metadata",
                mode="metadata_and_abstract_when_available",
                allowed_fields=("title", "authors", "year", "link", "abstract", "keywords", "departments", "professors"),
                notes=("Use public metadata fields only.", "Keep links and source labels."),
            ),
            PublicSource(
                source_id="expertise_like",
                name="Expertise-like public metadata",
                mode="profile_metadata",
                allowed_fields=("professor", "expertise", "departments", "summary", "link"),
                notes=("Treat expertise profiles as routing hints.", "Do not infer private activity."),
            ),
            PublicSource(
                source_id="demo_fixture",
                name="Demo fixture metadata",
                mode="test_fixture",
                allowed_fields=("atom_id", "title", "keywords", "methods", "claims", "limitations"),
                notes=("For tests and examples only.",),
            ),
        ),
        next_action="attach_source_id_to_absorption_records",
    )
