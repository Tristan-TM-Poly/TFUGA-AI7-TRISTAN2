"""Deterministic, streaming construction of organic-family space."""
from __future__ import annotations

import itertools
from dataclasses import replace
from collections.abc import Iterable, Iterator, Sequence

from .models import EvidenceTemplate, FamilyCell, FamilyCoordinate
from .oak import compatibility_score, contradictions_for
from .vocabularies import (
    ELECTRONIC_CLASSES,
    ENVIRONMENTS,
    FUNCTIONAL_FAMILIES,
    FUNCTIONAL_MARKERS,
    REACTION_ARCHETYPES,
    SKELETONS,
    SPECTRAL_MODALITIES,
    STEREO_CLASSES,
)


def base_coordinates(
    skeletons: Sequence[str] = SKELETONS,
    functional_families: Sequence[str] = FUNCTIONAL_FAMILIES,
    electronic_classes: Sequence[str] = ELECTRONIC_CLASSES,
    reaction_archetypes: Sequence[str] = REACTION_ARCHETYPES,
    stereo_classes: Sequence[str] = STEREO_CLASSES,
    environments: Sequence[str] = ENVIRONMENTS,
) -> Iterator[FamilyCoordinate]:
    """Yield the complete default 262,144-cell lattice without materializing it."""
    for values in itertools.product(
        skeletons,
        functional_families,
        electronic_classes,
        reaction_archetypes,
        stereo_classes,
        environments,
    ):
        yield FamilyCoordinate(*values)


def family_cells(
    coordinates: Iterable[FamilyCoordinate] | None = None,
    *,
    start_index: int = 0,
) -> Iterator[FamilyCell]:
    source = base_coordinates() if coordinates is None else coordinates
    for offset, coordinate in enumerate(source):
        index = start_index + offset
        contradictions = contradictions_for(coordinate)
        markers = tuple(FUNCTIONAL_MARKERS[coordinate.functional_family])
        yield FamilyCell(
            id=f"ORG-FAM-{index:08d}",
            coordinate=coordinate,
            compatibility_score=compatibility_score(coordinate),
            contradictions=contradictions,
            spectral_markers=markers,
            evidence_ids=(
                f"ORG-EVD-{3 * index:09d}",
                f"ORG-EVD-{3 * index + 1:09d}",
                f"ORG-EVD-{3 * index + 2:09d}",
            ),
        )


def evidence_templates(cells: Iterable[FamilyCell]) -> Iterator[EvidenceTemplate]:
    for index, cell in enumerate(cells):
        modality = SPECTRAL_MODALITIES[index % len(SPECTRAL_MODALITIES)]
        yield EvidenceTemplate(
            id=cell.evidence_ids[0],
            family_id=cell.id,
            kind="positive_bundle",
            modality=modality,
            expected=cell.spectral_markers,
            contradiction_if=(),
        )
        yield EvidenceTemplate(
            id=cell.evidence_ids[1],
            family_id=cell.id,
            kind="negative_control",
            modality=modality,
            expected=("alternative_family_must_fit_better",),
            contradiction_if=("mandatory_marker_absent", "mass_or_valence_inconsistent"),
        )
        yield EvidenceTemplate(
            id=cell.evidence_ids[2],
            family_id=cell.id,
            kind="cross_modal_corroboration",
            modality=SPECTRAL_MODALITIES[(index + 1) % len(SPECTRAL_MODALITIES)],
            expected=("independent_modality_agreement", "environment_context_recorded"),
            contradiction_if=("cross_modal_assignment_conflict",),
        )


def iter_requested_cells(work_items: int) -> Iterator[FamilyCell]:
    """Yield a finite experiment of any non-negative size without a built-in cap.

    The default vocabulary contains 262,144 base context cells. For larger experiments,
    epochs are namespaced while preserving the coordinate and provenance. A
    production registry should extend the vocabularies rather than treat epochs
    as distinct chemistry.
    """
    if work_items < 0:
        raise ValueError("work_items must be non-negative")
    if work_items == 0:
        return
    lattice_size = (
        len(SKELETONS)
        * len(FUNCTIONAL_FAMILIES)
        * len(ELECTRONIC_CLASSES)
        * len(REACTION_ARCHETYPES)
        * len(STEREO_CLASSES)
        * len(ENVIRONMENTS)
    )
    produced = 0
    epoch = 0
    while produced < work_items:
        remaining = work_items - produced
        take = min(remaining, lattice_size)
        coords = itertools.islice(base_coordinates(), take)
        for cell in family_cells(coords, start_index=produced):
            if epoch:
                cell = replace(
                    cell,
                    provenance=f"omega_org_fam_t_default_vocabulary_r01_epoch_{epoch}",
                )
            yield cell
        produced += take
        epoch += 1
