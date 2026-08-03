import json
from pathlib import Path

import numpy as np

from omega_vla_t.r02 import (
    CATALOG,
    CampaignConfig,
    FrontierCodec,
    TheoremFactory,
    analyze_residual,
    audit_max_system,
    run_campaign,
    spectral_dna,
)
from omega_vla_t.r02.cli import main
from omega_vla_t.r02.dedup import ContentDeduplicator, content_digest
from omega_vla_t.r02.models import EpistemicStatus, ResearchArtifact
from omega_vla_t.r02.store import ShardedJSONLStore


def test_catalog_has_large_logical_frontier_without_permanent_cap() -> None:
    summary = CATALOG.summary()
    assert summary["layers"] == 32
    assert summary["programs"] == 64
    assert summary["logical_frontier_cells"] > 10**12
    assert summary["permanent_total_cap"] is None


def test_frontier_codec_round_trip_at_boundaries_and_samples() -> None:
    codec = FrontierCodec()
    indices = [0, 1, codec.size // 2, codec.size - 2, codec.size - 1]
    indices.extend(codec.sample_indices(64, seed=23))
    for index in indices:
        address = codec.decode(index)
        assert codec.encode(address) == index
        assert address.canonical().startswith("layer=")
        assert len(address.digest()) == 64


def test_lazy_index_stream_is_unique_and_deterministic() -> None:
    codec = FrontierCodec()
    first = tuple(codec.iter_indices(2048, seed=91))
    second = tuple(codec.iter_indices(2048, seed=91))
    other = tuple(codec.iter_indices(2048, seed=92))
    assert first == second
    assert first != other
    assert len(first) == len(set(first))
    assert min(first) >= 0
    assert max(first) < codec.size


def test_theorem_factory_is_deterministic_falsifiable_and_claim_safe() -> None:
    codec = FrontierCodec()
    factory = TheoremFactory()
    address = codec.decode(codec.sample_indices(1, seed=7)[0])
    first = factory.generate(address)
    second = factory.generate(address)
    assert first == second
    assert first.theorem_claimed is False
    assert first.status not in {
        EpistemicStatus.FORMALLY_VERIFIED,
        EpistemicStatus.CANONICAL,
    }
    assert first.hypotheses
    assert first.baselines
    assert first.falsifiers
    assert first.expected_artifacts
    assert 0.0 <= first.utility_score() <= 1.0


def test_research_artifact_rejects_unsupported_theorem_claim() -> None:
    try:
        ResearchArtifact(
            artifact_id="bad",
            artifact_type="claim",
            title="Unsupported",
            definition="A generated statement.",
            status=EpistemicStatus.PROPOSITION,
            theorem_claimed=True,
        )
    except ValueError as exc:
        assert "proof-level" in str(exc)
    else:
        raise AssertionError("unsupported theorem claim should fail")


def test_content_dedup_ignores_volatile_metadata() -> None:
    left = {"cell": 1, "generated_at": "a", "nested": {"x": 2.0}}
    right = {"nested": {"x": 2.0}, "generated_at": "b", "cell": 1}
    assert content_digest(left) == content_digest(right)
    report = ContentDeduplicator().filter([left, right])
    assert len(report.accepted) == 1
    assert len(report.duplicates) == 1
    assert report.duplicate_rate == 0.5


def test_spectral_dna_known_normal_matrix() -> None:
    matrix = np.array([[2.0, -1.0], [1.0, 2.0]])
    dna = spectral_dna(matrix, pseudospectral_points=6)
    assert dna.numerical_rank == 2
    assert np.isclose(dna.spectral_radius, np.sqrt(5.0))
    assert np.isclose(dna.condition_number, 1.0)
    assert dna.normality_residual < 1e-12
    assert len(dna.pseudospectral_probe) == 6
    assert dna.theorem_claimed is False


def test_spectral_dna_rejects_nonsquare_and_nonfinite() -> None:
    for matrix in (
        np.ones((2, 3)),
        np.array([[1.0, np.nan], [0.0, 1.0]]),
    ):
        try:
            spectral_dna(matrix)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid matrix should be rejected")


def test_residual_intelligence_detects_oscillatory_structure() -> None:
    axis = np.linspace(0.0, 16.0 * np.pi, 512)
    profile = analyze_residual(np.sin(axis))
    assert profile.structured
    assert profile.classification in {
        "correlated",
        "oscillatory_or_multiscale",
    }
    assert profile.candidate_actions
    assert profile.scientific_validation_claimed is False


def test_residual_intelligence_handles_empty_and_sparse() -> None:
    empty = analyze_residual([])
    assert empty.classification == "negligible"
    sparse_values = np.zeros(100)
    sparse_values[[3, 70]] = [8.0, -9.0]
    sparse = analyze_residual(sparse_values)
    assert sparse.structured
    assert sparse.classification == "sparse_or_event_like"


def test_campaign_is_finite_deterministic_and_without_permanent_cap() -> None:
    config = CampaignConfig(
        work_items=1025,
        seed=44,
        initial_batch=64,
        min_batch=16,
        max_batch=256,
    )
    first = run_campaign(config).to_dict()
    second = run_campaign(config).to_dict()
    assert first == second
    assert first["proposed_cells"] == 1025
    assert first["accepted_cells"] == 1025
    assert first["duplicates"] == 0
    assert first["permanent_total_cap"] is None
    assert first["theorem_claimed"] is False
    assert first["formal_proof_claimed"] is False


def test_quality_filter_can_reject_without_promoting_claims() -> None:
    report = run_campaign(
        CampaignConfig(
            work_items=256,
            seed=5,
            initial_batch=32,
            min_batch=8,
            max_batch=64,
            min_utility=0.8,
            max_risk=0.4,
        )
    )
    assert report.proposed_cells == 256
    assert report.accepted_cells < 256
    assert report.rejected_quality > 0
    assert report.theorem_claimed is False


def test_sharded_store_creates_receipts_checkpoint_and_manifest(tmp_path: Path) -> None:
    records = [{"i": index, "value": index**2} for index in range(11)]
    store = ShardedJSONLStore(tmp_path, records_per_shard=4, prefix="fixture")
    manifest = store.write(records, checkpoint={"next": 11})
    assert manifest.records == 11
    assert len(manifest.shards) == 3
    assert sum(shard.records for shard in manifest.shards) == 11
    assert len(manifest.aggregate_sha256) == 64
    assert store.read_checkpoint() == {"next": 11}
    loaded = store.read_manifest()
    assert loaded["records"] == 11
    for shard in manifest.shards:
        assert (tmp_path / shard.path).exists()


def test_campaign_can_emit_sharded_evidence(tmp_path: Path) -> None:
    report = run_campaign(
        CampaignConfig(
            work_items=33,
            seed=2,
            initial_batch=8,
            min_batch=4,
            max_batch=16,
            records_per_shard=10,
            output_dir=str(tmp_path),
        )
    )
    assert report.store_manifest is not None
    assert report.store_manifest.records == report.accepted_cells
    assert (tmp_path / "manifest.json").exists()
    checkpoint = json.loads((tmp_path / "checkpoint.json").read_text())
    assert checkpoint["permanent_total_cap"] is None


def test_max_oak_report_passes_and_is_claim_safe() -> None:
    report = audit_max_system(seed=17, campaign_items=257)
    assert report.passed
    assert report.status == "OAK_PASS_SOFTWARE_RESEARCH_FIXTURES_R0_2_MAX"
    assert report.logical_frontier_cells == CATALOG.logical_frontier_size()
    assert report.theorem_claimed is False
    assert report.formal_proof_claimed is False
    assert report.scientific_validation_claimed is False


def test_cli_manifest_sample_benchmark_and_campaign(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest-output.json"
    assert main(["manifest", "--output", str(manifest_path)]) == 0
    manifest = json.loads(manifest_path.read_text())
    assert manifest["logical_frontier_cells"] > 10**12

    sample_path = tmp_path / "sample.json"
    assert main(["sample", "--count", "5", "--seed", "9", "--output", str(sample_path)]) == 0
    sample = json.loads(sample_path.read_text())
    assert sample["count"] == 5
    assert sample["theorem_claimed"] is False

    benchmark_path = tmp_path / "benchmark.json"
    assert main(["benchmark", "--output", str(benchmark_path)]) == 0
    benchmark = json.loads(benchmark_path.read_text())
    assert benchmark["passed"] is True

    report_path = tmp_path / "campaign-report.json"
    generated = tmp_path / "generated"
    assert main(
        [
            "campaign",
            "--work-items",
            "21",
            "--initial-batch",
            "8",
            "--min-batch",
            "4",
            "--max-batch",
            "16",
            "--output-dir",
            str(generated),
            "--report",
            str(report_path),
        ]
    ) == 0
    report = json.loads(report_path.read_text())
    assert report["proposed_cells"] == 21
    assert (generated / "manifest.json").exists()
