from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "tools" / "github_reactor" / "synergy_n_engine.py"
spec = importlib.util.spec_from_file_location("synergy_n_engine", MODULE_PATH)
engine = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)


def seed_repo(root: Path) -> None:
    (root / "docs" / "canon").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "docs" / "canon" / "systems.md").write_text(
        """# Canon

Ω-AUTO²-T orchestrates workflow automation with OAKGate.
Ω-ROSETTE-T extracts knowledge and provenance.
Ω-TRANSFORM-T provides mathematical transforms and CVCD compression.
Ω-ENERGY-T models physics, energy conservation, and simulation.
""",
        encoding="utf-8",
    )
    (root / "src" / "bridge.py").write_text(
        "# Ω-AUTO²-T + Ω-ROSETTE-T + OAKGate research pipeline\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_energy.py").write_text(
        "# Ω-ENERGY-T and Ω-TRANSFORM-T baseline test\n",
        encoding="utf-8",
    )


def test_discovery_and_bounded_orders(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    nodes, file_systems = engine.discover([tmp_path], max_nodes=50)
    names = {node.name for node in nodes}
    assert {"Ω-AUTO²-T", "Ω-ROSETTE-T", "Ω-TRANSFORM-T", "Ω-ENERGY-T", "OAKGate"} <= names
    results, pairs = engine.search(nodes, file_systems, max_order=4, beam=12, top=5)
    assert 2 in results
    assert all(candidate.order == order for order, values in results.items() for candidate in values)
    assert len(results[2]) <= 5
    assert pairs


def test_deterministic_candidate_ids(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    nodes, file_systems = engine.discover([tmp_path], max_nodes=50)
    first, _ = engine.search(nodes, file_systems, 3, 12, 5)
    second, _ = engine.search(nodes, file_systems, 3, 12, 5)
    assert [candidate.packet_id for candidate in first[2]] == [candidate.packet_id for candidate in second[2]]


def test_outputs_are_review_only(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    args = type("Args", (), {"max_order": 3, "beam_width": 12, "top_k": 5, "max_nodes": 50})()
    nodes, file_systems = engine.discover([tmp_path], max_nodes=50)
    results, pairs = engine.search(nodes, file_systems, 3, 12, 5)
    out = tmp_path / "reports"
    engine.write(out, [tmp_path], nodes, results, pairs, args)
    payload = json.loads((out / "synergy_n.json").read_text(encoding="utf-8"))
    assert payload["authority"] == "review_only_heuristic"
    assert payload["m_minus"]
    assert (out / "research_queue.json").exists()
    assert (out / "synergy_graph.dot").exists()
