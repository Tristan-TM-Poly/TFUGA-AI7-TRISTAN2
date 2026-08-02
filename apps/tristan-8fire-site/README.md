# Tristan Web OS R0.1

Static-first public interface for the Tristan corpus.

## Purpose

The site exposes a navigable path from ideas to evidence:

```text
idea -> theory -> claim -> evidence -> code -> test -> prototype -> use
```

It deliberately separates vision, hypothesis, architecture, prototype, tested result, and product state. OAK scores are provisional navigation signals, not truth probabilities.

## Run locally

```bash
cd apps/tristan-8fire-site
python -m http.server 8080
```

Open `http://localhost:8080`.

## Validate

From the repository root:

```bash
python -m pytest tests/test_tristan_web_os.py
```

## Files

- `index.html`: semantic single-page shell.
- `styles.css`: responsive accessible visual system.
- `app.js`: atlas rendering, filters, proof metrics, and detail panels.
- `data/theories.json`: public theory cards with OAK-safe epistemic states.

## Publication gates

No content should become public unless it clears:

```text
OAKGate AND IPGate AND PrivacyGate AND SecurityGate
```

Private notes, unprotected inventions, personal data, and unsupported claims remain outside the public dataset.

## R0.2 targets

- generate cards from canonical repository schemas;
- link cards to exact claims, tests, commits, and benchmarks;
- add bilingual canonical content;
- expose a read-only knowledge graph;
- add deploy preview and accessibility checks.
