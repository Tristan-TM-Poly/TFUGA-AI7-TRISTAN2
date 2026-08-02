"""Explainable feature-based classifier for family-space cells.

This classifier consumes explicit descriptors. It does not infer a certified
molecular identity from raw spectra or a SMILES string.
"""
from __future__ import annotations

from collections.abc import Iterable

from .models import ClassificationResult, FamilyCell


def classify_features(
    cells: Iterable[FamilyCell],
    features: set[str],
    *,
    top_k: int = 20,
) -> ClassificationResult:
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    scored: list[tuple[str, float]] = []
    matched: dict[str, list[str]] = {}
    rejected: dict[str, list[str]] = {}
    for cell in cells:
        coordinate_values = set(cell.coordinate.to_dict().values())
        marker_values = set(cell.spectral_markers)
        all_values = coordinate_values | marker_values
        hits = sorted(features & all_values)
        misses = sorted(features - all_values)
        score = cell.compatibility_score + 0.2 * len(hits) - 0.03 * len(misses)
        score -= 0.4 * len(cell.contradictions)
        if hits:
            matched[cell.id] = hits
        if cell.contradictions:
            rejected[cell.id] = list(cell.contradictions)
        scored.append((cell.id, round(score, 6)))
    scored.sort(key=lambda item: (-item[1], item[0]))
    result = ClassificationResult(
        ranked_family_ids=scored[:top_k],
        matched_features={key: matched[key] for key, _ in scored[:top_k] if key in matched},
        rejected_family_ids={key: rejected[key] for key, _ in scored[:top_k] if key in rejected},
    )
    if not features:
        result.warnings.append("No features supplied; ranking reflects compatibility priors only.")
    result.warnings.append(
        "Family ranking is a candidate-screening result, not analytical identification or synthesis authorization."
    )
    return result
