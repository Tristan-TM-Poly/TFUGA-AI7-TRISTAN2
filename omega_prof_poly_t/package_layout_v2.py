"""Omega Absorb OS v2 package layout model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class LayoutSection:
    name: str
    path: str
    purpose: str
    next_action: str


@dataclass(frozen=True)
class PackageLayoutV2:
    sections: Tuple[LayoutSection, ...]
    next_action: str


def build_package_layout_v2() -> PackageLayoutV2:
    sections = (
        LayoutSection("adapters", "omega_prof_poly_t/adapters", "source routing and normalization", "map_existing_modules"),
        LayoutSection("sources", "omega_prof_poly_t/sources", "source policies and schemas", "map_existing_modules"),
        LayoutSection("atoms", "omega_prof_poly_t/atoms", "ResearchAtom core", "map_existing_modules"),
        LayoutSection("claims", "omega_prof_poly_t/claims", "ClaimGraph and OAK claim tests", "map_existing_modules"),
        LayoutSection("methods", "omega_prof_poly_t/methods", "MethodGraph and reproduction packets", "map_existing_modules"),
        LayoutSection("tensors", "omega_prof_poly_t/tensors", "ProfessorTensor and weights", "map_existing_modules"),
        LayoutSection("twin", "omega_prof_poly_t/twin", "PolyResearchTwin strategy engines", "map_existing_modules"),
        LayoutSection("actions", "omega_prof_poly_t/actions", "top actions and local packets", "map_existing_modules"),
        LayoutSection("oak", "omega_prof_poly_t/oak", "OAK manifests and ledgers", "map_existing_modules"),
        LayoutSection("mminus", "omega_prof_poly_t/mminus", "memory minus rules", "map_existing_modules"),
        LayoutSection("github_packets", "omega_prof_poly_t/github_packets", "GitHub work bundles", "map_existing_modules"),
        LayoutSection("reports", "omega_prof_poly_t/reports_v2", "report atlas and writers", "map_existing_modules"),
    )
    return PackageLayoutV2(sections=sections, next_action="compile_v2_migration_packet")


def render_package_layout_v2(layout: PackageLayoutV2 | None = None) -> str:
    layout = layout or build_package_layout_v2()
    lines = ["# Omega Absorb Package Layout v2", "", "section | path | purpose", "--- | --- | ---"]
    for section in layout.sections:
        lines.append(f"{section.name} | `{section.path}` | {section.purpose}")
    return "\n".join(lines) + "\n"
