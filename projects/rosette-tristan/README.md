# Ω-ROSETTE-T / Rosette-Tristan

AIT local et OAK-safe pour transformer des PDF ou textes scientifiques en Markdown/JSON, fragments LaTeX, graphe théorie/claims, squelette de code, capsule d’absorption et rapport OAK.

> Axiome : OCR ≠ vérité. Résumé ≠ preuve. Code compilé ≠ modèle validé. Ressemblance LaTeX ≠ équivalence mathématique.

## Quickstart

```bash
pip install -e .[dev]
rosette compile examples/sample_paper.txt --out out --mode strict
rosette-fidelity examples/sample_paper.txt --out out_fidelity
pytest -q
```

## Sorties générées

```text
out/
  document.md
  document.json
  equations.tex
  theory_graph.json
  code/equations.py
  absorption.md
  OAK_REPORT.md
  M_MINUS.md

out_fidelity/
  source_refs.json
  fidelity_report.json
  theory_capsule.yaml
```

## Pipeline

```text
PDF/TXT → Ingest → Extract → SourceRefs/BBox → ConfidenceTensor → LaTeX Forge → Theory Capsule → OAK Report
```

## Rosette Fidelity

`rosette-fidelity` ajoute une couche de traçabilité :

- `SourceRef` avec chemin, page, span, bbox optionnelle, extracteur et méthode;
- `BBox` compatible PDF quand PyMuPDF expose des blocs;
- `ConfidenceTensor` text/layout/math/table/figure/citation/code/theory/reproduction;
- `source_refs.json` pour relier chaque artefact à sa région source;
- `fidelity_report.json` pour compter pages, bboxes, spans, extracteurs et statuts OAK;
- `theory_capsule.yaml` comme capsule théorie exploitable par HGFM/CVCD/OAK.

Pour fichiers texte de test, les pages peuvent être simulées par :

```text
---PAGE 1---
...
---PAGE 2---
...
```

## Statuts OAK

- `certified`: source + score élevé + vérifications réussies
- `usable`: utile mais à vérifier
- `uncertain`: ambigu, garder en M⁻
- `failed`: non fiable ou non reproductible

## Documents produits

- [`ROADMAP.md`](ROADMAP.md) : phases Rosette Fidelity, Theory Compiler, Code/Reproduction, RosetteBench et IP/Productization.
- [`docs/OAK_SPEC.md`](docs/OAK_SPEC.md) : axiomes et gates OAK minimaux.
- [`docs/ROSETTEBENCH.md`](docs/ROSETTEBENCH.md) : familles de benchmarks, métriques et acceptance gates.

## Zéro-touch / IP

Ce dossier est ajouté dans le monorepo sous `projects/rosette-tristan/` pour isoler l’expérience. Avant toute publication externe ou usage commercial, vérifier licence, citations, droits d’auteur et brevetabilité.
