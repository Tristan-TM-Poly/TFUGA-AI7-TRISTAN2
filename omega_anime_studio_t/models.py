"""Typed Anime-IR models for Ω-ANIME-STUDIO-T∞ R1.

The models separate internal coherence from artistic quality, market proof,
legal clearance and scientific truth.  Only standard-library types are used
so the kernel stays portable and auditable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any, Iterable


class OakStatus(str, Enum):
    EXPLORATORY = "EXPLORATORY"
    FORMALIZED = "FORMALIZED"
    SIMULATED = "SIMULATED"
    DEMONSTRATED = "DEMONSTRATED"
    REPLICATED = "REPLICATED"
    CANONICAL = "CANONICAL"


class InformationStatus(str, Enum):
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    POSSIBLE = "POSSIBLE"
    PROJECTED = "PROJECTED"
    DESIRED = "DESIRED"
    MANIPULATED = "MANIPULATED"
    UNKNOWN = "UNKNOWN"


class AssetState(str, Enum):
    IDEA = "IDEA"
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    REVISE = "REVISE"
    APPROVED = "APPROVED"
    LOCKED = "LOCKED"
    PRODUCED = "PRODUCED"
    INTEGRATED = "INTEGRATED"
    ARCHIVED = "ARCHIVED"


class FrontierDecision(str, Enum):
    EXPAND = "EXPAND"
    HOLD = "HOLD"
    RESHARD = "RESHARD"
    DEFER = "DEFER"
    COMPRESS = "COMPRESS"
    REGENERATE = "REGENERATE"
    REDESIGN = "REDESIGN"
    STOP_SAFELY = "STOP-SAFELY"


class ValidationError(ValueError):
    pass


def json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return json_ready(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, set)):
        return [json_ready(item) for item in value]
    return value


def require_text(value: str, location: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{location}: non-empty text required")


@dataclass(frozen=True)
class Provenance:
    source_id: str
    source_kind: str
    license_id: str
    created_by: str
    created_at: str
    derivation: tuple[str, ...] = ()
    private: bool = True

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name in ("source_id", "source_kind", "license_id", "created_by", "created_at"):
            require_text(getattr(self, name), f"provenance.{name}", errors)
        return errors


@dataclass(frozen=True)
class AnimeNode:
    node_id: str
    node_type: str
    label: str
    status: OakStatus = OakStatus.FORMALIZED
    attributes: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        require_text(self.node_id, "node.node_id", errors)
        require_text(self.node_type, f"node.{self.node_id}.node_type", errors)
        require_text(self.label, f"node.{self.node_id}.label", errors)
        return errors


@dataclass(frozen=True)
class HyperEdge:
    edge_id: str
    edge_type: str
    sources: tuple[str, ...]
    targets: tuple[str, ...]
    confidence: float = 1.0
    attributes: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        require_text(self.edge_id, "edge.edge_id", errors)
        require_text(self.edge_type, f"edge.{self.edge_id}.edge_type", errors)
        if not self.sources:
            errors.append(f"edge.{self.edge_id}.sources: at least one source required")
        if not self.targets:
            errors.append(f"edge.{self.edge_id}.targets: at least one target required")
        if not 0.0 <= self.confidence <= 1.0:
            errors.append(f"edge.{self.edge_id}.confidence: must be in [0, 1]")
        return errors


@dataclass(frozen=True)
class CharacterIR:
    character_id: str
    name: str
    desire: str
    need: str
    fear: str
    contradiction: str
    power: str
    limitation: str
    moral_boundary: str
    voice_markers: tuple[str, ...] = ()
    motion_markers: tuple[str, ...] = ()
    knowledge: tuple[str, ...] = ()
    relationships: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name in (
            "character_id", "name", "desire", "need", "fear",
            "contradiction", "power", "limitation", "moral_boundary",
        ):
            require_text(getattr(self, name), f"character.{self.character_id}.{name}", errors)
        if self.power.strip().casefold() == self.limitation.strip().casefold():
            errors.append(f"character.{self.character_id}: power and limitation must differ")
        return errors


@dataclass(frozen=True)
class SceneIR:
    scene_id: str
    episode_id: str
    sequence_id: str
    order: int
    title: str
    duration_target_s: int
    objective: str
    conflict: str
    irreversible_change: str
    audience_before: tuple[str, ...]
    audience_after: tuple[str, ...]
    characters: tuple[str, ...]
    location_id: str
    promise_ids: tuple[str, ...] = ()
    causal_debt_ids: tuple[str, ...] = ()
    asset_ids: tuple[str, ...] = ()
    oak_status: OakStatus = OakStatus.FORMALIZED

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name in (
            "scene_id", "episode_id", "sequence_id", "title", "objective",
            "conflict", "irreversible_change", "location_id",
        ):
            require_text(str(getattr(self, name)), f"scene.{self.scene_id}.{name}", errors)
        if self.order < 1:
            errors.append(f"scene.{self.scene_id}.order: must be >= 1")
        if self.duration_target_s < 1:
            errors.append(f"scene.{self.scene_id}.duration_target_s: must be >= 1")
        if not self.characters:
            errors.append(f"scene.{self.scene_id}.characters: at least one required")
        if set(self.audience_before) == set(self.audience_after):
            errors.append(f"scene.{self.scene_id}: audience information state must change")
        return errors


@dataclass(frozen=True)
class ShotIR:
    shot_id: str
    scene_id: str
    order: int
    duration_s: float
    purpose: str
    framing: str
    camera_motion: str
    subject_ids: tuple[str, ...]
    information_revealed: tuple[str, ...] = ()
    continuity_in: tuple[str, ...] = ()
    continuity_out: tuple[str, ...] = ()
    asset_ids: tuple[str, ...] = ()
    estimated_cost_units: float = 1.0

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name in ("shot_id", "scene_id", "purpose", "framing", "camera_motion"):
            require_text(str(getattr(self, name)), f"shot.{self.shot_id}.{name}", errors)
        if self.order < 1:
            errors.append(f"shot.{self.shot_id}.order: must be >= 1")
        if self.duration_s <= 0:
            errors.append(f"shot.{self.shot_id}.duration_s: must be positive")
        if not self.subject_ids:
            errors.append(f"shot.{self.shot_id}.subject_ids: at least one required")
        if self.estimated_cost_units < 0:
            errors.append(f"shot.{self.shot_id}.estimated_cost_units: cannot be negative")
        return errors


@dataclass(frozen=True)
class CausalDebt:
    debt_id: str
    origin_scene_id: str
    local_benefit: str
    displaced_constraint: str
    affected_system: str
    certainty: float
    status: str = "OPEN"
    deadline: str = "UNKNOWN"

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name in (
            "debt_id", "origin_scene_id", "local_benefit",
            "displaced_constraint", "affected_system", "status", "deadline",
        ):
            require_text(str(getattr(self, name)), f"causal_debt.{self.debt_id}.{name}", errors)
        if not 0.0 <= self.certainty <= 1.0:
            errors.append(f"causal_debt.{self.debt_id}.certainty: must be in [0,1]")
        return errors


@dataclass(frozen=True)
class AssetRecord:
    asset_id: str
    asset_type: str
    name: str
    state: AssetState
    provenance: Provenance
    dependencies: tuple[str, ...] = ()
    license_risk: str = "REVIEW"
    reusable: bool = True

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name in ("asset_id", "asset_type", "name", "license_risk"):
            require_text(str(getattr(self, name)), f"asset.{self.asset_id}.{name}", errors)
        errors.extend(self.provenance.validate())
        return errors


@dataclass(frozen=True)
class AnimeProjectR1:
    project_id: str
    title: str
    logline: str
    theme_question: str
    target_duration_s: int
    world_rules: tuple[str, ...]
    visual_invariants: tuple[str, ...]
    characters: tuple[CharacterIR, ...]
    scenes: tuple[SceneIR, ...]
    shots: tuple[ShotIR, ...]
    causal_debts: tuple[CausalDebt, ...]
    assets: tuple[AssetRecord, ...]
    nodes: tuple[AnimeNode, ...]
    edges: tuple[HyperEdge, ...]
    oak_status: OakStatus = OakStatus.FORMALIZED
    risks: tuple[str, ...] = ()
    next_actions: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name in ("project_id", "title", "logline", "theme_question"):
            require_text(str(getattr(self, name)), f"project.{name}", errors)
        if not self.theme_question.rstrip().endswith("?"):
            errors.append("project.theme_question: explicit question required")
        if self.target_duration_s < 30:
            errors.append("project.target_duration_s: must be >= 30")
        if len(self.world_rules) < 3:
            errors.append("project.world_rules: at least three required")
        if not self.visual_invariants:
            errors.append("project.visual_invariants: at least one required")
        if not self.risks:
            errors.append("project.risks: risk ledger required")

        collections: Iterable[Iterable[Any]] = (
            self.characters, self.scenes, self.shots, self.causal_debts,
            self.assets, self.nodes, self.edges,
        )
        for collection in collections:
            for item in collection:
                errors.extend(item.validate())

        scene_ids = {scene.scene_id for scene in self.scenes}
        shot_scene_ids = {shot.scene_id for shot in self.shots}
        unknown_scene_ids = shot_scene_ids - scene_ids
        if unknown_scene_ids:
            errors.append(f"project.shots: unknown scene ids {sorted(unknown_scene_ids)}")

        character_ids = {character.character_id for character in self.characters}
        for scene in self.scenes:
            unknown = set(scene.characters) - character_ids
            if unknown:
                errors.append(f"scene.{scene.scene_id}: unknown characters {sorted(unknown)}")

        asset_ids = {asset.asset_id for asset in self.assets}
        for shot in self.shots:
            unknown = set(shot.asset_ids) - asset_ids
            if unknown:
                errors.append(f"shot.{shot.shot_id}: unknown assets {sorted(unknown)}")

        node_ids = {node.node_id for node in self.nodes}
        if len(node_ids) != len(self.nodes):
            errors.append("project.nodes: duplicate node_id")
        for edge in self.edges:
            missing = (set(edge.sources) | set(edge.targets)) - node_ids
            if missing:
                errors.append(f"edge.{edge.edge_id}: unknown nodes {sorted(missing)}")

        scene_orders = [scene.order for scene in self.scenes]
        if scene_orders != sorted(scene_orders) or len(scene_orders) != len(set(scene_orders)):
            errors.append("project.scenes: order must be unique and ascending")

        for scene in self.scenes:
            scene_shots = sorted(
                (shot for shot in self.shots if shot.scene_id == scene.scene_id),
                key=lambda shot: shot.order,
            )
            if not scene_shots:
                errors.append(f"scene.{scene.scene_id}: at least one shot required")
                continue
            orders = [shot.order for shot in scene_shots]
            if orders != list(range(1, len(orders) + 1)):
                errors.append(f"scene.{scene.scene_id}: shot order must be contiguous")
            duration = sum(shot.duration_s for shot in scene_shots)
            tolerance = max(1.0, scene.duration_target_s * 0.05)
            if abs(duration - scene.duration_target_s) > tolerance:
                errors.append(
                    f"scene.{scene.scene_id}: shot duration {duration:.2f}s differs from target"
                )

        total_scene_duration = sum(scene.duration_target_s for scene in self.scenes)
        if total_scene_duration != self.target_duration_s:
            errors.append(
                f"project.duration: scene total {total_scene_duration} != target {self.target_duration_s}"
            )
        return errors

    def require_valid(self) -> None:
        errors = self.validate()
        if errors:
            raise ValidationError("\n".join(errors))

    def to_dict(self) -> dict[str, Any]:
        return json_ready(asdict(self))
