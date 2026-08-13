"""Bridge canonical ThesisSeeds into the sparse order-n thesis forest."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping

from omega_generative_closure_t.core import MaxMinVector
from .core import OAK_STATUS_ORDER, OAKStatus, ThesisSeed, example_seed
from .forest import ThesisForest, ZoomCandidate, ZoomPolicy, ZoomReceipt, root_thesis, zoom_thesis
from .seed_registry import CANONICAL_SEED_IDS, canonical_seeds

_VECTOR_FIELDS = (
    "verified_value", "evidence", "reuse", "reachability", "regenerability", "fertility",
    "cost", "structural_debt", "proof_debt", "semantic_debt", "uncertainty", "irreversibility",
)


def _cap_status(parent: OAKStatus, source: OAKStatus) -> OAKStatus:
    index = min(OAK_STATUS_ORDER.index(parent), OAK_STATUS_ORDER.index(source))
    return OAK_STATUS_ORDER[index]  # type: ignore[return-value]


def seed_candidate(seed: ThesisSeed, vector: MaxMinVector) -> ZoomCandidate:
    seed.validate()
    values = {name: float(getattr(vector, name)) for name in _VECTOR_FIELDS}
    if any(value < 0.0 or value > 1.0 for value in values.values()):
        raise ValueError("registry score vectors must be normalized to [0, 1]")
    return ZoomCandidate(
        segment=seed.id,
        title=seed.name,
        focus=seed.core_axiom,
        research_question=f"Which measurable evidence can strengthen or falsify {seed.name}?",
        baselines=("matched_external_baseline_required",),
        falsifiers=tuple(seed.oak_risks),
        **values,
    )


@dataclass(frozen=True)
class RegistryZoomReceipt:
    parent_id: str
    registry_seed_ids: tuple[str, ...]
    scored_seed_ids: tuple[str, ...]
    held_seed_ids: tuple[str, ...]
    selected_seed_ids: tuple[str, ...]
    status_caps: tuple[tuple[str, str], ...]
    zoom_receipt: ZoomReceipt
    score_inference_performed: bool = False
    oak_status_promoted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "omega-thesis-fractal/registry-zoom/v0.2",
            "parent_id": self.parent_id,
            "registry_seed_ids": list(self.registry_seed_ids),
            "scored_seed_ids": list(self.scored_seed_ids),
            "held_seed_ids": list(self.held_seed_ids),
            "selected_seed_ids": list(self.selected_seed_ids),
            "status_caps": [{"seed_id": key, "status": value} for key, value in self.status_caps],
            "zoom_receipt": self.zoom_receipt.to_dict(),
            "score_inference_performed": self.score_inference_performed,
            "oak_status_promoted": self.oak_status_promoted,
        }


def compile_registry_forest(
    vectors: Mapping[str, MaxMinVector],
    *,
    mother_seed: ThesisSeed | None = None,
    policy: ZoomPolicy = ZoomPolicy(min_power_density=0.45, max_active_children=3, max_order=1),
) -> tuple[ThesisForest, RegistryZoomReceipt]:
    seeds = canonical_seeds()
    root = root_thesis(mother_seed or example_seed())
    forest = ThesisForest()
    forest.add(root)
    scored = tuple(seed_id for seed_id in CANONICAL_SEED_IDS if seed_id in vectors)
    held = tuple(seed_id for seed_id in CANONICAL_SEED_IDS if seed_id not in vectors)
    candidates = tuple(seed_candidate(seeds[seed_id], vectors[seed_id]) for seed_id in scored)
    selected, zoom_receipt = zoom_thesis(root, candidates, policy=policy)

    selected_ids: list[str] = []
    caps: list[tuple[str, str]] = []
    for node in selected:
        seed_id = node.address.path[-1]
        source = seeds[seed_id]
        status = _cap_status(root.status, source.status)
        node = replace(node, status=status, local_claims=(source.core_axiom,), falsifiers=tuple(source.oak_risks))
        forest.add(node)
        selected_ids.append(seed_id)
        caps.append((seed_id, status))

    return forest, RegistryZoomReceipt(
        parent_id=root.id,
        registry_seed_ids=tuple(CANONICAL_SEED_IDS),
        scored_seed_ids=scored,
        held_seed_ids=held,
        selected_seed_ids=tuple(selected_ids),
        status_caps=tuple(caps),
        zoom_receipt=zoom_receipt,
    )
