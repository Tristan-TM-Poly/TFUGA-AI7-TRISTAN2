from omega_prof_poly_t import VERSION, build_release_bundle, build_version_manifest, run_cli


def test_cli_version():
    assert run_cli(["version"]) == "omega-absorb 1.0.0\n"
    assert VERSION == "1.0.0"


def test_cli_demo_contains_counts():
    output = run_cli(["demo"])
    assert "Omega absorb demo" in output
    assert "artifact_count=" in output
    assert "roadmap_steps=" in output


def test_cli_roadmap_renders_markdown():
    output = run_cli(["roadmap"])
    assert output.startswith("# Omega Absorb Roadmap")


def test_version_manifest_has_release_lineage():
    manifest = build_version_manifest()
    versions = [entry.version for entry in manifest.entries]
    assert versions[0] == "0.3"
    assert versions[-1] == "1.0"
    assert manifest.release == "1.0.0"


def test_release_bundle_builds_summary_and_roadmap():
    bundle = build_release_bundle()
    assert bundle.version == "1.0.0"
    assert "manifest_versions" in bundle.summary_json
    assert bundle.roadmap_markdown.startswith("# Omega Absorb Roadmap")
    assert bundle.next_action == "store_release_bundle_artifacts"
