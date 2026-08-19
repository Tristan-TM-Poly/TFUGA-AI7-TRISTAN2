import hashlib
import json
from importlib import metadata

import pytest

from omega_ai_tristan_lab.capabilities import CapabilitySpec
from omega_ai_tristan_lab.discovery import DiscoveryReport
from omega_ai_tristan_lab.environment import EnvironmentMatrix
from omega_ai_tristan_lab.provenance_runtime import DistributionFingerprint, fingerprint_distribution
from omega_ai_tristan_lab.runtime import TristanRuntime
from omega_ai_tristan_lab.schemas import SchemaSpec
from omega_ai_tristan_lab.supply_chain import SupplyChainOAK


class SchemaPluginA:
    name = "schema-a"
    version = "1.0"

    def capabilities(self): return ("make-mid",)
    def schema_specs(self): return (SchemaSpec("test.in", required_keys=("x",)), SchemaSpec("test.mid", required_keys=("y",)))
    def capability_specs(self): return (CapabilitySpec(id="test.make-mid", task="make-mid", input_schema="test.in", output_schema="test.mid"),)
    def run(self, task, payload): return {"y": int(payload["x"]) + 1}


class SchemaPluginB:
    name = "schema-b"
    version = "1.0"

    def capabilities(self): return ("make-out",)
    def schema_specs(self): return (SchemaSpec("test.mid", required_keys=("y",)), SchemaSpec("test.out", required_keys=("z",)))
    def capability_specs(self): return (CapabilitySpec(id="test.make-out", task="make-out", input_schema="test.mid", output_schema="test.out"),)
    def run(self, task, payload): return {"z": int(payload["y"]) * 2}


class BadOutputPlugin:
    name = "bad-output"

    def capabilities(self): return ("bad",)
    def schema_specs(self): return (SchemaSpec("test.in", required_keys=("x",)), SchemaSpec("test.required", required_keys=("required",)))
    def capability_specs(self): return (CapabilitySpec(id="test.bad-output", task="bad", input_schema="test.in", output_schema="test.required"),)
    def run(self, task, payload): return {"wrong": True}


def _schema_runtime():
    runtime = TristanRuntime(auto_discover=False)
    runtime.register(SchemaPluginA(), fingerprint=DistributionFingerprint(distribution="schema-a-dist", version="1.0", repository="https://example.invalid/schema-a.git", commit="a" * 40, install_source="https://example.invalid/schema-a.git"))
    runtime.register(SchemaPluginB(), fingerprint=DistributionFingerprint(distribution="schema-b-dist", version="1.0", repository="https://example.invalid/schema-b.git", commit="b" * 40, install_source="https://example.invalid/schema-b.git"))
    return runtime


def test_v09_schema_graph_compiles_and_executes_typed_pipeline():
    runtime = _schema_runtime()
    plan = runtime.pipeline_compiler().compile(["test.make-mid", "test.make-out"], initial_schema="test.in")
    assert plan.final_schema == "test.out"
    result = runtime.capability_pipeline(["test.make-mid", "test.make-out"], {"x": 4}, initial_schema="test.in")
    assert result["result"] == {"z": 10}
    assert result["plan"]["valid"] is True


def test_v09_schema_validation_fails_closed_on_bad_output():
    runtime = TristanRuntime(auto_discover=False)
    runtime.register(BadOutputPlugin())
    with pytest.raises(ValueError, match="Output schema"):
        runtime.execute_capability("test.bad-output", {"x": 1})


def test_v09_pipeline_compiler_rejects_incompatible_initial_schema():
    runtime = _schema_runtime()
    with pytest.raises(ValueError, match="Schema mismatch"):
        runtime.pipeline_compiler().compile(["test.make-out"], initial_schema="test.in")


def test_v09_pipeline_path_search_finds_two_step_route():
    runtime = _schema_runtime()
    plan = runtime.pipeline_compiler().find_path(source_schema="test.in", target_schema="test.out")
    assert [step.capability for step in plan.steps] == ["test.make-mid", "test.make-out"]


