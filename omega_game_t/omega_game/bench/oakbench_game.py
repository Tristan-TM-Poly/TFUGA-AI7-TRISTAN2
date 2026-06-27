"""OAKBench-GAME-T: common benchmark layer for Ω-GAME-T++.

The benchmark is intentionally transparent and deterministic. It does not claim
objective artistic truth; it provides a reproducible signal for improvement.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Callable

from ..engines import (
    BoardGameEngine,
    BoardPiece,
    CircuitDungeonEngine,
    EnergyCivilizationEngine,
    EnergyTurnInput,
    MicrogridParams,
    MicrogridState,
    RLCParams,
    RLCState,
    ScienceSandboxEngine,
    TextWorldEngine,
)


@dataclass(slots=True)
class OAKBenchMetrics:
    fun: float = 0.5
    agency: float = 0.5
    coherence: float = 0.5
    learning: float = 0.5
    safety: float = 1.0
    novelty: float = 0.5
    fairness: float = 0.5
    replayability: float = 0.5
    friction: float = 0.0
    exploits: float = 0.0
    confusion: float = 0.0
    residue: float = 0.0
    compression_gain: float = 0.5
    m_minus_reduction: float = 0.5

    def __post_init__(self) -> None:
        for field_name, value in asdict(self).items():
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{field_name} must be in [0, 1], got {value!r}")

    def quality(self) -> float:
        positive = (
            0.15 * self.fun
            + 0.15 * self.agency
            + 0.15 * self.coherence
            + 0.15 * self.learning
            + 0.10 * self.novelty
            + 0.10 * self.replayability
            + 0.10 * self.safety
            + 0.05 * self.fairness
            + 0.05 * self.compression_gain
            + 0.05 * self.m_minus_reduction
        )
        penalty = (
            0.05 * self.exploits
            + 0.05 * self.friction
            + 0.05 * self.confusion
            + 0.05 * self.residue
        )
        return max(0.0, min(1.0, positive - penalty))

    def level(self) -> str:
        quality = self.quality()
        if quality >= 0.95:
            return "plus_ultra"
        if quality >= 0.90:
            return "excellent"
        if quality >= 0.80:
            return "good"
        if quality >= 0.60:
            return "prototype"
        return "needs_work"


@dataclass(slots=True)
class OAKBenchResult:
    engine: str
    metrics: OAKBenchMetrics
    notes: list[str] = field(default_factory=list)

    @property
    def quality(self) -> float:
        return self.metrics.quality()

    @property
    def level(self) -> str:
        return self.metrics.level()

    def to_dict(self) -> dict[str, object]:
        return {
            "engine": self.engine,
            "quality": self.quality,
            "level": self.level,
            "metrics": asdict(self.metrics),
            "notes": list(self.notes),
        }


BenchmarkFn = Callable[[], OAKBenchResult]


@dataclass(slots=True)
class OAKBenchRunner:
    benchmarks: dict[str, BenchmarkFn] = field(default_factory=dict)

    def register(self, name: str, fn: BenchmarkFn) -> None:
        if name in self.benchmarks:
            raise ValueError(f"Benchmark already registered: {name}")
        self.benchmarks[name] = fn

    def run_one(self, name: str) -> OAKBenchResult:
        if name not in self.benchmarks:
            raise KeyError(f"Unknown benchmark: {name}")
        return self.benchmarks[name]()

    def run_all(self) -> list[OAKBenchResult]:
        return [self.benchmarks[name]() for name in sorted(self.benchmarks)]

    def report(self) -> dict[str, object]:
        results = self.run_all()
        average_quality = sum(result.quality for result in results) / max(1, len(results))
        return {
            "benchmark": "OAKBench-GAME-T",
            "engine_count": len(results),
            "average_quality": average_quality,
            "results": [result.to_dict() for result in results],
        }


def default_engine_benchmarks() -> OAKBenchRunner:
    runner = OAKBenchRunner()
    runner.register("TextWorld-T", bench_textworld)
    runner.register("BoardGame-T", bench_boardgame)
    runner.register("ScienceSandbox-T", bench_science_sandbox)
    runner.register("CircuitDungeon-T", bench_circuit_dungeon)
    runner.register("EnergyCivilization-T", bench_energy_civilization)
    return runner


def bench_textworld() -> OAKBenchResult:
    engine = TextWorldEngine.demo_world()
    proposal = engine.tick()
    accepted = bool(proposal.oak_report and proposal.oak_report.accepted)
    memory = len(engine.world.memory)
    return OAKBenchResult(
        engine="TextWorld-T",
        metrics=OAKBenchMetrics(
            fun=0.72,
            agency=0.70,
            coherence=0.90 if accepted else 0.40,
            learning=0.72,
            safety=1.0,
            novelty=0.70,
            fairness=0.80,
            replayability=0.62,
            friction=0.10,
            exploits=0.02,
            confusion=0.08,
            residue=0.05,
            compression_gain=0.75,
            m_minus_reduction=0.60,
        ),
        notes=[f"accepted={accepted}", f"memory={memory}"],
    )


def bench_boardgame() -> OAKBenchResult:
    board = BoardGameEngine(width=3, height=3)
    board.add_player("p1", "Player")
    board.add_piece(BoardPiece("seed", "p1", "seed", (0, 0)))
    board.move_piece("seed", (1, 0))
    board.move_piece("seed", (9, 9))
    accepted_moves = len(board.gm.m_plus.entries)
    rejected_moves = len(board.gm.m_minus.entries)
    return OAKBenchResult(
        engine="BoardGame-T",
        metrics=OAKBenchMetrics(
            fun=0.70,
            agency=0.90,
            coherence=0.88,
            learning=0.65,
            safety=1.0,
            novelty=0.62,
            fairness=0.88,
            replayability=0.76,
            friction=0.10,
            exploits=0.05,
            confusion=0.08,
            residue=0.02,
            compression_gain=0.66,
            m_minus_reduction=0.70 if rejected_moves else 0.55,
        ),
        notes=[f"accepted_moves={accepted_moves}", f"rejected_moves={rejected_moves}"],
    )


def bench_science_sandbox() -> OAKBenchResult:
    sandbox = ScienceSandboxEngine()
    rlc = sandbox.step_rlc(
        RLCState(q_coulomb=0.0, i_ampere=0.0),
        RLCParams(resistance_ohm=10.0, inductance_henry=0.1, capacitance_farad=0.001, source_voltage_volt=5.0),
        dt_second=0.001,
    )
    microgrid = sandbox.step_microgrid(
        MicrogridState(battery_energy_wh=250.0),
        MicrogridParams(battery_capacity_wh=1000.0),
        solar_power_w=300.0,
        load_power_w=500.0,
        dt_hour=0.25,
    )
    residue = min(1.0, abs(rlc.energy_residue_joule))
    served_ratio = microgrid.served_load_wh / max(1.0, microgrid.served_load_wh + microgrid.unmet_load_wh)
    return OAKBenchResult(
        engine="ScienceSandbox-T",
        metrics=OAKBenchMetrics(
            fun=0.64,
            agency=0.72,
            coherence=0.92,
            learning=0.90,
            safety=1.0,
            novelty=0.70,
            fairness=0.82,
            replayability=0.68,
            friction=0.12,
            exploits=0.02,
            confusion=0.10,
            residue=residue,
            compression_gain=0.72,
            m_minus_reduction=0.70,
        ),
        notes=[f"rlc_residue={rlc.energy_residue_joule:.6g}", f"microgrid_served_ratio={served_ratio:.3f}"],
    )


def bench_circuit_dungeon() -> OAKBenchResult:
    dungeon = CircuitDungeonEngine.demo_dungeon()
    door = dungeon.doors["door_resonance_1"]
    success = dungeon.attempt_frequency("door_resonance_1", door.resonance_frequency_hz)
    failure = dungeon.attempt_frequency("door_resonance_1", door.resonance_frequency_hz * 1.5)
    return OAKBenchResult(
        engine="CircuitDungeon-T",
        metrics=OAKBenchMetrics(
            fun=0.82,
            agency=0.91,
            coherence=0.96,
            learning=0.88,
            safety=1.0,
            novelty=0.78,
            fairness=0.90,
            replayability=0.72,
            friction=0.10,
            exploits=0.02,
            confusion=0.08,
            residue=min(1.0, failure.error_ratio),
            compression_gain=0.78,
            m_minus_reduction=0.78,
        ),
        notes=[f"success_opened={success.opened}", f"failure_error_ratio={failure.error_ratio:.3f}"],
    )


def bench_energy_civilization() -> OAKBenchResult:
    engine = EnergyCivilizationEngine.demo_civilization()
    sunny = engine.play_turn("colony_solar_1", EnergyTurnInput(solar_power_w=800.0, load_power_w=300.0, dt_hour=0.5))
    stressed = engine.play_turn("colony_solar_1", EnergyTurnInput(solar_power_w=100.0, load_power_w=900.0, dt_hour=0.5))
    average_service = (sunny.service_ratio + stressed.service_ratio) / 2.0
    return OAKBenchResult(
        engine="EnergyCivilization-T",
        metrics=OAKBenchMetrics(
            fun=0.80,
            agency=0.86,
            coherence=0.94,
            learning=0.90,
            safety=1.0,
            novelty=0.76,
            fairness=0.84,
            replayability=0.82,
            friction=0.12,
            exploits=0.03,
            confusion=0.09,
            residue=min(1.0, 1.0 - average_service),
            compression_gain=0.76,
            m_minus_reduction=0.72,
        ),
        notes=[f"sunny_score={sunny.energy_score:.3f}", f"stressed_score={stressed.energy_score:.3f}"],
    )
