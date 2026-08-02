"""Treasury preparation and bounded payment policy. No bank connector is included."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .models import ActionKind, ActionRequest, RiskLevel, TreasuryAllocation, TreasuryPolicy


def _money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class TreasuryEngine:
    def __init__(self, policy: TreasuryPolicy | None = None) -> None:
        self.policy = policy or TreasuryPolicy()

    def allocate_receipt(self, gross_cad: float) -> TreasuryAllocation:
        if gross_cad < 0:
            raise ValueError("gross_must_be_non_negative")
        gross = Decimal(str(gross_cad))
        tax = gross * Decimal(str(self.policy.reserve_tax_fraction))
        operating = gross * Decimal(str(self.policy.reserve_operating_fraction))
        rnd = gross * Decimal(str(self.policy.reserve_rnd_fraction))
        available = gross - tax - operating - rnd
        return TreasuryAllocation(_money(gross), _money(tax), _money(operating), _money(rnd), _money(available))

    def propose_payment(self, *, action_id: str, company_id: str, division_id: str | None, amount_cad: float, counterparty: str, category: str, invoice_id: str | None, known_vendor: bool) -> ActionRequest:
        if amount_cad <= 0:
            raise ValueError("amount_must_be_positive")
        risk = RiskLevel.MODERATE
        if category in self.policy.prohibited_categories or not known_vendor or amount_cad >= self.policy.two_approval_threshold_cad:
            risk = RiskLevel.HIGH
        return ActionRequest(
            action_id=action_id,
            company_id=company_id,
            division_id=division_id,
            kind=ActionKind.PAYMENT_EXECUTE,
            title=f"Payment to {counterparty}",
            payload={"category": category, "invoice_id": invoice_id, "known_vendor": known_vendor, "auto_execute_requested": False},
            risk_level=risk,
            reversible=False,
            external_effect=True,
            amount_cad=amount_cad,
            counterparty=counterparty,
        )
