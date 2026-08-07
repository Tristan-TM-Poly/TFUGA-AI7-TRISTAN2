import json
from pathlib import Path

import pytest

from omega_ai_tristan_lab.adapter_forge import AdapterForge
from omega_ai_tristan_lab.capabilities import CapabilitySpec
from omega_ai_tristan_lab.plugin import plugin as lab_plugin
from omega_ai_tristan_lab.policy import PolicyContext
from omega_ai_tristan_lab.repo_registry import RepoRegistry
from omega_ai_tristan_lab.runtime import TristanRuntime
from omega_ai_tristan_lab.tir import Provenance, TristanArtifact, stable_digest


class LegacyEcho:
    name = "echo"

    def capabilities(self):
        return ("echo", "increment")

    def run(self, task, payload):
        if task == "echo":
            return dict(payload)
        if task == "increment":
            return {"value": int(payload.get("value", 0)) + 1}
        raise KeyError(task)


class NetworkPlugin:
    name = "network"

    def capabilities(self):
        return ("fetch",)

    def capability_specs(self):
        return (CapabilitySpec(id="network.fetch", task="fetch", permissions=("NETWORK_READ",)),)

    def run(self, task, payload):
        return {"should_not_run_without_permission": True}


def test_v06_tir_digest_is_stable_across_mapping_order():
    assert stable_digest({"a": 1, "b": [2, 3]}) == stable_digest({"b": [2, 3], "a": 1})
    artifact = TristanArtifact.build(kind="test", payload={"x": 7}, provenance=Provenance(source="pytest"))
    assert artifact.id.startswith("tir:")
    assert artifact.digest


def test_v06_legacy_plugins_are_lifted_into_capability_graph():
    runtime = TristanRuntime(auto_discover=False)
    runtime.register(LegacyEcho())
    graph = runtime.capability_graph()
    assert "echo.echo" in graph.capability_ids()
    provider = graph.resolve("echo.increment")
    assert provider.plugin == "echo"
    assert provider.capability.task == "increment"


def test_v06_execute_capability_produces_artifact_and_capsule():
    runtime = TristanRuntime(auto_discover=False)
    runtime.register(LegacyEcho(), source="pytest")
    execution = runtime.execute_capability("echo.increment", {"value": 4})
    assert execution.output == {"value": 5}
    assert execution.artifact.provenance.source == "echo"
    assert execution.capsule.input_digest
    assert execution.capsule.output_digest
    assert execution.capsule.policy["allowed"] is True


def test_v06_capability_pipeline_composes_legacy_plugins():
    runtime = TristanRuntime(auto_discover=False)
    runtime.register(LegacyEcho())
    result = runtime.capability_pipeline(["echo.increment", "echo.increment"], {"value": 8})
    assert result["result"] == {"value": 10}
    assert len(result["history"]) == 2


def test_v06_policy_kernel_blocks_ungranted_network_access():
    runtime = TristanRuntime(auto_discover=False)
    runtime.register(NetworkPlugin())
    with pytest.raises(PermissionError):
        runtime.execute_capability("network.fetch", {})
    allowed = runtime.execute_capability("network.fetch", {}, policy_context=PolicyContext.sandbox(["NETWORK_READ"]))
    assert allowed.output["should_not_run_without_permission"] is True


def test_v06_builtin_plugin_has_rich_capability_spec():
    runtime = TristanRuntime(auto_discover=False)
    runtime.register(lab_plugin)
    provider = runtime.capability_graph().resolve("tristan.idea.analyze")
    assert provider.capability.output_kind == "analysis-report"
    assert provider.capability.permissions == ("PURE",)


def test_v06_adapter_forge_inspects_and_plans_without_mutating_source(tmp_path: Path):
    repo = tmp_path / "demo"
    package = repo / "src" / "demo_pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (repo / "pyproject.toml").write_text('[project]\nname = "demo-system"\nversion = "0.1.0"\n\n[project.scripts]\ndemo-run = "demo_pkg.cli:main"\n', encoding="utf-8")
    before = sorted(str(p.relative_to(repo)) for p in repo.rglob("*"))
    plan = AdapterForge().plan(repo)
    after = sorted(str(p.relative_to(repo)) for p in repo.rglob("*"))
    assert before == after
    assert plan.inspection.packaging_status == "package"
    assert plan.manifest["capabilities"][0]["id"] == "demo-system.cli.demo-run"
    assert "NotImplementedError" in plan.adapter_source


def test_v06_adapter_forge_materialization_requires_explicit_output(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "mod.py").write_text("x = 1\n", encoding="utf-8")
    out = tmp_path / "generated"
    manifest_path, adapter_path = AdapterForge().materialize(repo, out)
    assert manifest_path.exists()
    assert adapter_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema"] == "tristan-capability-manifest/0.1"
    with pytest.raises(FileExistsError):
        AdapterForge().materialize(repo, out)


def test_v06_repo_doctor_exposes_quantified_maturity():
    summary = RepoRegistry().doctor_summary()
    assert summary["repositories"] == 6
    assert 0 <= summary["packaging_maturity"] <= 1
    # v0.8 splits installable packaging from adapter-promotion maturity.
    assert summary["packaged"] + summary["adapter_candidates"] >= 4


def test_v06_capsule_can_be_persisted(tmp_path: Path):
    runtime = TristanRuntime(auto_discover=False)
    runtime.register(LegacyEcho())
    execution = runtime.execute_capability("echo.echo", {"hello": "world"})
    root = execution.capsule.write(tmp_path / "capsule", payload={"hello": "world"}, output=execution.output)
    assert (root / "manifest.json").exists()
    assert (root / "input.json").exists()
    assert (root / "output.json").exists()


def test_machine_manifest_and_tir_schema_follow_current_runtime():
    root = Path(__file__).parents[1]
    manifest = json.loads((root / "tristan.manifest.json").read_text(encoding="utf-8"))
    schema = json.loads((root / "schemas" / "tir_artifact.schema.json").read_text(encoding="utf-8"))
    assert manifest["system"]["version"] == lab_plugin.version
    assert manifest["integration"]["latest_status"] == "CI_VERIFIED_FOUR_REPO_R02"
    assert manifest["capabilities"][0]["id"] == "tristan.idea.analyze"
    assert schema["properties"]["schema_version"]["const"] == "tir-0.1"
