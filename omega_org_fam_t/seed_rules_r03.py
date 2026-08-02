"""Small reviewed seed surface for numeric family-level spectral rules.

Ranges are broad pedagogical/engineering seeds and require provenance expansion
before scientific use. They are deliberately not a comprehensive spectral DB.
"""
from __future__ import annotations

from .spectral_evidence import BandRange, NumericSpectralRule

SEED_RULES = (
    NumericSpectralRule("ftir-alcohol-r03", "alcohol_phenol", "ftir", (
        BandRange("O-H stretch", 3000, 3700, 1.4), BandRange("C-O stretch", 1000, 1300, 1.0)),
        (BandRange("C-H stretch", 2800, 3100, 0.3),), (BandRange("no oxygen control", 5000, 5100, 0.5),)),
    NumericSpectralRule("raman-alcohol-r03", "alcohol_phenol", "raman", (
        BandRange("C-O mode", 900, 1300, 1.0),), (BandRange("C-C mode", 700, 1200, 0.3),)),
    NumericSpectralRule("ftir-carbonyl-r03", "aldehyde_ketone", "ftir", (
        BandRange("C=O stretch", 1650, 1800, 1.5),), (BandRange("aldehydic C-H", 2700, 2900, 0.5),)),
    NumericSpectralRule("ftir-acid-r03", "carboxylic_acid", "ftir", (
        BandRange("acid C=O", 1680, 1780, 1.3), BandRange("acid O-H", 2400, 3400, 1.2))),
    NumericSpectralRule("ftir-ester-r03", "ester_anhydride", "ftir", (
        BandRange("ester C=O", 1700, 1800, 1.3), BandRange("C-O", 1000, 1350, 0.9))),
    NumericSpectralRule("ftir-amide-r03", "amide_imide", "ftir", (
        BandRange("amide I", 1600, 1700, 1.3), BandRange("amide II", 1480, 1580, 0.9)),
        (BandRange("N-H", 3100, 3500, 0.5),)),
    NumericSpectralRule("raman-nitrile-r03", "nitrile_isocyanate", "raman", (
        BandRange("triple-bond region", 2100, 2300, 1.4),)),
    NumericSpectralRule("ftir-amine-r03", "amine_imine", "ftir", (
        BandRange("N-H/C-N family", 1000, 1350, 0.8),), (BandRange("N-H stretch", 3200, 3500, 0.8),)),
    NumericSpectralRule("ftir-sulfone-r03", "sulfoxide_sulfone", "ftir", (
        BandRange("S=O region", 1000, 1400, 1.2),)),
    NumericSpectralRule("ftir-organohalogen-r03", "organohalogen", "ftir", (
        BandRange("C-X region", 450, 850, 1.0),)),
)
