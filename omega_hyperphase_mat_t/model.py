from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from math import exp, isfinite, log
from typing import Callable, Iterable, Mapping, Sequence


SpinConfiguration = tuple[int, ...]
Observable = Callable[[SpinConfiguration, "HypergraphState"], float]


@dataclass(frozen=True)
class Hyperedge:
    """A finite effective many-body interaction over material degrees of freedom.

    The reference model uses Ising-like ±1 variables so that arbitrary k-body
    interactions can be enumerated exactly for small systems. The hypergraph is
    a representation of interactions, not a claim that matter is literally a
    mathematical hypergraph.
    """

    nodes: tuple[int, ...]
    coupling: float
    label: str = "interaction"
    active: bool = True

    def __post_init__(self) -> None:
        if not self.nodes:
            raise ValueError("a hyperedge must contain at least one node")
        if len(set(self.nodes)) != len(self.nodes):
            raise ValueError("hyperedge nodes must be unique")
        if min(self.nodes) < 0:
            raise ValueError("node indices must be non-negative")
        if not isfinite(self.coupling):
            raise ValueError("coupling must be finite")

    @property
    def order(self) -> int:
        return len(self.nodes)

    def energy(self, spins: SpinConfiguration) -> float:
        if not self.active:
            return 0.0
        value = 1
        for node in self.nodes:
            try:
                value *= spins[node]
            except IndexError as exc:
                raise ValueError(f"node {node} is outside a {len(spins)}-site configuration") from exc
        return -self.coupling * value


@dataclass(frozen=True)
class HypergraphState:
    """One admissible interaction topology in a finite statistical ensemble."""

    name: str
    edges: tuple[Hyperedge, ...] = ()
    structural_energy: float = 0.0
    metadata: Mapping[str, str] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("hypergraph state name must be non-empty")
        if not isfinite(self.structural_energy):
            raise ValueError("structural_energy must be finite")

    def interaction_energy(self, spins: SpinConfiguration) -> float:
        return sum(edge.energy(spins) for edge in self.edges)

    def total_energy(self, spins: SpinConfiguration, fields: Sequence[float] | None = None) -> float:
        energy = self.structural_energy + self.interaction_energy(spins)
        if fields is not None:
            if len(fields) != len(spins):
                raise ValueError("fields must have one value per site")
            energy -= sum(h * s for h, s in zip(fields, spins))
        return energy

    @property
    def active_edge_count(self) -> int:
        return sum(edge.active for edge in self.edges)

    def order_histogram(self) -> dict[int, int]:
        out: dict[int, int] = {}
        for edge in self.edges:
            if edge.active:
                out[edge.order] = out.get(edge.order, 0) + 1
        return out


@dataclass(frozen=True)
class Microstate:
    spins: SpinConfiguration
    hypergraph_index: int
    energy: float
    probability: float


@dataclass(frozen=True)
class ThermodynamicState:
    temperature: float
    log_partition: float
    free_energy: float
    internal_energy: float
    entropy: float
    topology_entropy: float
    conditional_configuration_entropy: float
    entropy_chain_residual: float
    mean_magnetization: float
    mean_abs_magnetization: float
    susceptibility: float
    heat_capacity: float
    mean_active_edge_count: float
    hypergraph_probabilities: tuple[float, ...]
    microstates: tuple[Microstate, ...]

    @property
    def finite_size_only(self) -> bool:
        return True


@dataclass(frozen=True)
class CrossoverMarker:
    """Finite-size response maximum, deliberately not named a phase transition."""

    temperature: float
    observable: str
    value: float
    classification: str = "FINITE_SIZE_CROSSOVER"


