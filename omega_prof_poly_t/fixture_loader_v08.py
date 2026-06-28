"""Combined fixture record loader for Omega absorb v0.8."""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

from .poly_public_adapters import ExpertiseLikeAdapter, PolyPublieLikeAdapter


def combine_fixture_records(
    polypublie_like: Iterable[Dict[str, object]] = (),
    expertise_like: Iterable[Dict[str, object]] = (),
) -> Tuple[Dict[str, object], ...]:
    poly_records = PolyPublieLikeAdapter().normalize(polypublie_like)
    expertise_records = ExpertiseLikeAdapter().normalize(expertise_like)
    return tuple(poly_records + expertise_records)


def demo_combined_fixture_records() -> Tuple[Dict[str, object], ...]:
    return combine_fixture_records(
        polypublie_like=(
            {
                "identifier": "v08-poly-sensor",
                "dc.title": "Sensor uncertainty course lab fixture",
                "dc.creator": ["Professor Demo"],
                "dc.date": 2026,
                "dc.subject": ["sensors", "uncertainty", "signals"],
                "division": ["genie physique", "genie electrique"],
                "directors": ["Professor Demo"],
                "claims": ["Sensor uncertainty can seed a course lab."],
                "methods": ["FFT", "uncertainty estimation"],
                "limitations": ["demo record"],
            },
        ),
        expertise_like=(
            {
                "id": "v08-expertise-energy",
                "name": "Professor Energy Demo",
                "expertise": ["energy", "control", "model reduction"],
                "department": ["genie electrique", "genie mecanique"],
                "methods": ["control simulation", "reduced model"],
                "claims": ["Energy expertise can seed project packets."],
            },
        ),
    )
