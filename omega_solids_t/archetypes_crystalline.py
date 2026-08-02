from __future__ import annotations

from .genome import SolidGenome
from .models import (
    BondClass, BondContribution, CompositionComponent, DefectKind, DefectRecord,
    Dimensionality, EpistemicStatus, InterfaceRecord, OrderClass, PhaseRecord,
    PropertyDomain, PropertyRecord, Quantity,
)
from .archetypes_base import MODEL_STATUS, REFERENCE_STATUS, _p, _phase, _q

def metallic_crystal() -> SolidGenome:
    return SolidGenome(
        identifier="archetype-metallic-crystal-fcc",
        name="FCC metallic crystal archetype",
        family="metal/alloy",
        composition=(CompositionComponent("Al", 1.0, role="matrix"),),
        bonds=(BondContribution(BondClass.METALLIC, 1.0),),
        order=OrderClass.PERIODIC_CRYSTAL,
        phases=(_phase("fcc-alpha", 1.0, OrderClass.PERIODIC_CRYSTAL, space_group="Fm-3m"),),
        defects=(
            DefectRecord(
                DefectKind.DISLOCATION,
                density=_q(1e12, "m^-2", status=MODEL_STATUS),
                mobility=0.6,
                criticality=0.35,
                function="plastic deformation carrier",
            ),
            DefectRecord(
                DefectKind.VACANCY,
                density=_q(1e-6, "fraction", status=MODEL_STATUS),
                mobility=0.2,
                criticality=0.1,
                function="diffusion mediator",
            ),
        ),
        properties=(
            _p("density", PropertyDomain.GEOMETRIC, 2700, "kg/m^3", uncertainty=30),
            _p("young_modulus", PropertyDomain.MECHANICAL, 69e9, "Pa", uncertainty=3e9),
            _p("poisson_ratio", PropertyDomain.MECHANICAL, 0.33, "1", uncertainty=0.02),
            _p("thermal_conductivity", PropertyDomain.THERMAL, 205, "W/(m*K)", uncertainty=20),
            _p("electrical_conductivity", PropertyDomain.ELECTRICAL, 3.5e7, "S/m", uncertainty=4e6),
        ),
        geometry={"porosity": 0.0, "hierarchy_levels": 2, "grain_size_m": 2e-5},
        process=(
            {"name": "melting", "temperature_K": 1000},
            {"name": "casting", "cooling_rate_K_s": 10},
            {"name": "annealing", "temperature_K": 650, "duration_s": 3600},
        ),
        applications=("structural component", "thermal conductor"),
        risks=("fatigue", "corrosion", "creep at elevated temperature"),
        assumptions=("Reference values are illustrative and not alloy-grade certification."),
        next_experiments=("Measure texture-resolved stiffness.", "Quantify fatigue crack growth."),
        status=MODEL_STATUS,
    )


def ionic_crystal() -> SolidGenome:
    return SolidGenome(
        identifier="archetype-ionic-crystal-rocksalt",
        name="Rock-salt ionic crystal archetype",
        family="ceramic/ionic crystal",
        composition=(
            CompositionComponent("Na", 0.5, role="cation"),
            CompositionComponent("Cl", 0.5, role="anion"),
        ),
        bonds=(BondContribution(BondClass.IONIC, 0.92), BondContribution(BondClass.COVALENT, 0.08)),
        order=OrderClass.PERIODIC_CRYSTAL,
        phases=(_phase("rocksalt", 1.0, OrderClass.PERIODIC_CRYSTAL, space_group="Fm-3m"),),
        defects=(
            DefectRecord(
                DefectKind.VACANCY,
                density=_q(1e-7, "fraction"),
                mobility=0.25,
                criticality=0.2,
                function="ionic transport and stoichiometry deviation",
            ),
            DefectRecord(
                DefectKind.CRACK,
                geometry={"half_length_m": 2e-6},
                mobility=0.0,
                criticality=0.6,
                function="brittle failure initiator",
            ),
        ),
        properties=(
            _p("density", PropertyDomain.GEOMETRIC, 2160, "kg/m^3", uncertainty=30),
            _p("young_modulus", PropertyDomain.MECHANICAL, 40e9, "Pa", uncertainty=5e9),
            _p("band_gap", PropertyDomain.OPTICAL, 8.5, "eV", uncertainty=0.8),
            _p("ionic_conductivity", PropertyDomain.IONIC, 1e-12, "S/m", uncertainty=8e-13),
        ),
        geometry={"porosity": 0.0, "hierarchy_levels": 1},
        process=({"name": "solution_growth"}, {"name": "drying"}),
        risks=("brittle fracture", "humidity sensitivity"),
        assumptions=("The archetype represents bond/order logic, not a certified NaCl dataset."),
        next_experiments=("Measure defect-assisted ionic transport versus temperature.",),
        status=MODEL_STATUS,
    )