def test_v09_provenance_contains_distribution_commit_and_parent_lineage():
    runtime = _schema_runtime()
    result = runtime.capability_pipeline(["test.make-mid", "test.make-out"], {"x": 3}, initial_schema="test.in")
    first = result["history"][0]["artifact"]
    second = result["history"][1]["artifact"]
    assert first["provenance"]["distribution"] == "schema-a-dist"
    assert first["provenance"]["commit"] == "a" * 40
    assert second["provenance"]["parents"] == [first["digest"]]


def test_v09_discovery_negative_memory_records_broken_entrypoint(monkeypatch):
    broken = metadata.EntryPoint(name="broken", value="does_not_exist:plugin", group="tristan.plugins")
    monkeypatch.setattr(TristanRuntime, "_entry_points", staticmethod(lambda: (broken,)))
    runtime = TristanRuntime(auto_discover=False, discovery_mode="lenient")
    runtime.discover()
    report = runtime.discovery_report()
    assert isinstance(report, DiscoveryReport)
    assert len(report.failed) == 1
    assert report.failed[0].entrypoint == "broken"
    assert report.ok is True


def test_v09_oak_strict_discovery_rejects_broken_or_missing_plugins(monkeypatch):
    broken = metadata.EntryPoint(name="broken", value="does_not_exist:plugin", group="tristan.plugins")
    monkeypatch.setattr(TristanRuntime, "_entry_points", staticmethod(lambda: (broken,)))
    runtime = TristanRuntime(auto_discover=False, discovery_mode="oak-strict", expected_plugins=("must-exist",))
    with pytest.raises(RuntimeError, match="OAK-strict"):
        runtime.discover()


def test_v09_supply_chain_verifies_and_rejects_wheel_hashes(tmp_path):
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    wheel = wheelhouse / "demo.whl"
    wheel.write_bytes(b"wheel-bytes")
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    manifest = tmp_path / "hashes.json"
    manifest.write_text(json.dumps([{"file": wheel.name, "sha256": digest}]), encoding="utf-8")
    ok, errors = SupplyChainOAK().verify_wheelhouse(wheelhouse, manifest)
    assert ok is True and errors == ()
    manifest.write_text(json.dumps([{"file": wheel.name, "sha256": "0" * 64}]), encoding="utf-8")
    ok, errors = SupplyChainOAK().verify_wheelhouse(wheelhouse, manifest)
    assert ok is False
    assert "hash mismatch" in errors[0]


def test_v09_environment_matrix_distinguishes_declaration_from_receipt():
    payload = EnvironmentMatrix().to_dict()
    assert payload["current"]["key"]
    assert len(payload["declared_targets"]) == 9
    assert "not verification receipts" in payload["note"]


def test_v09_sandbox_executes_builtin_capability_in_fresh_process():
    runtime = TristanRuntime(auto_discover=True)
    result = runtime.execute_sandboxed("tristan.idea.analyze", {"idea": "schema and provenance sandbox smoke"}, timeout_seconds=15, memory_mb=512)
    assert result.returncode == 0
    assert result.isolation_strength == "USER_SPACE_BOUNDED"
    assert result.output["oak_report"]


def test_v09_supply_chain_inventory_never_claims_vulnerability_scan():
    report = SupplyChainOAK().report(["omega-ai-tristan-lab"])
    assert report.vulnerability_status == "NOT_SCANNED_NO_VULNERABILITY_DB"


def test_v09_distribution_fingerprint_never_borrows_unrelated_github_sha(monkeypatch):
    class FakeDistribution:
        version = "9.9"
        metadata = {"Name": "fake-dist", "License": "UNKNOWN"}
        def read_text(self, name): return None

    monkeypatch.setenv("GITHUB_SHA", "f" * 40)
    monkeypatch.setattr("omega_ai_tristan_lab.provenance_runtime.metadata.distribution", lambda name: FakeDistribution())
    fingerprint = fingerprint_distribution("fake-dist")
    assert fingerprint.version == "9.9"
    assert fingerprint.commit == ""
