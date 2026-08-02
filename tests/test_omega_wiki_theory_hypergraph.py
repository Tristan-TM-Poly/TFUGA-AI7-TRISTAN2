from __future__ import annotations

import json
from pathlib import Path

from omega_wiki_t.theory_hypergraph import TheoryHypergraphBuilder, node_key


def _write_fixture(root: Path) -> tuple[Path, Path, Path]:
    canon = root / "theory-canon.json"
    canon.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "name": "TFUGA",
                        "role": "generative theory root",
                        "status": "canonical fertile",
                        "risk": "overgeneralization",
                        "next": "define executable claim cards",
                    },
                    {
                        "name": "HGFM",
                        "role": "hypergraph representation",
                        "status": "operational scaffold",
                        "risk": "metaphor without schema",
                        "next": "export GraphML",
                    },
                    {
                        "name": "OAK",
                        "role": "verification gates",
                        "status": "core safety layer",
                        "risk": "false promotion",
                        "next": "claim matrix",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    master = root / "master.md"
    master.write_text(
        """### Layer A - Pre-axiomatic core
Canonical primitives:
- `OAK`: verification discipline.

### Layer B - Mathematical core
Initial candidates:
- HGFM: hypergraph representation.
- CVCD: compressed virtual computation.
- DCT++: evidence packet.

raw intuition -> formal object -> equation -> proof/test -> algorithm -> simulation -> prototype -> measurement -> OAK status -> canon update
""",
        encoding="utf-8",
    )
    index = root / "index.md"
    index.write_text(
        """| Rank | System | Primary repo/path | Current status | Why it matters | Next OAK action |
|---:|---|---|---|---|---|
| 1 | OAK + DCT-Ω | `docs/canon.md` | C/X | Converts theory into proof and test packets. | Generate packets. |
| 2 | AUTO² Kernel | `omega_auto2_kernel/` | D | Executable workflow compiler with tests. | Add CI. |
""",
        encoding="utf-8",
    )
    return canon, master, index


def test_builds_valid_traceable_hypergraph(tmp_path: Path) -> None:
    canon, master, index = _write_fixture(tmp_path)
    graph = TheoryHypergraphBuilder.from_files(
        theory_canon_json=canon,
        master_canon=master,
        system_index=index,
    )

    assert graph.validate() == []
    labels = {node.label for node in graph.nodes}
    assert {"TFUGA", "HGFM", "OAK", "CVCD", "DCT-Ω / DCT++"} <= labels
    cvcd = next(node for node in graph.nodes if node_key(node.label) == node_key("CVCD"))
    assert cvcd.role == "compressed virtual computation."
    assert str(master) in cvcd.source_paths
    assert any(edge.kind == "root_generates_representation" for edge in graph.hyperedges)
    assert any(edge.kind == "verification_governs" for edge in graph.hyperedges)
    assert graph.manifest["oak_status"] == "REPOSITORY_CANON_ABSORBED_NOT_SCIENTIFICALLY_CERTIFIED"


def test_ids_are_deterministic_and_status_is_not_downgraded(tmp_path: Path) -> None:
    canon, master, index = _write_fixture(tmp_path)
    first = TheoryHypergraphBuilder.from_files(
        theory_canon_json=canon,
        master_canon=master,
        system_index=index,
    )
    second = TheoryHypergraphBuilder.from_files(
        theory_canon_json=canon,
        master_canon=master,
        system_index=index,
    )

    assert [node.node_id for node in first.nodes] == [node.node_id for node in second.nodes]
    oak = next(node for node in first.nodes if node_key(node.label) == node_key("OAK"))
    assert oak.oak_status == "core safety layer"


def test_writer_emits_machine_and_human_views(tmp_path: Path) -> None:
    canon, master, index = _write_fixture(tmp_path)
    graph = TheoryHypergraphBuilder.from_files(
        theory_canon_json=canon,
        master_canon=master,
        system_index=index,
    )
    output = TheoryHypergraphBuilder.write(graph, tmp_path / "out")

    expected = {
        "manifest.json",
        "knowledge-hypergraph.json",
        "knowledge-hypergraph.graphml",
        "theory-nodes.jsonl",
        "knowledge-hyperedges.jsonl",
        "useful-knowledge.md",
    }
    assert expected == {path.name for path in output.iterdir()}
    assert "hyperedge:" in (output / "knowledge-hypergraph.graphml").read_text(encoding="utf-8")
    assert "Colonne vertébrale utile" in (output / "useful-knowledge.md").read_text(encoding="utf-8")
