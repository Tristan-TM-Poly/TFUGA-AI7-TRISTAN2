# Prototype — Ω-DRIVE-GITHUB-ABSORB-T

Ce dossier contient le MVP OAK-safe pour absorber des liens Google Drive vers GitHub sans action dangereuse par défaut.

## Usage dry-run

Version script autonome :

```bash
python prototypes/omega_drive_github_absorb/omega_drive_github_absorb.py input/drive_links.txt \
  --repo Tristan-TM-Poly/TFUGA-AI7-TRISTAN2 \
  --level L1 \
  --out generated/omega_drive_github_absorb
```

Version package réutilisable :

```bash
PYTHONPATH=prototypes/omega_drive_github_absorb \
python -m omega_drive_github_absorb examples/drive_links.example.txt \
  --repo Tristan-TM-Poly/TFUGA-AI7-TRISTAN2 \
  --level L1 \
  --max-level L1 \
  --out generated/omega_drive_github_absorb
```

Sorties générées localement :

```text
generated/omega_drive_github_absorb/
  drive_manifest.json
  github_sync_plan.json
  theory_seed_hypergraph.json
  oak_report.json
```

## Niveaux OAK

```text
L0 inventory only
L1 metadata + manifest
L2 download private
L3 extract
L4 generate repo locally
L5 create GitHub branch/issues
L6 PR ready
L7 public release — verrouillé par défaut
```

## Ce que le MVP fait déjà

- Résout les formats de liens Drive, Google Docs, Sheets et Slides.
- Produit un `drive_manifest.json` traçable.
- Produit un plan de synchronisation GitHub.
- Produit un hypergraphe initial `theory_seed_hypergraph.json`.
- Ajoute un scanner OAK léger pour repérer les formats inconnus et signaux sensibles dans les URLs.
- Bloque par défaut les actions dangereuses.
- Crée une base pour ajouter OAuth Drive, extraction Rosette, hypergraphes HGFM/CVCD et rapports OAK.

## Ce que le MVP refuse par défaut

- Télécharger sans consentement/OAuth explicite.
- Pousser dans la branche principale.
- Publier publiquement du contenu Drive.
- Supprimer des fichiers.
- Changer des permissions Drive.
- Ignorer les risques IP/confidentialité.

## Structure ajoutée

```text
omega_drive_github_absorb/
  __init__.py
  __main__.py
  cli.py
  core.py
schemas/
  drive_manifest.schema.json
  theory_seed_hypergraph.schema.json
examples/
  drive_links.example.txt
tests/
  test_core.py
```

## Principe anti-fuite

Ne jamais committer de vrais liens Drive privés dans un dépôt public. Les vrais liens doivent rester dans un fichier local ignoré, un secret manager, ou un environnement privé contrôlé par OAuth readonly.

## Prochaine couche

1. Ajouter OAuth Google Drive à moindre privilège.
2. Ajouter téléchargement privé L2 avec sha256 réel.
3. Ajouter extraction PDF/ZIP/DOCX.
4. Ajouter `chunks.jsonl` avec provenance page/bbox.
5. Ajouter hypergraphe `theory_graph.json`.
6. Ajouter scanner secrets/IP sur contenu téléchargé.
7. Générer issues/PR en brouillon seulement.
