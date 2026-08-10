# Ω-RECYCLE-T∞ — Structure-Preserving Recycling Lab

R0.6 turns the R0.5 source-aware kernel into an externally challenged circular-flow laboratory. The internal directed/time-expanded optimizers are cross-checked against SciPy/HiGHS, shared capacities can couple multiple materials in one fractional LP, temporal holdouts preserve baseline wins, and a read-only CI lane acquires live Eurostat/EPA content into hash-addressed evidence manifests.

Core law:

> Prefer the recovery path that destroys the least useful structure while producing the most future value, subject to measured cost, energy, risk, uncertainty, safety, physical constraints and explicit evidence boundaries.

## R0.6 pipeline

```text
ResourceGraph + passports
 -> route/baseline courts
 -> exact oracle <-> branch-and-bound
 -> calibration + temporal holdout
 -> symbiosis regret
 -> directed/time-expanded internal flow <-> SciPy/HiGHS
 -> shared-capacity fractional multi-commodity LP
 -> Eurostat/EPA source contracts + revision detection
 -> read-only live HTTP manifest (hash / ETag / Last-Modified)
 -> unit ontology + governed LCIA method descriptor
 -> OAK + M- + CI evidence
```

## New in R0.6

- independent SciPy/HiGHS cross-checks for directed and time-expanded flow;
- fractional multi-commodity optimization with shared arc capacities;
- temporal holdout scoring with a retained case where a persistence baseline beats Ω;
- minimal mass/energy unit ontology and incompatibility rejection;
- LCIA method governance requiring version, publisher, HTTPS source and factor-set hash;
- allowlisted, read-only live acquisition from Eurostat and US EPA;
- live manifest records for SHA256, HTTP status, content type, ETag and Last-Modified;
- dedicated weekly/manual/PR live-evidence workflow that uploads artifacts and never writes to the repository;
- CLI `omega-recycle evidence-r06`;
- CPython 3.11–3.13 courts retaining R0.3–R0.5 contracts.

## First live evidence run

Run `31412921771` acquired both configured public sources successfully (`success_count=2`, `failure_count=0`). The artifact `omega-recycle-r06-live-manifest` has artifact ID `9072280694` and archive digest `sha256:803bafc89f979011044641cd7c430a1336587999e7edf6b4e890c8961dda41be`.

The Eurostat response was JSON (3,677 bytes) with content SHA256 `f3fa4ef25f83227fe9fa26014fbf3819c9faca9154df142c0c9f43f4efe4d069`. The EPA response was HTML (65,422 bytes) with content SHA256 `6c413ec9c38ca99c07f74185117b4ce01cdf3fb4cfe16b0b89a19d2a44c73224`.

These hashes prove only the identity of retrieved HTTP content at that run.

## Permanent M- evidence

1. Greedy symbiosis can recover 1 unit where exact matching recovers 2.
2. A declared baseline can beat canonical Ω on held-out RMSE.
3. Two separately feasible material flows cannot each consume the full capacity of one shared bottleneck; R0.6 has a 1.5-unit shared-capacity court that rejects an invalid total flow of 2.

## Run

```bash
cd omega_recycle_t
python -m pip install -e ".[evidence]"
python -m omega_recycle oakbench
python -m omega_recycle evidence-r05
python -m omega_recycle evidence-r06
pytest -q
```

## Truth boundaries

- SciPy/HiGHS agreement is independent software evidence, not formal proof.
- Multi-commodity optimality is for the declared continuous/fractional LP only; integer/process/chemistry coupling is outside the certificate.
- Live hashes are provenance evidence, not semantic or factual certification.
- Temporal holdout scores supplied predictions; it does not train a model or establish causality.
- The unit ontology is intentionally small and must reject unsupported dimensions rather than guess.
- No recognized/proprietary LCIA factor set is bundled; method descriptors do not certify LCA conclusions.
- No environmental-superiority, profitability, regulatory-compliance or hazardous-processing claim is authorized.

## Promotion path

```text
R0.6 D-MVP++++ candidate
 -> R0.7 repeated live manifests + revision history
       + independent large-instance solver campaigns
       + integer/process-coupled multi-commodity models
       + real battery/electronics/building temporal campaigns
 -> R1.0 externally benchmarked decision engine
```

See `docs/DCT_OMEGA_CARD.md`, `docs/R06_EVIDENCE.md`, `docs/PUBLIC_DATASETS.md`, `docs/ARCHITECTURE.md` and `docs/M_MINUS.md`.
