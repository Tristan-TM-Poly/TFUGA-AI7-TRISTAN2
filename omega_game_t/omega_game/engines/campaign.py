from __future__ import annotations

import hashlib
import itertools
import json
import time
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Iterable, Mapping

from .layout import ArenaLayout
from .simulation import AgentGenome, ArenaConfig, run_arena_t0


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class CampaignJob:
    job_id: str
    left_id: str
    right_id: str
    seed: int
    layout_hash: str | None
    orientation: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CampaignShard:
    shard_id: int
    job_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"shard_id": self.shard_id, "job_ids": list(self.job_ids), "job_count": len(self.job_ids)}


@dataclass(frozen=True)
class CampaignManifest:
    agents: tuple[AgentGenome, ...]
    layouts: tuple[ArenaLayout, ...]
    seeds: tuple[int, ...]
    mirrored: bool
    arena_template: ArenaConfig
    jobs: tuple[CampaignJob, ...]
    shards: tuple[CampaignShard, ...]
    plan_receipt: str

    @property
    def job_count(self) -> int:
        return len(self.jobs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agents": [asdict(agent) for agent in self.agents],
            "layouts": [layout.normalized_dict() for layout in self.layouts],
            "seeds": list(self.seeds),
            "mirrored": self.mirrored,
            "arena_template": asdict(self.arena_template),
            "jobs": [job.to_dict() for job in self.jobs],
            "shards": [shard.to_dict() for shard in self.shards],
            "job_count": self.job_count,
            "plan_receipt": self.plan_receipt,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2) + "\n"

    def validate(self) -> None:
        if len(self.agents) < 2:
            raise ValueError("campaign requires at least two agents")
        if len({agent.agent_id for agent in self.agents}) != len(self.agents):
            raise ValueError("campaign agent IDs must be unique")
        if not self.seeds or len(set(self.seeds)) != len(self.seeds):
            raise ValueError("campaign seeds must be non-empty and unique")
        if self.layouts and len({layout.layout_hash for layout in self.layouts}) != len(self.layouts):
            raise ValueError("campaign layout hashes must be unique")
        if not self.shards:
            raise ValueError("campaign needs at least one shard")
        job_ids = [job.job_id for job in self.jobs]
        if len(set(job_ids)) != len(job_ids):
            raise ValueError("campaign job IDs must be unique")
        shard_job_ids = [job_id for shard in self.shards for job_id in shard.job_ids]
        if sorted(shard_job_ids) != sorted(job_ids):
            raise ValueError("shards must partition campaign jobs exactly once")
        expected = _manifest_receipt_payload(
            self.agents,
            self.layouts,
            self.seeds,
            self.mirrored,
            self.arena_template,
            self.jobs,
            self.shards,
        )
        if _canonical_hash(expected) != self.plan_receipt:
            raise ValueError("campaign plan receipt mismatch")


