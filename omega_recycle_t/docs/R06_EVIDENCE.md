# R0.6 Evidence Court — Ω-RECYCLE-T∞

R0.6 promotes no sustainability or industrial-superiority claim. It adds independent software, coupled-capacity and live-provenance courts.

## Court A — directed flow parallax

The internal finite directed min-cost maximum-flow engine is solved again as a lexicographic LP using `scipy.optimize.linprog(method="highs")`. R0.6 requires equal maximum flow and equal minimum cost within tolerance.

Status: PASS on CPython 3.11, 3.12 and 3.13 for PR #412 code head `76f5c48c921901f1320ee97e3af4ab090715030d`.

## Court B — time-expanded parallax

The time-expanded network is independently expanded to a directed LP, including holdover arcs, and cross-checked against HiGHS.

Status: PASS on CPython 3.11, 3.12 and 3.13.

## Court C — shared-capacity multi-commodity

Two commodities each request 1 unit, but one shared bottleneck has capacity 1.5. Independent per-commodity solutions could incorrectly imply total flow 2. The joint fractional LP enforces

```text
sum_k x[k, arc] <= capacity[arc]
```

and returns total flow 1.5. This is a permanent M- guard against capacity double-counting.

## Court D — temporal holdout

Prediction cases are split by a predeclared period. R0.6 retains a held-out fixture where the persistence baseline beats the canonical Ω predictions. The harness must report that loss rather than tune it away.

## Court E — live public-source identity

Workflow run `31412921771` completed successfully with contents-read permissions. It acquired two allowlisted HTTPS sources and uploaded artifact `9072280694`.

Observed manifest:

```text
success_count = 2
failure_count = 0
Eurostat: HTTP 200, application/json, 3,677 bytes,
  sha256=f3fa4ef25f83227fe9fa26014fbf3819c9faca9154df142c0c9f43f4efe4d069
EPA: HTTP 200, text/html; charset=UTF-8, 65,422 bytes,
  sha256=6c413ec9c38ca99c07f74185117b4ce01cdf3fb4cfe16b0b89a19d2a44c73224
artifact zip digest=803bafc89f979011044641cd7c430a1336587999e7edf6b4e890c8961dda41be
```

The live workflow does not commit, push or modify canon. Availability failures are recorded as evidence rather than silently reclassified as source revisions.

## Court F — unit and LCIA governance

The unit ontology converts only declared compatible dimensions. LCIA method descriptors require version, publisher, HTTPS source URL and a 64-hex factor-set hash. Unknown units fail closed.

## Claim boundary

```text
solver agreement != proof
LP optimum != industrial optimum outside the declared model
HTTP hash != truth
holdout score != causal validation
method descriptor != LCA certification
```
