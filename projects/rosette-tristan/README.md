# Ω-ROSETTE-T / Rosette-Tristan

AIT local et OAK-safe pour transformer des PDF ou textes scientifiques en Markdown/JSON, fragments LaTeX, graphe théorie/claims, squelette de code, capsule d’absorption et rapport OAK.

> Axiome : OCR ≠ vérité. Résumé ≠ preuve. Code compilé ≠ modèle validé. Ressemblance LaTeX ≠ équivalence mathématique.

## Quickstart

```bash
pip install -e .[dev]
rosette compile examples/sample_paper.txt --out out --mode strict
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
```

## Pipeline

```text
PDF/TXT → Ingest → Extract → LaTeX Forge → Theory Graph → Code Forge → Absorption → OAK Report
```

## Statuts OAK

- `certified`: source + score élevé + vérifications réussies
- `usable`: utile mais à vérifier
- `uncertain`: ambigu, garder en M⁻
- `failed`: non fiable ou non reproductible

## Zéro-touch / IP

Ce dossier est ajouté dans le monorepo sous `projects/rosette-tristan/` pour isoler l’expérience. Avant toute publication externe ou usage commercial, vérifier licence, citations, droits d’auteur et brevetabilité.
