# Public data source catalog — Ω-RECYCLE-T∞ R0.4

Verified 2026-08-10. This file records source descriptors, not a claim that upstream data are immutable or universally comparable.

## Eurostat `env_wasmun`

- Publisher: Eurostat
- Dataset: Municipal waste by waste management operations
- Online code: `env_wasmun`
- DOI: `10.2908/env_wasmun`
- Source: https://ec.europa.eu/eurostat/databrowser/view/env_wasmun/default/table?lang=en
- Coverage reported when verified: 1995–2024
- Important boundary: Eurostat warns that municipal-waste composition/scope can differ across countries; cross-country differences must not be interpreted causally without additional analysis.

R0.4 uses this source only as a provenance/catalog example and a tiny regression snapshot. Production ingestion must retain dimensions, units, flags, update date and source metadata.

## US EPA SMM Facts and Figures

- Publisher: US Environmental Protection Agency
- Series: Advancing Sustainable Materials Management: Facts and Figures
- Source: https://www.epa.gov/facts-and-figures-about-materials-waste-and-recycling/advancing-sustainable-materials-management
- EPA states that the most recent national Facts and Figures data are from 2018.
- Data cover US municipal solid waste generation and management pathways, with methodology documents maintained separately.

R0.4 does not mirror the EPA tables. It provides source metadata plus a generic snapshot/provenance layer so later adapters can ingest specific tables while retaining hashes and retrieval dates.

## OAK rule

```text
URL != provenance
hash != truth
catalog entry != dataset validation
one dataset != causal evidence
```

Every empirical adapter must preserve source, retrieval time, schema, units, upstream revision information, license/terms when known, and a canonical content hash.
