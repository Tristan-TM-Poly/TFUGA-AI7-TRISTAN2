from omega_ai_tristan_lab.repo_registry import RepoRegistry
from omega_ai_tristan_lab.runtime import PipelineStep, TristanRuntime


class EchoPlugin:
    name = "echo"

    def capabilities(self):
        return ("echo", "increment")

    def run(self, task, payload):
        if task == "echo":
            return dict(payload)
        if task == "increment":
            return {"value": int(payload.get("value", 0)) + 1}
        raise KeyError(task)


def test_v03_repo_registry_tracks_all_owned_repositories():
    registry = RepoRegistry()
    repos = registry.all()
    assert len(repos) == 6
    assert registry.get("pefa").visibility == "private"
    assert registry.get("omni-core").distribution == "tristan-omni-core"


def test_v03_repo_doctor_is_read_only_and_total():
    health = RepoRegistry().doctor()
    assert len(health) == 6
    assert {item.status for item in health} <= {"installed", "not-installed", "needs-packaging"}


def test_v03_runtime_registers_and_runs_plugin():
    runtime = TristanRuntime(auto_discover=False)
    runtime.register(EchoPlugin())
    assert runtime.run("echo", "echo", {"x": 7}) == {"x": 7}
    assert runtime.plugins()[0].capabilities == ("echo", "increment")


def test_v03_runtime_pipeline_composes_outputs():
    runtime = TristanRuntime(auto_discover=False)
    runtime.register(EchoPlugin())
    result = runtime.pipeline(
        [PipelineStep("echo", "increment"), ("echo", "increment")],
        {"value": 3},
    )
    assert result["result"]["value"] == 5
    assert len(result["history"]) == 2