class ExactHypergraphEnsemble:
    """Exact enumerator for small Ising-like hypergraph material models.

    Complexity grows as 2**N times the number of admissible hypergraph states,
    so this is a small-system truth model for tests and benchmarks rather than
    a bulk-material solver.
    """

    def __init__(
        self,
        n_sites: int,
        hypergraphs: Iterable[HypergraphState],
        *,
        fields: Sequence[float] | None = None,
        k_b: float = 1.0,
    ) -> None:
        if n_sites <= 0:
            raise ValueError("n_sites must be positive")
        if k_b <= 0 or not isfinite(k_b):
            raise ValueError("k_b must be finite and positive")
        graphs = tuple(hypergraphs)
        if not graphs:
            raise ValueError("at least one hypergraph state is required")
        if fields is not None and len(fields) != n_sites:
            raise ValueError("fields must have one value per site")
        for graph in graphs:
            for edge in graph.edges:
                if max(edge.nodes) >= n_sites:
                    raise ValueError(f"edge {edge.label!r} references a site outside n_sites={n_sites}")
        self.n_sites = n_sites
        self.hypergraphs = graphs
        self.fields = tuple(fields) if fields is not None else None
        self.k_b = float(k_b)

    @property
    def topology_is_dynamic(self) -> bool:
        return len(self.hypergraphs) > 1

    def configurations(self) -> tuple[SpinConfiguration, ...]:
        return tuple(product((-1, 1), repeat=self.n_sites))

    def _raw_states(self) -> list[tuple[SpinConfiguration, int, float]]:
        rows: list[tuple[SpinConfiguration, int, float]] = []
        for graph_index, graph in enumerate(self.hypergraphs):
            for spins in self.configurations():
                rows.append((spins, graph_index, graph.total_energy(spins, self.fields)))
        return rows

    def evaluate(self, temperature: float) -> ThermodynamicState:
        if temperature <= 0 or not isfinite(temperature):
            raise ValueError("temperature must be finite and positive")
        beta = 1.0 / (self.k_b * temperature)
        rows = self._raw_states()
        min_energy = min(row[2] for row in rows)
        scaled = [exp(-beta * (energy - min_energy)) for _, _, energy in rows]
        z_scaled = sum(scaled)
        log_z = -beta * min_energy + log(z_scaled)
        probabilities = [weight / z_scaled for weight in scaled]

        mean_energy = sum(p * row[2] for p, row in zip(probabilities, rows))
        mean_energy2 = sum(p * row[2] ** 2 for p, row in zip(probabilities, rows))
        energy_variance = max(0.0, mean_energy2 - mean_energy**2)
        free_energy = -self.k_b * temperature * log_z
        entropy = self.k_b * (log_z + beta * mean_energy)
        heat_capacity = energy_variance / (self.k_b * temperature**2)

        magnetizations = [sum(spins) / self.n_sites for spins, _, _ in rows]
        mean_m = sum(p * m for p, m in zip(probabilities, magnetizations))
        mean_m2 = sum(p * m * m for p, m in zip(probabilities, magnetizations))
        mean_abs_m = sum(p * abs(m) for p, m in zip(probabilities, magnetizations))
        susceptibility = self.n_sites * max(0.0, mean_m2 - mean_m**2) / (self.k_b * temperature)

        graph_probs = [0.0] * len(self.hypergraphs)
        for p, (_, graph_index, _) in zip(probabilities, rows):
            graph_probs[graph_index] += p
        topology_entropy = -self.k_b * sum(p * log(p) for p in graph_probs if p > 0.0)

        conditional = 0.0
        for graph_index, p_graph in enumerate(graph_probs):
            if p_graph == 0.0:
                continue
            conditional_entropy = 0.0
            for p, (_, idx, _) in zip(probabilities, rows):
                if idx == graph_index and p > 0.0:
                    p_cond = p / p_graph
                    conditional_entropy -= self.k_b * p_cond * log(p_cond)
            conditional += p_graph * conditional_entropy
        residual = entropy - (topology_entropy + conditional)

        mean_edges = sum(
            p * self.hypergraphs[idx].active_edge_count
            for p, (_, idx, _) in zip(probabilities, rows)
        )
        microstates = tuple(
            Microstate(spins=spins, hypergraph_index=idx, energy=energy, probability=p)
            for p, (spins, idx, energy) in zip(probabilities, rows)
        )
        return ThermodynamicState(
            temperature=temperature,
            log_partition=log_z,
            free_energy=free_energy,
            internal_energy=mean_energy,
            entropy=entropy,
            topology_entropy=topology_entropy,
            conditional_configuration_entropy=conditional,
            entropy_chain_residual=residual,
            mean_magnetization=mean_m,
            mean_abs_magnetization=mean_abs_m,
            susceptibility=susceptibility,
            heat_capacity=heat_capacity,
            mean_active_edge_count=mean_edges,
            hypergraph_probabilities=tuple(graph_probs),
            microstates=microstates,
        )

    def expectation(self, temperature: float, observable: Observable) -> float:
        state = self.evaluate(temperature)
        return sum(
            micro.probability * observable(micro.spins, self.hypergraphs[micro.hypergraph_index])
            for micro in state.microstates
        )

    def covariance(self, temperature: float, a: Observable, b: Observable) -> float:
        state = self.evaluate(temperature)
        values_a = [a(m.spins, self.hypergraphs[m.hypergraph_index]) for m in state.microstates]
        values_b = [b(m.spins, self.hypergraphs[m.hypergraph_index]) for m in state.microstates]
        mean_a = sum(m.probability * v for m, v in zip(state.microstates, values_a))
        mean_b = sum(m.probability * v for m, v in zip(state.microstates, values_b))
        mean_ab = sum(
            m.probability * va * vb
            for m, va, vb in zip(state.microstates, values_a, values_b)
        )
        return mean_ab - mean_a * mean_b

    def sweep(self, temperatures: Iterable[float]) -> tuple[ThermodynamicState, ...]:
        return tuple(self.evaluate(t) for t in temperatures)


def finite_size_crossover(
    states: Sequence[ThermodynamicState],
    *,
    observable: str = "heat_capacity",
) -> CrossoverMarker:
    if not states:
        raise ValueError("states must be non-empty")
    if observable not in {"heat_capacity", "susceptibility"}:
        raise ValueError("observable must be 'heat_capacity' or 'susceptibility'")
    peak = max(states, key=lambda state: getattr(state, observable))
    return CrossoverMarker(peak.temperature, observable, getattr(peak, observable))
