from datetime import date
from pathlib import Path
import json
import pytest

from omega_company_autopilot_t import (
    ActionKind, ActionRequest, AutonomyLevel, CompanyAutopilot, CompanyRecord,
    CompanyRegistry, CompanyState, DeadlineEngine, DivisionRecord, EvidenceLedger,
    EvidenceRef, GateDecision, GovernanceEngine, OAKCorporateGate, Obligation,
    RegistryError, RiskLevel, SpinoutEngine, TreasuryEngine,
)
from omega_company_autopilot_t.approvals import approve_action, valid_approvals
from omega_company_autopilot_t.cli import main
from omega_company_autopilot_t.execution import DryRunAdapter, ExecutionError, execute_bounded
from omega_company_autopilot_t.serialization import load_company, save_company


def company(state=CompanyState.CANDIDATE_LEGAL_ENTITY):
    return CompanyRecord(company_id="tristan_parent_opco", conceptual_name="Tristan Parent OpCo", state=state, divisions=[DivisionRecord("oak", "OAK", "audit")])


def action(kind=ActionKind.INTERNAL_REPORT, **changes):
    values = dict(action_id="ACT-1", company_id="tristan_parent_opco", division_id="oak", kind=kind, title="test", payload={}, risk_level=RiskLevel.LOW, reversible=True, external_effect=False)
    values.update(changes)
    return ActionRequest(**values)


def test_roundtrip(tmp_path: Path):
    path = tmp_path / "company.json"; save_company(company(), path)
    assert load_company(path).company_id == "tristan_parent_opco"


def test_illegal_transition():
    with pytest.raises(RegistryError): CompanyRegistry(company()).transition(CompanyState.OPERATING)


def test_registration_needs_verified_evidence():
    record = company(CompanyState.FILING_SUBMITTED); record.legal_name = "Example inc."
    with pytest.raises(RegistryError): CompanyRegistry(record).transition(CompanyState.REGISTERED)
    evidence = EvidenceRef("E1", "registry_snapshot", "vault://registry", verified=True)
    assert CompanyRegistry(record).transition(CompanyState.REGISTERED, evidence=[evidence]).state is CompanyState.REGISTERED


def test_operating_controls():
    record = company(CompanyState.POST_FORMATION); record.legal_identity_verified = True
    with pytest.raises(RegistryError): CompanyRegistry(record).transition(CompanyState.OPERATING)
    record.privacy_officer = "Tristan"; record.directors = ["Tristan"]
    assert CompanyRegistry(record).transition(CompanyState.OPERATING).state is CompanyState.OPERATING


def test_l4_internal_report_auto():
    record = company(CompanyState.OPERATING); record.autonomy_level = AutonomyLevel.L4_BOUNDED
    assert OAKCorporateGate().evaluate(record, action()).decision is GateDecision.AUTO


def test_external_email_blocked_before_authorization():
    result = OAKCorporateGate().evaluate(company(CompanyState.OPERATING), action(ActionKind.EXTERNAL_EMAIL, external_effect=True))
    assert result.decision is GateDecision.BLOCK


def test_contract_requires_professional_review():
    record = company(CompanyState.PRODUCTION_AUTHORIZED); record.production_enabled = True; record.contract_acceptance_enabled = True
    result = OAKCorporateGate().evaluate(record, action(ActionKind.CONTRACT_ACCEPT, reversible=False, external_effect=True, risk_level=RiskLevel.HIGH))
    assert result.decision is GateDecision.PROFESSIONAL_REVIEW


def test_high_value_payment_two_approvals():
    record = company(CompanyState.PRODUCTION_AUTHORIZED); record.production_enabled = True; record.banking_enabled = True
    result = OAKCorporateGate().evaluate(record, action(ActionKind.PAYMENT_EXECUTE, reversible=False, external_effect=True, amount_cad=2000, payload={"category":"software"}, risk_level=RiskLevel.HIGH))
    assert result.required_approvals == 2


