"""Adaptive frontier controller with no permanent total-object ceiling."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from itertools import product
from pathlib import Path
from typing import Iterator

from .models import FrontierDecision


@dataclass(frozen=True)
class FrontierBudget:
    memory_bytes: int
    wall_time_s: float
    output_bytes: int
    quality_floor: float = 0.70
    duplicate_ceiling: float = 0.02
    blocking_error_ceiling: int = 0

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.memory_bytes <= 0:
            errors.append('budget.memory_bytes: positive value required')
        if self.wall_time_s <= 0:
            errors.append('budget.wall_time_s: positive value required')
        if self.output_bytes <= 0:
            errors.append('budget.output_bytes: positive value required')
        if not 0 <= self.quality_floor <= 1:
            errors.append('budget.quality_floor: must be in [0,1]')
        return errors


@dataclass
class FrontierState:
    generated: int = 0
    unique: int = 0
    accepted: int = 0
    duplicates: int = 0
    blocking_errors: int = 0
    estimated_memory_bytes: int = 0
    output_bytes: int = 0
    batch_size: int = 128
    shard_count: int = 1
    quality_sum: float = 0.0
    decisions: list[str] = field(default_factory=list)
    m_minus: list[dict[str, object]] = field(default_factory=list)

    @property
    def quality_mean(self) -> float:
        return self.quality_sum / self.generated if self.generated else 0.0

    @property
    def duplicate_rate(self) -> float:
        return self.duplicates / self.generated if self.generated else 0.0

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload['quality_mean'] = self.quality_mean
        payload['duplicate_rate'] = self.duplicate_rate
        return payload


@dataclass(frozen=True)
class SceneVariant:
    variant_id: str
    scene_id: str
    objective: str
    conflict: str
    revelation: str
    cost: str
    staging: str
    quality: float
    signature: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


OBJECTIVES = (
    'clarify anomaly', 'intensify responsibility', 'expose opposition',
    'test relationship', 'reveal causal debt', 'force irreversible choice',
    'compress world history', 'demonstrate power limit',
)
CONFLICTS = (
    'instrument disagreement', 'time pressure', 'ethical veto', 'resource loss',
    'misread relation', 'institutional secrecy', 'ally opposition', 'remote consequence',
)
REVELATIONS = (
    'shared constraint', 'hidden observer', 'false positive', 'displaced cost',
    'manipulated evidence', 'unknown branch', 'memory inconsistency', 'countermeasure',
)
COSTS = (
    'cognitive overload', 'lost trust', 'energy debt', 'injury risk',
    'exposed secret', 'closed future', 'asset destruction', 'moral compromise',
)
STAGINGS = (
    'single locked camera', 'subjective network vision', 'cross-cut consequence',
    'silent close-up', 'wide spatial proof', 'reflection composition',
    'handheld uncertainty', 'geometric overhead',
)


def iter_scene_variants(scene_id: str) -> Iterator[SceneVariant]:
    for index, values in enumerate(
        product(OBJECTIVES, CONFLICTS, REVELATIONS, COSTS, STAGINGS), start=1
    ):
        objective, conflict, revelation, cost, staging = values
        raw = '|'.join((scene_id, *values))
        signature = hashlib.sha256(raw.encode('utf-8')).hexdigest()
        # Stable heuristic: useful for deterministic routing, not artistic truth.
        quality = 0.55 + (int(signature[:8], 16) % 4500) / 10000
        yield SceneVariant(
            variant_id=f'{scene_id}-V{index:05d}',
            scene_id=scene_id,
            objective=objective,
            conflict=conflict,
            revelation=revelation,
            cost=cost,
            staging=staging,
            quality=round(min(0.9999, quality), 4),
            signature=signature,
        )


class AdaptiveFrontierController:
    def __init__(self, budget: FrontierBudget, state: FrontierState | None = None):
        errors = budget.validate()
        if errors:
            raise ValueError('; '.join(errors))
        self.budget = budget
        self.state = state or FrontierState()
        self._seen: set[str] = set()

    def observe(self, variant: SceneVariant) -> None:
        state = self.state
        state.generated += 1
        state.quality_sum += variant.quality
        encoded_size = len(json.dumps(variant.to_dict(), ensure_ascii=False)) + 1
        state.output_bytes += encoded_size
        state.estimated_memory_bytes = len(self._seen) * 96
        if variant.signature in self._seen:
            state.duplicates += 1
            return
        self._seen.add(variant.signature)
        state.unique += 1
        if variant.quality >= self.budget.quality_floor:
            state.accepted += 1

    def decide(self) -> FrontierDecision:
        state = self.state
        if state.blocking_errors > self.budget.blocking_error_ceiling:
            decision = FrontierDecision.REDESIGN
        elif state.estimated_memory_bytes > self.budget.memory_bytes:
            decision = FrontierDecision.RESHARD
        elif state.output_bytes > self.budget.output_bytes:
            decision = FrontierDecision.COMPRESS
        elif state.duplicate_rate > self.budget.duplicate_ceiling:
            decision = FrontierDecision.REGENERATE
        elif state.generated and state.quality_mean < self.budget.quality_floor:
            decision = FrontierDecision.HOLD
        else:
            decision = FrontierDecision.EXPAND
        state.decisions.append(decision.value)
        return decision

    def adapt(self, decision: FrontierDecision) -> None:
        state = self.state
        if decision is FrontierDecision.EXPAND:
            finite_batch_budget = max(1, self.budget.memory_bytes // 256)
            state.batch_size = min(finite_batch_budget, max(1, (state.batch_size * 8) // 5))
        elif decision is FrontierDecision.RESHARD:
            previous = state.shard_count
            state.shard_count *= 2
            state.batch_size = max(1, state.batch_size // 2)
            state.m_minus.append({
                'failure': 'memory pressure',
                'previous_shards': previous,
                'replacement': 'double shards and halve active batch',
            })
        elif decision is FrontierDecision.COMPRESS:
            state.batch_size = max(1, state.batch_size // 2)
            state.m_minus.append({
                'failure': 'output budget pressure',
                'replacement': 'retain generators, hashes and Pareto candidates',
            })
        elif decision in {FrontierDecision.HOLD, FrontierDecision.REDESIGN}:
            state.batch_size = max(1, state.batch_size // 2)

    def checkpoint(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.state.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + '\n',
            encoding='utf-8',
        )


def compile_frontier_sample(
    path: str | Path,
    scene_ids: tuple[str, ...],
    work_items: int,
    budget: FrontierBudget,
) -> dict[str, object]:
    if work_items < 1:
        raise ValueError('work_items must be positive')
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    controller = AdaptiveFrontierController(budget)
    digest = hashlib.sha256()
    written = 0
    with target.open('w', encoding='utf-8', newline='\n') as handle:
        iterators = [iter_scene_variants(scene_id) for scene_id in scene_ids]
        while written < work_items:
            progressed = False
            for iterator in iterators:
                if written >= work_items:
                    break
                try:
                    variant = next(iterator)
                except StopIteration:
                    continue
                progressed = True
                controller.observe(variant)
                line = json.dumps(variant.to_dict(), ensure_ascii=False, sort_keys=True) + '\n'
                handle.write(line)
                digest.update(line.encode('utf-8'))
                written += 1
            if not progressed:
                break
            decision = controller.decide()
            controller.adapt(decision)
            if decision in {FrontierDecision.REDESIGN, FrontierDecision.STOP_SAFELY}:
                break
    return {
        'written': written,
        'sha256': digest.hexdigest(),
        'state': controller.state.to_dict(),
        'no_permanent_total_cap': True,
        'finite_experiment_work_items': work_items,
    }
