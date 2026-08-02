from __future__ import annotations

from .genome import SolidGenome
from .models import (
    BondClass, BondContribution, CompositionComponent, DefectKind, DefectRecord,
    Dimensionality, EpistemicStatus, InterfaceRecord, OrderClass, PhaseRecord,
    PropertyDomain, PropertyRecord, Quantity,
)
from .archetypes_base import MODEL_STATUS, REFERENCE_STATUS, _p, _phase, _q

def fiber_composite() -> SolidGenome:
    return SolidGenome(
        identifier="archetype-fiber-matrix-composite",
        name="Aligned fiber-matrix composite archetype",
        family="composite",
        composition=(
            CompositionComponent("carbon_fiber", 0.60, basis="volume", role="reinforcement"),
            CompositionComponent("epoxy", 0.40, basis="volume", role="matrix"),
        ),
        bonds=(
            BondContribution(BondClass.COVALENT, 0.45),
            BondContribution(BondClass.POLYMERIC, 0.35),
            BondContribution(BondClass.MOLECULAR, 0.10),
            BondContribution(BondClass.MIXED, 0.10),
        ),
        order=OrderClass.HIERARCHICAL,
        phases=(
            _phase("fiber", 0.60, OrderClass.HIERARCHICAL),
            _phase("matrix", 0.40, OrderClass.AMORPHOUS),
        ),
        interfaces=(
            InterfaceRecord(
                "fiber-matrix-interphase",
                ("fiber", "matrix"),
                thickness=_q(100e-9, "m"),
                energy=_q(0.3, "J/m^2"),
                properties={"interfacial_shear_strength": _q(50e6, "Pa")},
                defects=(
                    DefectRecord(
                        DefectKind.DELAMINATION,
                        criticality=0.7,
                        function="interface failure mode",
                    ),
                ),
            ),
        ),
        defects=(
            DefectRecord(DefectKind.PORE, density=_q(0.01, "volume_fraction"), criticality=0.5),
            DefectRecord(DefectKind.DELAMINATION, criticality=0.75, function="ply separation"),
            DefectRecord(DefectKind.CRACK, criticality=0.65, function="matrix cracking"),
        ),
        properties=(
            _p("density", PropertyDomain.GEOMETRIC, 1580, "kg/m^3", uncertainty=70),
            _p(
                "young_modulus",
                PropertyDomain.MECHANICAL,
                135e9,
                "Pa",
                uncertainty=15e9,
                tensor=((135e9, 0.0, 0.0), (0.0, 10e9, 0.0), (0.0, 0.0, 10e9)),
                note="Illustrative orthotropic stiffness projection.",
            ),
            _p("tensile_strength", PropertyDomain.MECHANICAL, 1.5e9, "Pa", uncertainty=3e8),
        ),
        geometry={
            "porosity": 0.01,
            "hierarchy_levels": 6,
            "fiber_orientation": [1.0, 0.0, 0.0],
            "layup": "unidirectional",
        },
        process=(
            {"name": "fiber_surface_treatment"},
            {"name": "layup"},
            {"name": "resin_infusion"},
            {"name": "cure", "temperature_K": 450},
        ),
        applications=("lightweight structure", "aerospace panel", "energy absorption"),
        risks=("delamination", "impact damage", "hidden porosity", "moisture uptake"),
        next_experiments=("Perform mode-I and mode-II interlaminar fracture tests.",),
        status=MODEL_STATUS,
    )


def porous_ceramic() -> SolidGenome:
    return SolidGenome(
        identifier="archetype-porous-ceramic",
        name="Hierarchical porous ceramic archetype",
        family="ceramic/architected",
        composition=(CompositionComponent("Al2O3", 1.0),),
        bonds=(BondContribution(BondClass.IONIC, 0.55), BondContribution(BondClass.COVALENT, 0.45)),
        order=OrderClass.HIERARCHICAL,
        phases=(_phase("alpha-alumina", 1.0, OrderClass.POLYCRYSTALLINE, space_group="R-3c"),),
        defects=(
            DefectRecord(
                DefectKind.PORE,
                density=_q(0.35, "volume_fraction"),
                geometry={"mean_radius_m": 20e-6, "connectivity": 0.8},
                criticality=0.55,
                function="transport and mass reduction",
            ),
            DefectRecord(
                DefectKind.GRAIN_BOUNDARY,
                density=_q(2e5, "m^-1"),
                criticality=0.35,
                function="sintering and fracture path",
            ),
            DefectRecord(
                DefectKind.CRACK,
                criticality=0.7,
                function="brittle failure initiator",
            ),
        ),
        properties=(
            _p("density", PropertyDomain.GEOMETRIC, 2500, "kg/m^3", uncertainty=150),
            _p("young_modulus", PropertyDomain.MECHANICAL, 80e9, "Pa", uncertainty=20e9),
            _p("thermal_conductivity", PropertyDomain.THERMAL, 8.0, "W/(m*K)", uncertainty=2.0),
            _p("permeability", PropertyDomain.CHEMICAL, 2e-12, "m^2", uncertainty=1e-12),
        ),
        geometry={
            "porosity": 0.35,
            "hierarchy_levels": 4,
            "pore_connectivity": 0.8,
            "pore_size_distribution": "bimodal",
        },
        process=(
            {"name": "powder_mixing"},
            {"name": "pore_former_addition"},
            {"name": "forming"},
            {"name": "sintering", "temperature_K": 1800},
        ),
        applications=("filtration", "thermal insulation", "catalyst support"),
        risks=("brittleness", "pore-size variability", "thermal shock"),
        next_experiments=("Tomographically quantify pore connectivity and critical flaws.",),
        status=MODEL_STATUS,
    )


def granular_solid() -> SolidGenome:
    return SolidGenome(
        identifier="archetype-granular-solid",
        name="Jammed granular solid archetype",
        family="granular",
        composition=(CompositionComponent("silica_grain", 1.0),),
        bonds=(
            BondContribution(BondClass.MOLECULAR, 0.15),
            BondContribution(BondClass.MIXED, 0.85, note="contact/friction network, not atomic bond fraction"),
        ),
        order=OrderClass.GRANULAR,
        phases=(_phase("jammed-contact-network", 1.0, OrderClass.GRANULAR),),
        defects=(
            DefectRecord(
                DefectKind.PORE,
                density=_q(0.38, "volume_fraction"),
                criticality=0.25,
                function="void network",
            ),
            DefectRecord(
                DefectKind.OTHER,
                geometry={"type": "force_chain_heterogeneity"},
                criticality=0.55,
                function="load-bearing force chain",
            ),
        ),
        properties=(
            _p("bulk_density", PropertyDomain.GEOMETRIC, 1600, "kg/m^3", uncertainty=150),
            _p("effective_young_modulus", PropertyDomain.MECHANICAL, 50e6, "Pa", uncertainty=30e6),
            _p("friction_angle", PropertyDomain.MECHANICAL, 32, "degree", uncertainty=4),
        ),
        geometry={
            "porosity": 0.38,
            "hierarchy_levels": 3,
            "grain_shape": "near_spherical",
            "coordination_number": 5.5,
        },
        process=(
            {"name": "pouring"},
            {"name": "compaction", "pressure_Pa": 1e6},
        ),
        history=({"name": "loading_cycles", "count": 0},),
        applications=("foundation medium", "powder handling", "granular damping"),
        risks=("liquefaction under vibration", "segregation", "localized shear band"),
        next_experiments=("Image force chains and calibrate contact-law parameters.",),
        status=MODEL_STATUS,
    )


