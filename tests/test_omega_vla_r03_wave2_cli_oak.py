import json
from pathlib import Path

from omega_vla_t.r03.wave2.benchmarks import logical_benchmark_frontier, run_atlas
from omega_vla_t.r03.wave2.cli import main
from omega_vla_t.r03.wave2.oak_wave2 import audit_wave2


def test_logical_benchmark_frontier_is_large_without_permanent_cap() -> None:
    frontier = logical_benchmark_frontier()
    assert frontier["logical_cases"] > 10**12
    assert frontier["permanent_total_cap"] is None
    assert frontier["materialized_cases"] == 0


def test_deterministic_benchmark_atlas() -> None:
    first = run_atlas(dimensions=(4, 8), seed=2026, tolerance=1e-9)
    second = run_atlas(dimensions=(4, 8), seed=2026, tolerance=1e-9)
    assert first.all_passed
    assert second.all_passed
    assert first.deterministic_digest == second.deterministic_digest
    assert first.to_dict() == second.to_dict()
    assert first.catalog_families >= 300
    assert len(first.cases) >= 20
    assert first.theorem_claimed is False


def test_wave2_oak_passes_and_is_claim_safe() -> None:
    report = audit_wave2(tolerance=1e-9)
    assert report.passed
    assert report.status == "OAK_PASS_SOFTWARE_RESEARCH_FIXTURES_R0_3_WAVE_2"
    assert report.family_count >= 300
    assert report.logical_benchmark_cases > 10**12
    assert report.theorem_claimed is False
    assert report.formal_proof_claimed is False
    assert report.scientific_validation_claimed is False
    assert all(check.passed for check in report.checks)


def test_cli_manifest_catalog_and_materialize(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    assert main(["manifest", "--output", str(manifest_path)]) == 0
    manifest = json.loads(manifest_path.read_text())
    assert manifest["catalog"]["families"] >= 300
    assert manifest["benchmark_frontier"]["logical_cases"] > 10**12
    assert manifest["theorem_claimed"] is False

    catalog_path = tmp_path / "catalog.json"
    assert main(
        [
            "catalog",
            "--realm",
            "physics",
            "--limit",
            "10",
            "--output",
            str(catalog_path),
        ]
    ) == 0
    catalog = json.loads(catalog_path.read_text())
    assert catalog["total_matches"] >= 30
    assert catalog["returned"] == 10

    materialized_path = tmp_path / "laplacian.json"
    assert main(
        [
            "materialize",
            "discrete_geometry.graphs_complexes.combinatorial_laplacian",
            "--dimension",
            "6",
            "--dense",
            "--output",
            str(materialized_path),
        ]
    ) == 0
    materialized = json.loads(materialized_path.read_text())
    assert materialized["matrix"]["shape"] == [6, 6]
    assert len(materialized["dense_real"]) == 6


def test_cli_properties_commutant_and_matrix_functions(tmp_path: Path) -> None:
    properties_path = tmp_path / "properties.json"
    assert main(
        [
            "properties",
            "[[1,0],[0,2]]",
            "--output",
            str(properties_path),
        ]
    ) == 0
    properties = json.loads(properties_path.read_text())
    by_name = {item["property_name"]: item for item in properties["evidence"]}
    assert by_name["positive_definite"]["supported"] is True
    assert by_name["unitary"]["supported"] is False

    commutant_path = tmp_path / "commutant.json"
    assert main(
        [
            "commutant",
            "[[1,0],[0,2]]",
            "--output",
            str(commutant_path),
        ]
    ) == 0
    commutant = json.loads(commutant_path.read_text())
    assert commutant["nullity"] == 2
    assert commutant["identity_in_span_residual"] < 1e-12

    for function, matrix in (
        ("exp", "[[0,-0.2],[0.2,0]]"),
        ("log", "[[1,0],[0,2]]"),
        ("sqrt", "[[1,0],[0,4]]"),
        ("sign", "[[-2,0],[0,3]]"),
    ):
        output = tmp_path / f"{function}.json"
        assert main(
            ["matrix-function", function, matrix, "--output", str(output)]
        ) == 0
        report = json.loads(output.read_text())
        assert report["passed"] is True
        assert report["theorem_claimed"] is False


def test_cli_benchmark_genome_and_oak(tmp_path: Path) -> None:
    benchmark_path = tmp_path / "benchmark.json"
    assert main(
        [
            "benchmark",
            "--dimensions",
            "4,8",
            "--output",
            str(benchmark_path),
        ]
    ) == 0
    benchmark = json.loads(benchmark_path.read_text())
    assert benchmark["all_passed"] is True
    assert benchmark["environmental_timing_included"] is False

    genome_path = tmp_path / "genome.json"
    database = tmp_path / "genomes.sqlite3"
    assert main(
        [
            "genome-demo",
            "--database",
            str(database),
            "--output",
            str(genome_path),
        ]
    ) == 0
    genome = json.loads(genome_path.read_text())
    assert genome["inserted"] is True
    assert genome["registry"]["genomes"] == 1
    assert genome["genome"]["theorem_claimed"] is False

    oak_path = tmp_path / "oak.json"
    assert main(["oak", "--output", str(oak_path)]) == 0
    oak = json.loads(oak_path.read_text())
    assert oak["passed"] is True
    assert oak["formal_proof_claimed"] is False
