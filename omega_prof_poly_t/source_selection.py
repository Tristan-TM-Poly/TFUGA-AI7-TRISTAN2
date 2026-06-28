"""Source selection helpers for Omega absorb v1.2."""

from __future__ import annotations

from typing import Dict, Tuple

from .fixture_loader_v08 import combine_fixture_records, demo_combined_fixture_records


def select_demo_records(source: str = "combined") -> Tuple[Dict[str, object], ...]:
    """Return demo public metadata records by source family."""

    source = source.strip().lower()
    if source == "combined":
        return demo_combined_fixture_records()
    if source == "polypublie":
        return combine_fixture_records(
            polypublie_like=(
                {
                    "identifier": "v12-poly-sensor",
                    "dc.title": "Sensor uncertainty source selection fixture",
                    "dc.creator": ["Professor Demo"],
                    "dc.date": 2026,
                    "dc.subject": ["sensors", "uncertainty"],
                    "division": ["genie physique", "genie electrique"],
                    "directors": ["Professor Demo"],
                    "claims": ["Sensor uncertainty can seed a source-selected packet."],
                    "methods": ["FFT", "uncertainty estimation"],
                    "limitations": ["demo record"],
                },
            )
        )
    if source == "expertise":
        return combine_fixture_records(
            expertise_like=(
                {
                    "id": "v12-expertise-energy",
                    "name": "Professor Energy Demo",
                    "expertise": ["energy", "control"],
                    "department": ["genie electrique", "genie mecanique"],
                    "methods": ["control simulation"],
                    "claims": ["Expertise metadata can seed a source-selected packet."],
                },
            )
        )
    raise ValueError(f"unknown source: {source}")


def available_demo_sources() -> Tuple[str, ...]:
    return ("combined", "polypublie", "expertise")
