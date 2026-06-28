# Omega AUTO2 Usage Events P0

This document materializes the next P0 batch from issues #125 and #126.

## Covered cards

- #125 — `usage_metering_input_schema_v1`
- #126 — `usage_metering_core_algorithm_v1`

## Files

- `scripts/omega_auto2_usage_events_p0.py`
- `fixtures/omega_auto2/usage_events/valid_event.json`
- `fixtures/omega_auto2/usage_events/invalid_event.json`
- `tests/test_omega_auto2_usage_events_p0.py`

## Event envelope

Required fields:

- `event_id`
- `request_id`
- `namespace`
- `operation`
- `unit_type`
- `units`
- `timestamp`
- `oak_context`

## Allowed unit types

- `request`
- `spectrum`
- `batch`
- `report`
- `test_run`

## OAK status

This is an offline synthetic P0 foundation. It creates normalized usage records for tests and local planning only.

It does not charge, invoice, contact customers, call external services, or process private data.

## M-minus failure memory

Known failure modes captured in this P0 implementation:

- missing required event field
- unsupported unit type
- unsupported operation
- negative unit count
- malformed OAK context
- private data flag in synthetic fixture
