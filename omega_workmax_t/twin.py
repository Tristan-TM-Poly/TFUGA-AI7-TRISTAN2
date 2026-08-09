from __future__ import annotations

from dataclasses import asdict, dataclass
import heapq

from .graph import WorkHypergraph
from .planner import priority_score


@dataclass(frozen=True)
class TwinResult:
    workers: int
    wall_seconds: float
    total_work_seconds: float
    critical_path_seconds: float
    theoretical_lower_bound_seconds: float
    utilization: float
    speedup_vs_serial: float
    scheduling_efficiency: float
    completion_order: tuple[str, ...]

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["completion_order"] = list(self.completion_order)
        return payload


def simulate(graph: WorkHypergraph, workers: int) -> TwinResult:
    if workers < 1:
        raise ValueError("workers must be positive")
    if not graph.packets:
        return TwinResult(workers, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, ())
    workers = min(workers, len(graph.packets))
    completed: set[str] = set()
    running_ids: set[str] = set()
    running: list[tuple[float, str]] = []
    completion_order: list[str] = []
    now = 0.0

    def schedule() -> None:
        nonlocal running
        candidates = [
            work_id
            for work_id in graph.ready(completed)
            if work_id not in running_ids and work_id not in completed
        ]
        candidates.sort(key=lambda work_id: (-priority_score(graph.packets[work_id], graph), work_id))
        while candidates and len(running) < workers:
            work_id = candidates.pop(0)
            finish = now + graph.packets[work_id].estimated_seconds
            heapq.heappush(running, (finish, work_id))
            running_ids.add(work_id)

    schedule()
    while running:
        now = running[0][0]
        finished_now: list[str] = []
        while running and running[0][0] == now:
            _, work_id = heapq.heappop(running)
            running_ids.remove(work_id)
            completed.add(work_id)
            finished_now.append(work_id)
        completion_order.extend(sorted(finished_now))
        schedule()

    if len(completed) != len(graph.packets):
        raise RuntimeError("twin ended with incomplete work")
    total = graph.total_work_seconds
    critical = graph.critical_path().seconds
    lower_bound = max(critical, total / workers)
    utilization = total / (now * workers) if now else 0.0
    speedup = total / now if now else 1.0
    efficiency = lower_bound / now if now else 1.0
    return TwinResult(workers, now, total, critical, lower_bound, utilization, speedup, efficiency, tuple(completion_order))


def adaptive_worker_sweep(graph: WorkHypergraph) -> tuple[TwinResult, ...]:
    """Power-of-two sweep ending at the actual finite job count.

    The workload itself defines the local endpoint; there is no permanent
    architectural worker-count ceiling encoded here.
    """
    count = len(graph.packets)
    if count == 0:
        return (simulate(graph, 1),)
    workers: list[int] = []
    value = 1
    while value < count:
        workers.append(value)
        value *= 2
    if not workers or workers[-1] != count:
        workers.append(count)
    return tuple(simulate(graph, worker_count) for worker_count in workers)
