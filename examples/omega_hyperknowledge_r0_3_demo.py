from __future__ import annotations

from pathlib import Path

from omega_wiki_t.hyperknowledge import HyperKnowledgeCompiler
from omega_wiki_t.knowledge_cell import KnowledgeCell


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cells = [
        KnowledgeCell.read(ROOT / "data/knowledge_cells/ffwt_hac_cvcd_r0_3.json"),
        KnowledgeCell.read(ROOT / "data/knowledge_cells/omega_lin_t_r0_3.json"),
    ]
    bundle = HyperKnowledgeCompiler.compile(cells)
    output = HyperKnowledgeCompiler.write(
        bundle,
        ROOT / "generated/omega_wiki_t/hyperknowledge-r0-3",
    )
    print(f"R0.3 bundle written to {output}")
    print(bundle["manifest"])


if __name__ == "__main__":
    main()
