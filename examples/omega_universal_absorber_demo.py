from __future__ import annotations

import tempfile
from pathlib import Path

from omega_prof_poly_t.universal_absorber import absorb_path, write_outputs


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "mini_corpus"
        root.mkdir()
        (root / "omega_theory.md").write_text(
            """# Ω-PDF-HYPERGRAPH-GITHUB-T\n\n"
            "Theory: every PDF page becomes provenance-preserving chunks, claim candidates, "
            "HGFM hyperedges, CVCD compression targets, and OAK gates.\n\n"
            "OAK: extraction is not proof; IP and brevet material stays private until review.\n"
            """,
            encoding="utf-8",
        )
        result = absorb_path(root)
        files = write_outputs(result, Path(tmp) / "generated")
        print("objects", result.oak_report["source_objects"])
        print("chunks", result.oak_report["chunks"])
        print("claims", result.oak_report["claim_candidates"])
        print("oak_status", result.oak_report["status"])
        for name, path in files.items():
            print(name, path)


if __name__ == "__main__":
    main()