def test_hash_bound_approval():
    request = action(); approval = approve_action(request, approval_id="A1", approver="Tristan", reason="ok")
    assert valid_approvals(request, [approval])
    request.payload["changed"] = True
    assert not valid_approvals(request, [approval])


def test_duplicate_approver_counts_once():
    request = action()
    approvals = [approve_action(request, approval_id="A1", approver="Tristan", reason="1"), approve_action(request, approval_id="A2", approver="Tristan", reason="2")]
    assert len(valid_approvals(request, approvals)) == 1


def test_execution_dry_run():
    request = action(ActionKind.INTERNAL_MESSAGE)
    gate = OAKCorporateGate().evaluate(company(), request)
    gate = gate.__class__(request.action_id, GateDecision.AUTO, gate.reasons)
    assert execute_bounded(request, gate, [], adapter=DryRunAdapter()).mode == "dry_run"


def test_external_execution_locked(monkeypatch):
    request = action(ActionKind.INTERNAL_MESSAGE)
    gate = OAKCorporateGate().evaluate(company(), request)
    gate = gate.__class__(request.action_id, GateDecision.AUTO, gate.reasons)
    monkeypatch.delenv("OMEGA_COMPANY_EXTERNAL_EXECUTION", raising=False)
    with pytest.raises(ExecutionError): execute_bounded(request, gate, [], adapter=DryRunAdapter(), execute_external=True)


def test_deadline_schedule():
    obligation = Obligation("O1", "c", "annual", date(2027,1,1), "registry", "QC", "operator")
    assert [x.offset_days for x in DeadlineEngine().schedule(obligation)] == [-90,-60,-30,-14,-7,-1,0]


def test_treasury_balances():
    allocation = TreasuryEngine().allocate_receipt(1000)
    assert round(allocation.tax_reserve_cad + allocation.operating_reserve_cad + allocation.rnd_reserve_cad + allocation.available_cad, 2) == 1000


def test_payment_never_auto_executes():
    request = TreasuryEngine().propose_payment(action_id="P1", company_id="c", division_id=None, amount_cad=50, counterparty="Vendor", category="software", invoice_id="INV", known_vendor=True)
    assert request.payload["auto_execute_requested"] is False


def test_immature_division_not_spun_out():
    assert SpinoutEngine().assess(DivisionRecord("d", "D", "test", ip_assets=20)).recommendation == "KEEP_AS_DIVISION"


def test_mature_division_review():
    division = DivisionRecord("d", "D", "test", revenue_cad=1_000_000, recurring_revenue_cad=500_000, active_customers=15, paid_pilots=5, external_partners=4, ip_assets=12, liability_isolation_need=.9, investor_interest=.8, administrative_cost_cad=10_000)
    assert SpinoutEngine().assess(division).recommendation == "PROFESSIONAL_SPINOUT_REVIEW"


def test_ledger_roundtrip(tmp_path: Path):
    ledger = EvidenceLedger(); ledger.append(entry_id="1", event_type="TEST", subject_id="x", payload={"a":1})
    path = tmp_path / "ledger.jsonl"; ledger.write_jsonl(path)
    assert EvidenceLedger.read_jsonl(path).verify()[0]


def test_board_pack_surfaces_missing_controls():
    pack = GovernanceEngine().build_board_pack(company(), as_of=date(2026,8,2))
    assert "legal_identity_unverified" in pack.risks and "privacy_officer_missing" in pack.risks


def test_autopilot_plan_and_ledger():
    record = company(CompanyState.OPERATING); record.autonomy_level = AutonomyLevel.L4_BOUNDED
    autopilot = CompanyAutopilot(); plan = autopilot.plan(record, [action()])
    assert plan.auto_ready == 1 and autopilot.ledger.verify()[0]


def test_cli_init_and_allocate(tmp_path: Path, capsys):
    path = tmp_path / "company.json"
    assert main(["init", str(path)]) == 0
    assert len(json.loads(path.read_text())["divisions"]) == 3
    assert main(["allocate-receipt", "1000"]) == 0
    assert "available_cad" in capsys.readouterr().out
