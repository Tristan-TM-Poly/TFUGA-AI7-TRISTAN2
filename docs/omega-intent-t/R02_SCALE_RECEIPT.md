# Ω-INTENT-TO-EVERYTHING-T∞ R0.2 — Local Scale Receipt

## Status

This receipt records finite local software experiments performed before
publication of R0.2. It is not a universal performance guarantee. CI hardware,
filesystem, Python, SQLite and repository load can produce different results.

## Initial negative result

The original per-record transaction path did not finish a 100,000-record run
inside the initial 120-second experiment window.

```text
M⁻ R0.2-001
cause: multiple SQLite transactions per work unit
correction: atomic batch terminalization
claim boundary: implementation bottleneck, not a fundamental SQLite limit
```

## Corrected 100k experiment

```text
records consumed:     100,000
validated:              99,900
rejected fixture:          100
executor failures:            0
adaptive batches:             11
checkpoint offset:       100,000
ledger work records:     100,000
ledger events:           100,012
final item budget:        56,240
elapsed wall time:          9.25 s
```

The deterministic negative fixture rejects offsets divisible by 997. These are
intentional test outcomes, not infrastructure failures.

## Corrected 250k experiment

```text
records consumed:     250,000
validated:             249,750
rejected fixture:          250
executor failures:            0
adaptive batches:             13
checkpoint offset:       250,000
ledger work records:     250,000
ledger events:           250,014
final item budget:       143,974
elapsed wall time:         19.30 s
SQLite main file:          202.2 MB
```

## Interpretation

The experiment demonstrates that this implementation can persist and audit a
finite 250k synthetic campaign on the local validation environment. It does not
show that every 250k-unit real campaign will fit the same time or storage, nor
that the generated units are valuable. Real workloads must include their own
executor cost, tests, artifacts, provider limits, review capacity and risk
gates.

## M⁺ candidate

```text
M⁺ R0.2-001
intervention: atomic terminalization per adaptive batch
observed effect: 100k campaign completed in 9.25 s after previous timeout
status: local finite software result; requires CI and independent repetition
```
