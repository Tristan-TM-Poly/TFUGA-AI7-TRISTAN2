"""Public research absorption utilities.

The absorber works on caller-provided public metadata records. It deliberately
avoids scraping or copying restricted full text. Full-text extraction belongs to
Rosette only when the source is open/licensed and source boundaries are kept.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from .research_atom import ResearchAtom, atom_from_public_record


@dataclass(frozen=True)
class AbsorptionReport:
    atoms: Tuple[ResearchAtom, ...]
    metadata_only_count: int
    metadata_plus_abstract_count: int
    warnings: Tuple[str, ...]
    next_action: str

    @property
    def total(self) -> int:
        return len(self.atoms)


def absorb_public_records(records: Iterable[Dict[str, object]]) -> AbsorptionReport:
    atoms = tuple(atom_from_public_record(record) for record in records)
    metadata_only_count = sum(atom.legal_absorption_level() == "metadata_only" for atom in atoms)
    metadata_plus_abstract_count = sum(atom.legal_absorption_level() == "metadata_plus_abstract" for atom in atoms)
    warnings = []
    for atom in atoms:
        if not atom.link:
            warnings.append(f"missing_link:{atom.atom_id}")
        if atom.oak and "no_evidence_attached" in atom.oak.warnings:
            warnings.append(f"low_evidence:{atom.atom_id}")
    return AbsorptionReport(
        atoms=atoms,
        metadata_only_count=metadata_only_count,
        metadata_plus_abstract_count=metadata_plus_abstract_count,
        warnings=tuple(warnings),
        next_action="build_professor_genomes_and_poly_research_twin",
    )


def demo_public_research_records() -> Tuple[Dict[str, object], ...]:
    return (
        {
            "atom_id": "demo-signal-sensor-2026",
            "title": "Signal processing for low-cost photonic sensors",
            "authors": ["Professor Demo", "Student Demo"],
            "year": 2026,
            "source": "public_demo_metadata",
            "link": "https://example.org/demo-signal-sensor",
            "abstract": "A demo record about signal processing, uncertainty, and sensor prototypes.",
            "keywords": ["signal processing", "sensors", "uncertainty", "photonics"],
            "departments": ["genie physique", "genie electrique", "genie logiciel"],
            "professors": ["Professor Demo"],
            "claims": ["Filtering improves interpretability under measured uncertainty."],
            "methods": ["FFT", "uncertainty estimation", "OAK residual audit"],
            "limitations": ["Synthetic demo metadata only."],
            "datasets": ["demo_sensor_dataset_stub"],
            "code_links": ["examples/omega_prof_poly_v02_demo.py"],
        },
        {
            "atom_id": "demo-battery-safety-2026",
            "title": "OAK-safe battery lab packet for teaching degradation",
            "authors": ["Professor Demo 2"],
            "year": 2026,
            "source": "public_demo_metadata",
            "link": "https://example.org/demo-battery-safety",
            "keywords": ["battery", "degradation", "teaching lab"],
            "departments": ["genie chimique", "genie electrique", "genie mecanique"],
            "professors": ["Professor Demo 2"],
            "claims": ["A simplified degradation lab can teach safe battery modeling."],
            "methods": ["reduced-order modeling", "thermal risk checklist"],
            "limitations": ["No hazardous cell manipulation."],
        },
    )
