from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from omega_solids_t.atlas import iter_archetypes
from omega_solids_t.inverse_design import PropertyObjective, SolidCompiler, maximum_porosity
from omega_solids_t.pipeline import SolidPipeline


def main() -> None:
    output = Path("generated/omega_solids_t/demo")
    pipeline = SolidPipeline()
    genomes = tuple(iter_archetypes())

    for genome in genomes:
        report = pipeline.analyze(genome)
        pipeline.materialize(report, output / genome.identifier)

    compiler = SolidCompiler(
        (
            PropertyObjective(
                "young_modulus",
                target=100e9,
                unit="Pa",
                tolerance=50e9,
                mode="maximize",
            ),
        ),
        (maximum_porosity(0.4),),
    )
    ranking = [candidate.to_dict() for candidate in compiler.rank(genomes)]
    (output / "young-modulus-ranking.json").write_text(
        json.dumps(ranking, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(ranking[:3], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
