import json
from pathlib import Path
import pytest

from omega_re_t.adaptive_campaign_r06 import CampaignBudget, run_adaptive_campaign
from omega_re_t.optional_signatures_r06 import backend_available, fail_closed_operation, generate_keypair, sign_message, verify_message
from omega_re_t.r06_cli import all_demos, main


def test_campaign_cost_gate_and_chain():
    steps, checkpoint = run_adaptive_campaign(
        ("a", "b", "c"),
        budget=CampaignBudget(5, 1.5, 1, 0.5),
        cost=lambda _: 1.0,
        risk=lambda _: 0.1,
        execute=lambda experiment: {"success": True, "experiment": experiment},
        posterior_entropy=lambda index: 1 / (index + 1),
        novelty_mass=lambda index: 0.1 * index,
    )
    assert len(steps) == 1
    assert checkpoint.stopped_reason == "cost_budget"
    assert checkpoint.chain_digest.startswith("sha256:")
    assert checkpoint.permanent_total_cap is None


def test_campaign_failure_gate():
    steps, checkpoint = run_adaptive_campaign(
        ("a", "b", "c"),
        budget=CampaignBudget(5, 5, 0, 0.5),
        cost=lambda _: 1.0,
        risk=lambda _: 0.1,
        execute=lambda experiment: {"success": False, "experiment": experiment},
        posterior_entropy=lambda _: 1.0,
        novelty_mass=lambda _: 0.0,
    )
    assert len(steps) == 1
    assert checkpoint.stopped_reason == "failure_budget"


def test_campaign_risk_gate_before_execution():
    called = []
    steps, checkpoint = run_adaptive_campaign(
        ("a",),
        budget=CampaignBudget(2, 5, 1, 0.2),
        cost=lambda _: 1.0,
        risk=lambda _: 0.9,
        execute=lambda experiment: called.append(experiment) or {"success": True},
        posterior_entropy=lambda _: 1.0,
        novelty_mass=lambda _: 0.0,
    )
    assert not steps and not called
    assert checkpoint.stopped_reason == "risk_gate"


def test_duplicate_experiment_rejected():
    with pytest.raises(ValueError):
        run_adaptive_campaign(
            ("a", "a"),
            budget=CampaignBudget(3, 5, 1, 0.5),
            cost=lambda _: 1.0,
            risk=lambda _: 0.1,
            execute=lambda _: {"success": True},
            posterior_entropy=lambda _: 1.0,
            novelty_mass=lambda _: 0.0,
        )


def test_key_generation_requires_explicit_permission():
    with pytest.raises(PermissionError):
        generate_keypair()


def test_optional_ed25519_roundtrip_or_fail_closed():
    if backend_available():
        private, _ = generate_keypair(allow_generation=True)
        envelope = sign_message(b"message", private)
        assert verify_message(b"message", envelope)
        assert not verify_message(b"tampered", envelope)
    else:
        with pytest.raises(RuntimeError):
            fail_closed_operation(lambda: object())


def test_all_demo_boundaries_and_determinism():
    left = all_demos()
    right = all_demos()
    assert left == right
    assert left["schema"] == "omega-re-r06-demo/1"
    assert left["boundaries"]["scientific_validation"] is False
    assert left["boundaries"]["permanent_total_cap"] is None
    assert left["calibration_chain"]["valid"] is True


def test_cli_writes_output(tmp_path: Path):
    output = tmp_path / "r06.json"
    assert main(["all", "--output", str(output)]) == 0
    payload = json.loads(output.read_text())
    assert payload["schema"] == "omega-re-r06-demo/1"


def test_cli_transparency_demo_is_valid():
    payload = all_demos()["transparency_log"]
    assert payload["proof_valid"] is True
    assert payload["audit"]["valid"] is True


def test_signature_invalid_key_length_if_backend_available():
    if backend_available():
        with pytest.raises(ValueError):
            sign_message(b"message", b"short")
