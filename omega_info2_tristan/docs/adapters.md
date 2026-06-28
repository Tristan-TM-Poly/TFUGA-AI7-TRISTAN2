# Ω-INFO²-T Adapters

This document describes the non-mutating adapter layer added after the MVP+ core.

## Rosette adapter

`rosette_adapter.py` converts a Rosette-Tristan PDF extraction payload into an OAK-safe `InfoObject`.

It preserves:

- document id,
- PDF source path,
- page number,
- bounding box,
- extraction method,
- extraction confidence,
- claims,
- concepts,
- equations,
- table and figure residue.

Important OAK rule: a Rosette extraction is not truth. It is parsed information that still needs source-page verification, evidence linking, counter-evidence search, and OAK validation.

## GitHub task draft exporter

`github_issue_exporter.py` renders an `InfoObject` route as a reviewable GitHub task draft.

It prepares:

- title,
- markdown body,
- labels,
- route,
- OAK status,
- scores,
- claims,
- failed checks,
- residue.

It does not publish anything by itself. This protects ZERO-TOUCH from becoming zero-control.

## Safe workflow

```text
Rosette PDF extraction
→ InfoObject
→ Bayes-Tristan update
→ CVCD invariants + residue
→ OAKInfoGate
→ InfoRouter
→ MMinusRegistry
→ Info2Graph
→ GitHub task draft
```

## Next adapter targets

- `rosette_json_loader.py` for loading extraction JSON.
- `github_connector_submitter.py` for explicit, human-approved task creation.
- `drive_manifest_adapter.py` for Drive file manifests.
- `patent_prior_art_adapter.py` for IP-sensitive prior-art routing.
