from __future__ import annotations

from typing import Iterable

from .core import AUTHORITIES, InvariantCheck, ObjectRef, TransformationReceipt, stable_digest


class ReceiptError(ValueError):
    pass


def _validate_ranges(uncertainty: float, risk: float, cost: float) -> None:
    if not 0.0 <= float(uncertainty) <= 1.0:
        raise ReceiptError("uncertainty must be in [0,1]")
    if not 0.0 <= float(risk) <= 1.0:
        raise ReceiptError("risk must be in [0,1]")
    if float(cost) < 0.0:
        raise ReceiptError("cost must be non-negative")


def issue_receipt(
    *,
    operator: str,
    inputs: Iterable[ObjectRef],
    outputs: Iterable[ObjectRef],
    assumptions: Iterable[str] = (),
    invariants: Iterable[InvariantCheck] = (),
    evidence_refs: Iterable[ObjectRef] = (),
    residuals: Iterable[str] = (),
    uncertainty: float = 0.0,
    cost: float = 0.0,
    authority: str = "read",
    risk: float = 0.0,
    rollback: str = "",
    provenance: Iterable[str] = (),
    oak_state: str = "UNKNOWN",
) -> TransformationReceipt:
    if not operator:
        raise ReceiptError("operator is required")
    if authority not in AUTHORITIES:
        raise ReceiptError(f"invalid authority: {authority}")
    _validate_ranges(uncertainty, risk, cost)
    inv = tuple(invariants)
    if oak_state == "PASS" and any(item.status != "PASS" for item in inv):
        raise ReceiptError("OAK PASS requires every declared invariant to PASS")
    if authority in {"write", "irreversible"} and not rollback:
        raise ReceiptError("mutating receipts require an explicit rollback/irreversibility statement")

    body = {
        "operator": operator,
        "inputs": [item.to_dict() for item in inputs],
        "outputs": [item.to_dict() for item in outputs],
        "assumptions": list(assumptions),
        "invariants": [item.__dict__ for item in inv],
        "evidence_refs": [item.to_dict() for item in evidence_refs],
        "residuals": list(residuals),
        "uncertainty": uncertainty,
        "cost": cost,
        "authority": authority,
        "risk": risk,
        "rollback": rollback,
        "provenance": list(provenance),
        "oak_state": oak_state,
    }
    receipt_id = f"receipt:{stable_digest(body)[:20]}"
    return TransformationReceipt(
        receipt_id=receipt_id,
        operator=operator,
        inputs=tuple(ObjectRef(**item) for item in body["inputs"]),
        outputs=tuple(ObjectRef(**item) for item in body["outputs"]),
        assumptions=tuple(body["assumptions"]),
        invariants=inv,
        evidence_refs=tuple(ObjectRef(**item) for item in body["evidence_refs"]),
        residuals=tuple(body["residuals"]),
        uncertainty=uncertainty,
        cost=cost,
        authority=authority,
        risk=risk,
        rollback=rollback,
        provenance=tuple(body["provenance"]),
        oak_state=oak_state,
    )


def validate_receipt(receipt: TransformationReceipt) -> dict[str, object]:
    errors: list[str] = []
    try:
        _validate_ranges(receipt.uncertainty, receipt.risk, receipt.cost)
    except ReceiptError as exc:
        errors.append(str(exc))
    if receipt.authority not in AUTHORITIES:
        errors.append(f"invalid authority: {receipt.authority}")
    if receipt.oak_state == "PASS" and any(item.status != "PASS" for item in receipt.invariants):
        errors.append("OAK PASS with non-PASS invariant")
    if receipt.authority in {"write", "irreversible"} and not receipt.rollback:
        errors.append("mutation missing rollback/irreversibility statement")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "receipt_id": receipt.receipt_id,
        "fingerprint": receipt.fingerprint,
    }
