"""Controlled vocabularies for Ω-ORG-FAM-T.

These labels describe family-space coordinates, not certified molecules.
Vocabularies are tuples for deterministic ordering and may be replaced by
reviewed external registries at runtime.
"""
from __future__ import annotations

SKELETONS = (
    "acyclic_linear",
    "acyclic_branched",
    "monocyclic_aliphatic",
    "fused_polycyclic",
    "bridged_polycyclic",
    "spirocyclic",
    "monocyclic_aromatic",
    "fused_aromatic",
    "heterocyclic_saturated",
    "heteroaromatic",
    "macrocyclic",
    "cage",
    "polymeric_linear",
    "polymeric_crosslinked",
    "dendritic",
    "conjugated_backbone",
)

FUNCTIONAL_FAMILIES = (
    "hydrocarbon",
    "alkene_alkyne",
    "alcohol_phenol",
    "ether_epoxide",
    "aldehyde_ketone",
    "carboxylic_acid",
    "ester_anhydride",
    "amide_imide",
    "amine_imine",
    "nitrile_isocyanate",
    "thiol_sulfide",
    "sulfoxide_sulfone",
    "organohalogen",
    "organophosphorus",
    "organosilicon",
    "multifunctional_mixed",
)

ELECTRONIC_CLASSES = (
    "saturated_sigma",
    "isolated_pi",
    "conjugated_pi",
    "aromatic_delocalized",
    "electron_rich_donor",
    "electron_poor_acceptor",
    "push_pull_charge_transfer",
    "radical_or_open_shell",
)

REACTION_ARCHETYPES = (
    "substitution",
    "addition",
    "elimination",
    "oxidation_reduction",
    "condensation_hydrolysis",
    "cyclization_ring_opening",
    "polymerization_depolymerization",
    "rearrangement_fragmentation",
)

STEREO_CLASSES = (
    "achiral_or_unspecified",
    "central_chirality",
    "geometric_e_z",
    "axial_planar_or_topological",
)

ENVIRONMENTS = ("gas_phase", "neat_or_liquid", "solid_or_crystalline", "solution_or_interface")

SPECTRAL_MODALITIES = ("ftir", "raman", "nmr", "mass_spectrometry", "uv_visible")

OAK_STATUSES = (
    "candidate_cell_unvalidated",
    "structurally_compatible",
    "multimodal_evidence",
    "reference_confirmed",
)

FUNCTIONAL_MARKERS = {
    "hydrocarbon": ("C-C/C-H framework",),
    "alkene_alkyne": ("pi-bond mode", "unsaturation marker"),
    "alcohol_phenol": ("O-H environment", "C-O mode"),
    "ether_epoxide": ("C-O-C mode",),
    "aldehyde_ketone": ("carbonyl mode",),
    "carboxylic_acid": ("carbonyl mode", "acidic O-H environment"),
    "ester_anhydride": ("carbonyl mode", "acyl-oxygen mode"),
    "amide_imide": ("amide carbonyl mode", "C-N coupling"),
    "amine_imine": ("N-H/C-N environment",),
    "nitrile_isocyanate": ("cumulene_or_triple-bond region",),
    "thiol_sulfide": ("sulfur-containing mode",),
    "sulfoxide_sulfone": ("S-O environment",),
    "organohalogen": ("carbon-halogen region",),
    "organophosphorus": ("phosphorus-containing mode",),
    "organosilicon": ("silicon-containing mode",),
    "multifunctional_mixed": ("multiple_functional_regions",),
}

# Rules are intentionally conservative. They flag tensions in family-space
# templates and do not claim that every non-flagged cell is chemically viable.
INCOMPATIBILITY_RULES = (
    ("saturated_sigma", "alkene_alkyne", "saturation_conflicts_with_explicit_pi_family"),
    ("saturated_sigma", "conjugated_backbone", "saturation_conflicts_with_conjugated_skeleton"),
    ("aromatic_delocalized", "acyclic_linear", "aromaticity_requires_cyclic_or_extended_context"),
    ("aromatic_delocalized", "acyclic_branched", "aromaticity_requires_cyclic_or_extended_context"),
    ("geometric_e_z", "monocyclic_aromatic", "e_z_label_needs_specific_non_aromatic_double_bond_context"),
)