@dataclass(frozen=True)
class CampaignResult:
    job_id: str
    replay_hash: str
    winner: str | None
    ticks: int
    event_count: int
    left_score: float
    right_score: float
    layout_hash: str | None
    result_receipt: str

    @classmethod
    def from_match(cls, job: CampaignJob, match) -> "CampaignResult":
        payload = {
            "job_id": job.job_id,
            "replay_hash": match.replay_hash,
            "winner": match.winner,
            "ticks": match.ticks,
            "event_count": len(match.replay),
            "left_score": float(match.metrics[match.left.agent_id]["score"]),
            "right_score": float(match.metrics[match.right.agent_id]["score"]),
            "layout_hash": match.layout_hash,
        }
        return cls(**payload, result_receipt=_canonical_hash(payload))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CampaignCheckpoint:
    plan_receipt: str
    completed: dict[str, CampaignResult] = field(default_factory=dict)

    @classmethod
    def empty(cls, manifest: CampaignManifest) -> "CampaignCheckpoint":
        return cls(plan_receipt=manifest.plan_receipt)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CampaignCheckpoint":
        required = {"plan_receipt", "completed"}
        allowed = required | {"checkpoint_receipt"}
        if not required.issubset(data) or not set(data).issubset(allowed):
            raise ValueError("invalid checkpoint fields")
        completed_raw = data["completed"]
        if not isinstance(completed_raw, Mapping):
            raise ValueError("checkpoint.completed must be an object")
        completed: dict[str, CampaignResult] = {}
        for job_id, value in completed_raw.items():
            if not isinstance(value, Mapping):
                raise ValueError("checkpoint result must be an object")
            result = CampaignResult(**dict(value))
            if result.job_id != job_id:
                raise ValueError("checkpoint result key/job_id mismatch")
            _validate_result_receipt(result)
            completed[job_id] = result
        checkpoint = cls(plan_receipt=str(data["plan_receipt"]), completed=completed)
        supplied_receipt = data.get("checkpoint_receipt")
        if supplied_receipt is not None and str(supplied_receipt) != checkpoint.checkpoint_receipt:
            raise ValueError("checkpoint receipt mismatch")
        return checkpoint

    @classmethod
    def from_json(cls, text: str) -> "CampaignCheckpoint":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("checkpoint JSON root must be object")
        return cls.from_dict(payload)

    @property
    def checkpoint_receipt(self) -> str:
        return _canonical_hash(self.to_dict(include_receipt=False))

    def to_dict(self, *, include_receipt: bool = True) -> dict[str, Any]:
        payload = {
            "plan_receipt": self.plan_receipt,
            "completed": {job_id: self.completed[job_id].to_dict() for job_id in sorted(self.completed)},
        }
        if include_receipt:
            payload["checkpoint_receipt"] = _canonical_hash(payload)
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2) + "\n"

    def validate_for(self, manifest: CampaignManifest) -> None:
        if self.plan_receipt != manifest.plan_receipt:
            raise ValueError("checkpoint belongs to a different campaign plan")
        known_jobs = {job.job_id for job in manifest.jobs}
        unknown = sorted(set(self.completed) - known_jobs)
        if unknown:
            raise ValueError(f"checkpoint contains unknown jobs: {','.join(unknown)}")
        for result in self.completed.values():
            _validate_result_receipt(result)


@dataclass(frozen=True)
class CampaignSliceReport:
    plan_receipt: str
    selected_shards: tuple[int, ...]
    executed_job_ids: tuple[str, ...]
    skipped_completed_job_ids: tuple[str, ...]
    remaining_selected_jobs: int
    total_completed_jobs: int
    complete_campaign: bool
    match_ticks_work_units: int
    event_work_units: int
    wall_clock_seconds: float
    checkpoint_receipt: str

    @property
    def observed_matches_per_second(self) -> float | None:
        if self.wall_clock_seconds <= 0:
            return None
        return len(self.executed_job_ids) / self.wall_clock_seconds

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["observed_matches_per_second"] = (
            None if self.observed_matches_per_second is None else round(self.observed_matches_per_second, 6)
        )
        return payload


