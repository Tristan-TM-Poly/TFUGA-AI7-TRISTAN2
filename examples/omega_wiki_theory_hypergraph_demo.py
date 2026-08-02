from __future__ import annotations

import json

from omega_wiki_t.theory_hypergraph import TheoryHypergraphBuilder


def main() -> None:
    graph = TheoryHypergraphBuilder.from_files(
        theory_canon_json="interfaces/chatgpt-tristan-v2/data/theory-canon.json",
        master_canon="docs/00_MASTER_CANON_TFUGA_AI7_AIT.md",
        system_index="MASTER_SYSTEM_INDEX.md",
    )
    output = TheoryHypergraphBuilder.write(
        graph,
        "generated/omega_wiki_t/theory-canon-r0-2",
    )
    systems = [node for node in graph.nodes if node.kind == "theory_system"]
    print(
        json.dumps(
            {
                "output": str(output),
                "nodes": len(graph.nodes),
                "hyperedges": len(graph.hyperedges),
                "top_systems": [node.label for node in systems[:10]],
                "oak_status": graph.manifest["oak_status"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
