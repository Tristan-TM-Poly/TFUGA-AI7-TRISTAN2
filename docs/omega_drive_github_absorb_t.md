# Ω-DRIVE-GITHUB-ABSORB-T — Absorption Google Drive → GitHub de Tristan

**Statut:** architecture canonique + MVP OAK-safe  
**Date:** 2026-07-03  
**Mode par défaut:** `DRY_RUN=true`, aucun push destructif, aucune publication publique, aucune suppression, aucun changement de permissions.

## But

Créer un système capable de prendre des liens Google Drive explicitement autorisés, de les transformer en corpus structuré, puis de les absorber dans GitHub sous forme de manifestes, hypergraphes, chunks, rapports OAK, issues, branches, prototypes et artefacts versionnés.

```text
Google Drive Link
→ Resolve permissions/file IDs
→ Download / inventory
→ Hash + manifest + provenance
→ Extract text/code/PDF/ZIP/docs/images
→ Rosette + INFO² + U² + OAK
→ Build hypergraphs HGFM/CVCD
→ Generate GitHub repo structure
→ Create issues/branches/PR-ready artifacts
→ OAK report + rollback ledger
```

## Modules canoniques

### 1. DriveLinkResolver-T

Détecte et normalise :

```text
drive.google.com/file/d/...
drive.google.com/drive/folders/...
docs.google.com/document/d/...
docs.google.com/spreadsheets/d/...
docs.google.com/presentation/d/...
```

Sortie minimale :

```yaml
drive_object:
  url: ...
  file_id: ...
  type: file | folder | doc | sheet | slides | zip | pdf | unknown
  owner_visibility: unknown | private | shared | public
  requires_oauth: true
  risk_level: low | medium | high
```

### 2. PermissionGate-T

Règle stricte :

```text
Aucun téléchargement, partage public, push GitHub public,
suppression, changement de permissions ou publication
sans consentement explicite + rapport OAK.
```

Niveaux :

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

### 3. DriveDownloader-T

Téléchargements supportés : PDF, ZIP, DOCX, Google Docs exportés, Sheets exportées, Slides exportées, images, code archives.

Gère : quotas, retry, checksum, gros fichiers, doublons, liens cassés, permissions insuffisantes.

### 4. ManifestBuilder-T

Chaque fichier devient une preuve traçable.

```json
{
  "source_url": "google_drive_link",
  "drive_file_id": "...",
  "name": "...",
  "mime_type": "...",
  "size_bytes": 123456,
  "sha256": "...",
  "downloaded_at": "...",
  "extraction_method": "rosette_v1",
  "oak_status": "pending",
  "github_target": "repo/path"
}
```

Principe : pas de contenu absorbé sans provenance, pas de provenance sans hash, pas de hash sans statut OAK.

### 5. RosetteDriveExtractor-T

Transforme les corpus massifs :

```text
PDF → pages → texte → équations → figures → tableaux → claims
ZIP → manifest → sous-fichiers → extraction récursive
Docs → Markdown propre
Slides → texte + images + structure
Sheets → tables + schémas + données
Images → métadonnées + description prudente
```

Chaque chunk conserve : fichier source, page, bbox si disponible, méthode d’extraction, score de confiance, incertitude U², risques M⁻.

### 6. HypergraphBuilder-T

Nœuds : fichiers, pages, concepts, équations, figures, claims, preuves, prototypes, dépôts GitHub, issues, branches, commits, risques, liens, auteurs, versions.

Hyperarêtes : contient, dérive_de, prouve_partiellement, contredit, implémente, nécessite_test, lié_à_GitHub, risque_IP, à_prototyper.

### 7. GitHubSyncPlanner-T

Prépare le transfert sans agir dangereusement :

```text
repo/
  README.md
  manifest/drive_manifest.json
  manifest/provenance_ledger.jsonl
  corpus/raw_index.md
  corpus/extracted_chunks.jsonl
  hypergraphs/theory_graph.json
  hypergraphs/claim_evidence_graph.json
  oak/oak_report.md
  oak/security_report.md
  oak/ip_report.md
  issues/generated_issues.md
  prototypes/package_skeleton/
```

### 8. RepoWriter-T

Écrit seulement dans des zones sûres : branches dédiées, dossiers generated/, commits identifiables, pas d’écrasement sans diff, pas de secrets, pas de fichiers sensibles publics.

### 9. IssuePRGenerator-T

Transforme les découvertes en issues : extraction PDF, vérification OAK, prototype, mémoire négative M⁻, revue IP, benchmark.

### 10. OAKDriveSecurityScanner-T

Détecte secrets API, tokens, mots de passe, données personnelles, documents sensibles, licences floues, contenu brevetable, fichiers propriétaires, liens publics dangereux, doublons et fichiers corrompus.

Verdicts : `ALLOW_PRIVATE_SYNC`, `ALLOW_BRANCH_ONLY`, `REQUIRES_REDACTION`, `REQUIRES_IP_REVIEW`, `BLOCK_PUBLICATION`, `BLOCK_DOWNLOAD`.

## Architecture cible

```text
Ω-DRIVE-GITHUB-ABSORB-T
│
├── input/
│   ├── drive_links.txt
│   └── permissions_policy.yaml
│
├── resolver/
│   └── drive_link_resolver.py
│
├── downloader/
│   └── drive_downloader.py
│
├── extraction/
│   ├── rosette_pdf_extractor.py
│   ├── zip_ingestor.py
│   ├── docs_exporter.py
│   └── table_extractor.py
│
├── graph/
│   ├── hypergraph_builder.py
│   ├── claim_evidence_graph.py
│   └── info2_provenance_graph.py
│
├── github/
│   ├── sync_planner.py
│   ├── repo_writer.py
│   ├── issue_generator.py
│   └── pr_generator.py
│
├── oak/
│   ├── permission_gate.py
│   ├── security_scanner.py
│   ├── ip_gate.py
│   └── oak_reporter.py
│
└── ledgers/
    ├── provenance_ledger.jsonl
    ├── rollback_ledger.jsonl
    └── m_minus_drive_errors.jsonl
```

## Règle OAK centrale

```text
Un lien Google Drive n’est pas une permission totale.
Un fichier téléchargé n’est pas une vérité.
Une extraction n’est pas une preuve.
Un hypergraphe n’est pas une validation.
Un push GitHub n’est jamais automatique sans verrou OAK.
```

## Commande future idéale

```bash
omega-drive-github absorb drive_links.txt \
  --repo Tristan/omega-corpus \
  --mode dry-run \
  --extract pdf,zip,docs \
  --oak strict \
  --github-plan issues-and-branch
```

## Pont canonique

```text
Drive = matière brute privée
Rosette = digestion
HGFM/CVCD = compression intelligente
OAK = sécurité/vérité/risque
GitHub = exécution/prototype/versionnement
```
