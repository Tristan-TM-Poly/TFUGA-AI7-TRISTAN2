from __future__ import annotations

from .genome import SolidGenome
from .models import (
    BondClass, BondContribution, CompositionComponent, DefectKind, DefectRecord,
    Dimensionality, EpistemicStatus, InterfaceRecord, OrderClass, PhaseRecord,
    PropertyDomain, PropertyRecord, Quantity,
)
from .archetypes_base import MODEL_STATUS, REFERENCE_STATUS, _p, _phase, _q

def amorphous_glass() -> SolidGenome:
    return SolidGenome(
        identifier="archetype-amorphous-silicate-glass",
        name="Amorphous silicate glass archetype",
        family="glass",
        composition=(
            CompositionComponent("SiO2", 0.72, basis="mass", role="network former"),
            CompositionComponent("Na2O", 0.14, basis="mass", role="modifier"),
            CompositionComponent("CaO", 0.14, basis="mass", role="stabilizer"),
        ),
        bonds=(
            BondContribution(BondClass.COVALENT, 0.65),
            BondContribution(BondClass.IONIC, 0.30),
            BondContribution(BondClass.MIXED, 0.05),
        ),
        order=OrderClass.AMORPHOUS,
        phases=(_phase("amorphous-network", 1.0, OrderClass.AMORPHOUS),),
        defects=(
            DefectRecord(
                DefectKind.CHEMICAL_DISORDER,
                criticality=0.25,
                function="intrinsic topological disorder",
            ),
            DefectRecord(
                DefectKind.CRACK,
                geometry={"surface_flaw_m": 5e-6},
                criticality=0.8,
                function="strength-limiting flaw",
            ),
            DefectRecord(
                DefectKind.RESIDUAL_STRESS,
                criticality=0.45,
                function="thermal-history memory",
            ),
        ),
        properties=(
            _p("density", PropertyDomain.GEOMETRIC, 2500, "kg/m^3", uncertainty=80),
            _p("young_modulus", PropertyDomain.MECHANICAL, 70e9, "Pa", uncertainty=8e9),
            _p("glass_transition_temperature", PropertyDomain.THERMAL, 830, "K", uncertainty=30),
            _p("refractive_index", PropertyDomain.OPTICAL, 1.52, "1", uncertainty=0.03),
        ),
        geometry={"porosity": 0.001, "hierarchy_levels": 2},
        process=(
            {"name": "melting", "temperature_K": 1700},
            {"name": "quenching", "cooling_rate_K_s": 50},
            {"name": "annealing", "purpose": "residual_stress_relief"},
        ),
        risks=("brittle fracture", "thermal shock", "surface flaw sensitivity"),
        next_experiments=("Measure fictive temperature and residual stress profile.",),
        status=MODEL_STATUS,
    )


def amorphous_polymer() -> SolidGenome:
    return SolidGenome(
        identifier="archetype-amorphous-polymer",
        name="Amorphous thermoplastic archetype",
        family="polymer",
        composition=(CompositionComponent("polymer_repeat_unit", 1.0, basis="molar"),),
        bonds=(
            BondContribution(BondClass.POLYMERIC, 0.75),
            BondContribution(BondClass.MOLECULAR, 0.25),
        ),
        order=OrderClass.AMORPHOUS,
        phases=(_phase("amorphous-chain-network", 1.0, OrderClass.AMORPHOUS),),
        defects=(
            DefectRecord(
                DefectKind.CHEMICAL_DISORDER,
                criticality=0.15,
                function="chain packing heterogeneity",
            ),
            DefectRecord(
                DefectKind.PORE,
                density=_q(0.002, "volume_fraction"),
                criticality=0.3,
                function="processing void",
            ),
        ),
        properties=(
            _p("density", PropertyDomain.GEOMETRIC, 1180, "kg/m^3", uncertainty=40),
            _p("young_modulus", PropertyDomain.MECHANICAL, 2.5e9, "Pa", uncertainty=8e8),
            _p("glass_transition_temperature", PropertyDomain.THERMAL, 370, "K", uncertainty=15),
            _p("thermal_conductivity", PropertyDomain.THERMAL, 0.2, "W/(m*K)", uncertainty=0.05),
        ),
        geometry={"porosity": 0.002, "hierarchy_levels": 3, "chain_orientation": "isotropic"},
        process=(
            {"name": "polymerization"},
            {"name": "melt_processing"},
            {"name": "cooling", "rate_dependent": True},
        ),
        history=({"name": "physical_ageing", "state": "unknown"},),
        risks=("creep", "solvent uptake", "UV ageing", "rate dependence"),
        next_experiments=("Run dynamic mechanical analysis across frequency and temperature.",),
        status=MODEL_STATUS,
    )


def semicrystalline_polymer() -> SolidGenome:
    return SolidGenome(
        identifier="archetype-semicrystalline-polymer",
        name="Semicrystalline polymer archetype",
        family="polymer",
        composition=(CompositionComponent("polyolefin_repeat_unit", 1.0),),
        bonds=(
            BondContribution(BondClass.POLYMERIC, 0.72),
            BondContribution(BondClass.MOLECULAR, 0.28),
        ),
        order=OrderClass.SEMICRYSTALLINE,
        phases=(
            _phase("crystalline-lamellae", 0.55, OrderClass.PERIODIC_CRYSTAL),
            _phase("amorphous-tie-network", 0.45, OrderClass.AMORPHOUS),
        ),
        interfaces=(
            InterfaceRecord(
                "lamella-amorphous-interface",
                ("crystalline-lamellae", "amorphous-tie-network"),
                thickness=_q(5e-9, "m"),
                energy=_q(0.05, "J/m^2"),
            ),
        ),
        defects=(
            DefectRecord(
                DefectKind.CHEMICAL_DISORDER,
                criticality=0.2,
                function="branching/sequence disorder",
            ),
            DefectRecord(
                DefectKind.DELAMINATION,
                criticality=0.45,
                function="lamellar separation candidate",
            ),
        ),
        properties=(
            _p("density", PropertyDomain.GEOMETRIC, 940, "kg/m^3", uncertainty=30),
            _p("young_modulus", PropertyDomain.MECHANICAL, 1.2e9, "Pa", uncertainty=5e8),
            _p("melting_temperature", PropertyDomain.THERMAL, 405, "K", uncertainty=12),
            _p("crystallinity", PropertyDomain.GEOMETRIC, 0.55, "fraction", uncertainty=0.08),
        ),
        geometry={"porosity": 0.001, "hierarchy_levels": 5, "spherulitic": True},
        process=(
            {"name": "melt_processing"},
            {"name": "controlled_cooling", "controls": "crystallinity"},
            {"name": "drawing", "optional": True},
        ),
        risks=("creep", "oxidative ageing", "anisotropy from processing"),
        next_experiments=("Correlate DSC crystallinity with SAXS/WAXS morphology.",),
        status=MODEL_STATUS,
    )


