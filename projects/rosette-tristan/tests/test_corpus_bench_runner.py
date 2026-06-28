import json
from pathlib import Path

from rosette_tristan.bench_corpus import CorpusCase, CorpusExpectation, CorpusManifest, create_minimal_corpus
from rosette_tristan.corpus_bench_runner import run_corpus_bench


def test_run_corpus_bench_minimal_corpus(tmp_path: Path):
    manifest_path = create_minimal_corpus(tmp_path / "corpus")
    report = run_corpus_bench(manifest_path, tmp_path / "out")
    assert report.oak_status == "corpus_bench_passed_not_certified"
    assert report.aggregate["case_count"] == 2
    assert report.aggregate["case_pass_rate"] == 1.0
    assert (tmp_path / "out" / "corpus_bench_report.json").exists()


def test_run_corpus_bench_detects_failed_expectation(tmp_path: Path):
    corpus = tmp_path / "corpus"
    cases = corpus / "cases"
    cases.mkdir(parents=True)
    (cases / "tiny.txt").write_text("# Tiny\n\nNo equation here.\n", encoding="utf-8")
    manifest = CorpusManifest(
        name="expectation_failure",
        version="0.1",
        cases=[
            CorpusCase(
                case_id="tiny",
                case_type="clean_text",
                path="cases/tiny.txt",
                license="synthetic",
                expected=CorpusExpectation(min_blocks=1, min_equations=1),
            )
        ],
    )
    manifest_path = corpus / "corpus_manifest.json"
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")
    report = run_corpus_bench(manifest_path, tmp_path / "out")
    assert report.oak_status == "corpus_bench_failed_expectations"
    assert report.case_results[0].status == "failed_expectations"
    assert report.case_results[0].expectation_results["min_equations"] is False


def test_run_corpus_bench_invalid_manifest(tmp_path: Path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    manifest = CorpusManifest(
        name="invalid",
        version="0.1",
        cases=[CorpusCase(case_id="missing", case_type="clean_text", path="missing.txt")],
    )
    manifest_path = corpus / "corpus_manifest.json"
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")
    report = run_corpus_bench(manifest_path, tmp_path / "out")
    assert report.oak_status == "corpus_bench_invalid_manifest"
    assert report.case_results == []
    assert any("missing file" in warning for warning in report.warnings)
