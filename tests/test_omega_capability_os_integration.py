from __future__ import annotations

from omega_capability_os_t.bridge import compile_workunit
from omega_capability_os_t.core import Capability, Intent, plan
from omega_capability_os_t.runtime import CapabilityRuntime, HandlerResult, learn_health
from omega_intent_t.models import WorkUnit


def _work_unit(*, risk: str = "normal", dependencies: tuple[str, ...] = ("WU-PREV",)) -> WorkUnit:
    return WorkUnit(
        work_unit_id="WU-DEMO",
        kind="implementation",
        objective="Generate a deterministic artifact and validate it",
        requirement_ids=("REQ-1",),
        dependency_ids=dependencies,
        outputs=("src/demo.py",),
        validations=("unit_tests",),
        language="python",
        risk=risk,
        generator="implementation_generator",
    )


def test_bridge_is_ready_when_declared_dependency_is_complete():
    bridge = compile_workunit(_work_unit(), completed_dependencies=("WU-PREV",))
    payload = plan(bridge.capabilities, bridge.intent)
    assert payload["status"] == "READY"
    assert [step["capability_id"] for step in payload["steps"]] == [
        "workunit.generate.WU-DEMO",
        bridge.capabilities[1].capability_id,
    ]


def test_bridge_holds_when_dependency_evidence_is_missing():
    bridge = compile_workunit(_work_unit())
    payload = plan(bridge.capabilities, bridge.intent)
    assert payload["status"] == "HOLD"
    assert "artifact:src/demo.py" in payload["unresolved_outputs"]


def test_elevated_work_unit_requires_mutation_permission():
    blocked = compile_workunit(_work_unit(risk="elevated", dependencies=()))
    assert plan(blocked.capabilities, blocked.intent)["status"] == "HOLD"

    allowed = compile_workunit(
        _work_unit(risk="elevated", dependencies=()),
        allow_mutation=True,
    )
    assert plan(allowed.capabilities, allowed.intent)["status"] == "READY"


def test_runtime_produces_exact_sha_receipt_and_mplus():
    bridge = compile_workunit(_work_unit(dependencies=()))
    generator, validator = bridge.capabilities
    runtime = CapabilityRuntime(
        {
            generator.capability_id: lambda cap, inputs: HandlerResult(
                outputs={cap.produces[0]: "print('ok')"},
                sources=("unit://generator",),
            ),
            validator.capability_id: lambda cap, inputs: {
                cap.produces[0]: {"passed": True}
            },
        }
    )
    receipt = runtime.execute(
        bridge.capabilities,
        bridge.intent,
        initial_values=bridge.initial_values,
        candidate_sha="abc123",
        evidence_sha="abc123",
    )
    assert receipt["execution_status"] == "COMPLETE"
    assert receipt["oak"]["status"] == "PASS"
    assert receipt["unresolved_runtime_outputs"] == []
    assert sum(item["m_plus"] for item in receipt["health_after"].values()) == 2


def test_runtime_without_handler_emits_action_required_not_fake_success():
    bridge = compile_workunit(_work_unit(dependencies=()))
    receipt = CapabilityRuntime().execute(
        bridge.capabilities,
        bridge.intent,
        initial_values=bridge.initial_values,
        candidate_sha="abc123",
        evidence_sha="abc123",
    )
    assert receipt["execution_status"] == "HOLD"
    assert receipt["oak"]["status"] == "HOLD"
    assert receipt["actions_required"][0]["capability_id"] == "workunit.generate.WU-DEMO"


def test_runtime_fallback_must_preserve_outputs_and_authority():
    primary = Capability(
        capability_id="primary",
        domains=("demo",),
        consumes=("input",),
        produces=("result",),
        authority="read",
        alternatives=("fallback", "unsafe"),
    )
    fallback = Capability(
        capability_id="fallback",
        domains=("demo",),
        consumes=("input",),
        produces=("result",),
        authority="read",
    )
    unsafe = Capability(
        capability_id="unsafe",
        domains=("demo",),
        consumes=("input",),
        produces=("result",),
        authority="write",
        quality=1.0,
    )
    intent = Intent(
        intent_id="I",
        available_inputs=("input",),
        required_outputs=("result",),
        domains=("demo",),
    )
    runtime = CapabilityRuntime(
        {
            "primary": lambda cap, inputs: (_ for _ in ()).throw(RuntimeError("boom")),
            "fallback": lambda cap, inputs: {"result": 42},
            "unsafe": lambda cap, inputs: {"result": 99},
        }
    )
    receipt = runtime.execute(
        (primary, fallback, unsafe),
        intent,
        candidate_sha="sha",
        evidence_sha="sha",
    )
    assert receipt["oak"]["status"] == "PASS"
    assert receipt["observations"][0]["fallback"] == "fallback"


def test_stale_evidence_forces_hold_after_successful_execution():
    bridge = compile_workunit(_work_unit(dependencies=()))
    generator, validator = bridge.capabilities
    runtime = CapabilityRuntime(
        {
            generator.capability_id: lambda cap, inputs: {cap.produces[0]: "x"},
            validator.capability_id: lambda cap, inputs: {cap.produces[0]: True},
        }
    )
    receipt = runtime.execute(
        bridge.capabilities,
        bridge.intent,
        initial_values=bridge.initial_values,
        candidate_sha="new",
        evidence_sha="old",
    )
    assert receipt["execution_status"] == "COMPLETE"
    assert receipt["oak"]["status"] == "HOLD"
    assert receipt["fresh"] is False


def test_health_learning_separates_mplus_and_mminus():
    health = learn_health(
        [
            {"capability_id": "a", "outcome": "SUCCESS"},
            {"capability_id": "a", "outcome": "FAILURE"},
            {"capability_id": "b", "outcome": "SUCCESS"},
            {"capability_id": "c", "outcome": "FAILURE"},
            {"capability_id": "c", "outcome": "FAILURE"},
        ]
    )
    assert health["a"]["status"] == "DEGRADED"
    assert health["a"]["m_plus"] == 1 and health["a"]["m_minus"] == 1
    assert health["b"]["status"] == "PASS"
    assert health["c"]["status"] == "FAIL"
