from __future__ import annotations

from .genome import SolidGenome
from .models import (
    BondClass, BondContribution, CompositionComponent, DefectKind, DefectRecord,
    Dimensionality, EpistemicStatus, InterfaceRecord, OrderClass, PhaseRecord,
    PropertyDomain, PropertyRecord, Quantity,
)
from .archetypes_base import MODEL_STATUS, REFERENCE_STATUS, _p, _phase, _q

def two_dimensional_material() -> SolidGenome:
    return SolidGenome(
        identifier="archetype-two-dimensional-layer",
        name="Two-dimensional covalent layer archetype",
        family="2D material",
        composition=(CompositionComponent("C", 1.0),),
        bonds=(
            BondContribution(BondClass.COVALENT, 0.96),
            BondContribution(BondClass.MOLECULAR, 0.04, note="interlayer/substrate coupling channel"),
        ),
        order=OrderClass.PERIODIC_CRYSTAL,
        dimensionality=Dimensionality.TWO_D,
        phases=(_phase("hexagonal-monolayer", 1.0, OrderClass.PERIODIC_CRYSTAL, space_group="P6/mmm"),),
        defects=(
            DefectRecord(
                DefectKind.VACANCY,
                density=_q(1e12, "m^-2"),
                mobility=0.05,
                criticality=0.45,
                function="scattering and chemical activity center",
            ),
            DefectRecord(
                DefectKind.GRAIN_BOUNDARY,
                density=_q(1e5, "m^-1"),
                criticality=0.5,
                function="transport barrier or functional line defect",
            ),
        ),
        interfaces=(
            InterfaceRecord(
                "layer-substrate",
                ("hexagonal-monolayer", "substrate"),
                thickness=_q(0.34e-9, "m"),
                energy=_q(0.4, "J/m^2"),
            ),
        ),
        properties=(
            _p("areal_density", PropertyDomain.GEOMETRIC, 7.6e-7, "kg/m^2", uncertainty=5e-8),
            _p("in_plane_young_modulus", PropertyDomain.MECHANICAL, 1.0e12, "Pa", uncertainty=1.5e11),
            _p("sheet_conductance", PropertyDomain.ELECTRICAL, 1e-3, "S", uncertainty=5e-4),
        ),
        geometry={"porosity": 0.0, "hierarchy_levels": 3, "thickness_m": 0.34e-9},
        process=({"name": "chemical_vapor_deposition_or_exfoliation"}, {"name": "transfer"}),
        applications=("sensor", "transparent conductor candidate", "nanoelectronic channel"),
        risks=("contamination", "wrinkling", "substrate coupling", "grain-boundary variability"),
        next_experiments=("Map Raman strain/doping and four-probe sheet conductance.",),
        status=MODEL_STATUS,
    )


def architected_lattice() -> SolidGenome:
    return SolidGenome(
        identifier="archetype-architected-lattice",
        name="Fractal-mycelial architected lattice archetype",
        family="architected material/metamaterial",
        composition=(CompositionComponent("base_solid", 1.0),),
        bonds=(BondContribution(BondClass.MIXED, 1.0, note="Effective structural connectivity channel"),),
        order=OrderClass.HIERARCHICAL,
        phases=(_phase("load_bearing_lattice", 1.0, OrderClass.HIERARCHICAL),),
        defects=(
            DefectRecord(
                DefectKind.PORE,
                density=_q(0.82, "volume_fraction"),
                geometry={"topology": "hierarchical_open_cell"},
                criticality=0.35,
                function="mass reduction and transport channel",
            ),
            DefectRecord(
                DefectKind.RESIDUAL_STRESS,
                criticality=0.4,
                function="manufacturing history",
            ),
            DefectRecord(
                DefectKind.OTHER,
                geometry={"type": "strut_diameter_variability"},
                criticality=0.55,
                function="geometric imperfection",
            ),
        ),
        properties=(
            _p("relative_density", PropertyDomain.GEOMETRIC, 0.18, "fraction", uncertainty=0.02),
            _p("effective_young_modulus", PropertyDomain.MECHANICAL, 1.8e9, "Pa", uncertainty=5e8),
            _p("specific_energy_absorption", PropertyDomain.MECHANICAL, 15e3, "J/kg", uncertainty=5e3),
            _p("permeability", PropertyDomain.CHEMICAL, 8e-9, "m^2", uncertainty=3e-9),
        ),
        geometry={
            "porosity": 0.82,
            "hierarchy_levels": 7,
            "topology": "hexagonal-fractal-mycelial",
            "unit_cell_m": 2e-3,
            "minimum_feature_m": 1e-4,
            "periodic": False,
        },
        process=(
            {"name": "topology_generation"},
            {"name": "manufacturability_filter"},
            {"name": "additive_manufacturing"},
            {"name": "inspection"},
        ),
        applications=("energy absorption", "heat exchange", "lightweight structure"),
        risks=("buckling", "manufacturing defects", "inspection difficulty", "model-form uncertainty"),
        assumptions=(
            "Effective properties are conceptual seeds and require geometry-specific simulation and coupons.",
        ),
        next_experiments=(
            "Print calibration coupons across feature sizes.",
            "Compare compression response to Gibson-Ashby and finite-element baselines.",
        ),
        status=EpistemicStatus.PROPOSED_DESIGN,
    )


