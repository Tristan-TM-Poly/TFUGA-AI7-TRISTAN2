# Public data source contracts — Ω-RECYCLE-T∞ R0.5

Verified 2026-08-10. This file records source contracts and evidence boundaries; it does not claim that upstream data are immutable or universally comparable.

## Eurostat `env_wasmun`

- Publisher: Eurostat
- Dataset: Municipal waste by waste management operations
- Online code: `env_wasmun`
- DOI: `10.2908/env_wasmun`
- Data-browser source: `https://ec.europa.eu/eurostat/databrowser/view/env_wasmun/default/table?lang=en`
- Coverage observed at verification: 1995–2024
- R0.5 adapter: Eurostat TSV parser plus `env_wasmun` contract.

The adapter retains raw dimension codes, time period, numeric value/missingness and observation status flags. The `env_wasmun` adapter requires at least `geo`, `unit` and `wst_oper`. Known unit normalization currently includes `KG_HAB -> kg_per_capita`, `THS_T -> thousand_tonnes`, and `T -> tonnes` while retaining the original unit code.

This is schema validation, not a claim that countries, years or methods are automatically comparable.

## US EPA SMM Facts and Figures

- Publisher: US Environmental Protection Agency
- Series: Advancing Sustainable Materials Management: Facts and Figures
- Source: `https://www.epa.gov/facts-and-figures-about-materials-waste-and-recycling/advancing-sustainable-materials-management`
- Current national Facts & Figures series identified at verification is through 2018.
- R0.5 adapter: normalized bridge CSV requiring `year`, `material`, `management_pathway`, `short_tons`.

The package performs explicit US-short-ton to metric-tonne conversion with `1 short ton = 0.90718474 metric tonnes`. It intentionally does not pretend that every EPA webpage, spreadsheet or PDF shares one stable machine-readable layout.

## Revision court

Normalized snapshots can be compared by declared key fields. R0.5 records:

- added records;
- removed records;
- modified records;
- structural field-set changes;
- deterministic structural hashes.

A revision report detects change. It does not decide that two revisions are semantically equivalent, methodologically comparable or factually correct.

## OAK rule

```text
URL != provenance
hash != truth
schema match != semantic equivalence
revision detected != revision explained
fixture != live evidence
one dataset != causal evidence
```

Every live empirical acquisition should preserve source, retrieval time, source/version/update metadata, schema, units, flags/codelists, license/terms when known and a canonical content hash.