@dataclass(frozen=True)
class CampaignBenchmarkReport:
    repetitions: int
    job_count: int
    deterministic_ticks_per_run: tuple[int, ...]
    deterministic_events_per_run: tuple[int, ...]
    wall_clock_seconds_per_run: tuple[float, ...]
    median_wall_clock_seconds: float
    result_receipt: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def plan_campaign(
    population: Iterable[AgentGenome],
    *,
    layouts: Iterable[ArenaLayout] = (),
    seeds: Iterable[int] = (0, 1, 2),
    arena_template: ArenaConfig | None = None,
    mirrored: bool = True,
    shard_count: int = 1,
    layout_fairness_threshold: float = 0.50,
) -> CampaignManifest:
    agents = tuple(sorted((agent.normalized() for agent in population), key=lambda item: item.agent_id))
    maps = tuple(sorted(tuple(layouts), key=lambda item: item.layout_hash))
    seed_tuple = tuple(sorted(int(seed) for seed in seeds))
    template = arena_template or ArenaConfig()
    template.validate()
    if len(agents) < 2 or len({agent.agent_id for agent in agents}) != len(agents):
        raise ValueError("campaign requires at least two unique agents")
    if not seed_tuple or len(set(seed_tuple)) != len(seed_tuple):
        raise ValueError("campaign seeds must be non-empty and unique")
    if shard_count < 1:
        raise ValueError("shard_count must be >= 1")
    if not 0.0 <= layout_fairness_threshold <= 1.0:
        raise ValueError("layout_fairness_threshold must be in [0, 1]")
    if maps and len({layout.layout_hash for layout in maps}) != len(maps):
        raise ValueError("campaign layouts must have unique hashes")
    for layout in maps:
        audit = layout.audit(fairness_threshold=layout_fairness_threshold)
        if not audit.accepted:
            raise ValueError(f"layout {layout.layout_hash[:12]} failed audit: {','.join(audit.flags)}")

    layout_values: tuple[ArenaLayout | None, ...] = maps if maps else (None,)
    jobs: list[CampaignJob] = []
    for layout in layout_values:
        layout_hash = None if layout is None else layout.layout_hash
        for first, second in itertools.combinations(agents, 2):
            orientations = ((first, second, 0), (second, first, 1)) if mirrored else ((first, second, 0),)
            for seed in seed_tuple:
                for left, right, orientation in orientations:
                    descriptor = {
                        "left_id": left.agent_id,
                        "right_id": right.agent_id,
                        "seed": seed,
                        "layout_hash": layout_hash,
                        "orientation": orientation,
                    }
                    jobs.append(
                        CampaignJob(
                            job_id=f"job-{_canonical_hash(descriptor)[:24]}",
                            left_id=left.agent_id,
                            right_id=right.agent_id,
                            seed=seed,
                            layout_hash=layout_hash,
                            orientation=orientation,
                        )
                    )
    jobs = sorted(jobs, key=lambda job: job.job_id)
    buckets: list[list[str]] = [[] for _ in range(shard_count)]
    for job in jobs:
        shard_id = int(job.job_id.removeprefix("job-")[:16], 16) % shard_count
        buckets[shard_id].append(job.job_id)
    shards = tuple(CampaignShard(index, tuple(sorted(bucket))) for index, bucket in enumerate(buckets))
    receipt_payload = _manifest_receipt_payload(agents, maps, seed_tuple, mirrored, template, tuple(jobs), shards)
    manifest = CampaignManifest(
        agents=agents,
        layouts=maps,
        seeds=seed_tuple,
        mirrored=mirrored,
        arena_template=template,
        jobs=tuple(jobs),
        shards=shards,
        plan_receipt=_canonical_hash(receipt_payload),
    )
    manifest.validate()
    return manifest


def run_campaign_slice(
    manifest: CampaignManifest,
    *,
    checkpoint: CampaignCheckpoint | None = None,
    shard_ids: Iterable[int] | None = None,
    max_jobs: int | None = None,
) -> tuple[CampaignCheckpoint, CampaignSliceReport]:
    manifest.validate()
    state = CampaignCheckpoint.empty(manifest) if checkpoint is None else checkpoint
    state.validate_for(manifest)
    if max_jobs is not None and max_jobs < 1:
        raise ValueError("max_jobs must be >= 1 when provided")

    available_shards = {shard.shard_id: shard for shard in manifest.shards}
    selected = tuple(sorted(available_shards)) if shard_ids is None else tuple(sorted(set(int(value) for value in shard_ids)))
    unknown_shards = [value for value in selected if value not in available_shards]
    if unknown_shards:
        raise ValueError(f"unknown shard IDs: {','.join(map(str, unknown_shards))}")
    selected_job_ids = [job_id for shard_id in selected for job_id in available_shards[shard_id].job_ids]
    selected_job_ids = sorted(selected_job_ids)
    jobs_by_id = {job.job_id: job for job in manifest.jobs}
    pending = [job_id for job_id in selected_job_ids if job_id not in state.completed]
    budget = len(pending) if max_jobs is None else min(len(pending), max_jobs)
    to_run = pending[:budget]
    skipped = tuple(job_id for job_id in selected_job_ids if job_id in state.completed)
    agents = {agent.agent_id: agent for agent in manifest.agents}
    layouts = {layout.layout_hash: layout for layout in manifest.layouts}

    ticks = 0
    events = 0
    start = time.perf_counter()
    for job_id in to_run:
        job = jobs_by_id[job_id]
        layout = None if job.layout_hash is None else layouts[job.layout_hash]
        config = manifest.arena_template
        if layout is not None:
            config = replace(config, width=layout.width, height=layout.height, resource_count=len(layout.resources))
            config.validate()
        match = run_arena_t0(
            agents[job.left_id],
            agents[job.right_id],
            seed=job.seed,
            config=config,
            layout=layout,
        )
        result = CampaignResult.from_match(job, match)
        state.completed[job_id] = result
        ticks += result.ticks
        events += result.event_count
    elapsed = time.perf_counter() - start

    remaining_selected = len([job_id for job_id in selected_job_ids if job_id not in state.completed])
    report = CampaignSliceReport(
        plan_receipt=manifest.plan_receipt,
        selected_shards=selected,
        executed_job_ids=tuple(to_run),
        skipped_completed_job_ids=skipped,
        remaining_selected_jobs=remaining_selected,
        total_completed_jobs=len(state.completed),
        complete_campaign=len(state.completed) == manifest.job_count,
        match_ticks_work_units=ticks,
        event_work_units=events,
        wall_clock_seconds=round(elapsed, 9),
        checkpoint_receipt=state.checkpoint_receipt,
    )
    return state, report


