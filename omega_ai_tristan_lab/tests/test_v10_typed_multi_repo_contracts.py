from omega_ai_tristan_lab.plugin import OmegaAITristanLabPlugin
from omega_ai_tristan_lab.runtime import TristanRuntime


_SHARED_INVARIANT = {
    "id": "tristan.evidence.cvcd-invariant.v1",
    "kind": "mapping",
    "required_keys": ("name", "source_names", "axis_names", "compression", "fertility", "residue"),
    "optional_keys": ("evidence_label", "m_minus_entries", "big_t_signature", "runtime_contract"),
    "allow_extra": True,
}


class MappingPEFA:
    name = "pefa-omega-em2"
    distribution = "pefa-fractal-energy-system"
    version = "0.1.2"

    def capabilities(self):
        return ("cvcd-extract",)

    def schema_specs(self):
        return (
            {
                "id": "tristan.pefa.cvcd-observation-batch.v1",
                "kind": "mapping",
                "required_keys": ("observations",),
                "optional_keys": ("name", "evidence_label"),
                "allow_extra": True,
            },
            dict(_SHARED_INVARIANT),
        )

    def capability_specs(self):
        return (
            {
                "id": "pefa-omega-em2.cvcd-extract",
                "task": "cvcd-extract",
                "input_kind": "cvcd-observation-batch",
                "output_kind": "cvcd-invariant",
                "input_schema": "tristan.pefa.cvcd-observation-batch.v1",
                "output_schema": "tristan.evidence.cvcd-invariant.v1",
                "permissions": ("PURE",),
                "deterministic": True,
            },
        )

    def run(self, task, payload):
        return {
            "name": str(payload.get("name", "fixture")),
            "source_names": ["a", "b"],
            "axis_names": ["stability", "fertility"],
            "compression": 0.8,
            "fertility": 0.7,
            "residue": 0.1,
            "evidence_label": "synthetic-v10",
            "m_minus_entries": ["external validation missing"],
        }


class MappingOmni:
    name = "tristan-omni-core"
    distribution = "tristan-omni-core"
    version = "0.2.2"

    def capabilities(self):
        return ("evidence-to-idea",)

    def schema_specs(self):
        return (dict(_SHARED_INVARIANT),)

    def capability_specs(self):
        return (
            {
                "id": "tristan-omni-core.evidence-to-idea",
                "task": "evidence-to-idea",
                "input_kind": "cvcd-invariant",
                "output_kind": "idea",
                "input_schema": "tristan.evidence.cvcd-invariant.v1",
                "output_schema": "tristan.idea.v1",
                "permissions": ("PURE",),
                "deterministic": True,
            },
        )

    def run(self, task, payload):
        return {"idea": f"Audit typed invariant {payload['name']}"}


class InvalidMappingPlugin:
    name = "invalid-mapping"

    def capabilities(self):
        return ("bad",)

    def capability_specs(self):
        return ({"task": "bad"},)

    def run(self, task, payload):
        return payload


def _runtime():
    runtime = TristanRuntime(auto_discover=False)
    runtime.register(MappingPEFA())
    runtime.register(MappingOmni())
    runtime.register(OmegaAITristanLabPlugin())
    return runtime


def test_v10_structural_peer_specs_compile_without_circular_dependency():
    runtime = _runtime()
    ids = (
        "pefa-omega-em2.cvcd-extract",
        "tristan-omni-core.evidence-to-idea",
        "tristan.idea.analyze",
    )
    plan = runtime.pipeline_compiler().compile(
        ids,
        initial_schema="tristan.pefa.cvcd-observation-batch.v1",
    )
    assert plan.final_schema == "tristan.analysis-report.v1"
    assert [step.input_schema for step in plan.steps] == [
        "tristan.pefa.cvcd-observation-batch.v1",
        "tristan.evidence.cvcd-invariant.v1",
        "tristan.idea.v1",
    ]
    assert all(step.input_schema != "tristan.any" and step.output_schema != "tristan.any" for step in plan.steps)


def test_v10_pipeline_compiler_synthesizes_same_three_step_path():
    runtime = _runtime()
    plan = runtime.pipeline_compiler().find_path(
        source_schema="tristan.pefa.cvcd-observation-batch.v1",
        target_schema="tristan.analysis-report.v1",
        max_steps=4,
    )
    assert [step.capability for step in plan.steps] == [
        "pefa-omega-em2.cvcd-extract",
        "tristan-omni-core.evidence-to-idea",
        "tristan.idea.analyze",
    ]


def test_v10_duplicate_shared_schema_is_identical_not_conflicting():
    graph = _runtime().schema_graph()
    shared = graph.get("tristan.evidence.cvcd-invariant.v1")
    assert shared.required_keys == (
        "name", "source_names", "axis_names", "compression", "fertility", "residue"
    )


def test_v10_typed_pipeline_executes_end_to_end():
    runtime = _runtime()
    result = runtime.capability_pipeline(
        (
            "pefa-omega-em2.cvcd-extract",
            "tristan-omni-core.evidence-to-idea",
            "tristan.idea.analyze",
        ),
        {"name": "v10-fixture", "observations": [{"synthetic": True}]},
        initial_schema="tristan.pefa.cvcd-observation-batch.v1",
    )
    assert result["result"]["oak_report"]
    assert result["plan"]["final_schema"] == "tristan.analysis-report.v1"
    assert [item["provider"] for item in result["history"]] == [
        "pefa-omega-em2", "tristan-omni-core", "omega-ai-tristan-lab"
    ]


def test_v10_invalid_peer_capability_mapping_fails_closed():
    runtime = TristanRuntime(auto_discover=False)
    runtime.register(InvalidMappingPlugin())
    try:
        runtime.capability_graph()
    except TypeError as exc:
        assert "id and task" in str(exc)
    else:
        raise AssertionError("invalid structural capability mapping must fail closed")
