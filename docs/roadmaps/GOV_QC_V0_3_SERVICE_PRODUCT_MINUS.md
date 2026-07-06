# Ω-GOV-QC-T v0.3 — Service / Product / M- Layer

Status: B/C — roadmap + implementation target
Date: 2026-07-06
Branch: omega-gov-qc-t-mvp

## 0. Mission

Add the third foundation layer for TristanGovGraph Québec:

```text
PublicService model
ProductCard model
MMinusEvent model
Service/Product factories
M- memory register
```

This converts Ω-GOV-QC-T from a graph-and-evidence skeleton into a productizable GovTech architecture.

## 1. Why this layer matters

v0.1 created the public-sector graph.
v0.2 added source, evidence, risk and report primitives.
v0.3 adds the bridge toward real products and reusable public-service analysis.

## 2. New primitives

### PublicService

Represents a public service as an explicit, reviewable unit:

- responsible entity ;
- target users ;
- required documents ;
- service channels ;
- data used ;
- review or appeal path ;
- human contact requirement ;
- OAK status.

### ProductCard

Represents a product candidate:

- product mission ;
- target users ;
- inputs ;
- outputs ;
- risk level ;
- maturity ;
- OAK requirements ;
- monetization hypothesis ;
- next milestone.

### MMinusEvent

Represents an error, anti-pattern or blocked pattern that should become a test or gate:

- module ;
- error type ;
- severity ;
- countermeasure ;
- test to add ;
- OAK note.

## 3. New files

```text
omega_gov_qc_t/src/omega_gov_qc_t/service_model.py
omega_gov_qc_t/src/omega_gov_qc_t/product_factory.py
omega_gov_qc_t/src/omega_gov_qc_t/m_minus.py
omega_gov_qc_t/schemas/public_service.schema.json
omega_gov_qc_t/schemas/product_card.schema.json
omega_gov_qc_t/schemas/m_minus_event.schema.json
omega_gov_qc_t/examples/product_cards.json
omega_gov_qc_t/examples/public_services_demo.json
omega_gov_qc_t/tests/test_service_product_minus.py
```

## 4. OAK rule

A product candidate is not allowed to graduate beyond demo status unless:

1. it has a public mission ;
2. it identifies data inputs ;
3. it defines outputs ;
4. it lists OAK requirements ;
5. it has a risk level ;
6. it records M- failure modes ;
7. it does not claim final authority.

## 5. Maturity ladder

| Level | Meaning |
|---|---|
| P0 | Doctrine only |
| P1 | Skeleton package |
| P2 | Reproducible demo |
| P3 | Reviewed pilot |
| P4 | Productized service |
| P5 | Platform integration |

## 6. M- seed events

- missing source metadata ;
- unclear public mission ;
- output presented without limitation ;
- high-impact context without human authority ;
- product card without risk level ;
- data input without permission status.

## 7. Next after v0.3

v0.4 should implement OpenData ingestion and dataset health:

```text
opendata_ingestor.py
dataset_health.py
json_exporter.py
CSV/JSON loader
schema mapper
freshness scoring
```
