"""Open-world sequential Monte Carlo for authorized reverse-engineering hypotheses.

Particles represent declared behavioral model classes and parameters. Posterior
mass is conditional on the proposal family and observations. A novelty particle
is a routing signal for model-class expansion, not proof of a new mechanism.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import random
from typing import Callable, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class Particle:
    particle_id: str
    model_class: str
    parameter: float
    weight: float
    provenance: str
    parent_id: str | None = None


@dataclass(frozen=True)
class Observation:
    experiment_id: str
    value: float
    sigma: float


@dataclass(frozen=True)
class SMCRound:
    sequence: int
    experiment_id: str
    observation: float
    effective_sample_size: float
    resampled: bool
    novelty_mass: float
    posterior_digest: str


@dataclass(frozen=True)
class SMCReport:
    particles: tuple[Particle, ...]
    rounds: tuple[SMCRound, ...]
    posterior_by_class: Mapping[str, float]
    novelty_mass: float
    expansion_recommended: bool
    claim: str = "open_world_behavioral_posterior_only"


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def normalize_particles(particles: Iterable[Particle]) -> tuple[Particle, ...]:
    items = tuple(particles)
    if not items:
        raise ValueError("particles cannot be empty")
    if len({item.particle_id for item in items}) != len(items):
        raise ValueError("particle ids must be unique")
    total = 0.0
    for item in items:
        if not math.isfinite(item.parameter):
            raise ValueError("particle parameter must be finite")
        if not math.isfinite(item.weight) or item.weight < 0:
            raise ValueError("particle weight must be finite and non-negative")
        if not item.model_class.strip() or not item.provenance.strip():
            raise ValueError("model class and provenance cannot be blank")
        total += item.weight
    if total <= 0:
        raise ValueError("particle weight sum must be positive")
    return tuple(
        Particle(
            particle_id=item.particle_id,
            model_class=item.model_class,
            parameter=item.parameter,
            weight=item.weight / total,
            provenance=item.provenance,
            parent_id=item.parent_id,
        )
        for item in items
    )


def gaussian_likelihood(observed: float, predicted: float, sigma: float) -> float:
    if not all(math.isfinite(value) for value in (observed, predicted, sigma)) or sigma <= 0:
        raise ValueError("gaussian inputs must be finite and sigma positive")
    z = (observed - predicted) / sigma
    return math.exp(-0.5 * z * z) / (sigma * math.sqrt(2 * math.pi))


def effective_sample_size(particles: Sequence[Particle]) -> float:
    return 1.0 / sum(item.weight * item.weight for item in particles)


def systematic_resample(
    particles: Sequence[Particle], *, seed: int, sequence: int
) -> tuple[Particle, ...]:
    if not particles:
        raise ValueError("particles cannot be empty")
    rng = random.Random((seed << 16) ^ sequence)
    count = len(particles)
    start = rng.random() / count
    positions = [start + index / count for index in range(count)]
    cumulative: list[float] = []
    running = 0.0
    for item in particles:
        running += item.weight
        cumulative.append(running)
    result: list[Particle] = []
    cursor = 0
    for index, position in enumerate(positions):
        while cursor < count - 1 and position > cumulative[cursor]:
            cursor += 1
        source = particles[cursor]
        result.append(
            Particle(
                particle_id=f"{source.particle_id}:r{sequence}:{index}",
                model_class=source.model_class,
                parameter=source.parameter,
                weight=1.0 / count,
                provenance="systematic-resample",
                parent_id=source.particle_id,
            )
        )
    return tuple(result)


def update_particles(
    particles: Sequence[Particle],
    observation: Observation,
    predictor: Callable[[Particle, str], float],
) -> tuple[Particle, ...]:
    if observation.sigma <= 0 or not math.isfinite(observation.value):
        raise ValueError("invalid observation")
    weighted: list[Particle] = []
    for item in particles:
        prediction = predictor(item, observation.experiment_id)
        likelihood = gaussian_likelihood(observation.value, prediction, observation.sigma)
        weighted.append(
            Particle(
                particle_id=item.particle_id,
                model_class=item.model_class,
                parameter=item.parameter,
                weight=item.weight * likelihood,
                provenance=item.provenance,
                parent_id=item.parent_id,
            )
        )
    if sum(item.weight for item in weighted) <= 0:
        raise ValueError("all particle likelihoods underflowed to zero")
    return normalize_particles(weighted)


def inject_novelty_particles(
    particles: Sequence[Particle],
    *,
    residual: float,
    threshold: float,
    count: int,
    seed: int,
) -> tuple[Particle, ...]:
    if count < 0:
        raise ValueError("count cannot be negative")
    if residual <= threshold or count == 0:
        return tuple(particles)
    rng = random.Random(seed)
    novelty_weight = min(0.35, max(0.05, (residual - threshold) / (abs(residual) + threshold + 1e-12)))
    base = normalize_particles(particles)
    retained = [
        Particle(
            particle_id=item.particle_id,
            model_class=item.model_class,
            parameter=item.parameter,
            weight=item.weight * (1.0 - novelty_weight),
            provenance=item.provenance,
            parent_id=item.parent_id,
        )
        for item in base
    ]
    for index in range(count):
        retained.append(
            Particle(
                particle_id=f"novel:{seed}:{index}",
                model_class="__novelty__",
                parameter=rng.uniform(-2.0, 2.0),
                weight=novelty_weight / count,
                provenance="residual-triggered-proposal",
            )
        )
    return normalize_particles(retained)


def posterior_by_class(particles: Sequence[Particle]) -> dict[str, float]:
    result: dict[str, float] = {}
    for item in particles:
        result[item.model_class] = result.get(item.model_class, 0.0) + item.weight
    return dict(sorted(result.items()))


def run_smc(
    particles: Iterable[Particle],
    observations: Sequence[Observation],
    predictor: Callable[[Particle, str], float],
    *,
    seed: int = 0,
    ess_fraction: float = 0.5,
    novelty_threshold: float = 2.0,
    novelty_count: int = 4,
    expansion_mass_threshold: float = 0.15,
) -> SMCReport:
    if not 0 < ess_fraction <= 1:
        raise ValueError("ess_fraction must be within (0, 1]")
    if not 0 <= expansion_mass_threshold <= 1:
        raise ValueError("expansion_mass_threshold must be within [0, 1]")
    current = normalize_particles(particles)
    rounds: list[SMCRound] = []
    for sequence, observation in enumerate(observations):
        if observation.sigma <= 0 or not math.isfinite(observation.sigma) or not math.isfinite(observation.value):
            raise ValueError("invalid observation")
        predictions = [predictor(item, observation.experiment_id) for item in current]
        residual = min(abs(observation.value - prediction) / observation.sigma for prediction in predictions)
        current = inject_novelty_particles(
            current,
            residual=residual,
            threshold=novelty_threshold,
            count=novelty_count,
            seed=(seed << 8) ^ sequence,
        )
        current = update_particles(current, observation, predictor)
        ess = effective_sample_size(current)
        resampled = ess < ess_fraction * len(current)
        class_mass = posterior_by_class(current)
        novelty_mass = class_mass.get("__novelty__", 0.0)
        digest = _digest([asdict(item) for item in current])
        rounds.append(
            SMCRound(
                sequence=sequence,
                experiment_id=observation.experiment_id,
                observation=observation.value,
                effective_sample_size=ess,
                resampled=resampled,
                novelty_mass=novelty_mass,
                posterior_digest=digest,
            )
        )
        if resampled:
            current = systematic_resample(current, seed=seed, sequence=sequence)
    class_mass = posterior_by_class(current)
    novelty_mass = class_mass.get("__novelty__", 0.0)
    return SMCReport(
        particles=tuple(current),
        rounds=tuple(rounds),
        posterior_by_class=class_mass,
        novelty_mass=novelty_mass,
        expansion_recommended=novelty_mass >= expansion_mass_threshold,
    )