def covalent_network() -> SolidGenome:
    return SolidGenome(
        identifier="archetype-covalent-network-diamond",
        name="Tetrahedral covalent network archetype",
        family="covalent ceramic",
        composition=(CompositionComponent("C", 1.0),),
        bonds=(BondContribution(BondClass.COVALENT, 1.0),),
        order=OrderClass.PERIODIC_CRYSTAL,
        phases=(_phase("diamond-cubic", 1.0, OrderClass.PERIODIC_CRYSTAL, space_group="Fd-3m"),),
        defects=(
            DefectRecord(
                DefectKind.VACANCY,
                density=_q(1e-9, "fraction"),
                mobility=0.01,
                criticality=0.3,
                function="electronic/optical center candidate",
            ),
            DefectRecord(
                DefectKind.SUBSTITUTION,
                density=_q(1e-6, "fraction"),
                criticality=0.2,
                function="dopant or color center",
            ),
        ),
        properties=(
            _p("density", PropertyDomain.GEOMETRIC, 3510, "kg/m^3", uncertainty=20),
            _p("young_modulus", PropertyDomain.MECHANICAL, 1.05e12, "Pa", uncertainty=8e10),
            _p("hardness", PropertyDomain.MECHANICAL, 70e9, "Pa", uncertainty=15e9),
            _p("thermal_conductivity", PropertyDomain.THERMAL, 1800, "W/(m*K)", uncertainty=400),
            _p("band_gap", PropertyDomain.OPTICAL, 5.5, "eV", uncertainty=0.3),
        ),
        geometry={"porosity": 0.0, "hierarchy_levels": 1},
        process=({"name": "high_pressure_high_temperature_or_cvd"},),
        applications=("abrasive", "thermal spreader", "optical platform"),
        risks=("brittleness", "synthesis cost", "defect sensitivity"),
        next_experiments=("Map defect-specific optical transitions.",),
        status=MODEL_STATUS,
    )


def semiconductor_crystal() -> SolidGenome:
    return SolidGenome(
        identifier="archetype-semiconductor-doped-silicon",
        name="Doped crystalline semiconductor archetype",
        family="semiconductor",
        composition=(
            CompositionComponent("Si", 0.999999, role="host"),
            CompositionComponent("P", 0.000001, role="donor"),
        ),
        bonds=(BondContribution(BondClass.COVALENT, 0.98), BondContribution(BondClass.MIXED, 0.02)),
        order=OrderClass.PERIODIC_CRYSTAL,
        phases=(_phase("diamond-cubic-Si", 1.0, OrderClass.PERIODIC_CRYSTAL, space_group="Fd-3m"),),
        defects=(
            DefectRecord(
                DefectKind.SUBSTITUTION,
                density=_q(5e20, "m^-3"),
                mobility=0.0,
                criticality=0.25,
                function="donor state",
            ),
            DefectRecord(
                DefectKind.ELECTRONIC,
                density=_q(1e15, "m^-3"),
                criticality=0.4,
                function="trap/recombination center",
            ),
        ),
        interfaces=(
            InterfaceRecord(
                "native-oxide-interface",
                ("diamond-cubic-Si", "SiO2"),
                thickness=_q(2e-9, "m"),
                energy=_q(0.5, "J/m^2"),
                properties={"interface_trap_density": _q(1e15, "m^-2")},
            ),
        ),
        properties=(
            _p("density", PropertyDomain.GEOMETRIC, 2330, "kg/m^3", uncertainty=10),
            _p("young_modulus", PropertyDomain.MECHANICAL, 130e9, "Pa", uncertainty=15e9),
            _p("band_gap", PropertyDomain.OPTICAL, 1.12, "eV", uncertainty=0.03),
            _p("electron_mobility", PropertyDomain.ELECTRICAL, 0.14, "m^2/(V*s)", uncertainty=0.04),
            _p("thermal_conductivity", PropertyDomain.THERMAL, 145, "W/(m*K)", uncertainty=20),
        ),
        geometry={"porosity": 0.0, "hierarchy_levels": 3, "wafer_orientation": "(100)"},
        process=(
            {"name": "single_crystal_growth"},
            {"name": "wafering"},
            {"name": "doping", "species": "P"},
            {"name": "oxidation"},
        ),
        risks=("contamination", "oxide trap states", "thermal budget sensitivity"),
        next_experiments=("Extract carrier density and mobility by Hall measurement.",),
        status=MODEL_STATUS,
    )


