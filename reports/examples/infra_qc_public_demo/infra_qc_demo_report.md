# InfrastructureGraph Quebec — Public-Safe Demo

Generated at: `2026-07-06T20:45:00Z`

> OAK note: This report is decision support, not a final engineering, legal, emergency or authority decision.

## Security Gate

- Status: `pass`
- Publishable: `true`
- Blockers: `none`
- Warnings: `none`

## Graph Summary

- Assets: 3
- Dependencies: 1
- Sensitive assets: 1

## Source Registry

- Sources: 1
- Allowed: 1
- Review required: 0
- Blocked: 0

## Evidence

- Evidence items: 1
- Status counts: `{'structured_evidence': 1}`

## Risk Tensors

- `asset:demo_bridge`: band `medium`, pressure `17`, maintenance priority `2.7`
- `asset:demo_water_facility`: band `medium`, pressure `19`, maintenance priority `2.25`

## Maintenance

- `asset:demo_bridge`: band `planned`, priority `2.85`, needs evidence `false`

## Resilience Scenarios

- `Generalized ice storm scenario`: kind `ice_storm`, band `medium`, affected asset count `2`

## Demo assets

| Asset | Sector | Visibility | OAK note |
|---|---|---|---|
| Demo Local Bridge | transport | public | generalized example |
| Demo Water Facility | water | review | public-safe summary only |
| Demo School Building | education | public | generalized example |

## Limits

- Demo or authorized data only by default.
- Public summaries must not expose sensitive details.
- Human review required for real assets and real decisions.
- Signals are not final judgments.

## Product interpretation

This artifact demonstrates the structure of an **Infra-OAK Audit Express** deliverable:

```text
sources -> assets -> evidence -> risks -> maintenance -> resilience -> report + JSON + GraphML
```
