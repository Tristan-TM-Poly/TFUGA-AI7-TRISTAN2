"""Omega-CQC-TFTS-CRFT 8x8 synergy matrix.

Generates the 64 research families created by crossing geometry classes with
physical regimes. This is a roadmap generator, not a physics solver.

Run:
    python examples/omega_cqc_synergy_matrix.py
"""

from __future__ import annotations

from dataclasses import dataclass


GEOMETRIES = [
    ("cubic", "high isotropy, high degeneracy, natural 3D baseline"),
    ("tetragonal", "one privileged axis, directional tuning"),
    ("hexagonal", "sixfold planar order, valley-like channels"),
    ("trigonal_rhombohedral", "chirality potential and rotational coupling"),
    ("orthorhombic", "three independent axes, natural stretch"),
    ("monoclinic_triclinic", "maximal anisotropy and nondegenerate spectra"),
    ("quasi_crystalline", "non-periodic rich mode density"),
    ("semi_crystalline_defected", "controlled localizations and symmetry breaking"),
]

REGIMES = [
    ("absorber", "maximize A(omega) with loss and impedance matching"),
    ("selective_emitter", "shape epsilon_T(omega) in a useful band"),
    ("antenna", "radiate efficiently with compact multi-scale aperture"),
    ("near_field_sensor", "maximize LDOS and useful local coupling"),
    ("bandgap", "create and use localized states in a gap"),
    ("plasmonic_metamaterial", "surface hot spots and strong absorption"),
    ("superconducting_josephson", "flux quantization and Josephson response"),
    ("topological_nonreciprocal", "robust modes or direction-dependent scattering"),
]


@dataclass(frozen=True)
class Family:
    index: int
    geometry: str
    regime: str
    thesis: str
    oak_gate: str
    priority: str


def priority_for(geometry: str, regime: str) -> str:
    """Heuristic roadmap priority, not proof of feasibility."""
    if regime in {"absorber", "selective_emitter", "antenna"} and geometry in {
        "cubic",
        "tetragonal",
        "hexagonal",
        "orthorhombic",
    }:
        return "Tier 1: simulate/prototype first"
    if regime in {"near_field_sensor", "bandgap", "plasmonic_metamaterial"}:
        return "Tier 2: needs EM solver and materials"
    return "Tier 3: advanced / OAK strict"


def oak_gate_for(regime: str) -> str:
    gates = {
        "absorber": "A_T(omega) > A_control(omega) at matched thickness/mass/volume",
        "selective_emitter": "epsilon_T(omega) improves target-band emission at controlled T",
        "antenna": "G_realized, bandwidth, efficiency, or compactness beats control",
        "near_field_sensor": "LDOS or SNR improves with useful outcoupling",
        "bandgap": "localized state exists in gap and has controlled eta_out",
        "plasmonic_metamaterial": "hot spots improve useful signal without loss domination",
        "superconducting_josephson": "Delta, Ic(B), R(T,B), flux signatures survive fractalization",
        "topological_nonreciprocal": "nu != 0 or S_ij != S_ji with gap/robustness/energy balance",
    }
    return gates[regime]


def generate_families() -> list[Family]:
    families: list[Family] = []
    index = 1
    for geometry, geometry_note in GEOMETRIES:
        for regime, regime_note in REGIMES:
            thesis = f"{geometry} geometry ({geometry_note}) used as {regime} regime ({regime_note})."
            families.append(
                Family(
                    index=index,
                    geometry=geometry,
                    regime=regime,
                    thesis=thesis,
                    oak_gate=oak_gate_for(regime),
                    priority=priority_for(geometry, regime),
                )
            )
            index += 1
    return families


def main() -> None:
    for family in generate_families():
        print(
            f"{family.index:02d}. {family.geometry} x {family.regime}\n"
            f"    thesis: {family.thesis}\n"
            f"    OAK: {family.oak_gate}\n"
            f"    priority: {family.priority}\n"
        )


if __name__ == "__main__":
    main()