def merge_checkpoints(manifest: CampaignManifest, checkpoints: Iterable[CampaignCheckpoint]) -> CampaignCheckpoint:
    manifest.validate()
    merged = CampaignCheckpoint.empty(manifest)
    for checkpoint in checkpoints:
        checkpoint.validate_for(manifest)
        for job_id, result in checkpoint.completed.items():
            existing = merged.completed.get(job_id)
            if existing is not None and existing.result_receipt != result.result_receipt:
                raise ValueError(f"conflicting checkpoint results for {job_id}")
            merged.completed[job_id] = result
    return merged


def benchmark_campaign(
    manifest: CampaignManifest,
    *,
    repetitions: int = 3,
) -> CampaignBenchmarkReport:
    if repetitions < 1:
        raise ValueError("repetitions must be >= 1")
    ticks: list[int] = []
    events: list[int] = []
    elapsed: list[float] = []
    deterministic_receipts: list[str] = []
    for _ in range(repetitions):
        checkpoint, report = run_campaign_slice(manifest)
        ticks.append(report.match_ticks_work_units)
        events.append(report.event_work_units)
        elapsed.append(report.wall_clock_seconds)
        deterministic_receipts.append(checkpoint.checkpoint_receipt)
    if len(set(deterministic_receipts)) != 1:
        raise ValueError("benchmark repetitions produced different deterministic receipts")
    deterministic_payload = {
        "plan_receipt": manifest.plan_receipt,
        "repetitions": repetitions,
        "job_count": manifest.job_count,
        "ticks": ticks,
        "events": events,
        "checkpoint_receipt": deterministic_receipts[0],
    }
    return CampaignBenchmarkReport(
        repetitions=repetitions,
        job_count=manifest.job_count,
        deterministic_ticks_per_run=tuple(ticks),
        deterministic_events_per_run=tuple(events),
        wall_clock_seconds_per_run=tuple(elapsed),
        median_wall_clock_seconds=round(statistics_median(elapsed), 9),
        result_receipt=_canonical_hash(deterministic_payload),
    )


def statistics_median(values: Iterable[float]) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("median requires values")
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _manifest_receipt_payload(
    agents: tuple[AgentGenome, ...],
    layouts: tuple[ArenaLayout, ...],
    seeds: tuple[int, ...],
    mirrored: bool,
    arena_template: ArenaConfig,
    jobs: tuple[CampaignJob, ...],
    shards: tuple[CampaignShard, ...],
) -> dict[str, Any]:
    return {
        "agents": [asdict(agent) for agent in agents],
        "layout_hashes": [layout.layout_hash for layout in layouts],
        "seeds": list(seeds),
        "mirrored": mirrored,
        "arena_template": asdict(arena_template),
        "jobs": [job.to_dict() for job in jobs],
        "shards": [shard.to_dict() for shard in shards],
    }


def _validate_result_receipt(result: CampaignResult) -> None:
    payload = {
        "job_id": result.job_id,
        "replay_hash": result.replay_hash,
        "winner": result.winner,
        "ticks": result.ticks,
        "event_count": result.event_count,
        "left_score": result.left_score,
        "right_score": result.right_score,
        "layout_hash": result.layout_hash,
    }
    if _canonical_hash(payload) != result.result_receipt:
        raise ValueError(f"campaign result receipt mismatch for {result.job_id}")
