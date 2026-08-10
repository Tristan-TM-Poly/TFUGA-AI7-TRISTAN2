# Public data source contracts — Ω-RECYCLE-T∞ R0.6

Verified/observed 2026-08-10. Source contracts, static anchors and live HTTP manifests are distinct evidence classes.

## Eurostat `env_wasmun`

- dataset code: `env_wasmun`
- DOI: `10.2908/env_wasmun`
- R0.5 contract retains dimensions, time, values/missingness, status flags and raw unit codes.
- R0.6 live spec requests the EU27 aggregate with the two latest periods through Eurostat's Statistics API.

First R0.6 live run: HTTP 200, JSON, 3,677 bytes, SHA256 `f3fa4ef25f83227fe9fa26014fbf3819c9faca9154df142c0c9f43f4efe4d069`.

## US EPA SMM Facts and Figures

- publisher: US EPA
- R0.5 normalized bridge remains the machine-contract layer for parsed table data.
- R0.6 live spec hashes the official Facts & Figures landing page instead of pretending every table/PDF/XLS shares one stable schema.

First R0.6 live run: HTTP 200, HTML, 65,422 bytes, SHA256 `6c413ec9c38ca99c07f74185117b4ce01cdf3fb4cfe16b0b89a19d2a44c73224`; ETag and Last-Modified were recorded by the manifest.

## Evidence classes

```text
SourceAnchor = manually web-verified dated descriptor
DatasetSnapshot = normalized parsed records + deterministic record hash
LiveSnapshot = raw HTTP content identity + retrieval metadata
RevisionReport = normalized record/schema change signal
```

These are intentionally not interchangeable.

## First live artifact

- workflow run: `31412921771`
- artifact ID: `9072280694`
- artifact archive SHA256: `803bafc89f979011044641cd7c430a1336587999e7edf6b4e890c8961dda41be`
- success count: 2
- failure count: 0

## OAK rule

```text
URL != provenance
HTTP 200 != factual truth
hash != semantic correctness
schema match != comparability
revision detected != revision explained
one successful live run != availability guarantee
one dataset != causal evidence
```
