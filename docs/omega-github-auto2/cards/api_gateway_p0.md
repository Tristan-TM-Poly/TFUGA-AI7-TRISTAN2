# Omega AUTO2 API Gateway P0

This document materializes the first API Gateway P0 batch from issues #113-#116.

## Covered cards

- #113 — `api_gateway_input_schema_v1`
- #114 — `api_gateway_output_schema_v1`
- #115 — `api_gateway_core_algorithm_v1`
- #116 — `api_gateway_oak_gate_v1`

## Files

- `scripts/omega_auto2_api_gateway_p0.py`
- `fixtures/omega_auto2/api_gateway/valid_request.json`
- `fixtures/omega_auto2/api_gateway/invalid_request.json`
- `tests/test_omega_auto2_api_gateway_p0.py`

## Input envelope

Required fields:

- `request_id`
- `namespace`
- `operation`
- `payload`
- `metadata`
- `oak_context`

Allowed operations:

- `healthcheck`
- `validate_spectrum`
- `clean_spectrum`
- `detect_drift`
- `batch_qc`
- `oak_report`

## Output envelope

The core returns:

- `request_id`
- `status`
- `result`
- `warnings`
- `errors`
- `oak_status`
- `residue_report`
- `next_action`
- `generated_at`

## OAK gate

The gate returns one of:

- `PASS`
- `REVIEW_REQUIRED`
- `FAIL`

The gate always sets:

- `external_actions_allowed = false`
- `production_billing_allowed = false`

## M-minus failure memory

Known failure modes captured in this P0 implementation:

- missing required field
- unsupported operation
- payload/metadata/oak_context not object-shaped
- empty request id
- production-only flags present in synthetic metadata

## OAK status

This is an offline synthetic prototype. It is not a production API gateway, does not activate billing, does not call external systems, and does not process customer data.
